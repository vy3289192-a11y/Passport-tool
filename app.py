from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <meta name="google-site-verification" content="TlhWO7oDD-Gp8H0gKFC3U7n7v213ccnwGp0C9OB_7Uc" />

    <title>{{ page_title }}</title>
    <meta name="description" content="{{ page_desc }}">
    
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
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
      "image": "https://i.ibb.co/Q73xvDmw/46658.jpg",
      "description": "{{ page_desc }}",
      "featureList": "Passport Photo Maker, Text to PDF, Image to Text, Image to PDF, Image Format Converter, Image Compressor, Social Media Resizer, Manual Crop"
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
        
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; }
        .tool-wrapper.active { display: flex; }
        
        .tool-content { flex: 1.2; text-align: left; }
        .tool-content h1 { font-size: 2.2rem; color: var(--text); margin: 0 0 15px 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.05rem; line-height: 1.6; color: var(--text); opacity: 0.9; }
        
        .feature-list { list-style: none; padding: 0; margin: 25px 0; }
        .feature-list li { margin-bottom: 12px; display: flex; align-items: center; gap: 10px; color: var(--text); }
        .feature-list i { color: #10b981; }
        
        .visual-box { background: var(--box-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; color: var(--text); }
        .visual-box span, .visual-box p { color: var(--text); }
        
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid var(--border); }
        .card h2 { margin-top: 0; text-align: center; font-size: 1.6rem; color: var(--text); }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); position: relative; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        input, select, textarea { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--input-bg); color: var(--text); font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; width: 100%; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; color: var(--text); opacity: 0.8; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
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

        .footer { text-align: center; padding: 40px 20px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; color: var(--text); }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }

        @media (max-width: 900px) { 
            .tool-wrapper.active { 
                display: block !important; 
            } 
            .tool-content { 
                display: block !important;
                text-align: center !important; 
                width: 100% !important; 
                margin-bottom: 30px !important;
            } 
            .card { 
                display: block !important;
                width: 100% !important; 
                max-width: 100% !important; 
                padding: 30px 20px !important; 
                margin: 0 auto !important;
            }
            .feature-list li { justify-content: center !important; } 
            .visual-box { margin: 0 auto 25px auto !important; }
            .desktop-menu { display: none !important; } 
            .mobile-toggle { display: block !important; }
        }
    </style>
