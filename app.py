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
<title>Snapzo Pro</title>

<style>
:root {
    --bg:#f5f7fa;
    --card:#ffffff;
    --text:#000;
}

body.dark {
    --bg:#0f172a;
    --card:#1e293b;
    --text:#fff;
}

body {
    margin:0;
    font-family:Arial;
    background:var(--bg);
    color:var(--text);
}

/* NAVBAR */
.navbar {
    display:flex;
    justify-content:space-between;
    padding:15px 20px;
    background:#111827;
    color:white;
}

button {
    cursor:pointer;
}

/* MAIN */
.main {
    text-align:center;
    margin-top:20px;
}

/* CARD */
.card {
    background:var(--card);
    max-width:500px;
    margin:20px auto;
    padding:25px;
    border-radius:15px;
    box-shadow:0 10px 30px rgba(0,0,0,0.1);
}

/* UPLOAD */
.upload {
    border:2px dashed #3b82f6;
    padding:30px;
    border-radius:12px;
}

/* INPUT */
input, select {
    width:100%;
    padding:10px;
    margin-top:10px;
    border-radius:8px;
}

/* PREVIEW */
img {
    max-width:120px;
    margin-top:10px;
    border-radius:10px;
}

/* LOADER */
.loader { display:none; }
.bar {
    width:0%;
    height:8px;
    background:#3b82f6;
    border-radius:5px;
}
</style>
</head>

<body>

<div class="navbar">
    <div>🔥 Snapzo Pro</div>
    <div>
        <button onclick="showPage('passport')">Passport</button>
        <button onclick="showPage('crop')">Crop</button>
        <button onclick="toggleTheme()">🌙</button>
    </div>
</div>

<div class="main">

<!-- PASSPORT -->
<div id="passport" class="card">

<h2>Passport Photo</h2>

<form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
<input type="hidden" name="tool" value="passport">

<div class="upload" onclick="fileInput.click()">
    <p>Click or Drag Image</p>
</div>

<input type="file" name="file" id="fileInput" hidden required>
<img id="preview" style="display:none">

<input type="number" name="count" value="8">

<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select>

<label><input type="checkbox" name="remove_bg"> Remove BG</label>

<button type="submit">Generate</button>

<div class="loader">
<p>Processing...</p>
<div class="bar" id="bar"></div>
</div>

</form>
</div>

<!-- CROP -->
<div id="crop" class="card" style="display:none;">
<h2>Crop Tool</h2>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="tool" value="crop">

<input type="file" name="file" required>

<input type="number" name="x" placeholder="Start X">
<input type="number" name="y" placeholder="Start Y">
<input type="number" name="w" placeholder="Width">
<input type="number" name="h" placeholder="Height">

<button type="submit">Crop</button>
</form>
</div>

</div>

<script>
function showPage(p){
document.getElementById("passport").style.display="none";
document.getElementById("crop").style.display="none";
document.getElementById(p).style.display="block";
}

function toggleTheme(){
document.body.classList.toggle("dark");
}

const fileInput = document.getElementById("fileInput");

fileInput.addEventListener("change", ()=>{
const img = document.getElementById("preview");
img.src = URL.createObjectURL(fileInput.files[0]);
img.style.display="block";
});

function showLoader(){
const bar=document.getElementById("bar");
let w=0;
let i=setInterval(()=>{
w+=10;
bar.style.width=w+"%";
if(w>=100)clearInterval(i);
},200);
}
</script>

</body>
</html>
'''

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':

        tool = request.form.get("tool")

        file = request.files.get('file')
        if not file:
            return "Upload image"

        os.makedirs("static", exist_ok=True)
        path="static/input.jpg"
        file.save(path)

        img=cv2.imread(path)
        if img is None:
            return "Image error"

        # PASSPORT
        if tool=="passport":
            count=int(request.form.get("count",8))
            filetype=request.form.get("type")
            remove_bg=request.form.get("remove_bg")

            face=cv2.resize(img,(413,531))

            if remove_bg:
                gray=cv2.cvtColor(face,cv2.COLOR_BGR2GRAY)
                _,mask=cv2.threshold(gray,240,255,cv2.THRESH_BINARY)
                face[mask==255]=[255,255,255]

            canvas=np.ones((1200,1000,3),dtype=np.uint8)*255

            i=0
            for r in range(3):
                for c in range(3):
                    if i>=count: break
                    y=r*400; x=c*350
                    bordered=cv2.copyMakeBorder(face,5,5,5,5,cv2.BORDER_CONSTANT,value=[0,0,0])
                    canvas[y:y+541,x:x+423]=bordered
                    i+=1

            img_path="static/output.jpg"
            cv2.imwrite(img_path,canvas)

            if filetype=="pdf":
                pdf="static/output.pdf"
                doc=SimpleDocTemplate(pdf,pagesize=A4)
                doc.build([RLImage(img_path,width=500,height=700)])
                return send_file(pdf,as_attachment=True)

            return send_file(img_path,as_attachment=True)

        # CROP
        if tool=="crop":
            try:
                x=int(request.form.get("x",0))
                y=int(request.form.get("y",0))
                w=int(request.form.get("w",100))
                h=int(request.form.get("h",100))

                crop=img[y:y+h,x:x+w]
                path="static/crop.jpg"
                cv2.imwrite(path,crop)
                return send_file(path,as_attachment=True)
            except:
                return "Crop error"

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
