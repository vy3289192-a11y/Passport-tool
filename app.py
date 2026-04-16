from flask import Flask, request, render_template_string, send_file, Response
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
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "SoftwareApplication",
      "name": "Snapzo Pro",
      "operatingSystem": "All",
      "applicationCategory": "MultimediaApplication",
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.9",
        "reviewCount": "1200000"
      },
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "INR"
      },
      "image": "''' + LOGO_URL + '''",
      "description": "{{ page_desc }}"
    }
    </script>
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
        .typing-link:hover {
            background: #facc15 !important;
            transform: scale(1.05);
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
        .testimonials { width: 100%; max-width: 1100px; margin: 40px auto; padding: 0 10px; }
        .testi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; }
        .testi-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 30px; }
        .testi-header { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
        .testi-avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border); }
        .testi-info h4 { margin: 0; color: var(--text); }
        .testi-info p { margin: 3px 0 0; color: var(--text-muted); font-size: 0.9rem; }
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
        <div class="tool-wrapper" id="tool-idcard">
            <div class="tool-content">
                <h1>ID Card Print Studio</h1>
                <p>Aadhar Card ya PAN Card ki Front aur Back photo ko ek perfect A4 size PDF mein merge karein. Cyber cafe jane ki zarurat nahi!</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Perfect standard size alignment</li>
                    <li><i class="fas fa-check-circle"></i> High Quality PDF output</li>
                </ul>
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
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Use ID Card Joiner?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Front and Back">
                        <h4>1. Upload 2 Photos</h4>
                        <p>Upload the Front side and Back side of your Aadhar/PAN card.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="AI Align">
                        <h4>2. AI Processing</h4>
                        <p>Our tool will automatically resize and align them like a Cyber Cafe print.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download">
                        <h4>3. Get A4 PDF</h4>
                        <p>Download the final A4 size PDF and print it directly anywhere.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-sign">
            <div class="tool-content">
                <h1>Auto-Signature Cleaner</h1>
                <p>Copy par kiye gaye sign ko upload karein. Hamara AI background ko pure white aur pen ink ko dark black kar dega online forms ke liye.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Removes dark shadows automatically</li>
                    <li><i class="fas fa-check-circle"></i> Official Bank/Govt size ready</li>
                </ul>
            </div>
           
            <div class="card">
                <h2>Clean Signature</h2>
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
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Clean Signature?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Raw Sign">
                        <h4>1. Upload Raw Sign</h4>
                        <p>Sign on a blank paper, click a photo with your phone and upload it.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="AI Magic">
                        <h4>2. Background Removal</h4>
                        <p>AI will remove shadows, grey background, and make pen ink pure black.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download">
                        <h4>3. Download Official Sign</h4>
                        <p>Download the perfectly cropped, clean B&W signature for exams.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-joiner">
            <div class="tool-content">
                <h1>Photo + Sign Joiner</h1>
                <p>Govt exams (UPSC/State forms) ke liye Passport Photo ke theek niche apna Signature merge karein sirf ek click mein.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Perfect ratio maintained</li>
                    <li><i class="fas fa-check-circle"></i> No complex editing required</li>
                </ul>
            </div>
           
            <div class="card">
                <h2>Merge Photo & Sign</h2>
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
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Merge Photo & Sign?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Images">
                        <h4>1. Upload Files</h4>
                        <p>Upload your Passport Photo in first box and Signature in second box.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Auto Merge">
                        <h4>2. Auto Alignment</h4>
                        <p>System automatically resizes the signature and attaches it below the photo.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download Result">
                        <h4>3. Download Image</h4>
                        <p>Download the combined single JPG image, ready for form upload.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-img2text">
            <div class="tool-content">
                <h1>Image to Text (OCR)</h1>
                <p>Kisi bhi photo (Notes, Books, Screenshots) mein likha hua text instantly extract karein. Copy karein aur kahin bhi use karein.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> 100% Free Client-Side Processing</li>
                    <li><i class="fas fa-check-circle"></i> Keeps your data completely private</li>
                </ul>
            </div>
           
            <div class="card">
                <h2>Extract Text</h2>
                <div class="upload-zone" onclick="document.getElementById('f-ocr').click()">
                    <input type="file" id="f-ocr" accept="image/*" hidden onchange="startOCR(this)">
                    <div id="t-ocr"><i class="fas fa-font" style="font-size:3rem; color:var(--accent);"></i><p>Upload Image with Text</p></div>
                    <img id="p-ocr" class="preview-img">
                </div>
               
                <div id="ocr-loading" style="display:none; text-align:center; margin-top:15px; color:var(--accent); font-weight:bold;">
                    Extracting Text... <span id="ocr-percent">0%</span>
                    <div class="progress-bar-container" style="display:block;"><div class="progress-bar" id="ocr-bar"></div></div>
                </div>
                <textarea id="ocr-result" placeholder="Extracted text will appear here..." style="margin-top:20px; height:150px; display:none;" readonly></textarea>
                <button type="button" class="btn" id="btn-copy-ocr" style="display:none; background:#10b981; margin-top:15px;" onclick="copyOCRText()">
                    <i class="fas fa-copy"></i> Copy Extracted Text
                </button>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/extract-text-from-image" onclick="switchTool('img2text', event)">Extract Text From Image</a> |
                    <a href="/picture-to-text" onclick="switchTool('img2text', event)">Picture to Text</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Extract Text from Image?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Image">
                        <h4>1. Upload Image</h4>
                        <p>Select a screenshot, book page, or any image containing text.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="OCR Scan">
                        <h4>2. Automatic Scan</h4>
                        <p>Our advanced OCR scanner will read and extract characters securely in browser.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Copy Text">
                        <h4>3. Copy & Paste</h4>
                        <p>The extracted text will appear in the box. Click 'Copy' to use it anywhere.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-textpdf">
            <div class="tool-content">
                <h1>Rich Text to PDF</h1>
                <p>Type your notes, format them like MS Word (Bold, Italic, Lists) and convert them into a beautiful PDF document instantly.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Advance Text Formatting Options</li>
                    <li><i class="fas fa-check-circle"></i> Superfast Client-Side PDF Creation</li>
                </ul>
            </div>
           
            <div class="card" style="max-width: 100%;">
                <h2>Document Editor</h2>
                <div style="margin-bottom: 20px;">
                    <div id="toolbar-container">
                        <span class="ql-formats">
                            <select class="ql-header"></select>
                        </span>
                        <span class="ql-formats">
                            <button class="ql-bold"></button>
                            <button class="ql-italic"></button>
                            <button class="ql-underline"></button>
                        </span>
                        <span class="ql-formats">
                            <button class="ql-list" value="ordered"></button>
                            <button class="ql-list" value="bullet"></button>
                            <button class="ql-indent" value="-1"></button>
                            <button class="ql-indent" value="+1"></button>
                        </span>
                        <span class="ql-formats">
                            <select class="ql-align"></select>
                        </span>
                    </div>
                    <div id="editor-container"></div>
                </div>
                <button type="button" class="btn" onclick="downloadRichPDF()"><i class="fas fa-file-pdf"></i> Download PDF Document</button>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/text-to-pdf-converter" onclick="switchTool('textpdf', event)">Text to PDF Converter</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Convert Text to PDF?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Type Text">
                        <h4>1. Type / Paste Text</h4>
                        <p>Write your assignments, notes, or essays in our rich document editor.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Format Text">
                        <h4>2. Add Formatting</h4>
                        <p>Make headings, bold texts, or bullet points using the top toolbar.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download PDF">
                        <h4>3. Download PDF</h4>
                        <p>Click 'Download PDF' and get your formatted file instantly.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Images to PDF (Scanner)</h1>
                <p>Combine multiple marksheets or documents into a single PDF file securely.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Secure Offline Conversion</li>
                    <li><i class="fas fa-check-circle"></i> Magic Scan (Cleans dark shadows)</li>
                </ul>
            </div>
           
            <div class="card">
                <h2>Select Files</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('f-pdf').click()">
                        <input type="file" id="f-pdf" name="file" hidden required multiple onchange="handleMultiple(this)">
                        <div id="t-pdf"><i class="fas fa-file-upload" style="font-size:3rem; color:var(--accent);"></i><p>Select Multiple Photos</p></div>
                        <div id="pdf-count" style="display:none; font-weight:bold; color:var(--accent);"></div>
                    </div>
                    <div class="check-container">
                        <input type="checkbox" id="magic_scan" name="magic_scan" value="yes">
                        <label for="magic_scan">Apply "Magic Scan" Filter (For clear B&W documents)</label>
                    </div>
                    <button class="btn">Generate PDF</button>
                </form>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/jpg-to-pdf" onclick="switchTool('pdf', event)">JPG to PDF</a> |
                    <a href="/png-to-pdf" onclick="switchTool('pdf', event)">PNG to PDF</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Make Image to PDF?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Select Multiple Images">
                        <h4>1. Select Images</h4>
                        <p>Click upload and select one or multiple photos/marksheets from gallery.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Magic Scan">
                        <h4>2. Apply Filter (Optional)</h4>
                        <p>Check the "Magic Scan" box if you want a clear Black & White scanned look.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download PDF">
                        <h4>3. Generate PDF</h4>
                        <p>Click generate and all your images will be securely combined into one PDF.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content">
                <h1>Manual Crop Studio</h1>
                <p>Cut unwanted parts from your photo with full control online.</p>
            </div>
           
            <div class="card">
                <form method="POST" enctype="multipart/form-data" id="cropForm">
                    <input type="hidden" name="tool_type" value="crop">
                    <input type="hidden" name="x" id="cX"><input type="hidden" name="y" id="cY"><input type="hidden" name="width" id="cW"><input type="hidden" name="height" id="cH">
                    <div class="upload-zone" id="z-crop" onclick="document.getElementById('f-crop').click()">
                        <input type="file" id="f-crop" name="file" hidden required onchange="initCrop(this)">
                        <i class="fas fa-crop-alt" style="font-size:3rem; color:var(--accent);"></i><p>Select Image to Crop</p>
                    </div>
                    <div id="c-wrapper" style="display:none;"><img id="i-crop" style="max-width:100%;"></div>
                    <button type="button" class="btn" onclick="doCrop()" style="margin-top:15px;">Crop Now</button>
                </form>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/crop-photo-online" onclick="switchTool('crop', event)">Crop Photo Online</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Crop Photo?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Image">
                        <h4>1. Upload Image</h4>
                        <p>Select the image you want to cut or crop.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Adjust Box">
                        <h4>2. Adjust Crop Box</h4>
                        <p>Drag the edges of the blue box over the area you want to keep.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Save Image">
                        <h4>3. Crop & Save</h4>
                        <p>Click 'Crop Now' and download your perfectly cropped picture.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content">
                <h1>Smart Image Compressor</h1>
                <p>Reduce photo size accurately for online form uploads without losing visual quality.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Auto-Target Size (Just type desired KB)</li>
                    <li><i class="fas fa-check-circle"></i> Best for SSC, UPSC, IBPS Forms</li>
                </ul>
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
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/reduce-image-size" onclick="switchTool('compress', event)">Reduce Image Size</a> |
                    <a href="/compress-image-to-50kb" onclick="switchTool('compress', event)">Compress Image to 50KB</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Compress Image Size?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Large File">
                        <h4>1. Upload Large Photo</h4>
                        <p>Select your heavy MB photo that is getting rejected in forms.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Type Target KB">
                        <h4>2. Type Target KB</h4>
                        <p>Enter the exact KB size you want (Example: 50 KB).</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Compress">
                        <h4>3. Smart Compress</h4>
                        <p>Our AI will compress it below your target size without making it blurry.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-social">
            <div class="tool-content">
                <h1>Social Media Resizer</h1>
                <p>Perfect size for YouTube Thumbnails, Instagram or FB.</p>
            </div>
           
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="social">
                    <div class="upload-zone" onclick="document.getElementById('f-soc').click()">
                        <input type="file" id="f-soc" name="file" hidden required onchange="handlePreview(this, 'p-soc', 't-soc')">
                        <div id="t-soc"><i class="fas fa-share-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-soc" class="preview-img">
                    </div>
                    <div class="row"><div class="group"><label>Platform</label><select name="platform"><option value="yt">YouTube Thumbnail</option><option value="insta">Instagram Post</option><option value="fb">Facebook Cover</option></select></div></div>
                    <button class="btn">Resize Now</button>
                </form>
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/youtube-thumbnail-resizer" onclick="switchTool('social', event)">YouTube Thumbnail Resizer</a> |
                    <a href="/instagram-photo-resizer" onclick="switchTool('social', event)">Instagram Photo Resizer</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Resize Photo?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload Media">
                        <h4>1. Upload Media</h4>
                        <p>Select the image you want to resize for social media.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Select Platform">
                        <h4>2. Select Platform</h4>
                        <p>Choose YouTube Thumbnail, Instagram Post, or Facebook Cover.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Download Ready">
                        <h4>3. Download Ready</h4>
                        <p>Download the image with perfect dimensions, ready to upload.</p>
                    </div>
                </div>
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
                            <select name="out_format">
                                <option value="jpg">JPG (Standard)</option>
                                <option value="png">PNG (High Quality)</option>
                                <option value="webp">WEBP (Web Optimized)</option>
                                <option value="bmp">BMP (Bitmap)</option>
                                <option value="tiff">TIFF (Print Quality)</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn">Convert & Download</button>
                </form>
               
                <div class="seo-links">
                    <p style="margin-bottom:5px;">Popular Searches:</p>
                    <a href="/jpg-to-png" onclick="switchTool('format', event, 'png')">JPG to PNG</a> |
                    <a href="/png-to-jpg" onclick="switchTool('format', event, 'jpg')">PNG to JPG</a> |
                    <a href="/webp-to-jpg" onclick="switchTool('format', event, 'jpg')">WEBP to JPG</a>
                </div>
            </div>
            <div class="how-to-use">
                <h3><i class="fas fa-question-circle"></i> How to Convert Image Format?</h3>
                <div class="step-grid">
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=300&q=80" alt="Upload File">
                        <h4>1. Upload File</h4>
                        <p>Upload your WEBP, PNG, or any image file.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=300&q=80" alt="Choose Format">
                        <h4>2. Choose Format</h4>
                        <p>Select the new format you need (like JPG or PNG) from the dropdown.</p>
                    </div>
                    <div class="step-card">
                        <img src="https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=300&q=80" alt="Convert">
                        <h4>3. Convert & Download</h4>
                        <p>Click Convert and get your newly formatted image instantly.</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-about">
            <div class="text-page-card">
                <h1>About Us</h1>
                <p>Welcome to <b>Snapzo Pro</b>, your number one source for all digital image and document tools. We're dedicated to providing you the very best of online utilities, with an emphasis on speed, privacy, and exact official requirements.</p>
                <p>Founded in 2025 by <b>Vishal</b>, Snapzo Pro has come a long way from its beginnings. When Vishal first started out, his passion for helping students and job aspirants solve daily digital problems drove him to start this platform.</p>
                <h2>Our Mission</h2>
                <p>Our mission is to simplify digital tasks for everyone. Whether you are filling out a government exam form (SSC, RRB, UPSC) and need an exact passport-size photo with a date, or you need to extract text from a quick screenshot, Snapzo Pro is built to save your time and money.</p>
                <p>We hope you enjoy our products as much as we enjoy offering them to you. If you have any questions or comments, please don't hesitate to contact us.</p>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-contact">
            <div class="text-page-card">
                <h1>Contact Us</h1>
                <p>We would love to hear from you! Whether you have a question about our tools, need assistance with an error, or just want to give feedback, we are here to help.</p>
                <h2>Get in Touch</h2>
                <ul>
                    <li><b>Email Support:</b> For all general inquiries, please email us directly at <i>contact@snapzopro.online</i>. We aim to respond within 24-48 hours.</li>
                    <li><b>Social Media:</b> You can also reach out to the founder directly via Instagram. Send a direct message to <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank">@rry.vishal</a>.</li>
                </ul>
                <p>We are constantly working to improve Snapzo Pro. If you want to suggest a new tool or feature, your ideas are always welcome!</p>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-privacy">
            <div class="text-page-card">
                <h1>Privacy Policy</h1>
                <p>At Snapzo Pro, accessible from https://snapzopro.online, one of our main priorities is the privacy of our visitors. This Privacy Policy document contains types of information that is collected and recorded by Snapzo Pro and how we use it.</p>
                <h2>Data Security & File Processing</h2>
                <p>We understand that you upload sensitive documents (ID Cards, Signatures, Photos). <b>Snapzo Pro does not store your files.</b></p>
                <ul>
                    <li>Most of our tools (like Image to Text OCR and Text to PDF) run entirely in your web browser. Your data never even leaves your device.</li>
                    <li>For tools that require server processing (like Passport Maker, Image Compressor), your files are processed securely in temporary memory and are <b>automatically and permanently deleted</b> immediately after the process is complete. We do not keep logs of your images.</li>
                </ul>
                <h2>Cookies and Google Analytics</h2>
                <p>Like any other website, Snapzo Pro uses 'cookies'. These cookies are used to store information including visitors' preferences, and the pages on the website that the visitor accessed or visited. We use <b>Google Analytics</b> to understand how users interact with our site to improve the user experience. Google Analytics may collect anonymous data about your device and location.</p>
                <h2>Consent</h2>
                <p>By using our website, you hereby consent to our Privacy Policy and agree to its Terms and Conditions.</p>
            </div>
        </div>
        <div class="tool-wrapper" id="tool-terms">
            <div class="text-page-card">
                <h1>Terms and Conditions</h1>
                <p>Welcome to Snapzo Pro!</p>
                <p>These terms and conditions outline the rules and regulations for the use of Snapzo Pro's Website, located at https://snapzopro.online.</p>
                <h2>License and Usage</h2>
                <p>Unless otherwise stated, Snapzo Pro and/or its licensors own the intellectual property rights for all material on Snapzo Pro. All intellectual property rights are reserved. You may access this from Snapzo Pro for your own personal use subjected to restrictions set in these terms and conditions.</p>
                <p>You must not:</p>
                <ul>
                    <li>Republish material from Snapzo Pro.</li>
                    <li>Sell, rent or sub-license material from Snapzo Pro.</li>
                    <li>Reproduce, duplicate or copy the core code logic of Snapzo Pro.</li>
                    <li>Use our tools to forge, fake, or manipulate illegal documents.</li>
                </ul>
                <h2>Disclaimer</h2>
                <p>The tools provided on this website are for general utility purposes. While we strive to provide exact dimensions for official forms (like SSC, RRB), Snapzo Pro takes no responsibility if an application is rejected due to formatting issues. Users are advised to verify their final documents before submission.</p>
            </div>
        </div>
                <div class="trust-section">
            <div class="trust-stats">
                <div class="stat-item">
                    <div class="stat-value">4.9 ⭐</div>
                    <div class="stat-label">User Rating</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">Fast & Free</div>
                    <div class="stat-label">No Login Required</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">100% Private</div>
                    <div class="stat-label">Files Auto Delete</div>
                </div>
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
               <div style="text-align: center; width: 100%; margin-top: 10px;">
    <a href="/about" style="margin: 0 15px; text-decoration: none; color: var(--accent); font-weight: 500;">About</a>
    <a href="/privacy" style="margin: 0 15px; text-decoration: none; color: var(--accent); font-weight: 500;">Privacy</a>
    <a href="/terms" style="margin: 0 15px; text-decoration: none; color: var(--accent); font-weight: 500;">Terms</a>
