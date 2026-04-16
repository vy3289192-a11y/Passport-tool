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
    return filename.lower().endswith(('.png','.jpg','.jpeg','.webp'))

def strict_passport_crop(img):
    h, w = img.shape[:2]
    target_ratio = 0.777
    if (w / h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.15)
        return img[offset:offset+new_h, :]

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
            --bg: #f8fafc;
            --card: #ffffff;
            --nav: #ffffff;
            --accent: #2563eb;
            --text: #1e293b;
            --text-muted: #475569;
            --border: #e2e8f0;
            --box-bg: #f1f5f9;
            --input-bg: #ffffff;
        }
        .typing-link {
            background: #ffde59 !important;
            color: #000 !important;
            font-weight: bold;
            border: 2px solid #eab308;
        }
        body.dark-mode {
            --bg: #0f172a;
            --card: #1e293b;
            --nav: #111827;
            --accent: #3b82f6;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
            --box-bg: #111827;
            --input-bg: #0f172a;
        }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; width: 100vw; max-width: 100%; transition: background 0.3s, color 0.3s; }
       
        .privacy-banner { background: #10b981; color: white; text-align: center; padding: 6px; font-size: 0.85rem; font-weight: bold; letter-spacing: 0.5px; }
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .desktop-menu { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }
        .menu-btn { text-decoration: none; padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; color: var(--text); display: inline-block; white-space: nowrap; font-weight: 500; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white; }
        .mobile-toggle { display: none; font-size: 1.5rem; cursor: pointer; color: var(--accent); }
        .sidebar { width: 250px; height: 100vh; background: var(--nav); position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; overflow-y: auto; border-right: 1px solid var(--border); }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { display: flex; text-decoration: none; align-items: center; gap: 15px; color: var(--text); border-radius: 8px; margin-bottom: 10px; transition: 0.2s; padding: 15px; font-size: 1rem; }
        .sidebar .menu-btn:hover, .sidebar .active-menu { background: var(--accent); color: white; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }
        .main { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; width: 100%; }
       
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; flex-wrap: wrap; }
        .tool-wrapper.active { display: flex; }
       
        .tool-content { flex: 1.2; text-align: left; order: 1; }
        .tool-content h1 { font-size: 2.2rem; color: var(--text); margin: 0 0 15px 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.05rem; line-height: 1.6; color: var(--text); opacity: 0.9; }
       
        .feature-list { list-style: none; padding: 0; margin: 15px 0; }
        .feature-list li { margin-bottom: 12px; display: flex; align-items: center; gap: 10px; color: var(--text); }
        .feature-list i { color: #10b981; }
       
        .visual-box { background: var(--box-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; color: var(--text); }
       
        .how-to-use { width: 100%; margin-top: 40px; border-top: 1px solid var(--border); padding-top: 25px; order: 3; }
        .how-to-use h3 { color: var(--text); font-size: 1.2rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 10px;}
        .step-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .step-card { background: var(--box-bg); padding: 12px; border-radius: 12px; text-align: center; border: 1px solid var(--border); }
        .step-card img { width: 100%; height: 90px; object-fit: cover; border-radius: 8px; margin-bottom: 10px; opacity: 0.9; }
        .step-card h4 { margin: 0 0 5px 0; color: var(--accent); font-size: 0.95rem; }
        .step-card p { margin: 0; font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; }
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid var(--border); order: 2; }
        .card h2 { margin-top: 0; text-align: center; font-size: 1.6rem; color: var(--text); margin-bottom: 20px; }
        .text-page-card { background: var(--card); padding: 40px; border-radius: 24px; width: 100%; max-width: 900px; margin: 0 auto; box-shadow: 0 15px 35px rgba(0,0,0,0.05); border: 1px solid var(--border); color: var(--text); line-height: 1.8; text-align: left; }
        .text-page-card h1 { color: var(--accent); margin-top: 0; font-size: 2.2rem; border-bottom: 2px solid var(--border); padding-bottom: 15px; margin-bottom: 20px;}
        .text-page-card h2 { color: var(--text); margin-top: 25px; font-size: 1.4rem; }
        .text-page-card p { color: var(--text-muted); font-size: 1.05rem; margin-bottom: 15px; }
        .text-page-card ul { color: var(--text-muted); margin-bottom: 20px; }
        .text-page-card a { color: var(--accent); text-decoration: none; font-weight: bold; }
        .text-page-card a:hover { text-decoration: underline; }
        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); position: relative; }
        .upload-zone.small { padding: 20px 10px; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }
        input, select, textarea { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; width: 100%; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; color: var(--text); opacity: 0.8; font-weight: 500;}
      
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top:10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.4); }
        #toolbar-container { background: var(--box-bg); border-radius: 10px 10px 0 0; border: 1px solid var(--border); border-bottom: none; }
        #editor-container { border-radius: 0 0 10px 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); height: 250px; font-size: 1rem; font-family: 'Segoe UI', sans-serif; }
        .ql-toolbar.ql-snow + .ql-container.ql-snow { border: 1px solid var(--border); }
        .ql-snow .ql-stroke { stroke: var(--text); }
        .ql-snow .ql-fill { fill: var(--text); }
        .ql-snow .ql-picker { color: var(--text); }
        .progress-bar-container { width: 100%; background: var(--border); border-radius: 10px; margin-top: 15px; display: none; overflow: hidden; }
        .progress-bar { height: 8px; background: #10b981; width: 0%; transition: 0.3s; }
        .trust-section { width: 100%; max-width: 900px; text-align: center; padding: 50px 0; border-top: 1px solid var(--border); margin-top: 20px; }
        .trust-stats { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-bottom: 30px; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: var(--text); }
        .stat-label { font-size: 0.9rem; color: var(--text-muted); margin-top: 5px; }
        .footer { text-align: center; padding: 40px 20px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; color: var(--text); margin-top: 20px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }
        .seo-links { margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border); text-align: center; font-size: 0.85rem; color: var(--text-muted); line-height: 1.8; }
        .seo-links a { color: var(--accent); text-decoration: none; margin: 0 5px; font-weight: 500; }
        .seo-links a:hover { text-decoration: underline; }
        .check-container { display: flex; align-items: center; gap: 10px; margin-top: 15px; background: rgba(59,130,246,0.1); padding: 10px 15px; border-radius: 8px; }
        .check-container input { width: 20px; height: 20px; cursor: pointer; }
        .check-container label { margin-bottom: 0; cursor: pointer; opacity: 1; color: var(--accent); font-weight: bold; }
        .footer-links { text-align: center; margin-bottom: 30px; }
        .footer-links h4 { color: var(--text); margin-bottom: 20px; font-size: 1.2rem; }
        .f-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; }
        .f-grid a { color: var(--text-muted); text-decoration: none; font-size: 0.9rem; transition: 0.2s; background: var(--box-bg); padding: 10px 18px; border-radius: 8px; border: 1px solid var(--border); font-weight: 500; }
        .f-grid a:hover { background: var(--accent); color: white; border-color: var(--accent); transform: translateY(-2px); }
        .tool-card { border: 1px solid var(--border); background: var(--box-bg); padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center; }
        .tool-card h3 { color: var(--text); margin: 10px 0; }
        .tool-card p { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 15px; }
        @media (max-width: 900px) {
            .tool-wrapper.active { flex-direction: column; align-items: center; gap: 30px; }
            .card { order: 1; width: 100%; max-width: 100%; padding: 30px 20px; margin-bottom: 0; }
            .tool-content { order: 2; text-align: center; width: 100%; margin-bottom: 10px; flex: auto;}
            .how-to-use { order: 3; margin-top: 20px; text-align: center;}
            .feature-list li { justify-content: center; }
            .visual-box { margin: 0 auto 25px auto; }
            .how-to-use h3 { justify-content: center; }
            .step-grid { grid-template-columns: 1fr; gap: 10px; }
            .text-page-card { padding: 30px 20px; }
            .desktop-menu { display: none; }
            .mobile-toggle { display: block; }
        }
    </style>
