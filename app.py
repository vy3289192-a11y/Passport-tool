from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # 10MB Limit

LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

def allowed_file(filename):
    return filename.lower().endswith(('.png','.jpg','.jpeg','.webp'))

def strict_passport_crop(img):
    h, w = img.shape[:2]
    target_ratio = 0.777 
    if (w/h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.15)
        return img[offset:offset+new_h, :]

# Yahan se HTML shuru hota hai (Maine isme Typing Link add kar diya hai)
# Pura HTML String niche wale block mein hai...
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="google-site-verification" content="TlhWO7oDD-Gp8H0gKFC3U7n7v213ccnwGp0C9OB_7Uc" />
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-TJ3VTE8QJE"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-TJ3VTE8QJE');
    </script>
    <title>{{ page_title }}</title>
    <meta name="description" content="{{ page_desc }}">
    <link rel="icon" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js"></script>

    <style>
        * { box-sizing: border-box; }
        :root { --bg: #f8fafc; --card: #ffffff; --nav: #ffffff; --accent: #2563eb; --text: #1e293b; --text-muted: #475569; --border: #e2e8f0; --box-bg: #f1f5f9; --input-bg: #ffffff; }
        body.dark-mode { --bg: #0f172a; --card: #1e293b; --nav: #111827; --accent: #3b82f6; --text: #f1f5f9; --text-muted: #94a3b8; --border: #334155; --box-bg: #111827; --input-bg: #0f172a; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; transition: 0.3s; }
        .typing-link { background: #ffde59 !important; color: #000 !important; font-weight: bold; border: 2px solid #eab308; }
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .desktop-menu { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }
        .menu-btn { text-decoration: none; padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; color: var(--text); font-weight: 500; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white !important; }
        .mobile-toggle { display: none; font-size: 1.5rem; cursor: pointer; color: var(--accent); }
        .sidebar { width: 250px; height: 100vh; background: var(--nav); position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; overflow-y: auto; border-right: 1px solid var(--border); }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; padding: 15px; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }
        .main { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; }
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; flex-wrap: wrap; }
        .tool-wrapper.active { display: flex; }
        .tool-content { flex: 1.2; text-align: left; order: 1; }
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid var(--border); order: 2; }
        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }
        input, select, textarea { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 1rem; }
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        @media (max-width: 900px) { .desktop-menu { display: none; } .mobile-toggle { display: block; } .tool-wrapper.active { flex-direction: column; } .card { order: 1; width: 100%; } }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right" style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <a href="https://typing.snapzopro.online" class="menu-btn typing-link"><i class="fas fa-keyboard"></i> Hindi Typing</a>
                <a href="/passport-maker" class="menu-btn active-menu" id="d-passport">Passport Maker</a>
                <a href="/id-card-print" class="menu-btn" id="d-idcard">ID Card Print</a>
                <a href="/signature-cleaner" class="menu-btn" id="d-sign">Sign Cleaner</a>
                <a href="/compress" class="menu-btn" id="d-compress">Compress</a>
                <a href="/image-to-text" class="menu-btn" id="d-img2text">OCR</a>
            </div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()"></i>
        </div>
    </div>

    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent);">Snapzo Menu</h3>
        <a href="https://typing.snapzopro.online" class="menu-btn typing-link"><i class="fas fa-keyboard"></i> Hindi Typing</a>
        <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)"><i class="fas fa-id-badge"></i> Passport Maker</a>
        <a href="/id-card-print" class="menu-btn" onclick="switchTool('idcard', event)"><i class="fas fa-address-card"></i> ID Card Print</a>
        <a href="/signature-cleaner" class="menu-btn" onclick="switchTool('sign', event)"><i class="fas fa-signature"></i> Signature Cleaner</a>
        <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)"><i class="fas fa-compress-arrows-alt"></i> Compress Image</a>
        <a href="/image-to-text" class="menu-btn" onclick="switchTool('img2text', event)"><i class="fas fa-file-word"></i> Image to Text</a>
    </div>

    <div class="main">
        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>AI Passport Photo Maker</h1>
                <p>SSC, RRB aur UP Police ke liye 3.5x4.5 ratio wali photo banayein Name/Date ke sath.</p>
            </div>
            <div class="card">
                <form method="POST" action="/process" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <input type="text" name="print_name" placeholder="Full Name" style="margin-top:15px;">
                    <input type="text" name="print_date" placeholder="Date of Photo" style="margin-top:10px;">
                    <button class="btn" style="margin-top:15px;">Generate Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-idcard">
            <div class="card">
                <h2>ID Card Joiner (Front + Back)</h2>
                <form method="POST" action="/process" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="idcard">
                    <label>Front Side</label><input type="file" name="front" required>
                    <label>Back Side</label><input type="file" name="back" required>
                    <button class="btn">Merge to PDF</button>
                </form>
            </div>
        </div>
        
        </div>

    <script>
        function toggleMenu() { document.getElementById('sidebar').classList.toggle('active'); }
        function handlePreview(input, pId, tId) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById(pId).src = e.target.result;
                    document.getElementById(pId).style.display = 'block';
                    document.getElementById(tId).style.display = 'none';
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        function switchTool(name, event) {
            if(event) event.preventDefault();
            document.querySelectorAll('.tool-wrapper').forEach(tw => tw.classList.remove('active'));
            document.getElementById('tool-'+name).classList.add('active');
            toggleMenu();
        }
    </script>
</body>
</html>
'''

# --- BACKEND ROUTES ---

@app.route('/', methods=['GET'])
@app.route('/<path:path>')
def home_route(path=None):
    return render_template_string(HTML, page_title='Snapzo Pro', page_desc='AI Image Tools', request_path='/')

@app.route('/process', methods=['POST'])
def process_route():
    # Yahan jo maine Part 1 mein logic diya tha, wahi use hoga
    return process()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