</div>
        </div>
        </div>
    </div>
    <script>
        let cropper;
        var quill = new Quill('#editor-container', {
            modules: { toolbar: '#toolbar-container' },
            placeholder: 'Start typing your document here...',
            theme: 'snow'
        });
        // 🟢 ADDED NEW PAGES TO ROUTEMAP 🟢
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
            'about': 'about',
            'contact': 'contact',
            'privacy': 'privacy',
            'terms': 'terms'
        };
        // 🟢 ADDED NEW PAGES TO PATHMAP 🟢
        const pathMap = {
            '/passport-maker': 'passport',
            '/id-card-print': 'idcard',
            '/signature-cleaner': 'sign',
            '/photo-sign-joiner': 'joiner',
            '/image-to-text': 'img2text',
            '/text-to-pdf': 'textpdf',
            '/image-to-pdf': 'pdf',
            '/image-crop': 'crop',
            '/compress': 'compress',
            '/social-size': 'social',
            '/convert-format': 'format',
            '/about': 'about',
            '/contact': 'contact',
            '/privacy': 'privacy',
            '/terms': 'terms',
           
            '/jpg-to-png': 'format',
            '/png-to-jpg': 'format',
            '/webp-to-jpg': 'format',
            '/ssc-photo-maker': 'passport',
            '/rrb-photo-maker': 'passport',
            '/extract-text-from-image': 'img2text',
            '/picture-to-text': 'img2text',
            '/text-to-pdf-converter': 'textpdf',
            '/jpg-to-pdf': 'pdf',
            '/png-to-pdf': 'pdf',
            '/crop-photo-online': 'crop',
            '/reduce-image-size': 'compress',
            '/compress-image-to-50kb': 'compress',
            '/youtube-thumbnail-resizer': 'social',
            '/instagram-photo-resizer': 'social'
        };
        function startOCR(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('p-ocr').src = e.target.result;
                    document.getElementById('p-ocr').style.display = 'block';
                    document.getElementById('t-ocr').style.display = 'none';
                    const loadDiv = document.getElementById('ocr-loading');
                    const resultArea = document.getElementById('ocr-result');
                    const copyBtn = document.getElementById('btn-copy-ocr');
                    const percentText = document.getElementById('ocr-percent');
                    const bar = document.getElementById('ocr-bar');
                    loadDiv.style.display = 'block';
                    resultArea.style.display = 'none';
                    copyBtn.style.display = 'none';
                    bar.style.width = '0%';
                    percentText.innerText = '0%';
                    Tesseract.recognize(
                      file, 'eng',
                      { logger: m => {
                          if(m.status === 'recognizing text'){
                              let p = Math.round(m.progress * 100);
                              percentText.innerText = p + '%';
                              bar.style.width = p + '%';
                          }
                      }}
                    ).then(({ data: { text } }) => {
                        loadDiv.style.display = 'none';
                        resultArea.style.display = 'block';
                        resultArea.value = text;
                        if(text.trim().length > 0) copyBtn.style.display = 'block';
                    }).catch(err => {
                        loadDiv.innerHTML = "<span style='color:red;'>Error extracting text. Try a clearer image!</span>";
                    });
                };
                reader.readAsDataURL(file);
            }
        }
        function copyOCRText() {
            const text = document.getElementById('ocr-result').value;
            navigator.clipboard.writeText(text).then(() => alert("Extracted Text Copied Successfully!"));
        }
        function downloadRichPDF() {
            var element = document.querySelector('.ql-editor');
            if (element.innerText.trim().length === 0) return alert("Please type some text first!");
            var opt = {
                margin: 0.8, filename: 'Snapzo_Document.pdf',
                image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
            };
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = element.innerHTML;
            tempDiv.style.color = 'black'; tempDiv.style.background = 'white';
            tempDiv.style.fontSize = '12pt'; tempDiv.style.fontFamily = 'Arial, sans-serif';
            html2pdf().set(opt).from(tempDiv).save();
        }
        function toggleTheme() { document.body.classList.toggle('dark-mode'); }
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }
        function switchTool(name, event, autoFormat = null) {
            if(event) event.preventDefault();
            // 🟢 ADDED NEW PAGES TO SWITCH ARRAY 🟢
            const tools = ['passport', 'idcard', 'sign', 'joiner', 'img2text', 'textpdf', 'pdf', 'crop', 'compress', 'social', 'format', 'about', 'contact', 'privacy', 'terms'];
            tools.forEach(t => {
                const el = document.getElementById('tool-'+t);
                if(el) { if (t === name) el.classList.add('active'); else el.classList.remove('active'); }
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) { if (t === name) deskBtn.classList.add('active-menu'); else deskBtn.classList.remove('active-menu'); }
                const mobBtn = document.getElementById('m-'+t);
                if(mobBtn) { if (t === name) mobBtn.classList.add('active-menu'); else mobBtn.classList.remove('active-menu'); }
            });
            if(autoFormat) {
                let dropdown = document.querySelector('select[name="out_format"]');
                if(dropdown) dropdown.value = autoFormat;
            }
           
            window.scrollTo({ top: 0, behavior: 'smooth' });
           
            let targetPath = window.location.pathname;
            if(event && !autoFormat) {
                if(event.target.getAttribute('href') && event.target.getAttribute('href').startsWith('/')) {
                    targetPath = event.target.getAttribute('href');
                } else {
                    targetPath = '/' + routeMap[name];
                }
                if(window.location.pathname !== targetPath) {
                    window.history.pushState(null, null, targetPath);
                }
            } else if (event && autoFormat) {
                 targetPath = event.target.getAttribute('href');
                 window.history.pushState(null, null, targetPath);
            }
           
            if(window.innerWidth <= 900) {
                document.getElementById('sidebar').classList.remove('active');
                document.getElementById('overlay').classList.remove('active');
            }
        }
        window.onload = function() {
            let path = window.location.pathname;
            if(pathMap[path]) {
                if(path === '/jpg-to-png') switchTool(pathMap[path], null, 'png');
                else if(path === '/png-to-jpg') switchTool(pathMap[path], null, 'jpg');
                else if(path === '/webp-to-jpg') switchTool(pathMap[path], null, 'jpg');
                else switchTool(pathMap[path], null);
            } else if (path !== '/') switchTool('passport', null);
        };
        window.addEventListener('popstate', function() {
            let path = window.location.pathname;
            if(pathMap[path]) {
                if(path === '/jpg-to-png') switchTool(pathMap[path], null, 'png');
                else if(path === '/png-to-jpg') switchTool(pathMap[path], null, 'jpg');
                else if(path === '/webp-to-jpg') switchTool(pathMap[path], null, 'jpg');
                else switchTool(pathMap[path], null);
            } else switchTool('passport', null);
        });
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
        function initCrop(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('z-crop').style.display = 'none';
                    document.getElementById('c-wrapper').style.display = 'block';
                    const img = document.getElementById('i-crop');
                    img.src = e.target.result;
                    if(cropper) cropper.destroy();
                    cropper = new Cropper(img, { viewMode: 1 });
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        function doCrop() {
            if(!cropper) return alert('Please upload image first');
            const data = cropper.getData(true);
            document.getElementById('cX').value = data.x; document.getElementById('cY').value = data.y;
            document.getElementById('cW').value = data.width; document.getElementById('cH').value = data.height;
            document.getElementById('cropForm').submit();
        }
    </script>
</body>
</html>
'''
# --- FLASK BACKEND LOGIC ---


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
# 🟢 ADDED NEW ROUTES FOR PAGES 🟢


@app.route('/', methods=['GET', 'POST'])
@app.route('/passport-maker', methods=['GET', 'POST'])
@app.route('/id-card-print', methods=['GET', 'POST'])
@app.route('/signature-cleaner', methods=['GET', 'POST'])
@app.route('/photo-sign-joiner', methods=['GET', 'POST'])
@app.route('/image-to-text', methods=['GET', 'POST'])
@app.route('/text-to-pdf', methods=['GET', 'POST'])
@app.route('/image-to-pdf', methods=['GET', 'POST'])
@app.route('/image-crop', methods=['GET', 'POST'])
@app.route('/compress', methods=['GET', 'POST'])
@app.route('/social-size', methods=['GET', 'POST'])
@app.route('/convert-format', methods=['GET', 'POST'])
@app.route('/about', methods=['GET', 'POST'])
@app.route('/contact', methods=['GET', 'POST'])
@app.route('/privacy', methods=['GET', 'POST'])
@app.route('/terms', methods=['GET', 'POST'])
@app.route('/jpg-to-png', methods=['GET', 'POST'])
@app.route('/png-to-jpg', methods=['GET', 'POST'])
@app.route('/webp-to-jpg', methods=['GET', 'POST'])
@app.route('/ssc-photo-maker', methods=['GET', 'POST'])
@app.route('/rrb-photo-maker', methods=['GET', 'POST'])
@app.route('/extract-text-from-image', methods=['GET', 'POST'])
@app.route('/picture-to-text', methods=['GET', 'POST'])
@app.route('/text-to-pdf-converter', methods=['GET', 'POST'])
@app.route('/jpg-to-pdf', methods=['GET', 'POST'])
@app.route('/png-to-pdf', methods=['GET', 'POST'])
@app.route('/crop-photo-online', methods=['GET', 'POST'])
@app.route('/reduce-image-size', methods=['GET', 'POST'])
@app.route('/compress-image-to-50kb', methods=['GET', 'POST'])
@app.route('/youtube-thumbnail-resizer', methods=['GET', 'POST'])
@app.route('/instagram-photo-resizer', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')

            if tool_type == 'textpdf':
                return "Use Client-Side PDF Generator", 400
            if tool_type == 'idcard':
                f_front = request.files.get('front')
                f_back = request.files.get('back')

                if not f_front or not f_back:
                    return "Both front and back sides are required", 400

                img_f = cv2.imdecode(np.frombuffer(
                    f_front.read(), np.uint8), cv2.IMREAD_COLOR)
                img_b = cv2.imdecode(np.frombuffer(
                    f_back.read(), np.uint8), cv2.IMREAD_COLOR)

                if img_f is None or img_b is None:
                    return "Invalid image files", 400

                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)

                # Front Side - better positioning
                _, buf_f = cv2.imencode('.jpg', img_f)
                c.drawImage(ImageReader(io.BytesIO(buf_f)),
                            120, 520, width=340, height=210)

                # Back Side - better spacing
                _, buf_b = cv2.imencode('.jpg', img_b)
                c.drawImage(ImageReader(io.BytesIO(buf_b)),
                            120, 280, width=340, height=210)

                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='id_card_print.pdf')
            if tool_type == 'sign':
                file = request.files.get('file')
                if not file or not allowed_file(file.filename):
                    return "Invalid or no file uploaded", 400

                img = cv2.imdecode(np.frombuffer(
                    file.read(), np.uint8), cv2.IMREAD_COLOR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(
                    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                coords = cv2.findNonZero(255 - thresh)

                if coords is None:
                    return "Signature nahi detect hui. Clear aur bright background wali photo upload karein.", 400

                x, y, w, h = cv2.boundingRect(coords)
                cropped = thresh[y:y+h, x:x+w]
                # Better border for official use
                cropped = cv2.copyMakeBorder(
                    cropped, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                _, buf = cv2.imencode('.png', cropped)
                return send_file(io.BytesIO(buf), mimetype='image/png', as_attachment=True, download_name='clean_signature.png')

            if tool_type == 'joiner':
                f_photo = request.files.get('photo')
                f_sign = request.files.get('sign')
                img_p = cv2.imdecode(np.frombuffer(
                    f_photo.read(), np.uint8), cv2.IMREAD_COLOR)
                img_s = cv2.imdecode(np.frombuffer(
                    f_sign.read(), np.uint8), cv2.IMREAD_COLOR)
                if not allowed_file(f_photo.filename) or not allowed_file(f_sign.filename):
                    return "Invalid file", 400

                face = cv2.resize(strict_passport_crop(img_p), (413, 531))
                sign_resized = cv2.resize(img_s, (413, 150))
                merged = np.vstack((face, sign_resized))
                _, buf = cv2.imencode('.jpg', merged)
                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='photo_sign_merged.jpg')
            if tool_type == 'pdf':
                files = request.files.getlist('file')
                if len(files) > 10:
                    return "Max 10 images allowed", 400

                apply_magic = request.form.get('magic_scan') == 'yes'
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                for f in files:
                    img = cv2.imdecode(np.frombuffer(
                        f.read(), np.uint8), cv2.IMREAD_COLOR)
                    if img is not None and img.shape[1] > 1500:
                        img = cv2.resize(
                            img, (1000, int(img.shape[0]*1000/img.shape[1])))
                    if img is not None:
                        if apply_magic:
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            clahe = cv2.createCLAHE(
                                clipLimit=2.0, tileGridSize=(8, 8))
                            enhanced = clahe.apply(gray)
                            _, img = cv2.threshold(
                                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                        _, buf = cv2.imencode('.jpg', img)
                        c.drawImage(ImageReader(io.BytesIO(buf)),
                                    50, 50, width=500, height=700)
                        c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_scanned.pdf')
            file = request.files.get('file')
            if file and not allowed_file(file.filename):
                return "Invalid file type", 400

            img = cv2.imdecode(np.frombuffer(
                file.read(), np.uint8), cv2.IMREAD_COLOR)
            if tool_type == 'passport':
                face = cv2.resize(strict_passport_crop(img), (413, 531))
                print_name = request.form.get("print_name", "").strip().upper()
                print_date = request.form.get("print_date", "").strip()

                if print_name or print_date:
                    # Bottom white bar for text
                    cv2.rectangle(face, (0, 531-90), (413, 531),
                                  (255, 255, 255), -1)
                    font = cv2.FONT_HERSHEY_SIMPLEX

                    if print_name and print_date:
                        # Name
                        n_size = cv2.getTextSize(print_name, font, 0.78, 2)[0]
                        cv2.putText(face, print_name, ((
                            413 - n_size[0])//2, 531-58), font, 0.78, (0, 0, 0), 2, cv2.LINE_AA)
                        # Date
                        d_size = cv2.getTextSize(print_date, font, 0.62, 2)[0]
                        cv2.putText(face, print_date, ((
                            413 - d_size[0])//2, 531-28), font, 0.62, (0, 0, 0), 2, cv2.LINE_AA)

                    elif print_name:
                        n_size = cv2.getTextSize(print_name, font, 0.82, 2)[0]
                        cv2.putText(face, print_name, ((
                            413 - n_size[0])//2, 531-45), font, 0.82, (0, 0, 0), 2, cv2.LINE_AA)

                    elif print_date:
                        d_size = cv2.getTextSize(print_date, font, 0.72, 2)[0]
                        cv2.putText(face, print_date, ((
                            413 - d_size[0])//2, 531-38), font, 0.72, (0, 0, 0), 2, cv2.LINE_AA)

                # Nice border for better printing
                bordered = cv2.copyMakeBorder(
                    face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[245, 245, 245])

                bh, bw = bordered.shape[:2]
                canvas = np.ones((2500, 1800, 3), dtype=np.uint8) * 255
                count = max(1, min(int(request.form.get("count", 8)), 12))

                for i in range(count):
                    r, c = i // 3, i % 3
                    start_y = r * (bh + 40) + 70
                    start_x = c * (bw + 30) + 70
                    canvas[start_y:start_y + bh,
                           start_x:start_x + bw] = bordered

                final = canvas[:((count-1)//3 + 1) * (bh + 40) +
                               100, :min(count, 3) * (bw + 30) + 100]

                _, buf = cv2.imencode('.jpg', final)

                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawImage(ImageReader(io.BytesIO(buf)),
                                50, 100, width=500, height=650)
                    c.save()
                    pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport_ready.pdf')

                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='passport_ready.jpg')

                bordered = cv2.copyMakeBorder(
                    face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[245, 245, 245])
                bh, bw = bordered.shape[:2]
                canvas = np.ones((2500, 1800, 3), dtype=np.uint8) * 255
                count = int(request.form.get("count", 8))
                for i in range(min(count, 12)):
                    r, c = i // 3, i % 3
                    canvas[r*(bh+40)+70:r*(bh+40)+70+bh, c *
                           (bw+30)+70:c*(bw+30)+70+bw] = bordered
                final = canvas[:((count-1)//3+1)*(bh+40)+100,
                               :(3 if count >= 3 else count)*(bw+30)+100]
                _, buf = cv2.imencode('.jpg', final)
                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawImage(ImageReader(io.BytesIO(buf)),
                                50, 100, width=500, height=650)
                    c.save()
                    pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport_ready.pdf')
                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='passport_ready.jpg')
            elif tool_type == 'crop':
                x = int(request.form.get('x'))
                y = int(request.form.get('y'))
                w = int(request.form.get('width'))
                h = int(request.form.get('height'))
                h_img, w_img = img.shape[:2]
                x = max(0, x)
                y = max(0, y)
                w = min(w, w_img - x)
                h = min(h, h_img - y)
                cropped = img[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', cropped)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='cropped.jpg')
            elif tool_type == 'compress':
                target_kb = int(request.form.get("target_kb", 50))
                target_bytes = target_kb * 1024
                quality = 92

                # First try with quality reduction
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, buffer = cv2.imencode('.jpg', img, encode_param)

                # Reduce quality gradually
                while len(buffer) > target_bytes and quality > 20:
                    quality -= 5
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                    _, buffer = cv2.imencode('.jpg', img, encode_param)

                # If still bigger, then resize + quality
                if len(buffer) > target_bytes:
                    scale = 0.95
                    while len(buffer) > target_bytes and scale > 0.4:
                        scale -= 0.05
                        new_w = int(img.shape[1] * scale)
                        new_h = int(img.shape[0] * scale)
                        resized = cv2.resize(
                            img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                        _, buffer = cv2.imencode('.jpg', resized, encode_param)

                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name=f'compressed_{target_kb}kb.jpg')
            elif tool_type == 'social':
                p = request.form.get('platform')
                dim = (1280, 720) if p == 'yt' else (
                    1080, 1080) if p == 'insta' else (820, 312)
                res = cv2.resize(img, dim)
                _, buffer = cv2.imencode('.jpg', res)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='social_resized.jpg')
            elif tool_type == 'format':
                f = request.form.get('out_format', 'png')
                _, buffer = cv2.imencode(f'.{f}', img)
                mime = f'image/{f}' if f != 'jpg' else 'image/jpeg'
                return send_file(io.BytesIO(buffer), mimetype=mime, as_attachment=True, download_name=f'converted.{f}')
        except Exception:
            return "Server Error", 500
    path = request.path
    seo_data = {
       '/': ('Snapzo Pro - Free AI Tools for SSC, RRB, UPSC | Passport Photo, Signature & Documents', 'Snapzo Pro - Free AI tools for SSC, RRB, UPSC & government exams. Passport size photo maker, signature cleaner, ID card joiner, image to PDF, compress and more. 100% Free & Private.'),
        '/passport-maker': ('Strict AI Passport Photo Maker | Snapzo Pro', 'Create exact 3.5x4.5 passport photos for SSC, RRB, and NTPC forms automatically.'),
        '/id-card-print': ('Aadhar & PAN Card Front Back PDF Joiner | Snapzo Pro', 'Merge Front and Back side of Aadhar or PAN card into a perfect A4 size PDF for printing.'),
        '/signature-cleaner': ('Auto-Signature Cleaner & Resizer | Snapzo Pro', 'Clean signature background automatically for official government forms.'),
        '/photo-sign-joiner': ('Merge Photo and Signature Online | Snapzo Pro', 'Combine passport size photo and signature into a single image vertically for state exams.'),
        '/image-to-text': ('Image to Text (OCR) Converter | Snapzo Pro', 'Extract text from images, notes, and screenshots instantly for free.'),
        '/text-to-pdf': ('Rich Text to PDF Converter Online | Snapzo Pro', 'Type and format your notes and convert them into a beautiful PDF.'),
        '/image-to-pdf': ('Image to PDF Converter | Combine Photos | Snapzo Pro', 'Combine multiple images and marksheets into a single PDF document securely.'),
        '/image-crop': ('Free Image Cropper Online | Snapzo Pro', 'Crop your photos manually with full control online.'),
        '/compress': ('Image Compressor | Reduce Photo Size in KB | Snapzo Pro', 'Reduce photo file size in KB for online form uploads without losing quality.'),
        '/social-size': ('Social Media Image Resizer | Snapzo Pro', 'Resize images perfectly for YouTube thumbnails, Instagram posts, and Facebook.'),
        '/convert-format': ('Image Format Converter | Snapzo Pro', 'Convert images to JPG, PNG, WEBP, BMP, and TIFF formats instantly for free.'),
        '/about': ('About Us | Snapzo Pro', 'Learn more about Snapzo Pro and our mission to provide free, fast, and secure image utility tools for students and professionals.'),
        '/contact': ('Contact Us | Snapzo Pro', 'Get in touch with the Snapzo Pro team for support, feedback, and queries.'),
        '/privacy': ('Privacy Policy | Snapzo Pro', 'Read our privacy policy to understand how we protect your data. Snapzo Pro does not store your files permanently.'),
        '/terms': ('Terms & Conditions | Snapzo Pro', 'Read the terms and conditions for using Snapzo Pro tools.'),
        '/jpg-to-png': ('JPG to PNG Converter Online | Snapzo Pro', 'Convert JPG images to transparent PNG format online for free without losing quality.'),
        '/png-to-jpg': ('PNG to JPG Converter Online | Snapzo Pro', 'Convert PNG images to standard JPG format online for free instantly.'),
        '/webp-to-jpg': ('WEBP to JPG Converter Online | Snapzo Pro', 'Convert WEBP web images to standard JPG format online for free.'),
        '/ssc-photo-maker': ('SSC Photo Maker Online | Snapzo Pro', 'Make perfect passport size photos for SSC exam forms with exact dimensions automatically.'),
        '/rrb-photo-maker': ('RRB Photo Maker Online | Snapzo Pro', 'Create official passport photos for RRB exams in seconds.'),
        '/extract-text-from-image': ('Extract Text From Image Free | Snapzo Pro', 'Easily extract text from any picture or screenshot with our advanced free AI OCR tool.'),
        '/picture-to-text': ('Picture to Text Converter | Snapzo Pro', 'Convert picture to text online instantly. Just upload and copy text for free.'),
        '/text-to-pdf-converter': ('Text to PDF Converter | Snapzo Pro', 'Convert text to PDF files online for free. Use our rich document editor.'),
        '/jpg-to-pdf': ('JPG to PDF Converter Online | Snapzo Pro', 'Convert JPG images to PDF documents securely and for free.'),
        '/png-to-pdf': ('PNG to PDF Converter Online | Snapzo Pro', 'Convert PNG images to PDF documents securely and for free.'),
        '/crop-photo-online': ('Crop Photo Online Free | Snapzo Pro', 'Free online image cropper. Crop photos, pictures, and images to any size.'),
        '/reduce-image-size': ('Reduce Image Size Online | Snapzo Pro', 'Reduce image file size quickly without losing quality. Best for online form uploads.'),
        '/compress-image-to-50kb': ('Compress Image to 50KB | Snapzo Pro', 'Compress your photos to exactly 50KB or any specific size for government form uploads.'),
        '/youtube-thumbnail-resizer': ('YouTube Thumbnail Resizer | Snapzo Pro', 'Resize images perfectly for YouTube thumbnails (1280x720) in one click.'),
        '/instagram-photo-resizer': ('Instagram Photo Resizer | Snapzo Pro', 'Resize images perfectly for Instagram Posts (1080x1080) for free.')
    }

    page_title, page_desc = seo_data.get(path, seo_data['/'])

    breadcrumb_schema = ""
    if path != '/':
        tool_name = page_title.split(' | ')[0]
        breadcrumb_schema = f'''
        <script type="application/ld+json">
        {{
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          "itemListElement": [{{
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "https://snapzopro.online/"
          }},{{
            "@type": "ListItem",
            "position": 2,
            "name": "{tool_name}",
            "item": "https://snapzopro.online{path}"
          }}]
        }}
        </script>
        '''

    return render_template_string(HTML, page_title=page_title, page_desc=page_desc, request_path=path, breadcrumb_schema=breadcrumb_schema)

# --- SEO: SITEMAP & ROBOTS.TXT ---

@app.route('/robots.txt')
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: https://snapzopro.online/sitemap.xml"
    ]
    return Response("\n".join(lines), mimetype="text/plain")

@app.route('/sitemap.xml')
def sitemap():
    pages = [
        '/', '/passport-maker', '/id-card-print', '/signature-cleaner',
        '/photo-sign-joiner', '/image-to-text', '/text-to-pdf', '/image-to-pdf',
        '/image-crop', '/compress', '/social-size', '/convert-format',
        '/about', '/contact', '/privacy', '/terms',
        '/jpg-to-png', '/png-to-jpg', '/webp-to-jpg', '/ssc-photo-maker',
        '/rrb-photo-maker', '/extract-text-from-image', '/picture-to-text',
        '/text-to-pdf-converter', '/jpg-to-pdf', '/png-to-pdf', '/crop-photo-online',
        '/reduce-image-size', '/compress-image-to-50kb', '/youtube-thumbnail-resizer',
        '/instagram-photo-resizer'
    ]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Main website pages
    for page in pages:
        xml += '  <url>\n'
        xml += f'    <loc>https://snapzopro.online{page}</loc>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += '    <priority>0.8</priority>\n'
        xml += '  </url>\n'
        
    # Typing sub-domain
    xml += '  <url>\n'
    xml += '    <loc>https://typing.snapzopro.online/</loc>\n'
    xml += '    <changefreq>weekly</changefreq>\n'
    xml += '    <priority>0.9</priority>\n'
    xml += '  </url>\n'
    
    xml += '</urlset>'
    return Response(xml, mimetype="application/xml")
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
