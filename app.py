from flask import Flask, request, render_template_string, send_file
import cv2
import os
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Passport Tool</title>

<style>
body {
    margin:0;
    font-family:Arial;
    background: linear-gradient(135deg,#667eea,#764ba2);
    color:white;
    transition:0.3s;
}

/* DARK MODE */
.dark {
    background:#111;
    color:#eee;
}

/* NAVBAR */
.navbar {
    display:flex;
    justify-content:space-between;
    padding:15px;
    background:rgba(0,0,0,0.3);
}

.navbar a {
    color:white;
    margin:0 10px;
    text-decoration:none;
}

/* CONTAINER */
.container {
    max-width:400px;
    margin:30px auto;
    padding:20px;
    background:rgba(255,255,255,0.1);
    border-radius:15px;
    text-align:center;
}

/* UPLOAD BOX */
.upload-box {
    border:2px dashed #ccc;
    padding:20px;
    border-radius:10px;
    cursor:pointer;
}

/* INPUT */
input, select {
    width:100%;
    padding:10px;
    margin:10px 0;
    border-radius:8px;
    border:none;
}

/* BUTTON */
button {
    width:100%;
    padding:12px;
    background:#ff758c;
    border:none;
    border-radius:10px;
    color:white;
    margin-top:10px;
}

/* PREVIEW */
img {
    max-width:100%;
    margin-top:10px;
    border-radius:10px;
}

/* LOADER */
.loader {
    display:none;
    border:5px solid #f3f3f3;
    border-top:5px solid #ff758c;
    border-radius:50%;
    width:40px;
    height:40px;
    animation:spin 1s linear infinite;
    margin:20px auto;
}

@keyframes spin {
    0% { transform:rotate(0deg); }
    100% { transform:rotate(360deg); }
}

/* PROGRESS BAR */
.progress {
    width:100%;
    background:#ddd;
    border-radius:10px;
    overflow:hidden;
    display:none;
}

.progress-bar {
    height:10px;
    width:0%;
    background:#ff758c;
}

</style>
</head>

<body>

<div class="navbar">
    <div>🔥 Passport Tool</div>
    <div>
        <a href="#">Home</a>
        <a href="#">Tools</a>
        <button onclick="toggleTheme()">🌙</button>
    </div>
</div>

<div class="container">

<h2>Make Passport Size Photo</h2>

<form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">

<div class="upload-box" onclick="fileInput.click()">
    <p>Select or Drag Image</p>
    <input type="file" name="file" id="fileInput" hidden required onchange="previewImage(event)">
</div>

<img id="preview" style="display:none">

<label>Photos</label>
<input type="number" name="count" value="8">

<label>Download Type</label>
<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select>

<label>
<input type="checkbox" name="removebg"> Remove Background
</label>

<button type="submit">Generate</button>

<div class="loader" id="loader"></div>

<div class="progress" id="progress">
    <div class="progress-bar" id="bar"></div>
</div>

</form>

</div>

<script>

// PREVIEW
function previewImage(event) {
    const img = document.getElementById('preview');
    img.src = URL.createObjectURL(event.target.files[0]);
    img.style.display = "block";
}

// LOADER + PROGRESS
function showLoader() {
    document.getElementById("loader").style.display = "block";
    document.getElementById("progress").style.display = "block";

    let bar = document.getElementById("bar");
    let width = 0;
    let interval = setInterval(() => {
        width += 10;
        bar.style.width = width + "%";
        if (width >= 100) clearInterval(interval);
    }, 200);
}

// DARK MODE
function toggleTheme() {
    document.body.classList.toggle("dark");
}

</script>

</body>
</html>
'''

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        file = request.files['file']
        count = int(request.form.get("count"))
        filetype = request.form.get("type")
        remove_bg = request.form.get("removebg")

        file.save("input.jpg")
        img = cv2.imread("input.jpg")

        # REMOVE BG (simple white bg)
        if remove_bg:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            bg = np.ones_like(img) * 255
            img = np.where(mask[:,:,None]==255, img, bg)

        h, w, _ = img.shape
        face = cv2.resize(img, (413, 531))

        gap = 40
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))

        canvas = np.ones((rows*600, cols*500, 3), dtype=np.uint8)*255

        i = 0
        for r in range(rows):
            for c in range(cols):
                if i >= count:
                    break
                y = r*600
                x = c*500
                canvas[y:y+531, x:x+413] = face
                i += 1

        os.makedirs("static", exist_ok=True)
        img_path = "static/output.jpg"
        cv2.imwrite(img_path, canvas)

        if filetype == "pdf":
            pdf_path = "static/output.pdf"
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = [RLImage(img_path, width=500, height=700)]
            doc.build(elements)
            return send_file(pdf_path, as_attachment=True)

        return send_file(img_path, as_attachment=True)

    return render_template_string(HTML)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
