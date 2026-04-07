from flask import Flask, request, render_template_string, send_file, make_response
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
    <title>Snapzo Pro | Official App & Image Tools</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#3b82f6">
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>

    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; --nav: #111827; }
        body.light-mode { --bg: #f8fafc; --card: #ffffff; --accent: #2563eb; --text: #1e293b; --border: #e2e8f0; --nav: #ffffff; }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); transition: 0.3s; overflow-x: hidden; }
        
        /* Nav */
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        
        .nav-right { display: flex; align-items: center; gap: 10px; }
        .install-btn { background: #10b981; color: white; padding: 8px 15px; border-radius: 8px; font-size: 0.8rem; cursor: pointer; display: none; border: none; font-weight: bold; }
        .desktop-menu { display: flex; gap: 5px; }
        .menu-btn { padding: 8px 12px; border-radius: 8px; cursor: pointer; font-size: 0.8rem; color: var(--text); transition: 0.2s; font-weight: 500; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white; }

        /* Main Layout */
        .main { padding: 50px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; }
        
        /* TWO-COLUMN LAYOUT RESTORED */
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 50px; }
        .tool-wrapper.active { display: flex; }
        
        /* Left Content Restored */
        .tool-content { flex: 1.2; text-align: left; color: var(--text); }
        .tool-content h1 { font-size: 2.3rem; margin-top: 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.1rem; line-height: 1.6; opacity: 0.9; margin-bottom: 25px; }
        
        .feature-list { list-style: none; padding: 0; margin-bottom: 30px; }
        .feature-list li { margin-bottom: 12px; font-size: 1rem; display: flex; align-items: center; gap: 10px; }
        .feature-list i { color: #10b981; }
        
        /* Graphic Boxes Restored */
        .visual-box { background: var(--nav); border: 1px solid var(--border); border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 20px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.2); }
        
        /* Right Card Tool */
        .card { flex: 1; background: var(--card); padding: 35px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 25px 50px rgba(0,0,0,0.2); border: 1px solid var(--border); }
        .card h2 { margin-top: 0; text-align: center; font-size: 1.6rem; color: var(--text); }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); }
        .preview-img { max-width: 100%; max-height: 200px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        textarea, input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg); color: var(--text); box-sizing: border-box; font-size: 1rem; }
        .row { display: flex; gap: 15px; margin: 20px 0; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(59,130,246,0.3); }

        /* Trust & Reviews RESTORED WITH IMAGES */
        .trust-section { width: 100%; max-width: 900px; text-align: center; padding: 50px 0; border-top: 1px solid var(--border); margin-top: 20px; color: var(--text); }
        
        .testimonials { width: 100%; max-width: 1100px; margin: 40px auto; padding: 0 20px; }
        .testimonials h2 { font-size: 2.2rem; text-align: center; color: var(--text); margin-bottom: 40px; }
        .testi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; }
        .testi-card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 30px; }
        .testi-header { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
        .testi-avatar { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border); }
        .testi-info h4 { margin: 0; color: var(--text); }
        .testi-info p { margin: 3px 0 0; color: var(--text); opacity: 0.7; font-size: 0.9rem; }
        .testi-text { color: var(--text); font-style: italic; opacity: 0.9; line-height: 1.6; }

        .footer { text-align: center; padding: 40px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }

        @media (max-width: 900px) { .tool-wrapper.active { flex-direction: column; align-items: center; } .tool-content { text-align: center; order: -1; } .feature-list li { justify-content: center; } .desktop-menu { display: none; } }
    </style>
