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
}

.container {
    max-width:400px;
    margin:30px auto;
    padding:20px;
    background:rgba(255,255,255,0.1);
    border-radius:15px;
    text-align:center;
}

.upload-box {
    border:2px dashed #ccc;
    padding:20px;
    border-radius:10px;
    cursor:pointer;
}

input, select {
    width:100%;
    padding:10px;
    margin:10px 0;
    border-radius:8px;
    border:none;
}

button {
    width:100%;
    padding:12px;
    background:#ff758c;
    border:none;
    border-radius:10px;
    color:white;
}

/* छोटा preview */
img {
    max-width:150px;
    margin-top:10px;
    border-radius:10px;
    border:2px solid white;
}

/* loader */
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

/* progress */
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

<div class="container">

<h2>Make Passport Size Photo</h2>

<form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">

<div class="upload-box" onclick="fileInput.click()">
    <p>Select Image</p>
    <input type="file" name="file" id="fileInput" hidden required onchange="previewImage(event)">
</div>

<img id="preview" style="display:none">

<input type="number" name="count" value="8">

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
function previewImage(event) {
    const img = document.getElementById('preview');
    img.src = URL.createObjectURL(event.target.files[0]);
    img.style.display = "block";
}

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

        # 🔥 REMOVE BG WORKING
        if remove_bg:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5,5), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            mask = cv2.bitwise_not(thresh)

            white_bg = np.ones_like(img) * 255
            img = np.where(mask[:,:,None]==255, img, white_bg)

        # resize
        face = cv2.resize(img, (413, 531))

        gap = 40
        border = 5

        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))

        cell_w = 413 + gap
        cell_h = 531 + gap

        canvas_w = cols * cell_w + gap
        canvas_h = rows * cell_h + gap

        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

        i = 0
        for r in range(rows):
            for c in range(cols):
                if i >= count:
                    break

                x = gap + c * cell_w
                y = gap + r * cell_h

                bordered = cv2.copyMakeBorder(
                    face, border, border, border, border,
                    cv2.BORDER_CONSTANT, value=[0,0,0]
                )

                h_b, w_b = bordered.shape[:2]
                canvas[y:y+h_b, x:x+w_b] = bordered

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
