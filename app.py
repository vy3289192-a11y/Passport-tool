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
<title>Snapzo</title>

<style>
body {
    font-family:Arial;
    margin:0;
    background: linear-gradient(135deg,#667eea,#764ba2);
    color:white;
}

/* NAVBAR */
.navbar {
    display:flex;
    justify-content:space-between;
    padding:15px;
    background:rgba(0,0,0,0.3);
}

.navbar button {
    margin:5px;
    padding:8px 15px;
    border:none;
    border-radius:8px;
    cursor:pointer;
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

/* INPUT */
input, select {
    width:100%;
    padding:10px;
    margin:10px 0;
    border-radius:8px;
    border:none;
}

/* BUTTON */
button.submit {
    width:100%;
    padding:12px;
    background:#ff758c;
    border:none;
    border-radius:10px;
    color:white;
}

/* PREVIEW */
img {
    max-width:120px;
    margin-top:10px;
    border-radius:10px;
}
</style>
</head>

<body>

<div class="navbar">
    <div>🔥 Snapzo</div>
    <div>
        <button onclick="showPage('passport')">Passport</button>
        <button onclick="showPage('crop')">Crop</button>
    </div>
</div>

<div class="container">

<!-- PASSPORT -->
<div id="passport">
<h2>Passport Photo</h2>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="tool" value="passport">

<input type="file" name="file" required onchange="previewImage(event)">
<img id="preview" style="display:none">

<input type="number" name="count" value="8">

<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select>

<label>
<input type="checkbox" name="remove_bg"> Remove Background
</label>

<button class="submit" type="submit">Generate</button>
</form>
</div>

<!-- CROP -->
<div id="crop" style="display:none;">
<h2>Crop Image</h2>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="tool" value="crop">

<input type="file" name="file" required>

<input type="number" name="x" placeholder="Start X">
<input type="number" name="y" placeholder="Start Y">
<input type="number" name="w" placeholder="Width">
<input type="number" name="h" placeholder="Height">

<button class="submit" type="submit">Crop</button>
</form>
</div>

</div>

<script>
function showPage(page){
    document.getElementById("passport").style.display = "none";
    document.getElementById("crop").style.display = "none";
    document.getElementById(page).style.display = "block";
}

function previewImage(event){
    const img = document.getElementById("preview");
    img.src = URL.createObjectURL(event.target.files[0]);
    img.style.display = "block";
}
</script>

</body>
</html>
'''

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        tool = request.form.get("tool")
        file = request.files['file']

        os.makedirs("static", exist_ok=True)

        file_path = "static/input.jpg"
        file.save(file_path)

        img = cv2.imread(file_path)

        if img is None:
            return "Error loading image"

        # 🔥 PASSPORT
        if tool == "passport":
            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")
            remove_bg = request.form.get("remove_bg")

            # resize
            face = cv2.resize(img, (413, 531))

            # REMOVE BG (simple white replace)
            if remove_bg:
                gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
                face[mask == 255] = [255,255,255]

            canvas = np.ones((1200, 1000, 3), dtype=np.uint8) * 255

            i = 0
            for r in range(3):
                for c in range(3):
                    if i >= count:
                        break

                    y = r * 400
                    x = c * 350

                    bordered = cv2.copyMakeBorder(
                        face,5,5,5,5,
                        cv2.BORDER_CONSTANT,value=[0,0,0]
                    )

                    canvas[y:y+541, x:x+423] = bordered
                    i += 1

            img_path = "static/output.jpg"
            cv2.imwrite(img_path, canvas)

            if filetype == "pdf":
                pdf_path = "static/output.pdf"
                doc = SimpleDocTemplate(pdf_path, pagesize=A4)
                elements = [RLImage(img_path, width=500, height=700)]
                doc.build(elements)
                return send_file(pdf_path, as_attachment=True)

            return send_file(img_path, as_attachment=True)

        # ✂️ CROP
        if tool == "crop":
            try:
                x = int(request.form.get("x", 0))
                y = int(request.form.get("y", 0))
                w = int(request.form.get("w", 100))
                h = int(request.form.get("h", 100))

                crop = img[y:y+h, x:x+w]

                path = "static/crop.jpg"
                cv2.imwrite(path, crop)

                return send_file(path, as_attachment=True)
            except:
                return "Invalid crop values"

    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