</head>
<body class="dark-mode">

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right">
            <button id="installApp" class="install-btn"><i class="fas fa-download"></i> Install App</button>
            <div class="desktop-menu">
                <div class="menu-btn active-menu" onclick="switchTool('passport')" id="d-passport">Passport Maker</div>
                <div class="menu-btn" onclick="switchTool('textpdf')" id="d-textpdf">Text to PDF</div>
                <div class="menu-btn" onclick="switchTool('pdf')" id="d-pdf">Image to PDF</div>
                <div class="menu-btn" onclick="switchTool('crop')" id="d-crop">Crop</div>
                <div class="menu-btn" onclick="switchTool('compress')" id="d-compress">Compress</div>
                <div class="menu-btn" onclick="switchTool('social')" id="d-social">Social</div>
                <div class="menu-btn" onclick="switchTool('format')" id="d-format">Convert</div>
            </div>
            <div onclick="toggleTheme()" style="cursor: pointer; color: var(--accent); font-size: 1.3rem; margin-left: 10px;"><i class="fas fa-adjust"></i></div>
        </div>
    </div>

    <div class="main">
        
        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>Strict AI Passport Maker</h1>
                <p>Ab photo size ki galti kabhi nahi hogi! Hamara AI strictly Indian Govt. rules (3.5x4.5 ratio) use karke perfect pixel output deta hai.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px;">
                        <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80" style="width:90px; height:90px; object-fit:cover; border-radius:10px;">
                        <i class="fas fa-arrow-right" style="font-size:1.5rem; color:var(--accent);"></i>
                        <img src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&q=80" style="width:90px; height:116px; object-fit:cover; border:3px solid white; border-radius:2px;">
                    </div>
                    <p style="margin-top:10px; font-size:0.9rem; color:var(--text);">AI Auto-Crop ensures correct size hamesha.</p>
                </div>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Permanent 413x531 Pixels (3.5x4.5 cm)</li>
                    <li><i class="fas fa-check-circle"></i> Perfect for SSC, RRB, NTPC & State Exams</li>
                    <li><i class="fas fa-check-circle"></i> Multiple Copies Layout (Print Ready)</li>
                </ul>
            </div>
            <div class="card">
                <h2>Generate Passport</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group"><label>Quantity</label><input type="number" name="count" value="8"></div>
                        <div class="group"><label>Type</label><select name="type"><option value="jpg">JPG Image</option><option value="pdf">PDF Document</option></select></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Process Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-textpdf">
            <div class="tool-content">
                <h1>Text to PDF Converter</h1>
                <p>Type kijiye aur instantly ek clean PDF document download karein. Students ke notes ya letters ke liye best hai.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Clean A4 Layout</li>
                    <li><i class="fas fa-check-circle"></i> Fast Document Creation</li>
                </ul>
            </div>
            <div class="card">
                <h2>Type Text</h2>
                <form method="POST">
                    <input type="hidden" name="tool_type" value="textpdf">
                    <textarea name="pdf_text" placeholder="Yahan apna content likhein..." required></textarea>
                    <button class="btn"><i class="fas fa-file-pdf"></i> Download PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Image to PDF Converter</h1>
                <p>Single ya multiple photos (marksheets, docs) ko ek hi PDF file mein merge karein securely.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:15px; font-size:2rem;">
                        <i class="fas fa-file-image" style="color:#38bdf8;"></i>
                        <i class="fas fa-plus" style="font-size:1rem; opacity:0.6;"></i>
                        <i class="fas fa-file-image" style="color:#38bdf8;"></i>
                        <i class="fas fa-arrow-right" style="color:var(--accent);"></i>
                        <i class="fas fa-file-pdf" style="color:#ef4444;"></i>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>Upload Docs</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('f-pdf').click()">
                        <input type="file" id="f-pdf" name="file" hidden required multiple onchange="handleMultiple(this)">
                        <div id="t-pdf"><i class="fas fa-images" style="font-size:3rem; color:var(--accent);"></i><p>Select Photos</p></div>
                        <div id="pdf-count" style="display:none; font-weight:bold; color:var(--accent); font-size:1.1rem;"></div>
                    </div>
                    <button class="btn" style="margin-top:20px;">Create PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content">
                <h1>Manual Crop Studio</h1>
                <p>Photo ka unwanted area remove karein full precision ke sath. Drag karke sahi area select karein.</p>
            </div>
            <div class="card">
                <h2>Adjust Photo</h2>
                <form method="POST" enctype="multipart/form-data" id="cropForm">
                    <input type="hidden" name="tool_type" value="crop">
                    <input type="hidden" name="x" id="cX"><input type="hidden" name="y" id="cY"><input type="hidden" name="width" id="cW"><input type="hidden" name="height" id="cH">
                    <div class="upload-zone" id="z-crop" onclick="document.getElementById('f-crop').click()">
                        <input type="file" id="f-crop" name="file" hidden required onchange="initCrop(this)">
                        <i class="fas fa-crop-alt" style="font-size:3rem; color:var(--accent);"></i><p>Select Photo to Crop</p>
                    </div>
                    <div id="c-wrapper" style="display:none; max-height:300px; overflow:hidden;"><img id="i-crop" style="max-width:100%;"></div>
                    <button type="button" class="btn" onclick="doCrop()" style="margin-top:20px;">Crop & Download</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content">
                <h1>Image Compressor</h1>
                <p>Heavy photos ki file size kam karein visual quality maintain rakhte hue. Govt forms upload ke liye useful.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:20px; font-weight:bold;">
                        <span style="color:#ef4444; border:2px solid; padding:10px; border-radius:8px;">5.2 MB</span>
                        <i class="fas fa-chevron-right" style="color:var(--accent);"></i>
                        <span style="color:#10b981; background:#10b981; color:white; padding:10px; border-radius:8px;">150 KB</span>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>Optimize Size</h2>
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
            <div class="tool-content">
                <h1>Social Media Resizer</h1>
                <p>Kahin bhi guesses nahi! YouTube Thumbnail, Instagram Post ya FB Cover ke liye strictly correct dimensions payein.</p>
                <div class="visual-box">
                    <div style="display:flex; justify-content:space-around; align-items:center; font-size:1.8rem;">
                        <i class="fab fa-youtube" style="color:#ef4444;" title="YouTube"></i>
                        <i class="fab fa-instagram" style="color:#ec4899;" title="Instagram"></i>
                        <i class="fab fa-facebook" style="color:#3b82f6;" title="Facebook"></i>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>Resize Photo</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="social">
                    <div class="upload-zone" onclick="document.getElementById('f-soc').click()">
                        <input type="file" id="f-soc" name="file" hidden required onchange="handlePreview(this, 'p-soc', 't-soc')">
                        <div id="t-soc"><i class="fas fa-share-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload</p></div>
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
                <p>Photo extension badlein turant. PNG ko JPG ya WebP ko PNG banayein high quality mein.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:15px; font-weight:bold; color:var(--accent);">
                        <span>.JPG</span> <i class="fas fa-exchange-alt"></i> <span>.PNG</span> <i class="fas fa-exchange-alt"></i> <span>.WebP</span>
                    </div>
                </div>
            </div>
            <div class="card">
                <h2>Convert Extension</h2>
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="format">
                    <div class="upload-zone" onclick="document.getElementById('f-fmt').click()">
                        <input type="file" id="f-fmt" name="file" hidden required onchange="handlePreview(this, 'p-fmt', 't-fmt')">
                        <div id="t-fmt"><i class="fas fa-exchange-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload</p></div>
                        <img id="p-fmt" class="preview-img">
                    </div>
                    <div class="row"><div class="group"><label>Output Format</label><select name="out_format"><option value="png">PNG (High Quality)</option><option value="jpg">JPG (Standard)</option><option value="webp">WebP (Web Optimized)</option></select></div></div>
                    <button class="btn">Convert Now</button>
                </form>
            </div>
        </div>

        <div class="testimonials">
            <h2>User Reviews ⭐⭐⭐⭐⭐</h2>
            <div class="testi-grid">
                
                <div class="testi-card">
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=11" alt="Ravi Sharma" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Ravi Sharma</h4>
                            <p>Govt. Job Aspirant</p>
                        </div>
                    </div>
                    <p class="testi-text">"Bhai strictly strict size fix hai! NTPC form ke liye exact passport ban gayi without cyber cafe jaye. Awesome."</p>
                </div>

                <div class="testi-card">
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=5" alt="Neha Verma" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Neha Verma</h4>
                            <p>College Student</p>
                        </div>
                    </div>
                    <p class="testi-text">"Multiple marksheets ki PDF banani thi securely, bahut jaldi ho gaya. App download karke rakh liya ab."</p>
                </div>

                <div class="testi-card">
                    <div class="testi-header">
                        <img src="https://i.pravatar.cc/150?img=60" alt="Arjun" class="testi-avatar">
                        <div class="testi-info">
                            <h4>Arjun</h4>
                            <p>Freelancer</p>
                        </div>
                    </div>
                    <p class="testi-text">"Social resizer YouTube thumbnails ke liye ekdum perfect size deta hai. Highly recommended tool suite."</p>
                </div>

            </div>
        </div>

        <div class="footer">
            <p>Trusted by 1.2M+ Users Worldwide | 100% Free & Secure</p>
            <p>Built with ❤️ by <b>Vishal</b></p>
            <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" class="insta-btn"><i class="fab fa-instagram"></i> Follow on Instagram</a>
        </div>
    </div>

    <script>
        let cropper;
        // Theme Toggle Restored
        function toggleTheme() {
            const body = document.body;
            body.classList.toggle('light-mode');
            body.classList.toggle('dark-mode');
            const icon = document.querySelector('.theme-toggle i');
            if(body.classList.contains('light-mode')) icon.className = 'fas fa-moon';
            else icon.className = 'fas fa-sun';
        }

        function switchTool(name) {
            const tools = ['passport', 'textpdf', 'pdf', 'crop', 'compress', 'social', 'format'];
            tools.forEach(t => {
                const el = document.getElementById('tool-'+t);
                if(el) el.style.display = (t === name) ? 'flex' : 'none';
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) deskBtn.classList.toggle('active-menu', t === name);
            });
            // Auto close mobile sidebar if implemented
        }

        function handlePreview(input, pId, tId) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    const img = document.getElementById(pId);
                    img.src = e.target.result;
                    img.style.display = 'block';
                    document.getElementById(tId).style.display = 'none';
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        function handleMultiple(input) {
            const div = document.getElementById('pdf-count');
            div.innerText = input.files.length + " Images Selected ✅";
            div.style.display = 'block';
            document.getElementById('t-pdf').style.display = 'none';
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
                    cropper = new Cropper(img, { viewMode: 1, background: false });
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        function doCrop() {
            if(!cropper) return alert('Pahle photo select karein');
            const data = cropper.getData(true);
            document.getElementById('cX').value = data.x;
            document.getElementById('cY').value = data.y;
            document.getElementById('cW').value = data.width;
            document.getElementById('cH').value = data.height;
            document.getElementById('cropForm').submit();
        }

        // PWA App Installation Logic (Retained)
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault(); deferredPrompt = e;
            document.getElementById('installApp').style.display = 'block';
        });
        document.getElementById('installApp').addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') document.getElementById('installApp').style.display = 'none';
                deferredPrompt = null;
            }
        });
        if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js'); }
    </script>
