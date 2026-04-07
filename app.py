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
<title>AI Image Tool</title>

<link href="https://unpkg.com/cropperjs/dist/cropper.min.css" rel="stylesheet"/>
<script src="https://unpkg.com/cropperjs"></script>

<style>
body {
    margin:0;
    font-family:Arial;
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
    padding:8px 15px;
    border:none;
    border-radius:8px;
    cursor:pointer;
}

/* CARD */
.card {
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
    border:none;
    border-radius:8px;
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

/* PREVIEW SMALL */
.preview {
    max-width:120px;
    margin-top:10px;
    border-radius:10px;
}

/* CROP IMAGE */
#cropImage {
    max-width:100%;
}
</style>
</head>

<body>

<div class="navbar">
    <div>🔥 AI Image Tool</div>
    <div>
        <button onclick="showPage('passport')">Passport</button>
        <button onclick="showPage('crop')">Crop</button>
    </div>
</div>

<!-- PASSPORT -->
<div id="passport" class="card">
<h2>Passport Photo</h2>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="tool" value="passport">

<input type="file" name="file" required onchange="previewImage(event)">
<img id="preview" class="preview" style="display:none">

<input type="number" name="count" value="8">

<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select>

<label>
<input type="checkbox" name="removebg"> Remove Background
</label>

<button class="submit">Generate</button>
</form>
</div>

<!-- CROP TOOL -->
<div id="crop" class="card" style="display:none;">
<h2>Crop Image</h2>

<input type="file" id="cropInput">
<br><br>

<img id="cropImage">

<br><br>

<button class="submit" onclick="cropImage()">Crop & Download</button>
</div>

<script>
function showPage(p){
    document.getElementById("passport").style.display="none";
    document.getElementById("crop").style.display="none";
    document.getElementById(p).style.display="block";
}

function previewImage(event){
    let img = document.getElementById("preview");
    img.src = URL.createObjectURL(event.target.files[0]);
    img.style.display="block";
}

/* CROP JS */
let cropper;

document.getElementById("cropInput").addEventListener("change", function(e){
    const file = e.target.files[0];
    const img = document.getElementById("cropImage");

    img.src = URL.createObjectURL(file);

    if(cropper) cropper.destroy();

    cropper = new Cropper(img, {
        viewMode:1,
        zoomable:true,
        movable:true
    });
});

function cropImage(){
    const canvas = cropper.getCroppedCanvas();
    canvas.toBlob(function(blob){
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "crop.jpg";
        a.click();
    });
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

        file.save("input.jpg")
        img = cv2.imread("input.jpg")

        if tool == "passport":
            count = int(request.form.get("count"))
            filetype = request.form.get("type")
            removebg = request.form.get("removebg")

            # REMOVE BG (simple white)
            if removebg:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                img[mask==255] = [255,255,255]

            face = cv2.resize(img, (413,531))

            canvas = np.ones((1200,1000,3), dtype=np.uint8)*255

            i=0
            for r in range(3):
                for c in range(3):
                    if i>=count: break

                    y=r*400
                    x=c*350

                    bordered = cv2.copyMakeBorder(
                        face,5,5,5,5,
                        cv2.BORDER_CONSTANT,value=[0,0,0]
                    )

                    canvas[y:y+541, x:x+423] = bordered
                    i+=1

            os.makedirs("static", exist_ok=True)
            img_path="static/output.jpg"
            cv2.imwrite(img_path, canvas)

            if filetype=="pdf":
                pdf_path="static/output.pdf"
                doc=SimpleDocTemplate(pdf_path,pagesize=A4)
                doc.build([RLImage(img_path,width=500,height=700)])
                return send_file(pdf_path, as_attachment=True)

            return send_file(img_path, as_attachment=True)

    return render_template_string(HTML)


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
