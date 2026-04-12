from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import json

app = Flask(__name__)

LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

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
    
    <meta property="og:site_name" content="Snapzo Pro" />
    <meta property="og:title" content="{{ page_title }}" />
    <meta property="og:description" content="{{ page_desc }}" />
    <meta property="og:image" content="''' + LOGO_URL + '''" />
    <meta property="og:url" content="https://snapzopro.online{{ request_path }}" />
    
    <link rel="icon" href="''' + LOGO_URL + '''">
    <link rel="apple-touch-icon" href="''' + LOGO_URL + '''">
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js"></script>

    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Snapzo Pro",
      "alternateName": "SnapzoPro",
      "url": "https://snapzopro.online/"
    }
    </script>

    {{ breadcrumb_schema | safe }}

    <style>
        * { box-sizing: border-box; }
        :root { --bg: #f8fafc; --card: #ffffff; --nav: #ffffff; --accent: #2563eb; --text: #1e293b; --text-muted: #475569; --border: #e2e8f0; --box-bg: #f1f5f9; --input-bg: #ffffff; }
        body.dark-mode { --bg: #0f172a; --card: #1e293b; --nav: #111827; --accent: #3b82f6; --text: #f1f5f9; --text-muted: #94a3b8; --border: #334155; --box-bg: #111827; --input-bg: #0f172a; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; transition: background 0.3s, color 0.3s; }
        .privacy-banner { background: #10b981; color: white; text-align: center; padding: 6px; font-size: 0.85rem; font-weight: bold; }
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .desktop-menu { display: flex; gap: 5px; align-items: center; }
        .menu-btn { text-decoration: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; color: var(--text); font-weight: 500; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white; }
        .typing-btn { background: #ffde59; color: #000 !important; font-weight: bold; border: 1px solid #eab308; }
        .mobile-toggle { display: none; font-size: 1.5rem; cursor: pointer; color: var(--accent); }
        .sidebar { width: 250px; height: 100vh; background: var(--nav); position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; border-right: 1px solid var(--border); }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { display: flex; margin-bottom: 10px; padding: 15px; font-size: 1rem; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }
        .main { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; }
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; margin-bottom: 40px; flex-wrap: wrap; }
        .tool-wrapper.active { display: flex; }
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid var(--border); }
        .upload-zone { border: 2px dashed var(--accent); padding: 30px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); }
        .preview-img { max-width: 100%; max-height: 200px; border-radius: 8px; display: none; margin-top: 10px; }
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .footer { text-align: center; padding: 40px; border-top: 1px solid var(--border); width: 100%; }
        @media (max-width: 900px) { .desktop-menu { display: none; } .mobile-toggle { display: block; } .tool-wrapper.active { flex-direction: column; } }
    </style>
</head>
<body class="light-mode">

    <div class="privacy-banner"><i class="fas fa-shield-alt"></i> 100% SECURE - FILES AUTO-DELETE AFTER PROCESSING</div>

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <a href="https://typing.snapzopro.online" class="menu-btn typing-btn"><i class="fas fa-keyboard"></i> Hindi Typing</a>
                <a href="/passport-maker" class="menu-btn active-menu" id="d-passport">Passport Maker</a>
                <a href="/image-to-text" class="menu-btn" id="d-img2text">OCR</a>
                <a href="/compress" class="menu-btn" id="d-compress">Compress</a>
            </div>
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.2rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()"></i>
        </div>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <a href="https://typing.snapzopro.online" class="menu-btn typing-btn"><i class="fas fa-keyboard"></i> Hindi Typing</a>
        <a href="/passport-maker" class="menu-btn active-menu" id="m-passport">Passport Maker</a>
        <a href="/image-to-text" class="menu-btn" id="m-img2text">OCR Studio</a>
        <a href="/compress" class="menu-btn" id="m-compress">Compress</a>
    </div>

    <div class="main">
        <div class="tool-wrapper active" id="tool-passport">
            <div class="card" style="max-width: 500px;">
                <h2>AI Passport Studio</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    
                    <label>Exam/Size Preset</label>
                    <select id="examPreset" onchange="applyPreset()" style="margin-bottom:15px;">
                        <option value="custom">-- Custom Size --</option>
                        <option value="ssc">SSC (3.5 x 4.5 cm)</option>
                        <option value="rrb">Railway RRB/NTPC (3.5 x 4.5 cm)</option>
                        <option value="up">UP Police (5-20 KB)</option>
                    </select>

                    <div style="display:flex; gap:10px; margin-bottom:15px;">
                        <div style="flex:1;"><label>Width</label><input type="number" name="w" id="tw" value="413"></div>
                        <div style="flex:1;"><label>Height</label><input type="number" name="h" id="th" value="531"></div>
                    </div>

                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:2rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    
                    <div style="margin-top:15px;">
                        <label>Print Name</label><input type="text" name="print_name" placeholder="E.g. VISHAL YADAV">
                        <label style="margin-top:10px; display:block;">Quantity</label><input type="number" name="count" value="8">
                    </div>

                    <button class="btn"><i class="fas fa-bolt"></i> Generate Passport Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-img2text">
             <div class="card"><h2>OCR - Image to Text</h2><p>Select OCR from menu to use.</p></div>
        </div>
    </div>

    <script>
        function applyPreset() {
            const p = document.getElementById('examPreset').value;
            const w = document.getElementById('tw');
            const h = document.getElementById('th');
            if(p === 'ssc' || p === 'rrb' || p === 'up') { w.value = 413; h.value = 531; }
        }

        function toggleTheme() { document.body.classList.toggle('dark-mode'); }
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

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
    </script>
</body>
</html>
'''

def strict_passport_crop(img, target_w, target_h):
    h, w = img.shape[:2]
    target_ratio = target_w / target_h
    if (w/h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.15)
        return img[offset:offset+new_h, :]

@app.route('/', methods=['GET', 'POST'])
@app.route('/passport-maker', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tool_type = request.form.get('tool_type')
        if tool_type == 'passport':
            file = request.files.get('file')
            target_w = int(request.form.get('w', 413))
            target_h = int(request.form.get('h', 531))
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            
            # Smart Crop based on your UI inputs
            face = cv2.resize(strict_passport_crop(img, target_w, target_h), (target_w, target_h))
            
            print_name = request.form.get("print_name", "").strip().upper()
            if print_name:
                cv2.rectangle(face, (0, target_h-60), (target_w, target_h), (255,255,255), -1)
                cv2.putText(face, print_name, (20, target_h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)

            _, buf = cv2.imencode('.jpg', face)
            return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='passport.jpg')

    return render_template_string(HTML, page_title="Snapzo Pro Tools", page_desc="Professional Exam Photo Tools", request_path="/")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