</head>
<body>
    <div class="privacy-banner">
        <i class="fas fa-shield-alt"></i> 100% Secure & Private • Files are automatically deleted after processing
    </div>
    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right" style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <a href="https://typing.snapzopro.online" class="menu-btn typing-link"><i class="fas fa-keyboard"></i> Hindi Typing</a>
                <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="d-passport">Passport Maker</a>
                <a href="/id-card-print" class="menu-btn" onclick="switchTool('idcard', event)" id="d-idcard">ID Card Print</a>
                <a href="/signature-cleaner" class="menu-btn" onclick="switchTool('sign', event)" id="d-sign">Sign Cleaner</a>
                <a href="/photo-sign-joiner" class="menu-btn" onclick="switchTool('joiner', event)" id="d-joiner">Photo+Sign Join</a>
                <a href="/image-to-text" class="menu-btn" onclick="switchTool('img2text', event)" id="d-img2text">Image to Text</a>
                <a href="/text-to-pdf" class="menu-btn" onclick="switchTool('textpdf', event)" id="d-textpdf">Text to PDF</a>
                <a href="/image-to-pdf" class="menu-btn" onclick="switchTool('pdf', event)" id="d-pdf">Image to PDF</a>
                <a href="/image-crop" class="menu-btn" onclick="switchTool('crop', event)" id="d-crop">Crop</a>
                <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)" id="d-compress">Compress</a>
                <a href="/social-size" class="menu-btn" onclick="switchTool('social', event)" id="d-social">More Tools <i class="fas fa-caret-down"></i></a>
            </div>
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.3rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()" style="margin-left: 10px;"></i>
        </div>
    </div>
    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Snapzo Menu</h3>
        <a href="https://typing.snapzopro.online" class="menu-btn typing-link"><i class="fas fa-keyboard"></i> Hindi Typing</a>
        <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="m-passport"><i class="fas fa-id-badge"></i> Passport Maker</a>
        <a href="/id-card-print" class="menu-btn" onclick="switchTool('idcard', event)" id="m-idcard"><i class="fas fa-address-card"></i> ID Card Print</a>
        <a href="/signature-cleaner" class="menu-btn" onclick="switchTool('sign', event)" id="m-sign"><i class="fas fa-signature"></i> Signature Cleaner</a>
        <a href="/photo-sign-joiner" class="menu-btn" onclick="switchTool('joiner', event)" id="m-joiner"><i class="fas fa-object-group"></i> Photo + Sign Joiner</a>
        <a href="/image-to-text" class="menu-btn" onclick="switchTool('img2text', event)" id="m-img2text"><i class="fas fa-file-word"></i> Image to Text (OCR)</a>
        <a href="/text-to-pdf" class="menu-btn" onclick="switchTool('textpdf', event)" id="m-textpdf"><i class="fas fa-file-alt"></i> Text to PDF</a>
        <a href="/image-to-pdf" class="menu-btn" onclick="switchTool('pdf', event)" id="m-pdf"><i class="fas fa-images"></i> Image to PDF</a>
        <a href="/image-crop" class="menu-btn" onclick="switchTool('crop', event)" id="m-crop"><i class="fas fa-crop-alt"></i> Manual Crop</a>
        <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)" id="m-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</a>
        <a href="/social-size" class="menu-btn" onclick="switchTool('social', event)" id="m-social"><i class="fas fa-share-alt"></i> Social Size</a>
        <a href="/convert-format" class="menu-btn" onclick="switchTool('format', event)" id="m-format"><i class="fas fa-exchange-alt"></i> Convert Format</a>
    </div>
    <div class="main">
      
        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>Strict AI Passport Maker</h1>
                <p>Turn a regular photo into an official passport photo fast. Hamara AI strictly 3.5x4.5 ratio use karta hai taaki SSC/RRB forms me koi galti na ho.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Permanent 413x531 Pixels (Official Size)</li>
                    <li><i class="fas fa-check-circle"></i> Auto-Print Name & Date on Photo</li>
                    <li><i class="fas fa-check-circle"></i> Multiple Copies Ready to Print</li>
                </ul>
            </div>
          
            <div class="card">
                <h2>Passport Studio</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:3rem; color:var(--accent);"></i><p>Upload any Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <div class="row" style="margin-bottom:0;">
                        <div class="group"><label>Print Name (Optional)</label><input type="text" name="print_name" placeholder="E.g., VISHAL YADAV"></div>
                        <div class="group"><label>Print Date (Optional)</label><input type="text" name="print_date" placeholder="E.g., 10/04/2026"></div>
                    </div>
                    <div class="row">
                        <div class="group"><label>Quantity</label><input type="number" name="count" value="8"></div>
                        <div class="group"><label>Format</label><select name="type"><option value="jpg">JPG Image</option><option value="pdf">PDF Document</option></select></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Generate Photo</button>
                </form>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/ssc-photo-maker" onclick="switchTool('passport', event)">SSC Photo Maker</a> |
                    <a href="/rrb-photo-maker" onclick="switchTool('passport', event)">RRB Photo Maker</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Use Passport Maker?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Photo">
                        <h4>1. Upload Photo</h4>
                        <p>Select any normal front-facing photo from your mobile gallery.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Enter Details">
                        <h4>2. Add Name & Date</h4>
                        <p>Type your Name and Date. Our AI will print it perfectly on the photo.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download">
                        <h4>3. Download Print</h4>
                        <p>Select quantity and download ready-to-print A4 PDF instantly.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Baaki tools ke wrappers yahan paste kar sakte ho. Abhi sirf Passport active hai. -->

        <div class="trust-section">
            <div class="trust-stats">
                <div class="stat-item"><div class="stat-value">4.9 ⭐</div><div class="stat-label">User Rating</div></div>
                <div class="stat-item"><div class="stat-value">Fast & Free</div><div class="stat-label">No Login Required</div></div>
                <div class="stat-item"><div class="stat-value">100% Private</div><div class="stat-label">Files Auto Delete</div></div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div style="max-width:1100px; margin:0 auto; padding:30px 20px; text-align:center;">
            <p style="font-size:1.1rem; margin-bottom:10px;">
                Built with ❤️ by <b>Vishal</b> from Varanasi
            </p>
            <p style="color:var(--text-muted); margin-bottom:25px;">
                Free AI tools for SSC, RRB, UPSC, PAN, Aadhaar and other government forms
            </p>
            <a href="https://www.instagram.com/rry.vishal" target="_blank" class="insta-btn">
                <i class="fab fa-instagram"></i> Follow on Instagram @rry.vishal
            </a>
        </div>
        <div style="border-top:1px solid var(--border); padding:25px 20px; font-size:0.9rem; color:var(--text-muted); text-align:center;">
            <p>© 2026 Snapzo Pro • All tools are completely free</p>
            <p style="margin-top:10px;">
                <a href="/about" style="color:var(--accent); margin:0 12px;">About</a>
                <a href="/privacy" style="color:var(--accent); margin:0 12px;">Privacy</a>
                <a href="/terms" style="color:var(--accent); margin:0 12px;">Terms</a>
            </p>
        </div>
    </div>

    <script>
        let cropper;
        var quill = new Quill('#editor-container', {
            modules: { toolbar: '#toolbar-container' },
            placeholder: 'Start typing your document here...',
            theme: 'snow'
        });

        const routeMap = {
            'passport': 'passport-maker',
            'idcard': 'id-card-print',
            'sign': 'signature-cleaner',
            'joiner': 'photo-sign-joiner',
            'img2text': 'image-to-text',
            'textpdf': 'text-to-pdf',
            'pdf': 'image-to-pdf',
            'crop': 'image-crop',
            'compress': 'compress',
            'social': 'social-size',
            'format': 'convert-format',
            'about': 'about'
        };

        function toggleTheme() { document.body.classList.toggle('dark-mode'); }
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }
        function switchTool(name, event) {
            if(event) event.preventDefault();
            document.querySelectorAll('.tool-wrapper').forEach(t => t.classList.remove('active'));
            const el = document.getElementById('tool-' + name);
            if(el) el.classList.add('active');
        }
        function handlePreview(input, pId, tId) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    const img = document.getElementById(pId);
                    img.src = e.target.result; img.style.display = 'block';
                    document.getElementById(tId).style.display = 'none';
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
    </script>