</body>
</html>
'''

# --- PYTHON BACKEND LOGIC (Strict Sizing + Multi-PDF Working) ---

def strict_passport_crop(img):
    """3.5x4.5 ratio strictly follow karta hai"""
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
def home(): return render_template_string(HTML)

@app.route('/manifest.json')
def manifest():
    return {
        "name": "Snapzo Pro AI Tools", "short_name": "SnapzoPro",
        "start_url": "/", "display": "standalone",
        "background_color": "#0f172a", "theme_color": "#3b82f6",
        "icons": [{"src": LOGO_URL, "sizes": "512x512", "type": "image/jpg"}]
    }

@app.route('/sw.js')
def service_worker():
    response = make_response("self.addEventListener('fetch', function(event) {});")
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/', methods=['POST'])
def handle_tools():
    tool_type = request.form.get('tool_type')
    try:
        # Tool: Text to PDF
        if tool_type == 'textpdf':
            text = request.form.get('pdf_text', '')
            pdf_io = io.BytesIO()
            c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
            text_obj = c.beginText(50, 800)
            text_obj.setFont("Helvetica", 12)
            for line in text.split('\\n'): text_obj.textLine(line)
            c.drawText(text_obj)
            c.save()
            pdf_io.seek(0)
            return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='notes.pdf')

        # Tool: Images to PDF (Multiple Support)
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
            c.save()
            pdf_io.seek(0)
            return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='documents.pdf')

        # Handle other tools (require single 'file' input)
        file = request.files.get('file')
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

        if tool_type == 'passport':
            # Strict ratio + strict size resize
            cropped = strict_passport_crop(img)
            face = cv2.resize(cropped, (413, 531)) # 3.5x4.5cm at 300DPI approx
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
                c.save()
                pdf_io.seek(0)
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
