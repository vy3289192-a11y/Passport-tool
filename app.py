from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

def allowed_file(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

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

    <style>
        * { box-sizing: border-box; }
        :root { 
            --bg: #f8fafc; --card: #ffffff; --nav: #ffffff;
            --accent: #2563eb; --text: #1e293b; --text-muted: #475569;
            --border: #e2e8f0; --box-bg: #f1f5f9; --input-bg: #ffffff;
        }
        body.dark-mode { 
            --bg: #0f172a; --card: #1e293b; --nav: #111827;
            --accent: #3b82f6; --text: #f1f5f9; --text-muted: #94a3b8;
            --border: #334155; --box-bg: #111827; --input-bg: #0f172a;
        }

        /* 🟡 Typing Link Styles 🟡 */
        .typing-link {
            background: #ffde59 !important;
            color: #000 !important;
            font-weight: 800 !important;
            border: 2px solid #eab308 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .typing-link:hover {
            background: #facc15 !important;
            transform: scale(1.05);
        }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; width: 100vw; max-width: 100%; transition: background 0.3s, color 0.3s; }
        .privacy-banner { background: #10b981; color: white; text-align: center; padding: 6px; font-size: 0.85rem; font-weight: bold; letter-spacing: 0.5px; }
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .desktop-menu { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }
        .menu-btn { text-decoration: none; padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; color: var(--text); display: inline-block; white-space: nowrap; font-weight: 500; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white !important; }

        .mobile-toggle { display: none; font-size: 1.5rem; cursor: pointer; color: var(--accent); }
        .sidebar { width: 250px; height: 100vh; background: var(--nav); position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; overflow-y: auto; border-right: 1px solid var(--border); }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { display: flex; text-decoration: none; align-items: center; gap: 15px; color: var(--text); border-radius: 8px; margin-bottom: 10px; transition: 0.2s; padding: 15px; font-size: 1rem; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }

        .main { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; width: 100%; }
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; flex-wrap: wrap; }
        .tool-wrapper.active { display: flex; }
        .tool-content { flex: 1.2; text-align: left; order: 1; }
        .tool-content h1 { font-size: 2.2rem; color: var(--text); margin: 0 0 15px 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid var(--border); order: 2; }
        
        /* 🔵 Homepage Typing Card Logic 🔵 */
        .typing-promo-card {
            background: #fffbeb;
            border: 2px solid #fcd34d;
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 15px;
            text-decoration: none;
            color: #92400e;
            transition: 0.3s;
        }
        .typing-promo-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.05); }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); position: relative; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }
        input, select, textarea { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; width: 100%; }
        .group { flex: 1; }
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top:10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.4); }

        @media (max-width: 900px) { 
            .tool-wrapper.active { flex-direction: column; align-items: center; gap: 30px; } 
            .desktop-menu { display: none; } 
            .mobile-toggle { display: block; }
            .card { order: 1; width: 100%; }
        }
    </style>
</head>
<body>

    <div class="privacy-banner">
        <i class="fas fa-shield-alt"></i> 100% SECURE & PRIVATE - FILES AUTO-DELETE AFTER PROCESSING
    </div>

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
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.3rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()"></i>
        </div>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Snapzo Menu</h3>
        <a href="https://typing.snapzopro.online" class="menu-btn typing-link"><i class="fas fa-keyboard"></i> Hindi Typing</a>
        <a href="/passport-maker" class="menu-btn active-menu"><i class="fas fa-id-badge"></i> Passport Maker</a>
        <a href="/signature-cleaner" class="menu-btn"><i class="fas fa-signature"></i> Signature Cleaner</a>
        <a href="/compress" class="menu-btn"><i class="fas fa-compress-arrows-alt"></i> Compress Image</a>
        <a href="/image-to-text" class="menu-btn"><i class="fas fa-file-word"></i> Image to Text</a>
        <a href="/image-to-pdf" class="menu-btn"><i class="fas fa-images"></i> Image to PDF</a>
    </div>

    <div class="main">
        
        <div class="tool-wrapper active" id="tool-home-promo" style="max-width: 1100px; width: 100%; margin-bottom: 0;">
             <a href="https://typing.snapzopro.online" class="typing-promo-card">
                <i class="fas fa-keyboard" style="font-size: 2rem;"></i>
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem;">New: Hindi Typing Studio</h3>
                    <p style="margin: 0; font-size: 0.85rem; opacity: 0.8;">English to Hindi, Kruti Dev & Unicode Converter inside.</p>
                </div>
                <i class="fas fa-arrow-right" style="margin-left: auto;"></i>
            </a>
        </div>

        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>Strict AI Passport Maker</h1>
                <p>Turn a regular photo into an official passport photo fast. SSC, RRB, NTPC forms ke liye ekdum sahi 3.5x4.5 ratio.</p>
                <ul style="list-style: none; padding: 0; margin-top: 15px;">
                    <li style="margin-bottom: 10px;"><i class="fas fa-check-circle" style="color:#10b981"></i> Permanent 413x531 Pixels</li>
                    <li style="margin-bottom: 10px;"><i class="fas fa-check-circle" style="color:#10b981"></i> Auto-Print Name & Date</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Passport Studio</h2>
                <form method="POST" enctype="multipart/form-data" action="/passport-maker">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <div class="row" style="margin-bottom:0;">
                        <div class="group"><label>Print Name</label><input type="text" name="print_name" placeholder="VISHAL YADAV"></div>
                        <div class="group"><label>Print Date</label><input type="text" name="print_date" placeholder="10/04/2026"></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Generate Photo</button>
                </form>
            </div>
        </div>
        
        </div>

    <script>
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

# --- BACKEND ---

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

@app.route('/')
@app.route('/passport-maker', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            face = cv2.resize(strict_passport_crop(img), (413, 531))
            
            name = request.form.get("print_name", "").strip().upper()
            date = request.form.get("print_date", "").strip()
            if name or date:
                cv2.rectangle(face, (0, 451), (413, 531), (255,255,255), -1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                if name: cv2.putText(face, name, (30, 485), font, 0.7, (0,0,0), 2)
                if date: cv2.putText(face, date, (30, 515), font, 0.6, (0,0,0), 2)
            
            _, buf = cv2.imencode('.jpg', face)
            return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_passport.jpg')
        except: return "Error", 500

    return render_template_string(HTML, page_title='Snapzo Pro | Free AI Passport Photo & Image Tools', page_desc='AI passport photo maker, Hindi typing, and document tools.', request_path=request.path)

# Extra routes for SEO logic
@app.route('/compress')
@app.route('/signature-cleaner')
@app.route('/image-to-text')
@app.route('/id-card-print')
def other_pages():
    return render_template_string(HTML, page_title='Snapzo Pro Tools', page_desc='Secure Image Processing Tools.', request_path=request.path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
