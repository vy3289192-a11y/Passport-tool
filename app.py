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
    
    <meta name="google-site-verification" content="TlhW07oDD-Gp8H0gKFC3U7n7v2l3ccnwGpOC90B_7Uc" />

    <title>Snapzo Pro | Free AI Passport Photo Maker & Image Tools</title>
    
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>

    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; }
        body.light-mode { --bg: #f8fafc; --card: #ffffff; --accent: #2563eb; --text: #1e293b; --border: #e2e8f0; }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; transition: 0.3s; }
        
        .nav { background: #111827; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: white; font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }

        .desktop-menu { display: flex; gap: 5px; }
        .menu-btn { padding: 8px 12px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; color: #cbd5e1; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white; }

        .mobile-toggle { display: none; font-size: 1.5rem; cursor: pointer; color: var(--accent); }
        .sidebar { width: 250px; height: 100vh; background: #111827; position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; box-sizing: border-box; overflow-y: auto; }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { padding: 15px; display: flex; align-items: center; gap: 15px; color: #cbd5e1; border-radius: 8px; margin-bottom: 10px; transition: 0.2s; cursor: pointer; font-size: 1rem; }
        .sidebar .menu-btn:hover, .sidebar .active-menu { background: var(--accent); color: white; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }

        .main { padding: 50px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; }
        
        /* TWO-COLUMN LAYOUT */
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; }
        .tool-wrapper.active { display: flex; }
        
        .tool-content { flex: 1.2; text-align: left; }
        .tool-content h1 { font-size: 2.2rem; color: white; margin: 0 0 15px 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.05rem; line-height: 1.6; opacity: 0.9; }
        
        .feature-list { list-style: none; padding: 0; margin: 25px 0; }
        .feature-list li { margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
        .feature-list i { color: #10b981; }
        
        .visual-box { background: #111827; border: 1px solid var(--border); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; }
        
        .card { flex: 1; background: var(--card); padding: 35px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 25px 50px rgba(0,0,0,0.3); border: 1px solid var(--border); }
        .card h2 { margin-top: 0; text-align: center; font-size: 1.6rem; color: white; }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        textarea, input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; box-sizing: border-box; font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.4); }

        /* Trust Stats */
        .trust-section { width: 100%; max-width: 900px; text-align: center; padding: 50px 0; border-top: 1px solid var(--border); margin-top: 20px; }
        .trust-stats { display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-bottom: 30px; }
        .stat-item { display: flex; flex-direction: column; align-items: center; }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: white; }
        .stat-label { font-size: 0.9rem; color: #94a3b8; margin-top: 5px; }

        /* Testimonials */
        .testimonials { width: 100%; max-width: 1100px; margin: 40px auto; padding: 0 20px; }
        .testi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
        .testi-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 30px; }
        .testi-header { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
        .testi-avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border); }
        .testi-info h4 { margin: 0; color: white; }
        .testi-info p { margin: 3px 0 0; color: #94a3b8; font-size: 0.9rem; }

        .footer { text-align: center; padding: 40px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }

        @media (max-width: 900px) { 
            .tool-wrapper.active { flex-direction: column; align-items: center; } 
            .tool-content { text-align: center; order: -1; } 
            .feature-list li { justify-content: center; } 
            .desktop-menu { display: none; } 
            .mobile-toggle { display: block; }
        }
    </style>
</head>
<body>

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right" style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <div class="menu-btn active-menu" onclick="switchTool('passport')" id="d-passport">Passport Maker</div>
                <div class="menu-btn" onclick="switchTool('textpdf')" id="d-textpdf">Text to PDF</div>
                <div class="menu-btn" onclick="switchTool('pdf')" id="d-pdf">Image to PDF</div>
                <div class="menu-btn" onclick="switchTool('crop')" id="d-crop">Crop</div>
                <div class="menu-btn" onclick="switchTool('compress')" id="d-compress">Compress</div>
                <div class="menu-btn" onclick="switchTool('social')" id="d-social">Social Size</div>
            </div>
            <div onclick="toggleTheme()" style="cursor:pointer; color:var(--accent); font-size:1.3rem;"><i class="fas fa-adjust"></i></div>
            <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()" style="margin-left: 10px;"></i>
        </div>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Snapzo Menu</h3>
        <div class="menu-btn active-menu" onclick="switchTool('passport')" id="m-passport"><i class="fas fa-id-badge"></i> Passport Maker</div>
        <div class="menu-btn" onclick="switchTool('textpdf')" id="m-textpdf"><i class="fas fa-file-alt"></i> Text to PDF</div>
        <div class="menu-btn" onclick="switchTool('pdf')" id="m-pdf"><i class="fas fa-images"></i> Image to PDF</div>
        <div class="menu-btn" onclick="switchTool('crop')" id="m-crop"><i class="fas fa-crop-alt"></i> Manual Crop</div>
        <div class="menu-btn" onclick="switchTool('compress')" id="m-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</div>
        <div class="menu-btn" onclick="switchTool('social')" id="m-social"><i class="fas fa-share-alt"></i> Social Size</div>
        <div class="menu-btn" onclick="switchTool('format')" id="m-format"><i class="fas fa-exchange-alt"></i> Format Convert</div>
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

        <div class="tool-wrapper" id="tool-textpdf">
            <div class="tool-content">
                <h1>Text to PDF Converter</h1>
                <p>Type your notes or letters and convert them into a clean PDF document instantly. Best for students.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Professional A4 Formatting</li>
                    <li><i class="fas fa-check-circle"></i> High Quality PDF Output</li>
                </ul>
            </div>
            <div class="card">
                <h2>Type Content</h2>
                <form method="POST">
                    <input type="hidden" name="tool_type" value="textpdf">
                    <textarea name="pdf_text" placeholder="Start typing here..." required></textarea>
                    <button class="btn"><i class="fas fa-file-pdf"></i> Create PDF</button>
                </form>
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
                                <option value="png">PNG (High Quality)</option>
                                <option value="jpg">JPG (Standard)</option>
                                <option value="webp">WEBP (Best for Websites)</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="btn">Convert</button>
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
                    <p>"Multiple marksheets ki PDF banani thi securely, bahut jaldi ho gaya. Interface bahut clean hai."</p>
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

        function toggleTheme() { document.body.classList.toggle('light-mode'); }
        
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function switchTool(name) {
            const tools = ['passport', 'textpdf', 'pdf', 'crop', 'compress', 'social', 'format'];
            tools.forEach(t => {
                const el = document.getElementById('tool-'+t);
                if(el) el.style.display = (t === name) ? 'flex' : 'none';
                
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) deskBtn.classList.toggle('active-menu', t === name);
                
                const mobBtn = document.getElementById('m-'+t);
                if(mobBtn) mobBtn.classList.toggle('active-menu', t === name);
            });
            window.scrollTo(0,0);
            
            // Close mobile menu automatically after selection
            if(window.innerWidth <= 900) {
                document.getElementById('sidebar').classList.remove('active');
                document.getElementById('overlay').classList.remove('active');
            }
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

# --- BACKEND LOGIC ---

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
def home():
    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')
            
            if tool_type == 'textpdf':
                text = request.form.get('pdf_text', '')
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                y = 800
                for line in text.split('\\n'):
                    c.drawString(50, y, line); y -= 20
                c.save(); pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='notes.pdf')

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
                return send_file(io.BytesIO(buffer), mimetype=f'image/{f}', as_attachment=True, download_name=f'converted.{f}')

        except Exception as e: return f"Error: {str(e)}", 500
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
