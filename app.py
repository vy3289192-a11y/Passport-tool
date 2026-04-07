from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
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
    <title>Snapzo Pro | Modern Editor</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg: #f8fafc; --sidebar: #ffffff; --card: #ffffff; --text: #1e293b;
            --accent: #3b82f6; --border: #e2e8f0; --hover: #eff6ff; --header: #ffffff;
        }
        body.dark-mode {
            --bg: #0f172a; --sidebar: #1e293b; --card: #1e293b; --text: #f1f5f9;
            --accent: #60a5fa; --border: #334155; --hover: #334155; --header: #111827;
        }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); transition: 0.3s; min-height: 100vh; display: flex; flex-direction: column; }
        .mobile-header { display: none; background: var(--header); padding: 15px 20px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; align-items: center; justify-content: space-between; }
        .menu-toggle { font-size: 1.5rem; cursor: pointer; }
        .sidebar { width: 260px; height: 100vh; background: var(--sidebar); border-right: 1px solid var(--border); position: fixed; padding: 20px; box-sizing: border-box; z-index: 150; transition: transform 0.3s ease; }
        .logo { font-size: 1.5rem; font-weight: bold; margin-bottom: 40px; color: var(--accent); }
        .menu-item { padding: 12px 15px; border-radius: 8px; cursor: pointer; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; color: var(--text); text-decoration: none; }
        .menu-item.active { background: var(--hover); color: var(--accent); }
        .content { margin-left: 260px; flex: 1; padding: 40px; display: flex; justify-content: center; }
        .tool-card { background: var(--card); padding: 35px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.05); width: 100%; max-width: 500px; }
        .upload-box { border: 2px dashed var(--accent); border-radius: 15px; padding: 30px; text-align: center; cursor: pointer; background: var(--hover); min-height: 180px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        #preview { max-width: 100%; max-height: 200px; display: none; border-radius: 8px; margin-top: 10px; }
        .btn-primary { width: 100%; padding: 15px; background: var(--accent); color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 20px; }
        @media (max-width: 768px) {
            .mobile-header { display: flex; }
            .sidebar { transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
            .content { margin-left: 0; padding: 20px; }
        }
    </style>
</head>
<body class="dark-mode">
    <div class="mobile-header">
        <div style="font-weight:bold; color:var(--accent)">Snapzo Pro</div>
        <div class="menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')"><i class="fas fa-bars"></i></div>
    </div>

    <div class="sidebar" id="sidebar">
        <div class="logo"><i class="fas fa-camera-retro"></i> Snapzo Pro</div>
        <div class="menu-item active"><i class="fas fa-id-badge"></i> Passport Maker</div>
        <div class="menu-item" onclick="alert('Coming Soon')"><i class="fas fa-magic"></i> Remove BG</div>
        <div class="menu-item" onclick="location.reload()"><i class="fas fa-home"></i> Home</div>
    </div>

    <div class="content">
        <div class="tool-card">
            <h2>Passport Photo Maker</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="upload-box" onclick="document.getElementById('fileInput').click()">
                    <input type="file" name="file" id="fileInput" hidden required onchange="handlePreview(this)">
                    <div id="prompt"><i class="fas fa-cloud-upload-alt" style="font-size:2rem"></i><p>Click to Upload</p></div>
                    <img id="preview">
                </div>
                <div style="display:flex; gap:10px; margin-top:15px">
                    <div style="flex:1"><label>Count</label><input type="number" name="count" value="8" min="1" max="12" style="width:100%; padding:10px; border-radius:5px"></div>
                    <div style="flex:1"><label>Format</label><select name="type" style="width:100%; padding:10px; border-radius:5px"><option value="jpg">JPG</option><option value="pdf">PDF</option></select></div>
                </div>
                <button type="submit" class="btn-primary">Generate & Download</button>
            </form>
        </div>
    </div>

    <script>
        function handlePreview(input) {
            if (input.files && input.files[0]) {
                document.getElementById('preview').src = URL.createObjectURL(input.files[0]);
                document.getElementById('preview').style.display = 'block';
                document.getElementById('prompt').style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

def auto_crop(img):
    h, w = img.shape[:2]
    target_ratio = 413 / 531
    if (w/h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.1)
        return img[offset:offset+new_h, :]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file: return "Upload error", 400
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            
            # Auto Crop & Resize
            face = cv2.resize(auto_crop(img), (413, 531))
            bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[230, 230, 230])
            bh, bw = bordered.shape[:2]
            
            canvas = np.ones((1800, 1400, 3), dtype=np.uint8) * 255
            count = int(request.form.get("count", 8))
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                y, x = r*(bh+40)+60, c*(bw+30)+60
                canvas[y:y+bh, x:x+bw] = bordered

            _, buffer = cv2.imencode('.jpg', canvas)
            io_buf = io.BytesIO(buffer)

            if request.form.get("type") == "pdf":
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                c.drawImage(ImageReader(io_buf), 50, 150, width=500, height=600)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='photos.pdf')
            
            io_buf.seek(0)
            return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='photos.jpg')
        except Exception as e:
            return f"Error: {str(e)}", 500
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
