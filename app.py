from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from rembg import remove # AI Background Removal ke liye
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo AI Studio</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg: #0f172a; --sidebar: #1e293b; --card: #1e293b; --text: #f1f5f9;
            --accent: #3b82f6; --border: #334155; --hover: #2d3a4f;
        }
        body { margin: 0; font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; min-height: 100vh; overflow-x: hidden; }

        /* Navigation */
        .mobile-header { display: none; background: #111827; padding: 15px 20px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; align-items: center; justify-content: space-between; }
        .sidebar { width: 260px; height: 100vh; background: var(--sidebar); border-right: 1px solid var(--border); position: fixed; padding: 25px; box-sizing: border-box; display: flex; flex-direction: column; z-index: 1500; transition: 0.3s ease; }
        .logo { font-size: 1.6rem; font-weight: 800; margin-bottom: 40px; color: var(--accent); display: flex; align-items: center; gap: 12px; }
        .menu-item { padding: 14px 18px; border-radius: 12px; cursor: pointer; margin-bottom: 10px; display: flex; align-items: center; gap: 15px; transition: 0.2s; color: #94a3b8; text-decoration: none; font-size: 1rem; }
        .menu-item:hover, .menu-item.active { background: var(--hover); color: white; border-left: 4px solid var(--accent); }
        
        /* Layout */
        .content { margin-left: 260px; flex: 1; padding: 40px; display: flex; justify-content: center; }
        .tool-card { background: var(--card); padding: 35px; border-radius: 24px; box-shadow: 0 20px 50px rgba(0,0,0,0.3); width: 100%; max-width: 550px; border: 1px solid var(--border); }

        /* Upload UI */
        .upload-area { border: 2px dashed #475569; border-radius: 20px; padding: 40px 20px; text-align: center; cursor: pointer; background: #161e2e; transition: 0.3s; position: relative; }
        .upload-area:hover { border-color: var(--accent); background: #1e293b; }
        #preview { max-width: 140px; border-radius: 12px; display: none; margin: 15px auto; border: 4px solid var(--accent); box-shadow: 0 10px 20px rgba(0,0,0,0.4); }

        /* Settings Grid */
        .settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }
        .setting-box { background: #161e2e; padding: 12px; border-radius: 12px; border: 1px solid var(--border); }
        label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 5px; display: block; }
        select, input { width: 100%; background: transparent; border: none; color: white; font-size: 0.95rem; outline: none; margin-top: 5px; }

        .btn-magic { width: 100%; padding: 18px; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; border-radius: 15px; font-weight: 700; font-size: 1.1rem; cursor: pointer; transition: 0.3s; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.4); }
        .btn-magic:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(37, 99, 235, 0.5); }

        /* Mobile Adjustments */
        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .mobile-header { display: flex; }
            .content { margin-left: 0; padding: 20px; }
            .settings-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

    <div class="mobile-header">
        <div style="font-weight:bold; color:var(--accent);"><i class="fas fa-bolt"></i> SNAPZO AI</div>
        <i class="fas fa-bars" style="font-size:1.5rem;" onclick="toggleMenu()"></i>
    </div>

    <div class="sidebar" id="sidebar">
        <div class="logo"><i class="fas fa-camera-retro"></i> <span>Snapzo Pro</span></div>
        <a href="/" class="menu-item active"><i class="fas fa-id-card"></i> <span>Passport AI</span></a>
        <a href="#" class="menu-item"><i class="fas fa-user-edit"></i> <span>Portrait Editor</span></a>
        <a href="#" class="menu-item"><i class="fas fa-history"></i> <span>Recent Jobs</span></a>
        <div style="margin-top:auto; font-size:0.7rem; color:#475569;">V2.0.1 - AI Powered</div>
    </div>

    <div class="content">
        <div class="tool-card">
            <h2 style="margin:0 0 10px 0;">Passport Studio</h2>
            <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:25px;">AI will auto-crop, brighten, and fix your background.</p>

            <form method="POST" enctype="multipart/form-data">
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    <input type="file" name="file" id="fileInput" hidden accept="image/*" onchange="previewFile(this)">
                    <div id="prompt">
                        <i class="fas fa-cloud-upload-alt" style="font-size:3rem; color:var(--accent); margin-bottom:15px;"></i>
                        <p>Drop your photo here</p>
                    </div>
                    <img id="preview">
                </div>

                <div class="settings-grid">
                    <div class="setting-box">
                        <label>AI Background</label>
                        <select name="bg_color">
                            <option value="original">Original</option>
                            <option value="white">Pure White</option>
                            <option value="blue">Studio Blue</option>
                        </select>
                    </div>
                    <div class="setting-box">
                        <label>Face Retouch</label>
                        <select name="retouch">
                            <option value="on">Auto Brighten</option>
                            <option value="off">Natural</option>
                        </select>
                    </div>
                    <div class="setting-box">
                        <label>Sheet Layout</label>
                        <select name="count">
                            <option value="8">8 Photos (Grid)</option>
                            <option value="12">12 Photos (Full)</option>
                            <option value="1">Single Photo</option>
                        </select>
                    </div>
                    <div class="setting-box">
                        <label>Format</label>
                        <select name="type">
                            <option value="jpg">High-Res JPG</option>
                            <option value="pdf">Print-Ready PDF</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="btn-magic"><i class="fas fa-magic"></i> Generate Professional Grid</button>
            </form>
        </div>
    </div>

    <script>
        function toggleMenu() { document.getElementById('sidebar').classList.toggle('open'); }
        function previewFile(input) {
            const file = input.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('preview').src = e.target.result;
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('prompt').style.display = 'none';
                }
                reader.readAsDataURL(file);
            }
        }
    </script>
