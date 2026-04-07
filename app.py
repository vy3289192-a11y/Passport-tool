from flask import Flask, request, render_template_string, send_file
import cv2
import os
import numpy as np
import uuid
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

# Render ke liye /tmp folder use karna zaroori hai
UPLOAD_FOLDER = '/tmp/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro - AI Editor</title>
    <style>
        :root { --bg:#0f172a; --card:#1e293b; --text:#f1f5f9; --accent:#3b82f6; }
        body { margin:0; font-family:sans-serif; background:var(--bg); color:var(--text); transition: 0.3s; }
        .navbar { display:flex; justify-content:space-between; align-items:center; padding:15px 30px; background:#111827; color:white; }
        .main { padding: 40px 20px; display:flex; flex-direction:column; align-items:center; }
        .card { background:var(--card); width:100%; max-width:450px; padding:30px; border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.3); }
        .upload-area { border:2px dashed var(--accent); padding:40px; border-radius:12px; cursor:pointer; text-align:center; }
        input[type="number"], select { width:100%; padding:12px; margin:10px 0; border-radius:8px; border:none; background:#334155; color:white; }
        button.submit-btn { width:100%; padding:14px; background:var(--accent); color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin-top:15px; }
        #preview { width:120px; display:none; margin: 15px auto; border: 2px solid var(--accent); }
    </style>
</head>
<body>
<div class="navbar">
    <div style="font-size:1.5rem; font-weight:bold;">📸 Snapzo Pro</div>
    <div><button onclick="location.reload()" style="background:none; border:none; color:white; cursor:pointer;">Home</button></div>
</div>
<div class="main">
    <div class="card">
        <h2>Passport Photo Maker</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="tool" value="passport">
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <p>Click to upload photo</p>
                <input type="file" name="file" id="fileInput" hidden required onchange="document.getElementById('preview').src=URL.createObjectURL(this.files[0]);document.getElementById('preview').style.display='block'">
            </div>
            <img id="preview">
            <label>Number of Photos:</label>
            <input type="number" name="count" value="8" min="1" max="12">
            <label>Format:</label>
            <select name="type"><option value="jpg">JPG</option><option value="pdf">PDF</option></select>
            <button type="submit" class="submit-btn">Download Now</button>
        </form>
    </div>
</div>
</body>
</html>
'''

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        tool = request.form.get("tool")
        file = request.files.get('file')

        if not file or file.filename == '':
            return "File select karein!"

        job_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_in.jpg")
        file.save(input_path)

        img = cv2.imread(input_path)
        if img is None:
            return "Error: Image readable nahi hai."

        if tool == "passport":
            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")
            
            face = cv2.resize(img, (413, 531))
            canvas = np.ones((1500, 1250, 3), dtype=np.uint8) * 255

            i = 0
            for r in range(4):
                for c in range(3):
                    if i >= count: break
                    y, x = r * 580 + 50, c * 430 + 30
                    bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[200, 200, 200])
                    canvas[y:y+bordered.shape[0], x:x+bordered.shape[1]] = bordered
                    i += 1

            output_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_out.jpg")
            cv2.imwrite(output_path, canvas)

            if filetype == "pdf":
                pdf_path = output_path.replace(".jpg", ".pdf")
                doc = SimpleDocTemplate(pdf_path, pagesize=A4)
                doc.build([RLImage(output_path, width=450, height=550)])
                return send_file(pdf_path, as_attachment=True)

            return send_file(output_path, as_attachment=True)

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True)
