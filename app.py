from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

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
            --bg: #f8fafc; --card: #ffffff; --nav: #ffffff; --accent: #2563eb;
            --text: #1e293b; --text-muted: #475569; --border: #e2e8f0;
        }
        body.dark-mode {
            --bg: #0f172a; --card: #1e293b; --nav: #111827; --accent: #3b82f6;
            --text: #f1f5f9; --text-muted: #94a3b8; --border: #334155;
        }
        body { margin:0; font-family:'Segoe UI',sans-serif; background:var(--bg); color:var(--text); }
        .privacy-banner { background:#10b981; color:white; text-align:center; padding:8px; font-weight:bold; }
        .nav { background:var(--nav); padding:12px 20px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--border); position:sticky; top:0; z-index:1000; }
        .nav-brand { display:flex; align-items:center; gap:12px; text-decoration:none; color:var(--text); font-weight:bold; font-size:1.35rem; }
        .nav-brand img { height:38px; border-radius:6px; }
        .menu-btn { padding:8px 12px; border-radius:8px; color:var(--text); text-decoration:none; }
        .menu-btn:hover, .active-menu { background:var(--accent); color:white; }
        .main { padding:30px 20px; min-height:85vh; }
        .tool-wrapper { display:none; width:100%; max-width:1100px; margin:0 auto; gap:40px; flex-wrap:wrap; }
        .tool-wrapper.active { display:flex; }
        .card { background:var(--card); padding:30px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1); border:1px solid var(--border); }
        .upload-zone { border:2px dashed var(--accent); padding:40px 20px; border-radius:16px; text-align:center; cursor:pointer; }
        .preview-img { max-width:100%; max-height:280px; border-radius:12px; margin-top:15px; border:2px solid var(--accent); display:none; }
        .btn { width:100%; padding:16px; background:var(--accent); color:white; border:none; border-radius:12px; font-weight:bold; margin-top:15px; cursor:pointer; }
        .btn:hover { transform:translateY(-3px); }
        @media (max-width:900px) { .tool-wrapper.active { flex-direction:column; } }
    </style>
</head>
<body>
    <div class="privacy-banner">
        <i class="fas fa-shield-alt"></i> 100% SECURE & PRIVATE - FILES AUTO-DELETE AFTER PROCESSING
    </div>

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div onclick="toggleTheme()" style="cursor:pointer;font-size:1.4rem;"><i class="fas fa-adjust"></i></div>
    </div>

    <div class="main">
        <!-- About Section (Fixed) -->
        <div class="tool-wrapper active" id="tool-about">
            <div class="card" style="max-width:800px;margin:0 auto;">
                <h1>About Us</h1>
                <p>Welcome to <b>Snapzo Pro</b>.</p>
                <p><b>Founded in 2026 by Vishal</b> from Varanasi. This platform is made to help students and job aspirants with completely free tools for passport size photos, signature cleaning, ID card joining and other document needs for government exams.</p>
            </div>
        </div>
    </div>

    <script>
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
        }
        function switchTool(name) {
            document.querySelectorAll('.tool-wrapper').forEach(t => t.classList.remove('active'));
            document.getElementById('tool-' + name).classList.add('active');
        }
    </script>
</body>
</html>
'''

# ====================== BACKEND ======================
def strict_passport_crop(img):
    h, w = img.shape[:2]
    target_ratio = 0.777
    if (w / h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset + new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.15)
        return img[offset:offset + new_h, :]

@app.route('/', methods=['GET', 'POST'])
@app.route('/passport-maker', methods=['GET', 'POST'])
@app.route('/signature-cleaner', methods=['GET', 'POST'])
@app.route('/about', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')

            if tool_type == 'sign':
                file = request.files.get('file')
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                coords = cv2.findNonZero(255 - thresh)
                if coords is None:
                    return "Signature nahi detect hui. Clear photo upload karein.", 400
                x, y, w, h = cv2.boundingRect(coords)
                cropped = thresh[y:y+h, x:x+w]
                cropped = cv2.copyMakeBorder(cropped, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255,255,255])
                _, buf = cv2.imencode('.png', cropped)
                return send_file(io.BytesIO(buf), mimetype='image/png', as_attachment=True, download_name='clean_signature.png')

        except Exception as e:
            print("Error:", str(e))
            return "Server Error", 500

    return render_template_string(HTML, page_title="Snapzo Pro - Free AI Tools", page_desc="Free online passport photo maker, signature cleaner and more", request_path=request.path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
