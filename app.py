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
    <title>Snapzo Pro | Official App</title>
    
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
        .nav { background: var(--nav); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.3rem; }
        .nav-brand img { height: 35px; border-radius: 5px; }

        .nav-right { display: flex; align-items: center; gap: 10px; }
        .install-btn { background: #10b981; color: white; padding: 8px 15px; border-radius: 8px; font-size: 0.8rem; cursor: pointer; display: none; border: none; font-weight: bold; }
        
        .desktop-menu { display: flex; gap: 5px; }
        .menu-btn { padding: 8px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; color: var(--text); transition: 0.2s; }
        .menu-btn:hover, .active-menu { background: var(--accent); color: white; }

        .main { padding: 40px 20px; display: flex; flex-direction: column; align-items: center; min-height: 85vh; }
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 40px; align-items: flex-start; justify-content: space-between; margin-bottom: 40px; }
        .tool-wrapper.active { display: flex; }
        
        .tool-content { flex: 1.2; text-align: left; }
        .tool-content h1 { font-size: 2.2rem; color: var(--text); margin: 0 0 15px 0; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .tool-content p { font-size: 1.05rem; line-height: 1.6; opacity: 0.8; }
        
        .card { flex: 1; background: var(--card); padding: 30px; border-radius: 24px; width: 100%; max-width: 450px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); border: 1px solid var(--border); }
        .upload-zone { border: 2px dashed var(--accent); padding: 35px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); }
        .preview-img { max-width: 100%; max-height: 200px; border-radius: 10px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        textarea, input, select { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg); color: var(--text); box-sizing: border-box; font-size: 1rem; }
        .row { display: flex; gap: 10px; margin: 15px 0; }
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(59,130,246,0.4); }

        .footer { text-align: center; padding: 30px; border-top: 1px solid var(--border); width: 100%; max-width: 1100px; margin-top: 50px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433, #dc2743, #bc1888); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 15px; }

        @media (max-width: 900px) { .tool-wrapper.active { flex-direction: column; align-items: center; } .tool-content { text-align: center; order: -1; } .desktop-menu { display: none; } }
    </style>
</head>
<body class="dark-mode">

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right">
            <button id="installApp" class="install-btn"><i class="fas fa-download"></i> App</button>
            <div class="desktop-menu">
                <div class="menu-btn active-menu" onclick="switchTool('passport')" id="d-passport">Passport</div>
                <div class="menu-btn" onclick="switchTool('textpdf')" id="d-textpdf">Text to PDF</div>
                <div class="menu-btn" onclick="switchTool('pdf')" id="d-pdf">Image to PDF</div>
                <div class="menu-btn" onclick="switchTool('crop')" id="d-crop">Crop</div>
                <div class="menu-btn" onclick="switchTool('compress')" id="d-compress">Compress</div>
                <div class="menu-btn" onclick="switchTool('social')" id="d-social">Social</div>
            </div>
            <div onclick="toggleTheme()" style="cursor: pointer; color: var(--accent); font-size: 1.3rem; margin-left: 10px;"><i class="fas fa-adjust"></i></div>
        </div>
    </div>

    <div class="main">
        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>Strict AI Passport Maker</h1>
                <p>Ab photo size ki galti kabhi nahi hogi! Hamara AI strictly 3.5x4.5 ratio use karke perfect 413x531 pixel output deta hai.</p>
                <div style="background:var(--card); padding:20px; border-radius:15px; border:1px solid var(--border); margin-top:20px;">
                    <i class="fas fa-id-card" style="font-size:2rem; color:var(--accent);"></i>
                    <h4 style="margin:10px 0 5px;">Indian Govt. Ready</h4>
                    <p style="margin:0; font-size:0.9rem;">SSC, RRB, aur sabhi sarkari forms ke liye 100% verified size.</p>
                </div>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <div class="row">
                        <div class="group"><label>Quantity</label><input type="number" name="count" value="8"></div>
                        <div class="group"><label>Format</label><select name="type"><option value="jpg">JPG</option><option value="pdf">PDF</option></select></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Make Passport Photo</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-textpdf">
            <div class="tool-content"><h1>Text to PDF</h1><p>Apne notes ya letters type karein aur instantly PDF document download karein. Students ke liye best tool.</p></div>
            <div class="card">
                <form method="POST">
                    <input type="hidden" name="tool_type" value="textpdf">
                    <textarea name="pdf_text" placeholder="Yahan apna text likhein..." required></textarea>
                    <button class="btn"><i class="fas fa-file-pdf"></i> Create PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content"><h1>Multi-Images to PDF</h1><p>Sabhi documents ko ek sath select karke ek single PDF file banayein. Secure aur fast.</p></div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('f-pdf').click()">
                        <input type="file" id="f-pdf" name="file" hidden required multiple onchange="handleMultiple(this)">
                        <div id="t-pdf"><i class="fas fa-images" style="font-size:3rem; color:var(--accent);"></i><p>Select Multiple Photos</p></div>
                        <div id="pdf-count" style="display:none; font-weight:bold; color:var(--accent);"></div>
                    </div>
                    <button class="btn">Create PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content"><h1>Manual Crop Studio</h1><p>Photo ka wo hissa kaatein jo aapko chahiye. Full control aur high quality.</p></div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data" id="cropForm">
                    <input type="hidden" name="tool_type" value="crop">
                    <input type="hidden" name="x" id="cX"><input type="hidden" name="y" id="cY"><input type="hidden" name="width" id="cW"><input type="hidden" name="height" id="cH">
                    <div class="upload-zone" id="z-crop" onclick="document.getElementById('f-crop').click()">
                        <input type="file" id="f-crop" name="file" hidden required onchange="initCrop(this)">
                        <i class="fas fa-crop-alt" style="font-size:3rem; color:var(--accent);"></i><p>Select Photo</p>
                    </div>
                    <div id="c-wrapper" style="display:none;"><img id="i-crop" style="max-width:100%;"></div>
                    <button type="button" class="btn" onclick="doCrop()" style="margin-top:15px;">Crop Now</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-compress">
            <div class="tool-content"><h1>Image Compressor</h1><p>Heavy photos ki size kam karein bina quality kharab kiye. Upload limits ke liye best tool.</p></div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="compress">
                    <div class="upload-zone" onclick="document.getElementById('f-comp').click()">
                        <input type="file" id="f-comp" name="file" hidden required onchange="handlePreview(this, 'p-comp', 't-comp')">
                        <div id="t-comp"><i class="fas fa-compress-arrows-alt" style="font-size:3rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-comp" class="preview-img">
                    </div>
                    <div class="row"><div class="group"><label>Quality (10-100)</label><input type="number" name="quality" value="60"></div></div>
                    <button class="btn">Compress & Download</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-social">
            <div class="tool-content"><h1>Social Media Resizer</h1><p>YouTube, Instagram aur Facebook ke liye perfect size mein photo resize karein.</p></div>
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
    </div>

    <div class="footer">
        <p>Trusted by 1.2M+ Users Worldwide ⭐⭐⭐⭐⭐</p>
        <p>Built with ❤️ by <b>Vishal</b></p>
        <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" class="insta-btn"><i class="fab fa-instagram"></i> Follow on Instagram</a>
    </div>

    <script>
        let cropper;
        function toggleTheme() { document.body.classList.toggle('light-mode'); document.body.classList.toggle('dark-mode'); }
        function switchTool(name) {
            ['passport', 'textpdf', 'pdf', 'crop', 'compress', 'social'].forEach(t => {
                document.getElementById('tool-'+t).classList.toggle('active', t === name);
                const deskBtn = document.getElementById('d-'+t);
                if(deskBtn) deskBtn.classList.toggle('active-menu', t === name);
            });
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
                    cropper = new Cropper(img, { viewMode: 1 });
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        function doCrop() {
            const data = cropper.getData(true);
            document.getElementById('cX').value = data.x;
            document.getElementById('cY').value = data.y;
            document.getElementById('cW').value = data.width;
            document.getElementById('cH').value = data.height;
            document.getElementById('cropForm').submit();
        }

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

# --- BACKEND LOGIC (STRICT SIZE FIX + TOOLS) ---

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
            return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='images.pdf')

        file = request.files.get('file')
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

        if tool_type == 'passport':
            cropped = strict_passport_crop(img)
            face = cv2.resize(cropped, (413, 531))
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

    except Exception as e: return f"Error: {str(e)}", 500
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
