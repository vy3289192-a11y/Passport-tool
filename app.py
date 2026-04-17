from flask import Flask, request, render_template_string, send_file, Response
import cv2
import numpy as np
import io
import requests
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

# 👇 यहाँ अपना Hugging Face वाला टोकन डालना है 👇
HF_API_TOKEN = "यहाँ_अपना_TOKEN_पेस्ट_करो"

def allowed_file(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.heic'))

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
        .typing-link { background: #ffde59 !important; color: #000 !important; font-weight: bold; border: 2px solid #eab308; }
        .typing-link:hover { background: #facc15 !important; transform: scale(1.05); }
        .new-badge { background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; margin-left: 5px; animation: pulse 1.5s infinite;}
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
        
        body.dark-mode { --bg: #0f172a; --card: #1e293b; --nav: #111827; --accent: #3b82f6; --text: #f1f5f9; --text-muted: #94a3b8; --border: #334155; --box-bg: #111827; --input-bg: #0f172a; }
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
        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); position: relative; }
        .upload-zone.small { padding: 20px 10px; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }
        input, select, textarea { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; width: 100%; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; color: var(--text); opacity: 0.8; font-weight: 500;}
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top:10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.4); }
        .progress-bar-container { width: 100%; background: var(--border); border-radius: 10px; margin-top: 15px; display: none; overflow: hidden; }
        .progress-bar { height: 8px; background: #10b981; width: 0%; transition: 0.3s; }
        .trust-section { width: 100%; max-width: 900px; text-align: center; padding: 50px 0; border-top: 1px solid var(--border); margin-top: 20px; }
        .trust-stats { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-bottom: 30px; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: var(--text); }
        .stat-label { font-size: 0.9rem; color: var(--text-muted); margin-top: 5px; }
        .footer { text-align: center; padding: 40px 20px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; color: var(--text); margin: 20px auto 0 auto;}
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }
        .seo-links { margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border); text-align: center; font-size: 0.85rem; color: var(--text-muted); line-height: 1.8; }
        .seo-links a { color: var(--accent); text-decoration: none; margin: 0 5px; font-weight: 500; }
        @media (max-width: 900px) {
            .tool-wrapper.active { flex-direction: column; align-items: center; gap: 30px; }
            .card { order: 1; width: 100%; max-width: 100%; padding: 30px 20px; margin-bottom: 0; }
            .tool-content { order: 2; text-align: center; width: 100%; margin-bottom: 10px; flex: auto;}
            .how-to-use { order: 3; margin-top: 20px; text-align: center;}
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
                <a href="/remove-background" class="menu-btn" onclick="switchTool('removebg', event)" id="d-removebg">Remove BG <span class="new-badge">AI</span></a>
                <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="d-passport">Passport Maker</a>
                <a href="/id-card-print" class="menu-btn" onclick="switchTool('idcard', event)" id="d-idcard">ID Card Print</a>
                <a href="/signature-cleaner" class="menu-btn" onclick="switchTool('sign', event)" id="d-sign">Sign Cleaner</a>
                <a href="/photo-sign-joiner" class="menu-btn" onclick="switchTool('joiner', event)" id="d-joiner">Photo+Sign Join</a>
                <a href="/image-to-pdf" class="menu-btn" onclick="switchTool('pdf', event)" id="d-pdf">Image to PDF</a>
                <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)" id="d-compress">Compress</a>
                <a href="/convert-format" class="menu-btn" onclick="switchTool('format', event)" id="d-format">Format</a>
            </div>
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.3rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()" style="margin-left: 10px;"></i>
        </div>
    </div>
    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Snapzo Menu</h3>
        <a href="/remove-background" class="menu-btn" onclick="switchTool('removebg', event)" id="m-removebg"><i class="fas fa-eraser"></i> Remove BG <span class="new-badge">AI</span></a>
        <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="m-passport"><i class="fas fa-id-badge"></i> Passport Maker</a>
        <a href="/id-card-print" class="menu-btn" onclick="switchTool('idcard', event)" id="m-idcard"><i class="fas fa-address-card"></i> ID Card Print</a>
        <a href="/signature-cleaner" class="menu-btn" onclick="switchTool('sign', event)" id="m-sign"><i class="fas fa-signature"></i> Signature Cleaner</a>
        <a href="/photo-sign-joiner" class="menu-btn" onclick="switchTool('joiner', event)" id="m-joiner"><i class="fas fa-object-group"></i> Photo + Sign Join</a>
        <a href="/image-to-pdf" class="menu-btn" onclick="switchTool('pdf', event)" id="m-pdf"><i class="fas fa-images"></i> Image to PDF</a>
        <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)" id="m-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</a>
        <a href="/convert-format" class="menu-btn" onclick="switchTool('format', event)" id="m-format"><i class="fas fa-exchange-alt"></i> Convert Format</a>
    </div>
    <div class="main">
        
        <div class="tool-wrapper" id="tool-removebg">
            <div class="tool-content">
                <h1>AI Background Remover</h1>
                <p>Upload any photo and our deep-learning AI will automatically detect the subject and remove the background in seconds. 100% Free.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Clean, Transparent PNG Output</li>
                    <li><i class="fas fa-check-circle"></i> High Quality Edge Detection</li>
                    <li><i class="fas fa-check-circle"></i> Powered by Hugging Face AI</li>
                </ul>
            </div>
            <div class="card">
                <h2>Remove Background</h2>
                <form method="POST" enctype="multipart/form-data" id="bgForm" onsubmit="showLoading()">
                    <input type="hidden" name="tool_type" value="removebg">
                    <div class="upload-zone" onclick="document.getElementById('f-rmbg').click()">
                        <input type="file" id="f-rmbg" name="file" hidden required onchange="handlePreview(this, 'p-rmbg', 't-rmbg')">
                        <div id="t-rmbg"><i class="fas fa-magic" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-rmbg" class="preview-img">
                    </div>
                    <button class="btn" id="bgBtn"><i class="fas fa-eraser"></i> Remove Background</button>
                    <p id="bgLoading" style="display:none; color:var(--accent); font-weight:bold; text-align:center; margin-top:10px;"><i class="fas fa-spinner fa-spin"></i> AI is processing... please wait 5-10 seconds.</p>
                </form>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Remove Background?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload">
                        <h4>1. Upload Photo</h4>
                        <p>Select any image from your device.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="AI Magic">
                        <h4>2. AI Magic</h4>
                        <p>Our AI scans the image and perfectly isolates the main subject.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download">
                        <h4>3. Download PNG</h4>
                        <p>Instantly download your transparent image!</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>{{ passport_h1 | default('Strict AI Passport Maker') }}</h1>
                <p>{{ passport_p | default('Turn a regular photo into an official passport photo fast. Hamara AI strictly 3.5x4.5 ratio use karta hai taaki SSC/RRB forms me koi galti na ho.') }}</p>
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
            </div>
        </div>

        <div class="tool-wrapper" id="tool-idcard">
            <div class="tool-content">
                <h1>ID Card Print Studio</h1>
                <p>Aadhar Card ya PAN Card ki Front aur Back photo ko ek perfect A4 size PDF mein merge karein. Cyber cafe jane ki zarurat nahi!</p>
            </div>
            <div class="card">
                <h2>Aadhar/PAN Joiner</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="idcard">
                    <div class="row">
                        <div class="group">
                            <label>Front Side</label>
                            <div class="upload-zone small" onclick="document.getElementById('f-id-front').click()">
                                <input type="file" id="f-id-front" name="front" hidden required onchange="handlePreview(this, 'p-id-front', 't-id-front')">
                                <div id="t-id-front"><i class="fas fa-id-card" style="font-size:2rem; color:var(--accent);"></i><p style="margin:5px 0 0; font-size:0.8rem;">Upload Front</p></div>
                                <img id="p-id-front" class="preview-img" style="margin-top:5px;">
                            </div>
                        </div>
                        <div class="group">
                            <label>Back Side</label>
                            <div class="upload-zone small" onclick="document.getElementById('f-id-back').click()">
                                <input type="file" id="f-id-back" name="back" hidden required onchange="handlePreview(this, 'p-id-back', 't-id-back')">
                                <div id="t-id-back"><i class="fas fa-id-card-alt" style="font-size:2rem; color:var(--accent);"></i><p style="margin:5px 0 0; font-size:0.8rem;">Upload Back</p></div>
                                <img id="p-id-back" class="preview-img" style="margin-top:5px;">
                            </div>
                        </div>
                    </div>
                    <button class="btn"><i class="fas fa-print"></i> Generate Print PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-sign">
            <div class="tool-content">
                <h1>Auto-Signature Cleaner</h1>
                <p>Copy par kiye gaye sign ko upload karein. Hamara AI background ko pure white aur pen ink ko dark black kar dega.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="sign">
                    <div class="upload-zone" onclick="document.getElementById('f-sign').click()">
                        <input type="file" id="f-sign" name="file" hidden required onchange="handlePreview(this, 'p-sign', 't-sign')">
                        <div id="t-sign"><i class="fas fa-signature" style="font-size:3rem; color:var(--accent);"></i><p>Upload Raw Signature</p></div>
                        <img id="p-sign" class="preview-img">
                    </div>
                    <button class="btn"><i class="fas fa-magic"></i> Clean & Resize</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-joiner">
            <div class="tool-content">
                <h1>Photo + Sign Joiner</h1>
                <p>Passport Photo ke theek niche apna Signature merge karein sirf ek click mein.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="joiner">
                    <div class="row">
                        <div class="group">
                            <label>Passport Photo</label>
                            <div class="upload-zone small" onclick="document.getElementById('f-join-photo').click()">
                                <input type="file" id="f-join-photo" name="photo" hidden required onchange="handlePreview(this, 'p-join-photo', 't-join-photo')">
                                <div id="t-join-photo"><i class="fas fa-user" style="font-size:2rem; color:var(--accent);"></i><p style="margin:5px 0 0; font-size:0.8rem;">Upload Photo</p></div>
                                <img id="p-join-photo" class="preview-img" style="margin-top:5px;">
                            </div>
                        </div>
                        <div class="group">
                            <label>Signature</label>
                            <div class="upload-zone small" onclick="document.getElementById('f-join-sign').click()">
                                <input type="file" id="f-join-sign" name="sign" hidden required onchange="handlePreview(this, 'p-join-sign', 't-join-sign')">
                                <div id="t-join-sign"><i class="fas fa-signature" style="font-size:2rem; color:var(--accent);"></i><p style="margin:5px 0 0; font-size:0.8rem;">Upload Sign</p></div>
                                <img id="p-join-sign" class="preview-img" style="margin-top:5px;">
                            </div>
                        </div>
                    </div>
                    <button class="btn"><i class="fas fa-object-group"></i> Merge Together</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Images to PDF</h1>
                <p>Combine multiple marksheets or documents into a single PDF file securely.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('f-pdf').click()">
                        <input type="file" id="f-pdf" name="file" hidden required multiple onchange="handleMultiple(this)">
                        <div id="t-pdf"><i class="fas fa-file-upload" style="font-size:3rem; color:var(--accent);"></i><p>Select Multiple Photos</p></div>
                        <div id="pdf-count" style="display:none; font-weight:bold; color:var(--accent);"></div>
                    </div>
                    <button class="btn">Generate PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content">
                <h1>Smart Image Compressor</h1>
                <p>Reduce photo size accurately for online form uploads without losing visual quality.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="compress">
                    <div class="upload-zone" onclick="document.getElementById('f-comp').click()">
                        <input type="file" id="f-comp" name="file" hidden required onchange="handlePreview(this, 'p-comp', 't-comp')">
                        <div id="t-comp"><i class="fas fa-compress-arrows-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-comp" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group">
                            <label>Target File Size (In KB)</label>
                            <input type="number" name="target_kb" value="50" placeholder="E.g., 50">
                        </div>
                    </div>
                    <button class="btn">Smart Compress</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-format">
            <div class="tool-content">
                <h1>Format Converter</h1>
                <p>Convert any image format instantly. Supports JPG, PNG, WEBP, BMP, and TIFF.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="format">
                    <div class="upload-zone" onclick="document.getElementById('fileInputFormat').click()">
                        <input type="file" name="file" id="fileInputFormat" hidden required onchange="handlePreview(this, 'preview-format', 'drop-text-format')">
                        <div id="drop-text-format">
                            <i class="fas fa-exchange-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                            <p style="margin:0"><b>Upload Image</b></p>
                        </div>
                        <img id="preview-format" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group">
                            <label>Convert To</label>
                            <select name="out_format"><option value="jpg">JPG (Standard)</option><option value="png">PNG (High Quality)</option><option value="webp">WEBP (Web Optimized)</option></select>
                        </div>
                    </div>
                    <button type="submit" class="btn">Convert & Download</button>
                </form>
            </div>
        </div>

        <div class="trust-section">
            <div class="trust-stats">
                <div class="stat-item"><div class="stat-value">4.9 ⭐</div><div class="stat-label">User Rating</div></div>
                <div class="stat-item"><div class="stat-value">Fast & Free</div><div class="stat-label">No Login Required</div></div>
                <div class="stat-item"><div class="stat-value">100% Private</div><div class="stat-label">Files Auto Delete</div></div>
            </div>
        </div>
        
        <div class="footer">
            <div style="max-width:1100px; margin:0 auto; padding:30px 20px; text-align:center;">
                <p style="font-size:1.1rem; margin-bottom:10px;">Built with ❤️ by <b>Vishal</b> from Varanasi</p>
                <p style="color:var(--text-muted); margin-bottom:25px;">Free AI tools for SSC, RRB, UPSC, PAN, Aadhaar and other government forms</p>
                <a href="https://www.instagram.com/rry.vishal" target="_blank" class="insta-btn"><i class="fab fa-instagram"></i> Follow on Instagram @rry.vishal</a>
            </div>
        </div>
    </div>

    <script>
        const routeMap = {
            'removebg': 'remove-background',
            'passport': 'passport-maker',
            'idcard': 'id-card-print',
            'sign': 'signature-cleaner',
            'joiner': 'photo-sign-joiner',
            'pdf': 'image-to-pdf',
            'compress': 'compress',
            'format': 'convert-format'
        };
        
        const pathMap = {
            '/remove-background': 'removebg',
            '/passport-maker': 'passport',
            '/id-card-print': 'idcard',
            '/signature-cleaner': 'sign',
            '/photo-sign-joiner': 'joiner',
            '/image-to-pdf': 'pdf',
            '/compress': 'compress',
            '/convert-format': 'format'
        };

        function toggleTheme() { document.body.classList.toggle('dark-mode'); }
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }
        function switchTool(name, event) {
            if(event) event.preventDefault();
            const tools = ['removebg', 'passport', 'idcard', 'sign', 'joiner', 'pdf', 'compress', 'format'];
            tools.forEach(t => {
                const el = document.getElementById('tool-'+t);
                if(el) { if (t === name) el.classList.add('active'); else el.classList.remove('active'); }
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) { if (t === name) deskBtn.classList.add('active-menu'); else deskBtn.classList.remove('active-menu'); }
                const mobBtn = document.getElementById('m-'+t);
                if(mobBtn) { if (t === name) mobBtn.classList.add('active-menu'); else mobBtn.classList.remove('active-menu'); }
            });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            let targetPath = window.location.pathname;
            if(event) {
                targetPath = '/' + routeMap[name];
                if(window.location.pathname !== targetPath) { window.history.pushState(null, null, targetPath); }
            }
            if(window.innerWidth <= 900) { document.getElementById('sidebar').classList.remove('active'); document.getElementById('overlay').classList.remove('active'); }
        }
        window.onload = function() {
            let path = window.location.pathname;
            if(pathMap[path]) switchTool(pathMap[path], null);
            else if (path !== '/') switchTool('passport', null);
        };
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
        function handleMultiple(input) {
            const div = document.getElementById('pdf-count');
            div.innerText = input.files.length + " Images Selected ✅";
            div.style.display = 'block'; document.getElementById('t-pdf').style.display = 'none';
        }
        function showLoading() {
            document.getElementById('bgBtn').style.display = 'none';
            document.getElementById('bgLoading').style.display = 'block';
        }
    </script>
