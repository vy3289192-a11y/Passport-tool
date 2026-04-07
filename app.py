from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# Aapka Direct Image Link
LOGO_URL = "https://i.ibb.co/Cp1Dzh0t/46596.png"

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro | AI Passport Maker</title>
    
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; }
        
        /* Navbar */
        .nav { background: #111827; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: white; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .nav-brand span { font-weight: bold; font-size: 1.3rem; letter-spacing: 0.5px; }

        /* Sidebar (Mobile Menu) */
        .sidebar { width: 250px; height: 100vh; background: #111827; position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; box-sizing: border-box; }
        .sidebar.active { left: 0; }
        .menu-item { padding: 15px; display: flex; align-items: center; gap: 15px; color: var(--text); text-decoration: none; border-radius: 8px; margin-bottom: 10px; transition: 0.2s; }
        .menu-item:hover { background: var(--accent); }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }

        /* Main Content */
        .main { padding: 40px 20px; display: flex; justify-content: center; min-height: 85vh; align-items: flex-start; }
        .card { background: var(--card); padding: 35px; border-radius: 24px; width: 100%; max-width: 480px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid var(--border); }
        
        h2 { margin-top: 0; font-size: 1.8rem; text-align: center; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        /* Upload Area */
        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); transition: 0.3s; }
        .upload-zone:hover { background: rgba(59,130,246,0.08); border-color: white; }
        #preview { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        /* Form Control */
        .row { display: flex; gap: 15px; margin: 20px 0; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8; }
        input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; box-sizing: border-box; font-size: 1rem; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); }
        .btn:hover { background: #2563eb; transform: translateY(-2px); }

        @media (max-width: 768px) {
            .nav-brand span { font-size: 1.1rem; }
            .card { padding: 25px; }
        }
    </style>
</head>
<body>

    <div class="nav">
        <a href="/" class="nav-brand">
            <img src="''' + LOGO_URL + '''" alt="Logo">
            <span>Snapzo Pro</span>
        </a>
        <i class="fas fa-bars" style="font-size: 1.4rem; cursor: pointer;" onclick="toggleMenu()"></i>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent)">Menu</h3>
        <a href="/" class="menu-item"><i class="fas fa-id-card"></i> Passport Maker</a>
        <a href="#" class="menu-item" onclick="alert('AI Feature coming soon!')"><i class="fas fa-magic"></i> Remove BG</a>
        <a href="/" class="menu-item"><i class="fas fa-home"></i> Home</a>
    </div>

    <div class="main">
        <div class="card">
            <h2>AI Passport Studio</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
                    <input type="file" name="file" id="fileInput" hidden required onchange="handleFile(this)">
                    <div id="drop-text">
                        <i class="fas fa-cloud-upload-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                        <p style="margin:0"><b>Click to upload</b> or drag image</p>
                    </div>
                    <img id="preview">
                </div>

                <div class="row">
                    <div class="group">
                        <label>Quantity</label>
                        <input type="number" name="count" value="8" min="1" max="12">
                    </div>
                    <div class="group">
                        <label>File Type</label>
                        <select name="type">
                            <option value="jpg">Image (JPG)</option>
                            <option value="pdf">Document (PDF)</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="btn">
                    <i class="fas fa-bolt"></i> Generate & Download
                </button>
            </form>
        </div>
    </div>

    <script>
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function handleFile(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('preview').src = e.target.result;
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('drop-text').style.display = 'none';
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
    </script>
</body>
</html>
'''

def auto_crop_passport(img):
    h, w = img.shape[:2]
    target_ratio = 413 / 531
    if (w / h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.1) # Crop for face safety
        return img[offset:offset+new_h, :]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file: return "Error: No file", 400
            
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            
            # Smart Crop and Resize
            face = cv2.resize(auto_crop_passport(img), (413, 531))
            bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[235, 235, 235])
            bh, bw = bordered.shape[:2]

            # Dynamic Canvas (Prevents Shape Mismatch)
            canvas = np.ones((2000, 1500, 3), dtype=np.uint8) * 255
            count = int(request.form.get("count", 8))
            
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                y_p, x_p = r*(bh+45)+70, c*(bw+30)+70
                canvas[y_p:y_p+bh, x_p:x_p+bw] = bordered

            _, buffer = cv2.imencode('.jpg', canvas)
            io_buf = io.BytesIO(buffer)

            if request.form.get("type") == "pdf":
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                c.drawImage(ImageReader(io_buf), 45, 100, width=505, height=680)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_photos.pdf')
            
            io_buf.seek(0)
            return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='snapzo_photos.jpg')
        except Exception as e:
            return f"Server Error: {str(e)}", 500
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