</body>
</html>
'''

def process_ai_features(img, bg_choice, retouch):
    # 1. AI Background Removal
    if bg_choice != "original":
        # Rembg ka use karke background hatana
        img_no_bg = remove(img)
        
        # Naya background color set karna
        h, w = img.shape[:2]
        if bg_choice == "white":
            bg_color = (255, 255, 255)
        else: # Blue
            bg_color = (255, 100, 0) # BGR for Studio Blue
            
        new_bg = np.full((h, w, 3), bg_color, dtype=np.uint8)
        
        # Masking (Alpha channel handle karna)
        if img_no_bg.shape[2] == 4:
            alpha = img_no_bg[:, :, 3] / 255.0
            for c in range(3):
                new_bg[:, :, c] = (alpha * img_no_bg[:, :, c] + (1 - alpha) * new_bg[:, :, c]).astype(np.uint8)
            img = new_bg

    # 2. Studio Retouching (Auto Brightness)
    if retouch == "on":
        # Contrast adjustment
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        img = cv2.merge((cl, a, b))
        img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
        
    return img

def studio_crop(img):
    h, w = img.shape[:2]
    target_ratio = 413 / 531
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        img = img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.1) # Face focus ke liye thoda upar se rakha
        img = img[offset:offset+new_h, :]
    return cv2.resize(img, (413, 531))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            bg_choice = request.form.get("bg_color")
            retouch = request.form.get("retouch")
            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")

            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # AI Processing
            img = process_ai_features(img, bg_choice, retouch)
            face = studio_crop(img)
            
            # Passport styling
            bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[230, 230, 230])
            bh, bw = bordered.shape[:2]

            # Result Canvas
            canvas = np.ones((2000, 1500, 3), dtype=np.uint8) * 255
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                y, x = r * (bh + 40) + 100, c * (bw + 30) + 100
                canvas[y:y+bh, x:x+bw] = bordered

            _, buffer = cv2.imencode('.jpg', canvas)
            io_buf = io.BytesIO(buffer)

            if filetype == "pdf":
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                img_r = ImageReader(io_buf)
                c.drawImage(img_r, 40, 100, width=520, height=680)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='studio_photos.pdf')

            io_buf.seek(0)
            return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='studio_photos.jpg')
            
        except Exception as e:
            return f"Studio Error: {str(e)}", 500

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()
