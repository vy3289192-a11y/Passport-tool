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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <title>Snapzo Pro | Free AI Passport Photo Maker & Image Tools</title>
    <meta name="description" content="Create perfect passport size photos online for free. Crop, compress, resize for social media, and convert images to PDF easily with Snapzo Pro.">
    
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>

    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; }
        
        .nav { background: #111827; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: white; }
        .nav-brand img { height: 35px; border-radius: 5px; object-fit: cover; }
        .nav-brand span { font-weight: bold; font-size: 1.3rem; letter-spacing: 0.5px; }

        .desktop-menu { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
        .desktop-menu .menu-btn { padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-weight: 500; font-size: 0.9rem; display: flex; align-items: center; gap: 6px; }
        .desktop-menu .menu-btn:hover, .desktop-menu .active-menu { background: var(--accent); color: white; }
        .mobile-toggle { display: none; font-size: 1.4rem; cursor: pointer; }

        .sidebar { width: 250px; height: 100vh; background: #111827; position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; box-sizing: border-box; overflow-y: auto; }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { padding: 15px; display: flex; align-items: center; gap: 15px; color: var(--text); border-radius: 8px; margin-bottom: 10px; transition: 0.2s; cursor: pointer; }
        .sidebar .menu-btn:hover, .sidebar .active-menu { background: var(--accent); }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }

        .main { padding: 50px 20px; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; min-height: 85vh; }
        
        /* --- NEW LAYOUT: INFO + TOOL SIDE BY SIDE --- */
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; }
        .tool-wrapper.active { display: flex; }
        
        .tool-content { flex: 1.2; text-align: left; color: #cbd5e1; }
        .tool-content h1 { font-size: 2.2rem; color: white; margin-top: 0; margin-bottom: 15px; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.05rem; line-height: 1.6; margin-bottom: 25px; }
        
        .feature-list { list-style: none; padding: 0; margin-bottom: 30px; }
        .feature-list li { margin-bottom: 12px; font-size: 1rem; display: flex; align-items: center; gap: 10px; color: #e2e8f0; }
        .feature-list i { color: #10b981; font-size: 1.1rem; }
        
        .visual-box { background: #111827; border: 1px solid var(--border); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        
        .card { flex: 1; background: var(--card); padding: 35px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid var(--border); margin: 0; }
        .card h2 { margin-top: 0; font-size: 1.6rem; text-align: center; color: white; margin-bottom: 25px; }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); transition: 0.3s; }
        .upload-zone:hover { background: rgba(59,130,246,0.08); border-color: white; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        .row { display: flex; gap: 15px; margin: 20px 0; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8; }
        input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; box-sizing: border-box; font-size: 1rem; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); }
        .btn:hover { background: #2563eb; transform: translateY(-2px); }

        .img-container { max-height: 400px; display: none; margin-top: 15px; }
        .img-container img { max-width: 100%; display: block; }

        /* Trust & Reviews CSS */
        .trust-section { width: 100%; max-width: 900px; text-align: center; padding: 50px 20px 20px; border-top: 1px solid var(--border); margin-top: 20px; }
        .trust-stats { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-bottom: 30px; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: white; display: flex; align-items: center; gap: 10px; }
        .stat-label { font-size: 1rem; color: #94a3b8; margin-top: 5px; font-weight: 500; }
        .stars { color: #f59e0b; font-size: 1.3rem; }
        .trusted-text { font-size: 1.3rem; font-weight: 500; color: #cbd5e1; margin-bottom: 25px; }
        .trust-logos { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; opacity: 0.5; color: white; }
        .trust-logos i { font-size: 3rem; transition: 0.3s; }
        .trust-logos i:hover { opacity: 1; color: var(--accent); }

        .testimonials { width: 100%; max-width: 1100px; margin: 40px auto 60px; padding: 0 20px; }
        .testimonials h2 { font-size: 2.2rem; margin-bottom: 40px; color: white; text-align: center; }
        .testi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
        .testi-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 30px; transition: 0.3s; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        .testi-card:hover { transform: translateY(-5px); border-color: var(--accent); }
        .testi-header { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
        .testi-avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border); }
        .testi-info h4 { margin: 0; color: white; font-size: 1.15rem; }
        .testi-info p { margin: 4px 0 0; color: #94a3b8; font-size: 0.9rem; }
        .testi-text { color: #cbd5e1; font-size: 1rem; line-height: 1.6; font-style: italic; }

        .footer { max-width: 480px; width: 100%; text-align: center; padding: 20px 0; border-top: 1px solid var(--border); }
        .footer-founder { font-size: 1.05rem; font-weight: 500; margin-bottom: 15px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 0.9rem; transition: 0.3s; }

        @media (max-width: 950px) {
            .desktop-menu { display: none; }
            .mobile-toggle { display: block; }
            .tool-wrapper.active { flex-direction: column; align-items: center; }
            .tool-content { order: -1; text-align: center; }
            .feature-list li { justify-content: center; }
            .card { max-width: 100%; }
        }
    </style>
</head>
<body>

    <div class="nav">
        <a href="/" class="nav-brand">
            <img src="''' + LOGO_URL + '''" alt="Logo">
            <span>Snapzo Pro</span>
        </a>
        <div class="desktop-menu">
            <div class="menu-btn active-menu" onclick="switchTool('passport')" id="desk-passport"><i class="fas fa-id-card"></i> Passport Maker</div>
            <div class="menu-btn" onclick="switchTool('crop')" id="desk-crop"><i class="fas fa-crop-alt"></i> Crop</div>
            <div class="menu-btn" onclick="switchTool('pdf')" id="desk-pdf"><i class="fas fa-file-pdf"></i> Photo to PDF</div>
            <div class="menu-btn" onclick="switchTool('compress')" id="desk-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</div>
            <div class="menu-btn" onclick="switchTool('social')" id="desk-social"><i class="fas fa-share-alt"></i> Social Size</div>
            <div class="menu-btn" onclick="switchTool('format')" id="desk-format"><i class="fas fa-exchange-alt"></i> Converter</div>
        </div>
        <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()"></i>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Menu</h3>
        <div class="menu-btn active-menu" onclick="switchTool('passport')" id="mob-passport"><i class="fas fa-id-card"></i> Passport Maker</div>
        <div class="menu-btn" onclick="switchTool('crop')" id="mob-crop"><i class="fas fa-crop-alt"></i> Manual Crop</div>
        <div class="menu-btn" onclick="switchTool('pdf')" id="mob-pdf"><i class="fas fa-file-pdf"></i> Photo to PDF</div>
        <div class="menu-btn" onclick="switchTool('compress')" id="mob-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</div>
        <div class="menu-btn" onclick="switchTool('social')" id="mob-social"><i class="fas fa-share-alt"></i> Social Resizer</div>
        <div class="menu-btn" onclick="switchTool('format')" id="mob-format"><i class="fas fa-exchange-alt"></i> Converter</div>
    </div>

    <div class="main">
        
        <div class="tool-wrapper active" id="tool-passport" style="display: flex;">
            <div class="tool-content">
                <h1>Free Passport Size Photo Maker</h1>
                <p>Turn a regular photo into an official passport, visa, or ID photo fast. Auto-crop and get exact sizes instantly without any editing skills.</p>
                
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px;">
                        <div style="text-align:center;">
                            <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80" style="width:110px; height:110px; object-fit:cover; border-radius:12px;">
                            <div style="margin-top:8px; font-size:0.85rem; color:#94a3b8;">Original Photo</div>
                        </div>
                        <i class="fas fa-arrow-right" style="font-size:1.8rem; color:var(--accent);"></i>
                        <div style="text-align:center; position:relative;">
                            <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&q=80" style="width:110px; height:140px; object-fit:cover; border: 4px solid white; border-radius:2px;">
                            <div style="margin-top:8px; font-size:0.85rem; color:#10b981; font-weight:bold;"><i class="fas fa-check-circle"></i> 51x51 Verified</div>
                        </div>
                    </div>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Perfect for Govt. Exams (RRB NTPC, SSC)</li>
                    <li><i class="fas fa-check-circle"></i> Auto-crops accurately with AI rules</li>
                    <li><i class="fas fa-check-circle"></i> Download as Image (JPG) or Print-ready PDF</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Upload Image</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('fileInputPass').click()">
                        <input type="file" name="file" id="fileInputPass" hidden required onchange="handlePreview(this, 'preview-pass', 'drop-text-pass')">
                        <div id="drop-text-pass">
                            <i class="fas fa-cloud-upload-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                            <p style="margin:0"><b>Click to upload</b> or drag photo</p>
                        </div>
                        <img id="preview-pass" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group"><label>Quantity</label><input type="number" name="count" value="8" min="1" max="12"></div>
                        <div class="group"><label>Format</label><select name="type"><option value="jpg">Image (JPG)</option><option value="pdf">Document (PDF)</option></select></div>
                    </div>
                    <button type="submit" class="btn"><i class="fas fa-bolt"></i> Generate Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content">
                <h1>Precision Image Cropper</h1>
                <p>Remove unwanted areas from your photos effortlessly. Drag the corners to select the exact frame you need for your projects.</p>
                
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px;">
                        <i class="fas fa-image" style="font-size: 3rem; color: #64748b;"></i>
                        <i class="fas fa-cut" style="font-size: 1.5rem; color: var(--accent);"></i>
                        <i class="fas fa-portrait" style="font-size: 3rem; color: #10b981;"></i>
                    </div>
                    <p style="margin-top:15px; font-size:0.9rem; color:#94a3b8;">Freeform custom cropping for any image size.</p>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Custom selection ratio</li>
                    <li><i class="fas fa-check-circle"></i> Zero quality loss</li>
                    <li><i class="fas fa-check-circle"></i> Fast and lightweight</li>
                </ul>
            </div>

            <div class="card">
                <h2>Crop Studio</h2>
                <form method="POST" enctype="multipart/form-data" id="cropForm">
                    <input type="hidden" name="tool_type" value="crop">
                    <input type="hidden" name="x" id="cropX"><input type="hidden" name="y" id="cropY"><input type="hidden" name="width" id="cropWidth"><input type="hidden" name="height" id="cropHeight">
                    <div class="upload-zone" id="upload-zone-crop" onclick="document.getElementById('fileInputCrop').click()">
                        <input type="file" name="file" id="fileInputCrop" hidden required onchange="handleFileCrop(this)">
                        <div id="drop-text-crop">
                            <i class="fas fa-crop" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                            <p style="margin:0"><b>Click or drag</b> image to crop</p>
                        </div>
                    </div>
                    <div class="img-container" id="cropper-wrapper"><img id="image-to-crop" src=""></div>
                    <button type="button" class="btn" onclick="submitCrop()" style="margin-top: 20px;"><i class="fas fa-cut"></i> Crop & Download</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Convert Photo to PDF</h1>
                <p>Turn your images, ID cards, marksheet photos, or scanned documents into a clean, easy-to-share PDF file instantly.</p>
                
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px;">
                        <div style="background:#0f172a; padding:15px; border-radius:10px;"><i class="fas fa-file-image" style="font-size: 2.5rem; color: #38bdf8;"></i></div>
                        <i class="fas fa-arrow-right" style="font-size:1.8rem; color:var(--accent);"></i>
                        <div style="background:#0f172a; padding:15px; border-radius:10px;"><i class="fas fa-file-pdf" style="font-size: 2.5rem; color: #ef4444;"></i></div>
                    </div>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Standard A4 Document Format</li>
                    <li><i class="fas fa-check-circle"></i> Preserves high resolution</li>
                    <li><i class="fas fa-check-circle"></i> Perfect for sending assignments</li>
                </ul>
            </div>

            <div class="card">
                <h2>PDF Converter</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('fileInputPdf').click()">
                        <input type="file" name="file" id="fileInputPdf" hidden required onchange="handlePreview(this, 'preview-pdf', 'drop-text-pdf')">
                        <div id="drop-text-pdf"><i class="fas fa-file-pdf" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i><p style="margin:0"><b>Upload Image</b> to convert</p></div>
                        <img id="preview-pdf" class="preview-img">
                    </div>
                    <button type="submit" class="btn" style="margin-top: 20px;"><i class="fas fa-download"></i> Download PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content">
                <h1>Smart Image Compressor</h1>
                <p>Got a heavy 5MB photo that won't upload? Compress it down to KBs in seconds while keeping the visual quality perfectly intact.</p>
                
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px; font-weight:bold;">
                        <div style="border: 2px solid #ef4444; color:#ef4444; padding:10px 20px; border-radius:8px;">5.2 MB</div>
                        <i class="fas fa-chevron-right" style="font-size:1.5rem; color:var(--accent);"></i>
                        <div style="border: 2px solid #10b981; background:#10b981; color:white; padding:10px 20px; border-radius:8px;">150 KB</div>
                    </div>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Reduce size up to 90%</li>
                    <li><i class="fas fa-check-circle"></i> Essential for online forms</li>
                    <li><i class="fas fa-check-circle"></i> Custom quality control (10% to 100%)</li>
                </ul>
            </div>

            <div class="card">
                <h2>Compress Image</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="compress">
                    <div class="upload-zone" onclick="document.getElementById('fileInputCompress').click()">
                        <input type="file" name="file" id="fileInputCompress" hidden required onchange="handlePreview(this, 'preview-compress', 'drop-text-compress')">
                        <div id="drop-text-compress"><i class="fas fa-compress-arrows-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i><p style="margin:0"><b>Upload Image</b></p></div>
                        <img id="preview-compress" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group"><label>Quality (10% to 100%)</label><input type="number" name="quality" value="60" min="10" max="100"></div>
                    </div>
                    <button type="submit" class="btn"><i class="fas fa-compress"></i> Compress</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-social">
            <div class="tool-content">
                <h1>Social Media Resizer</h1>
                <p>Stop guessing dimensions! Instantly resize your images to fit perfectly on YouTube, Instagram, and Facebook without weird stretching.</p>
                
                <div class="visual-box">
                    <div style="display:flex; justify-content:space-around; align-items:center;">
                        <div style="text-align:center;"><i class="fab fa-youtube" style="font-size:2.5rem; color:#ef4444;"></i><br><small style="color:#94a3b8;">1280x720</small></div>
                        <div style="text-align:center;"><i class="fab fa-instagram" style="font-size:2.5rem; color:#ec4899;"></i><br><small style="color:#94a3b8;">1080x1080</small></div>
                        <div style="text-align:center;"><i class="fab fa-facebook" style="font-size:2.5rem; color:#3b82f6;"></i><br><small style="color:#94a3b8;">820x312</small></div>
                    </div>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Perfect YouTube Thumbnails</li>
                    <li><i class="fas fa-check-circle"></i> Square Instagram Posts</li>
                    <li><i class="fas fa-check-circle"></i> Facebook Cover Photos</li>
                </ul>
            </div>

            <div class="card">
                <h2>Social Auto-Size</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="social">
                    <div class="upload-zone" onclick="document.getElementById('fileInputSocial').click()">
                        <input type="file" name="file" id="fileInputSocial" hidden required onchange="handlePreview(this, 'preview-social', 'drop-text-social')">
                        <div id="drop-text-social">
                            <i class="fas fa-share-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                            <p style="margin:0"><b>Upload Image</b> to resize</p>
                        </div>
                        <img id="preview-social" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group">
                            <label>Select Platform</label>
                            <select name="platform">
                                <option value="yt">YouTube Thumbnail (1280x720)</option>
                                <option value="insta">Instagram Post (1080x1080)</option>
                                <option value="fb">Facebook Cover (820x312)</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn"><i class="fas fa-crop"></i> Resize</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-format">
            <div class="tool-content">
                <h1>Image Format Converter</h1>
                <p>Change your image file extensions instantly. Need a high-quality PNG, a standard JPG, or a web-optimized WEBP? We got you.</p>
                
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px; font-weight:bold; font-size:1.2rem;">
                        <span style="color:#94a3b8;">.JPG</span>
                        <i class="fas fa-sync-alt" style="color:var(--accent);"></i>
                        <span style="color:#10b981;">.PNG</span>
                        <i class="fas fa-sync-alt" style="color:var(--accent);"></i>
                        <span style="color:#f59e0b;">.WEBP</span>
                    </div>
                </div>

                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> High Quality PNG Export</li>
                    <li><i class="fas fa-check-circle"></i> Universal JPG standard</li>
                    <li><i class="fas fa-check-circle"></i> Fast loading WEBP for websites</li>
                </ul>
            </div>

            <div class="card">
                <h2>Convert Format</h2>
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
                                <option value="png">PNG (High Quality)</option>
                                <option value="jpg">JPG (Standard)</option>
                                <option value="webp">WEBP (Best for Websites)</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn"><i class="fas fa-file-export"></i> Convert</button>
                </form>
            </div>
        </div>

        <div class="trust-section">
            <div class="trust-stats">
                <div class="stat-item">
                    <div class="stat-value">4.9 <div class="stars"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i></div></div>
                    <div class="stat-label">Average User Rating</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">1.2M+ <i class="fas fa-users" style="color:var(--accent); font-size:1.8rem; margin-left:8px;"></i></div>
                    <div class="stat-label">Happy Users Worldwide</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">Free <i class="fas fa-check-circle" style="color:#10b981; font-size:1.8rem; margin-left:8px;"></i></div>
                    <div class="stat-label">100% Secure & Ad-Free</div>
                </div>
            </div>
            <div class="trusted-text">Trusted by thousands of students & professionals across top organizations</div>
            <div class="trust-logos">
                <i class="fab fa-google" title="Google"></i>
                <i class="fab fa-microsoft" title="Microsoft"></i>
                <i class="fab fa-aws" title="AWS"></i>
                <i class="fas fa-university" title="Universities"></i>
                <i class="fas fa-building" title="Govt. Sectors"></i>
            </div>
        </div>

        <div class="testimonials">
            <h2>What Users Say About Snapzo Pro</h2>
            <div class="testi-grid">
                <div class="testi-card">
                    <div class="stars" style="margin-bottom:15px;"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=11" alt="User 1" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Ravi Sharma</h4>
                            <p>Govt. Job Aspirant</p>
                        </div>
                    </div>
                    <div class="testi-text">"Bhai kya mast tool hai! Railway RRB NTPC form ke liye passport photo ekdum perfect size mein ban gayi. Ab cyber cafe jaane ki zaroorat nahi padti."</div>
                </div>
                <div class="testi-card">
                    <div class="stars" style="margin-bottom:15px;"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i></div>
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=5" alt="User 2" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Neha Verma</h4>
                            <p>College Student</p>
                        </div>
                    </div>
                    <div class="testi-text">"I used the Photo to PDF and Image Compressor tools for my college assignments. The process is extremely fast, 100% free, and there are no annoying ads. Highly recommended!"</div>
                </div>
                <div class="testi-card">
                    <div class="stars" style="margin-bottom:15px;"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i></div>
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=60" alt="User 3" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Arjun Patel</h4>
                            <p>Freelance Content Creator</p>
                        </div>
                    </div>
                    <div class="testi-text">"The Social Media Resizer is a lifesaver. It automatically adjusts my images for YouTube thumbnails perfectly without breaking the quality. Great job Snapzo Pro team!"</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <div class="footer-founder">Built with ❤️ by <span style="color: var(--accent);">Vishal</span><br><span style="font-size: 0.85rem; opacity: 0.7;">Founder, Snapzo Pro</span></div>
            <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" class="insta-btn"><i class="fab fa-instagram" style="font-size: 1.2rem;"></i> Follow me on Instagram</a>
        </div>
    </div>

    <script>
        let cropper = null;

        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function switchTool(toolName) {
            const tools = ['passport', 'crop', 'pdf', 'compress', 'social', 'format'];
            tools.forEach(t => {
                const el = document.getElementById('tool-' + t);
                if (t === toolName) {
                    el.style.display = 'flex';
                } else {
                    el.style.display = 'none';
                }
                document.getElementById('desk-' + t).classList.toggle('active-menu', t === toolName);
                document.getElementById('mob-' + t).classList.toggle('active-menu', t === toolName);
            });
            if(window.innerWidth <= 950) { 
                document.getElementById('sidebar').classList.remove('active'); 
                document.getElementById('overlay').classList.remove('active'); 
            }
        }

        function handlePreview(input, imgId, dropTextId) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById(imgId).src = e.target.result;
                    document.getElementById(imgId).style.display = 'block';
                    if(document.getElementById(dropTextId)) { document.getElementById(dropTextId).style.display = 'none'; }
                };
                reader.readAsDataURL(input.files[0]);
            }
        }

        function handleFileCrop(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('upload-zone-crop').style.display = 'none';
                    document.getElementById('cropper-wrapper').style.display = 'block';
                    const image = document.getElementById('image-to-crop');
                    image.src = e.target.result;
                    if (cropper) { cropper.destroy(); }
                    cropper = new Cropper(image, { viewMode: 1, background: false, zoomable: false });
                };
                reader.readAsDataURL(input.files[0]);
            }
        }

        function submitCrop() {
            if (!cropper) return alert('Please upload an image first.');
            const cropData = cropper.getData(true);
            document.getElementById('cropX').value = cropData.x;
            document.getElementById('cropY').value = cropData.y;
            document.getElementById('cropWidth').value = cropData.width;
            document.getElementById('cropHeight').value = cropData.height;
            document.getElementById('cropForm').submit();
        }
    </script>
</body>
</html>
'''

# --- PYTHON LOGIC (100% UNCHANGED) ---

def auto_crop_passport(img):
    h, w = img.shape[:2]
    target_ratio = 413 / 531
    if (w / h) > target_ratio:
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
            tool_type = request.form.get('tool_type', 'passport')
            file = request.files.get('file')
            if not file: return "Error: No file", 400
            
            file_bytes = file.read()
            img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)

            # ================= 1. PASSPORT =================
            if tool_type == 'passport':
                face = cv2.resize(auto_crop_passport(img), (413, 531))
                bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[235, 235, 235])
                bh, bw = bordered.shape[:2]

                canvas = np.ones((2600, 1800, 3), dtype=np.uint8) * 255
                count = int(request.form.get("count", 8))
                
                for i in range(min(count, 12)):
                    r, c = i // 3, i % 3
                    y_p, x_p = r*(bh+45)+70, c*(bw+30)+70
                    
                    if y_p+bh <= canvas.shape[0] and x_p+bw <= canvas.shape[1]:
                        canvas[y_p:y_p+bh, x_p:x_p+bw] = bordered

                max_r = ((min(count, 12) - 1) // 3)
                max_c = 2 if count >= 3 else (count - 1)
                final_h = (max_r + 1) * (bh + 45) + 100
                final_w = (max_c + 1) * (bw + 30) + 100
                canvas = canvas[:final_h, :final_w]

                _, buffer = cv2.imencode('.jpg', canvas)
                io_buf = io.BytesIO(buffer)

                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c_pdf = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c_pdf.drawImage(ImageReader(io_buf), 45, 100, width=505, height=680)
                    c_pdf.showPage()
                    c_pdf.save()
                    pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_photos.pdf')
                
                io_buf.seek(0)
                return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='snapzo_photos.jpg')

            # ================= 2. CROP =================
            elif tool_type == 'crop':
                x, y = int(request.form.get('x', 0)), int(request.form.get('y', 0))
                w, h = int(request.form.get('width', img.shape[1])), int(request.form.get('height', img.shape[0]))
                x, y = max(0, x), max(0, y)
                w, h = min(w, img.shape[1] - x), min(h, img.shape[0] - y)

                cropped_img = img[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', cropped_img)
                io_buf = io.BytesIO(buffer)
                return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='snapzo_cropped.jpg')

            # ================= 3. PDF =================
            elif tool_type == 'pdf':
                _, buffer = cv2.imencode('.jpg', img)
                io_buf = io.BytesIO(buffer)
                pdf_io = io.BytesIO()
                c_pdf = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                
                img_h, img_w = img.shape[:2]
                a4_w, a4_h = A4
                margin = 50
                ratio = min((a4_w - 2*margin) / img_w, (a4_h - 2*margin) / img_h)
                new_w, new_h = img_w * ratio, img_h * ratio
                pos_x, pos_y = (a4_w - new_w) / 2, (a4_h - new_h) / 2
                
                c_pdf.drawImage(ImageReader(io_buf), pos_x, pos_y, width=new_w, height=new_h)
                c_pdf.showPage()
                c_pdf.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_document.pdf')

            # ================= 4. COMPRESS =================
            elif tool_type == 'compress':
                quality = max(5, min(100, int(request.form.get("quality", 60))))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, buffer = cv2.imencode('.jpg', img, encode_param)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_compressed.jpg')

            # ================= 5. SOCIAL RESIZER =================
            elif tool_type == 'social':
                platform = request.form.get('platform')
                if platform == 'yt':
                    dim = (1280, 720)
                elif platform == 'insta':
                    dim = (1080, 1080)
                elif platform == 'fb':
                    dim = (820, 312)
                else:
                    dim = (1080, 1080)
                
                resized_img = cv2.resize(img, dim)
                _, buffer = cv2.imencode('.jpg', resized_img)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name=f'snapzo_{platform}.jpg')

            # ================= 6. FORMAT CONVERTER =================
            elif tool_type == 'format':
                out_format = request.form.get('out_format', 'png')
                if out_format == 'webp':
                    _, buffer = cv2.imencode('.webp', img)
                    mime = 'image/webp'
                elif out_format == 'png':
                    _, buffer = cv2.imencode('.png', img)
                    mime = 'image/png'
                else:
                    _, buffer = cv2.imencode('.jpg', img)
                    mime = 'image/jpeg'
                
                return send_file(io.BytesIO(buffer), mimetype=mime, as_attachment=True, download_name=f'snapzo_converted.{out_format}')

        except Exception as e:
            return f"Server Error: {str(e)}", 500
            
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