</body>
</html>
'''

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

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def home(path):
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')
            
            # 🟢 NEW: HUGGING FACE REMOVE BACKGROUND LOGIC 🟢
            if tool_type == 'removebg':
                file = request.files.get('file')
                if not file or not allowed_file(file.filename):
                    return "Invalid file type. Please upload a photo.", 400
                
                # API URL for Bria AI Background Removal Model
                api_url = "https://api-inference.huggingface.co/models/briaai/RMBG-1.4"
                headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
                
                try:
                    img_bytes = file.read()
                    response = requests.post(api_url, headers=headers, data=img_bytes)
                    
                    if response.status_code == 200:
                        # Success! Return the transparent PNG
                        return send_file(io.BytesIO(response.content), mimetype='image/png', as_attachment=True, download_name='snapzopro_no_bg.png')
                    else:
                        return f"AI Server Error: {response.status_code}. Server par load hai, thodi der baad try karein.", 500
                except Exception as e:
                    return f"Error connecting to AI: {str(e)}", 500

            # OLD TOOLS BELOW (Untouched and Safe)
            if tool_type == 'idcard':
                f_front = request.files.get('front')
                f_back = request.files.get('back')

                if not f_front or not f_back:
                    return "Both front and back sides are required", 400

                img_f = cv2.imdecode(np.frombuffer(f_front.read(), np.uint8), cv2.IMREAD_COLOR)
                img_b = cv2.imdecode(np.frombuffer(f_back.read(), np.uint8), cv2.IMREAD_COLOR)

                if img_f is None or img_b is None:
                    return "Invalid image files", 400

                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                _, buf_f = cv2.imencode('.jpg', img_f)
                c.drawImage(ImageReader(io.BytesIO(buf_f)), 120, 520, width=340, height=210)
                _, buf_b = cv2.imencode('.jpg', img_b)
                c.drawImage(ImageReader(io.BytesIO(buf_b)), 120, 280, width=340, height=210)

                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='id_card_print.pdf')
            
            if tool_type == 'sign':
                file = request.files.get('file')
                img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                coords = cv2.findNonZero(255 - thresh)
                x, y, w, h = cv2.boundingRect(coords)
                cropped = thresh[y:y+h, x:x+w]
                cropped = cv2.copyMakeBorder(cropped, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                _, buf = cv2.imencode('.png', cropped)
                return send_file(io.BytesIO(buf), mimetype='image/png', as_attachment=True, download_name='clean_signature.png')

            if tool_type == 'joiner':
                f_photo = request.files.get('photo')
                f_sign = request.files.get('sign')
                img_p = cv2.imdecode(np.frombuffer(f_photo.read(), np.uint8), cv2.IMREAD_COLOR)
                img_s = cv2.imdecode(np.frombuffer(f_sign.read(), np.uint8), cv2.IMREAD_COLOR)
                face = cv2.resize(strict_passport_crop(img_p), (413, 531))
                sign_resized = cv2.resize(img_s, (413, 150))
                merged = np.vstack((face, sign_resized))
                _, buf = cv2.imencode('.jpg', merged)
                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='photo_sign_merged.jpg')
            
            if tool_type == 'pdf':
                files = request.files.getlist('file')
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                for f in files:
                    img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        if img.shape[1] > 1500: img = cv2.resize(img, (1000, int(img.shape[0]*1000/img.shape[1])))
                        _, buf = cv2.imencode('.jpg', img)
                        c.drawImage(ImageReader(io.BytesIO(buf)), 50, 50, width=500, height=700)
                        c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_scanned.pdf')
            
            file = request.files.get('file')
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            
            if tool_type == 'passport':
                face = cv2.resize(strict_passport_crop(img), (413, 531))
                bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[245, 245, 245])
                bh, bw = bordered.shape[:2]
                canvas = np.ones((2500, 1800, 3), dtype=np.uint8) * 255
                count = max(1, min(int(request.form.get("count", 8)), 12))
                for i in range(count):
                    r, c = i // 3, i % 3
                    canvas[r * (bh + 40) + 70 : r * (bh + 40) + 70 + bh, c * (bw + 30) + 70 : c * (bw + 30) + 70 + bw] = bordered
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
            
            elif tool_type == 'compress':
                target_kb = int(request.form.get("target_kb", 50))
                target_bytes = target_kb * 1024
                quality = 92
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, buffer = cv2.imencode('.jpg', img, encode_param)
                while len(buffer) > target_bytes and quality > 20:
                    quality -= 5
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                    _, buffer = cv2.imencode('.jpg', img, encode_param)
                if len(buffer) > target_bytes:
                    scale = 0.95
                    while len(buffer) > target_bytes and scale > 0.4:
                        scale -= 0.05
                        resized = cv2.resize(img, (int(img.shape[1] * scale), int(img.shape[0] * scale)), interpolation=cv2.INTER_AREA)
                        _, buffer = cv2.imencode('.jpg', resized, encode_param)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name=f'compressed_{target_kb}kb.jpg')
            
            elif tool_type == 'format':
                f = request.form.get('out_format', 'png')
                _, buffer = cv2.imencode(f'.{f}', img)
                mime = f'image/{f}' if f != 'jpg' else 'image/jpeg'
                return send_file(io.BytesIO(buffer), mimetype=mime, as_attachment=True, download_name=f'converted.{f}')
                
        except Exception as e:
            print("Error:", str(e))
            return "Server Error! Please try again.", 500

    page_title = "Snapzo Pro | Free Online Utility Tools"
    page_desc = "Free AI tools for SSC, RRB, UPSC & government exams."
    return render_template_string(HTML, page_title=page_title, page_desc=page_desc, request_path="/" + path)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