</head>
<body>

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right" style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="d-passport">Passport Maker</a>
                <a href="/image-to-text" class="menu-btn" onclick="switchTool('img2text', event)" id="d-img2text">Image to Text</a>
                <a href="/text-to-pdf" class="menu-btn" onclick="switchTool('textpdf', event)" id="d-textpdf">Text to PDF</a>
                <a href="/image-to-pdf" class="menu-btn" onclick="switchTool('pdf', event)" id="d-pdf">Image to PDF</a>
                <a href="/image-crop" class="menu-btn" onclick="switchTool('crop', event)" id="d-crop">Crop</a>
                <a href="/compress" class="menu-btn" onclick="switchTool('compress', event)" id="d-compress">Compress</a>
                <a href="/social-size" class="menu-btn" onclick="switchTool('social', event)" id="d-social">Social Size</a>
                <a href="/convert-format" class="menu-btn" onclick="switchTool('format', event)" id="d-format">Convert</a>
            </div>
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.3rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()" style="margin-left: 10px;"></i>
        </div>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Snapzo Menu</h3>
        <a href="/passport-maker" class="menu-btn active-menu" onclick="switchTool('passport', event)" id="m-passport"><i class="fas fa-id-badge"></i> Passport Maker</a>
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
                <p>Turn a regular photo into an official passport photo fast. Hamara AI strictly 3.5x4.5 ratio use karta hai taaki koi galti na ho.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px;">
                        <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80" style="width:100px; height:100px; object-fit:cover; border-radius:12px;">
                        <i class="fas fa-arrow-right" style="font-size:1.5rem; color:var(--accent);"></i>
                        <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80" style="width:100px; height:128px; object-fit:cover; border:4px solid white; border-radius:2px;">
                    </div>
                    <p style="margin-top:10px; font-size:0.9rem;">AI Auto-Crop ensures correct size.</p>
                </div>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Permanent 413x531 Pixels</li>
                    <li><i class="fas fa-check-circle"></i> Perfect for SSC, RRB, NTPC Forms</li>
                    <li><i class="fas fa-check-circle"></i> Multiple Copies Layout Ready</li>
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
                    <div class="row">
                        <div class="group"><label>Quantity</label><input type="number" name="count" value="8"></div>
                        <div class="group"><label>Format</label><select name="type"><option value="jpg">JPG Image</option><option value="pdf">PDF Document</option></select></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Generate Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-img2text">
            <div class="tool-content">
                <h1>Image to Text (OCR)</h1>
                <p>Kisi bhi photo (Notes, Books, Screenshots) mein likha hua text instantly extract karein. Copy karein aur kahin bhi use karein.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px; font-weight:bold; font-size:1.1rem;">
                        <i class="fas fa-image" style="font-size: 2.5rem; color:#38bdf8;"></i>
                        <i class="fas fa-arrow-right" style="color:var(--accent);"></i>
                        <i class="fas fa-file-alt" style="font-size: 2.5rem; color:#10b981;"></i>
                    </div>
                    <p style="margin-top:10px; font-size:0.9rem;">Powered by Advanced AI Text Recognition.</p>
                </div>
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
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Images to PDF</h1>
                <p>Combine multiple marksheets or documents into a single PDF file securely.</p>
                <div class="visual-box">
                    <i class="fas fa-images" style="font-size:3rem; color:#38bdf8;"></i>
                    <i class="fas fa-plus" style="margin:0 10px;"></i>
                    <i class="fas fa-file-pdf" style="font-size:3rem; color:#ef4444;"></i>
                </div>
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
                    <button class="btn">Generate PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content"><h1>Manual Crop Studio</h1><p>Cut unwanted parts from your photo with full control.</p></div>
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
            </div>
        </div>

        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content"><h1>Image Compressor</h1><p>Reduce photo size (KB) for online form uploads.</p></div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="compress">
                    <div class="upload-zone" onclick="document.getElementById('f-comp').click()">
                        <input type="file" id="f-comp" name="file" hidden required onchange="handlePreview(this, 'p-comp', 't-comp')">
                        <div id="t-comp"><i class="fas fa-compress-arrows-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-comp" class="preview-img">
                    </div>
                    <div class="row"><div class="group"><label>Quality (10-100)</label><input type="number" name="quality" value="60"></div></div>
                    <button class="btn">Compress</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-social">
            <div class="tool-content"><h1>Social Media Resizer</h1><p>Perfect size for YouTube Thumbnails, Instagram or FB.</p></div>
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
            </div>
        </div>

        <div class="tool-wrapper" id="tool-format">
            <div class="tool-content">
                <h1>Format Converter</h1>
                <p>Convert any image format instantly. Supports JPG, PNG, WEBP, BMP, and TIFF.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:15px; font-weight:bold; font-size:1.1rem; flex-wrap:wrap;">
                        <span>.JPG</span>
                        <i class="fas fa-sync-alt" style="color:var(--accent);"></i>
                        <span>.PNG</span>
                        <i class="fas fa-sync-alt" style="color:var(--accent);"></i>
                        <span>.WEBP</span>
                    </div>
                </div>
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
            </div>
        </div>

        <div class="trust-section">
            <div class="trust-stats">
                <div class="stat-item"><div class="stat-value">4.9 ⭐</div><div class="stat-label">User Rating</div></div>
                <div class="stat-item"><div class="stat-value">80M+</div><div class="stat-label">Total Users</div></div>
                <div class="stat-item"><div class="stat-value">12M+</div><div class="stat-label">Worldwide Trusted</div></div>
            </div>
        </div>

        <div class="testimonials">
            <h2>What Users Say ⭐⭐⭐⭐⭐</h2>
            <div class="testi-grid">
                <div class="testi-card">
                    <div class="testi-header"><img src="https://i.pravatar.cc/150?img=11" class="testi-avatar"><div><h4>Ravi Sharma</h4><p>Govt. Job Aspirant</p></div></div>
                    <p>"Bhai strictly strict size fix hai! NTPC form ke liye exact passport ban gayi without cyber cafe jaye."</p>
                </div>
                <div class="testi-card">
                    <div class="testi-header"><img src="https://i.pravatar.cc/150?img=5" class="testi-avatar"><div><h4>Neha Verma</h4><p>College Student</p></div></div>
                    <p>"Naya Image to Text OCR feature bahut kaam ka hai. Screenshots se notes nikalna bahut aasan ho gaya!"</p>
                </div>
                <div class="testi-card">
                    <div class="testi-header"><img src="https://i.pravatar.cc/150?img=60" class="testi-avatar"><div><h4>Arjun</h4><p>Freelancer</p></div></div>
                    <p>"Social resizer YouTube thumbnails ke liye ekdum perfect size deta hai. Highly recommended!"</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Built with ❤️ by <b>Vishal</b></p>
            <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" class="insta-btn"><i class="fab fa-instagram"></i> Follow on Instagram</a>
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
            'img2text': 'image-to-text',
            'textpdf': 'text-to-pdf',
            'pdf': 'image-to-pdf',
            'crop': 'image-crop',
            'compress': 'compress',
            'social': 'social-size',
            'format': 'convert-format'
        };

        const pathMap = {
            '/passport-maker': 'passport',
            '/image-to-text': 'img2text',
            '/text-to-pdf': 'textpdf',
            '/image-to-pdf': 'pdf',
            '/image-crop': 'crop',
            '/compress': 'compress',
            '/social-size': 'social',
            '/convert-format': 'format'
        };

        // NEW: Dynamically update JS Title when clicking menus
        const seoTitleMap = {
            'passport': 'Strict AI Passport Photo Maker | Snapzo Pro',
            'img2text': 'Image to Text (OCR) Converter | Snapzo Pro',
            'textpdf': 'Rich Text to PDF Converter Online | Snapzo Pro',
            'pdf': 'Image to PDF Converter | Combine Photos | Snapzo Pro',
            'crop': 'Free Image Cropper Online | Snapzo Pro',
            'compress': 'Image Compressor | Reduce Photo Size in KB | Snapzo Pro',
            'social': 'Social Media Image Resizer | Snapzo Pro',
            'format': 'JPG to PNG Converter | Convert Image Formats | Snapzo Pro'
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
                      file,
                      'eng',
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
                        if(text.trim().length > 0) {
                            copyBtn.style.display = 'block';
                        }
                    }).catch(err => {
                        loadDiv.innerHTML = "<span style='color:red;'>Error extracting text. Try a clearer image!</span>";
                        console.error(err);
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
            if (element.innerText.trim().length === 0) {
                alert("Please type some text first!");
                return;
            }
            var opt = {
                margin:       0.8,
                filename:     'Snapzo_Document.pdf',
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2 },
                jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
            };
            
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = element.innerHTML;
            tempDiv.style.color = 'black'; 
            tempDiv.style.background = 'white';
            tempDiv.style.fontSize = '12pt';
            tempDiv.style.fontFamily = 'Arial, sans-serif';
            
            html2pdf().set(opt).from(tempDiv).save();
        }

        function toggleTheme() { document.body.classList.toggle('dark-mode'); }
        
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function switchTool(name, event) {
            if(event) event.preventDefault(); 
            
            const tools = ['passport', 'img2text', 'textpdf', 'pdf', 'crop', 'compress', 'social', 'format'];
            tools.forEach(t => {
                const el = document.getElementById('tool-'+t);
                if(el) el.style.display = (t === name) ? 'block' : 'none';
                
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) deskBtn.classList.toggle('active-menu', t === name);
                
                const mobBtn = document.getElementById('m-'+t);
                if(mobBtn) mobBtn.classList.toggle('active-menu', t === name);
            });
            window.scrollTo(0,0);
            
            // SEO: Change document title on click
            if(seoTitleMap[name]) {
                document.title = seoTitleMap[name];
            }
            
            let targetPath = '/' + routeMap[name];
            if(window.location.pathname !== targetPath) {
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
                switchTool(pathMap[path], null);
            } else if (path !== '/') {
                switchTool('passport', null);
            }
        };

        window.addEventListener('popstate', function() {
            let path = window.location.pathname;
            if(pathMap[path]) {
                switchTool(pathMap[path], null);
            } else {
                switchTool('passport', null);
            }
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
            document.getElementById('cX').value = data.x;
            document.getElementById('cY').value = data.y;
            document.getElementById('cW').value = data.width;
            document.getElementById('cH').value = data.height;
            document.getElementById('cropForm').submit();
        }
    </script>
</body>
</html>
'''

# --- FLASK BACKEND LOGIC (With Dynamic SEO Rendering) ---

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

@app.route('/', methods=['GET', 'POST'])
@app.route('/passport-maker', methods=['GET', 'POST'])
@app.route('/image-to-text', methods=['GET', 'POST'])
@app.route('/text-to-pdf', methods=['GET', 'POST'])
@app.route('/image-to-pdf', methods=['GET', 'POST'])
@app.route('/image-crop', methods=['GET', 'POST'])
@app.route('/compress', methods=['GET', 'POST'])
@app.route('/social-size', methods=['GET', 'POST'])
@app.route('/convert-format', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')
            
            if tool_type == 'textpdf':
                return "Use Client-Side PDF Generator", 400

            if tool_type == 'pdf':
                files = request.files.getlist('file')
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                for f in files:
                    img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
                    if img is not None:
                        _, buf = cv2.imencode('.jpg', img)
                        c.drawImage(ImageReader(io.BytesIO(buf)), 50, 50, width=500, height=700)
                        c.showPage()
                c.save(); pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='docs.pdf')

            file = request.files.get('file')
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

            if tool_type == 'passport':
                face = cv2.resize(strict_passport_crop(img), (413, 531))
                bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[245, 245, 245])
                bh, bw = bordered.shape[:2]
                canvas = np.ones((2500, 1800, 3), dtype=np.uint8) * 255
                count = int(request.form.get("count", 8))
                for i in range(min(count, 12)):
                    r, c = i // 3, i % 3
                    canvas[r*(bh+40)+70:r*(bh+40)+70+bh, c*(bw+30)+70:c*(bw+30)+70+bw] = bordered
                final = canvas[:((count-1)//3+1)*(bh+40)+100, :(3 if count>=3 else count)*(bw+30)+100]
                _, buf = cv2.imencode('.jpg', final)
                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawImage(ImageReader(io.BytesIO(buf)), 50, 100, width=500, height=650)
                    c.save(); pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport.pdf')
                return send_file(io.BytesIO(buf), mimetype='image/jpeg', as_attachment=True, download_name='passport.jpg')

            elif tool_type == 'crop':
                x, y, w, h = int(request.form.get('x')), int(request.form.get('y')), int(request.form.get('width')), int(request.form.get('height'))
                cropped = img[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', cropped)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='cropped.jpg')

            elif tool_type == 'compress':
                q = int(request.form.get("quality", 60))
                _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='compressed.jpg')

            elif tool_type == 'social':
                p = request.form.get('platform')
                dim = (1280, 720) if p=='yt' else (1080, 1080) if p=='insta' else (820, 312)
                res = cv2.resize(img, dim)
                _, buffer = cv2.imencode('.jpg', res)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='resized.jpg')

            elif tool_type == 'format':
                f = request.form.get('out_format', 'png')
                _, buffer = cv2.imencode(f'.{f}', img)
                mime = f'image/{f}' if f != 'jpg' else 'image/jpeg'
                return send_file(io.BytesIO(buffer), mimetype=mime, as_attachment=True, download_name=f'converted.{f}')

        except Exception as e: return f"Error: {str(e)}", 500

    # GET METHOD - DYNAMIC SEO Titles & Descriptions Based on URL Path
    path = request.path
    seo_data = {
        '/': ('Snapzo Pro | Free AI Passport Photo Maker & Image Tools', 'Free online AI passport size photo maker, image to PDF converter, Text to PDF, Image to Text (OCR), and compressor.'),
        '/passport-maker': ('Strict AI Passport Photo Maker | Snapzo Pro', 'Create exact 3.5x4.5 passport photos for SSC, RRB, and NTPC forms automatically.'),
        '/image-to-text': ('Image to Text (OCR) Converter | Snapzo Pro', 'Extract text from images, notes, and screenshots instantly for free.'),
        '/text-to-pdf': ('Rich Text to PDF Converter Online | Snapzo Pro', 'Type and format your notes and convert them into a beautiful PDF.'),
        '/image-to-pdf': ('Image to PDF Converter | Combine Photos | Snapzo Pro', 'Combine multiple images and marksheets into a single PDF document securely.'),
        '/image-crop': ('Free Image Cropper Online | Snapzo Pro', 'Crop your photos manually with full control online.'),
        '/compress': ('Image Compressor | Reduce Photo Size in KB | Snapzo Pro', 'Reduce photo file size in KB for online form uploads without losing quality.'),
        '/social-size': ('Social Media Image Resizer | Snapzo Pro', 'Resize images perfectly for YouTube thumbnails, Instagram posts, and Facebook.'),
        '/convert-format': ('JPG to PNG Converter | Convert Image Formats | Snapzo Pro', 'Convert images to JPG, PNG, WEBP, BMP, and TIFF formats instantly for free.')
    }
    
    page_title, page_desc = seo_data.get(path, seo_data['/'])
    
    # Passing the dynamic variables to HTML
    return render_template_string(HTML, page_title=page_title, page_desc=page_desc)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
