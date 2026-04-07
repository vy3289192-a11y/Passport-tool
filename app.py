from flask import Flask, request, render_template_string, send_file
import cv2
import os
import numpy as np
import uuid
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

# Folder setup
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro - AI Editor</title>
    <style>
        :root { --bg:#f5f7fa; --card:#ffffff; --text:#1e293b; --accent:#3b82f6; }
        body.dark { --bg:#0f172a; --card:#1e293b; --text:#f1f5f9; }
        body { margin:0; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:var(--bg); color:var(--text); transition: 0.3s; }
        
        .navbar { display:flex; justify-content:space-between; align-items:center; padding:15px 30px; background:#111827; color:white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .nav-btns button { background:transparent; border:1px solid #374151; color:white; padding:8px 15px; border-radius:6px; cursor:pointer; margin-left:10px; transition:0.2s; }
        .nav-btns button:hover { background:#3b82f6; border-color:#3b82f6; }

        .main { padding: 40px 20px; display:flex; flex-direction:column; align-items:center; }
        .card { background:var(--card); width:100%; max-width:450px; padding:30px; border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.05); }
        
        .upload-area { border:2px dashed var(--accent); padding:40px; border-radius:12px; cursor:pointer; margin-bottom:20px; transition:0.2s; }
        .upload-area:hover { background: rgba(59, 130, 246, 0.05); }
        
        input[type="number"], select { width:100%; padding:12px; margin:10px 0; border:1px solid #ddd; border-radius:8px; box-sizing: border-box; }
        button.submit-btn { width:100%; padding:14px; background:var(--accent); color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin-top:15px; }
        
        #preview { width:120px; height:150px; object-fit:cover; border-radius:8px; margin: 15px auto; display:none; border: 2px solid var(--accent); }
        
        .loader { display:none; margin-top:20px; }
        .progress-container { width:100%; background:#e2e8f0; border-radius:10px; height:8px; overflow:hidden; }
        .progress-bar { width:0%; height:100%; background:var(--accent); transition:0.3s; }
    </style>
</head>
<body class="dark">

<div class="navbar">
    <div style="font-size:1.5rem; font-weight:bold;">📸 Snapzo Pro</div>
    <div class="nav-btns">
        <button onclick="showPage('passport')">Passport</button>
        <button onclick="showPage('crop')">Crop</button>
        <button onclick="toggleTheme()">🌓</button>
    </div>
</div>

<div class="main">
    <div id="passport" class="card">
        <h2 style="margin-top:0">Passport Photo Maker</h2>
        <form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
            <input type="hidden" name="tool" value="passport">
            
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <p>Click to upload photo</p>
                <input type="file" name="file" id="fileInput" hidden required onchange="previewImg(this)">
            </div>
            
            <img id="preview">

            <label>Number of Photos:</label>
            <input type="number" name="count" value="8" min="1" max="12">

            <label>Output Format:</label>
            <select name="type">
                <option value="jpg">Image (JPG)</option>
                <option value="pdf">Document (PDF)</option>
            </select>

            <button type="submit" class="submit-btn">Generate & Download</button>
        </form>

        <div class="loader" id="loader">
            <p>Processing your photo...</p>
            <div class="progress-container"><div class="progress-bar" id="bar"></div></div>
        </div>
    </div>

    <div id="crop" class="card" style="display:none;">
        <h2 style="margin-top:0">Manual Crop</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="tool" value="crop">
            <input type="file" name="file" required style="margin-bottom:10px">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px">
                <input type="number" name="x" placeholder="X (Left)">
                <input type="number" name="y" placeholder="Y (Top)">
                <input type="number" name="w" placeholder="Width">
                <input type="number" name="h" placeholder="Height">
            </div>
            <button type="submit" class="submit-btn">Crop & Download</button>
        </form>
    </div>
</div>

<script>
    function showPage(p){
        document.getElementById("passport").style.display="none";
        document.getElementById("crop").style.display="none";
        document.getElementById(p).style.display="block";
    }

    function toggleTheme(){ document.body.classList.toggle("dark"); }

    function previewImg(input) {
        const preview = document.getElementById('preview');
        if (input.files && input.files[0]) {
            preview.src = URL.createObjectURL(input.files[0]);
            preview.style.display = "block";
        }
    }

    function showLoader(){
        document.getElementById("loader").style.display="block";
        let w = 0;
        let bar = document.getElementById("bar");
        let interval = setInterval(() => {
            w += 5;
            bar.style.width = w + "%";
            if(w >= 100) clearInterval(interval);
        }, 100);
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

        if not file or file.filename == '':
            return "File select karein!"

        # Create unique filename
        job_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_in.jpg")
        file.save(input_path)

        img = cv2.imread(input_path)
        if img is None:
            return "Image read nahi ho paayi."

        if tool == "passport":
            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")
            
            # Passport Standard Ratio (approx 3.5x4.5)
            face = cv2.resize(img, (413, 531))
            
            # Canvas size for A4 feel (Width 1250, Height 1500)
            canvas = np.ones((1500, 1250, 3), dtype=np.uint8) * 255

            i = 0
            # Grid system: 3 photos per row
            for r in range(4): # 4 rows
                for c in range(3): # 3 columns
                    if i >= count: break
                    y = r * 580 + 50  # Vertical gap
                    x = c * 430 + 30  # Horizontal gap
                    
                    # Border add karna
                    bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[200, 200, 200])
                    h, w, _ = bordered.shape
                    
                    # Insert into canvas
                    canvas[y:y+h, x:x+w] = bordered
                    i += 1

            output_filename = f"{job_id}_out.jpg"
            output_path = os.path.join(UPLOAD_FOLDER, output_filename)
            cv2.imwrite(output_path, canvas)

            if filetype == "pdf":
                pdf_path = output_path.replace(".jpg", ".pdf")
                doc = SimpleDocTemplate(pdf_path, pagesize=A4)
                doc.build([RLImage(output_path, width=450, height=550)])
                return send_file(pdf_path, as_attachment=True)

            return send_file(output_path, as_attachment=True)

        if tool == "crop":
            try:
                H, W, _ = img.shape
                x = int(request.form.get("x", 0))
                y = int(request.form.get("y", 0))
                w = int(request.form.get("w", 100))
                h = int(request.form.get("h", 100))
                
                # Boundary safety
                crop = img[y:y+h, x:x+w]
                crop_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_crop.jpg")
                cv2.imwrite(crop_path, crop)
                return send_file(crop_path, as_attachment=True)
            except:
                return "Crop dimensions galat hain."

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