</body>
</html>
'''

# ====================== BACKEND ======================
@app.route('/', methods=['GET', 'POST'])
@app.route('/passport-maker', methods=['GET', 'POST'])
@app.route('/id-card-print', methods=['GET', 'POST'])
@app.route('/signature-cleaner', methods=['GET', 'POST'])
@app.route('/photo-sign-joiner', methods=['GET', 'POST'])
@app.route('/image-to-text', methods=['GET', 'POST'])
@app.route('/about', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')

            if tool_type == 'sign':
                file = request.files.get('file')
                if not file or not allowed_file(file.filename):
                    return "Invalid or no file uploaded", 400
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                coords = cv2.findNonZero(255 - thresh)
                if coords is None:
                    return "Signature nahi detect hui. Clear aur bright photo upload karein.", 400
                x, y, w, h = cv2.boundingRect(coords)
                cropped = thresh[y:y+h, x:x+w]
                cropped = cv2.copyMakeBorder(cropped, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                _, buf = cv2.imencode('.png', cropped)
                return send_file(io.BytesIO(buf), mimetype='image/png', as_attachment=True, download_name='clean_signature.png')

            if tool_type == 'idcard':
                f_front = request.files.get('front')
                f_back = request.files.get('back')
                if not f_front or not f_back:
                    return "Both front and back sides are required", 400
                img_f = cv2.imdecode(np.frombuffer(f_front.read(), np.uint8), cv2.IMREAD_COLOR)
                img_b = cv2.imdecode(np.frombuffer(f_back.read(), np.uint8), cv2.IMREAD_COLOR)
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                _, buf_f = cv2.imencode('.jpg', img_f)
                _, buf_b = cv2.imencode('.jpg', img_b)
                c.drawImage(ImageReader(io.BytesIO(buf_f)), 120, 520, width=340, height=210)
                c.drawImage(ImageReader(io.BytesIO(buf_b)), 120, 280, width=340, height=210)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='id_card_print.pdf')

            if tool_type == 'passport':
                face = cv2.resize(strict_passport_crop(img), (413, 531))
                print_name = request.form.get("print_name", "").strip().upper()
                print_date = request.form.get("print_date", "").strip()

                if print_name or print_date:
                    cv2.rectangle(face, (0, 531-90), (413, 531), (255,255,255), -1)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    if print_name and print_date:
                        n_size = cv2.getTextSize(print_name, font, 0.78, 2)[0]
                        cv2.putText(face, print_name, ((413 - n_size[0])//2, 531-58), font, 0.78, (0,0,0), 2, cv2.LINE_AA)
                        d_size = cv2.getTextSize(print_date, font, 0.62, 2)[0]
                        cv2.putText(face, print_date, ((413 - d_size[0])//2, 531-28), font, 0.62, (0,0,0), 2, cv2.LINE_AA)
                    elif print_name:
                        n_size = cv2.getTextSize(print_name, font, 0.82, 2)[0]
                        cv2.putText(face, print_name, ((413 - n_size[0])//2, 531-45), font, 0.82, (0,0,0), 2, cv2.LINE_AA)
                    elif print_date:
                        d_size = cv2.getTextSize(print_date, font, 0.72, 2)[0]
                        cv2.putText(face, print_date, ((413 - d_size[0])//2, 531-38), font, 0.72, (0,0,0), 2, cv2.LINE_AA)

                bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[245, 245, 245])
                bh, bw = bordered.shape[:2]
                canvas = np.ones((2500, 1800, 3), dtype=np.uint8) * 255
                count = max(1, min(int(request.form.get("count", 8)), 12))

                for i in range(count):
                    r, c = i // 3, i % 3
                    start_y = r * (bh + 40) + 70
                    start_x = c * (bw + 30) + 70
                    canvas[start_y:start_y + bh, start_x:start_x + bw] = bordered

                final = canvas[:((count-1)//3 + 1) * (bh + 40) + 100, :min(count, 3) * (bw + 30) + 100]
                _, buf = cv2.imencode('.jpg', final)

                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawImage(ImageReader(io.BytesIO(buf)), 50, 100, width=500, height=650)
                    c.save()
                    pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport_ready.pdf')

                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='passport_ready.jpg')

        except Exception as e:
            print("Error:", str(e))
            return "Some error occurred. Please try again with a smaller or clearer image.", 500

    return render_template_string(HTML, page_title="Snapzo Pro - Free AI Passport Photo Maker & Exam Tools", page_desc="Free online passport photo maker, signature cleaner and document tools", request_path=request.path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
