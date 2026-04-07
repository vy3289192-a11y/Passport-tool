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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Snapzo Pro | Official AI App</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>

    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; --nav: #111827; }
        body.light-mode { --bg: #f8fafc; --card: #ffffff; --accent: #2563eb; --text: #1e293b; --border: #e2e8f0; --nav: #ffffff; }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); transition: 0.3s; padding-bottom: 70px; }
        
        /* Top Nav */
        .nav { background: var(--nav); padding: 15px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--text); font-weight: bold; font-size: 1.2rem; }
        .nav-brand img { height: 30px; border-radius: 4px; }

        /* App Bottom Menu */
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--nav); display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid var(--border); z-index: 2000; box-shadow: 0 -2px 10px rgba(0,0,0,0.2); }
        .nav-item { display: flex; flex-direction: column; align-items: center; color: var(--text); text-decoration: none; font-size: 0.7rem; opacity: 0.6; cursor: pointer; transition: 0.2s; }
        .nav-item.active { opacity: 1; color: var(--accent); }
        .nav-item i { font-size: 1.3rem; margin-bottom: 4px; }

        /* Layout */
        .main { padding: 25px 15px; display: flex; flex-direction: column; align-items: center; }
        .tool-wrapper { display: none; width: 100%; max-width: 1100px; gap: 30px; flex-direction: column; }
        .tool-wrapper.active { display: flex; }
        
        @media (min-width: 900px) {
            .tool-wrapper.active { flex-direction: row; align-items: flex-start; }
            .bottom-nav { display: none; }
            .desktop-menu { display: flex !important; gap: 10px; }
        }

        .desktop-menu { display: none; }
        .menu-btn { padding: 8px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; }
        .menu-btn.active { background: var(--accent); color: white; }

        /* Content & Cards */
        .tool-content { flex: 1.2; text-align: left; }
        .tool-content h1 { font-size: 2rem; margin: 0 0 10px 0; color: var(--accent); }
        .visual-box { background: var(--nav); border: 1px solid var(--border); border-radius: 15px; padding: 20px; text-align: center; margin: 15px 0; }
        .feature-list { list-style: none; padding: 0; margin: 15px 0; }
        .feature-list li { margin-bottom: 8px; display: flex; align-items: center; gap: 10px; font-size: 0.95rem; }
        .feature-list i { color: #10b981; }

        .card { flex: 1; background: var(--card); padding: 25px; border-radius: 20px; border: 1px solid var(--border); width: 100%; box-sizing: border-box; }
        .upload-zone { border: 2px dashed var(--accent); padding: 30px 10px; border-radius: 15px; text-align: center; background: rgba(59,130,246,0.05); cursor: pointer; }
        .preview-img { max-width: 100%; max-height: 180px; border-radius: 10px; display: none; margin: 15px auto; border: 2px solid var(--accent); }

        textarea, input, select { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg); color: var(--text); box-sizing: border-box; }
        .btn { width: 100%; padding: 15px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size: 1rem; }

        /* Reviews */
        .testi-card { background: var(--card); border: 1px solid var(--border); border-radius: 15px; padding: 20px; margin-bottom: 15px; width: 100%; max-width: 350px; }
        .testi-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
        .testi-avatar { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; }
    </style>
</head>
<body class="dark-mode">

    <div class="nav">
        <a href="/" class="nav-brand"><img src="''' + LOGO_URL + '''"><span>Snapzo Pro</span></a>
        <div class="nav-right" style="display:flex; align-items:center; gap:15px;">
            <div class="desktop-menu">
                <div class="menu-btn active" onclick="switchTool('passport')">Passport</div>
                <div class="menu-btn" onclick="switchTool('textpdf')">Text to PDF</div>
                <div class="menu-btn" onclick="switchTool('pdf')">Image to PDF</div>
            </div>
            <button id="installApp" style="display:none; background:#10b981; color:white; border:none; padding:6px 12px; border-radius:6px; font-size:0.75rem; font-weight:bold;">Install App</button>
            <i class="fas fa-adjust" onclick="toggleTheme()" style="cursor:pointer; color:var(--accent);"></i>
        </div>
    </div>

    <div class="main">
        
        <div class="tool-wrapper active" id="tool-passport">
            <div class="tool-content">
                <h1>Strict AI Passport Maker</h1>
                <p>Ab size ki tension khatam! AI automatically 3.5x4.5cm ratio mein crop karta hai.</p>
                <div class="visual-box">
                    <div style="display:flex; align-items:center; justify-content:center; gap:15px;">
                        <div style="text-align:center;"><img src="https://i.pravatar.cc/150?img=32" style="width:70px; height:70px; object-fit:cover; border-radius:8px;"><br><small>Before</small></div>
                        <i class="fas fa-arrow-right" style="color:var(--accent);"></i>
                        <div style="text-align:center;"><img src="https://i.pravatar.cc/150?img=32" style="width:70px; height:90px; object-fit:cover; border:3px solid white; border-radius:2px;"><br><small>Strict Size</small></div>
                    </div>
                </div>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Permanent 413x531 Pixels</li>
                    <li><i class="fas fa-check-circle"></i> Verified for SSC, RRB, NTPC</li>
                </ul>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="passport">
                    <div class="upload-zone" onclick="document.getElementById('f-pass').click()">
                        <input type="file" id="f-pass" name="file" hidden required onchange="handlePreview(this, 'p-pass', 't-pass')">
                        <div id="t-pass"><i class="fas fa-camera" style="font-size:2.5rem; color:var(--accent);"></i><p>Upload Photo</p></div>
                        <img id="p-pass" class="preview-img">
                    </div>
                    <div style="display:flex; gap:10px; margin-top:15px;">
                        <div style="flex:1;"><label style="font-size:0.7rem;">Quantity</label><input type="number" name="count" value="8"></div>
                        <div style="flex:1;"><label style="font-size:0.7rem;">Type</label><select name="type"><option value="jpg">JPG</option><option value="pdf">PDF</option></select></div>
                    </div>
                    <button class="btn"><i class="fas fa-bolt"></i> Generate Passport</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-textpdf">
            <div class="tool-content">
                <h1>Text to PDF</h1>
                <p>Apne notes ko instantly professional document mein badlein.</p>
                <ul class="feature-list">
                    <li><i class="fas fa-check-circle"></i> Clean A4 Layout</li>
                    <li><i class="fas fa-check-circle"></i> High Quality Fonts</li>
                </ul>
            </div>
            <div class="card">
                <form method="POST">
                    <input type="hidden" name="tool_type" value="textpdf">
                    <textarea name="pdf_text" placeholder="Yahan apna content likhein..." required></textarea>
                    <button class="btn"><i class="fas fa-file-pdf"></i> Create PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-pdf">
            <div class="tool-content">
                <h1>Multi-Image to PDF</h1>
                <p>Sabhi documents ko ek hi PDF file mein merge karein.</p>
            </div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="tool_type" value="pdf">
                    <div class="upload-zone" onclick="document.getElementById('f-pdf').click()">
                        <input type="file" id="f-pdf" name="file" hidden required multiple onchange="handleMultiple(this)">
                        <div id="t-pdf"><i class="fas fa-images" style="font-size:2.5rem; color:var(--accent);"></i><p>Select Multiple Photos</p></div>
                        <div id="pdf-count" style="display:none; font-weight:bold; color:var(--accent);"></div>
                    </div>
                    <button class="btn">Generate PDF</button>
                </form>
            </div>
        </div>

        <div class="tool-wrapper" id="tool-crop">
            <div class="tool-content"><h1>Manual Crop</h1><p>Photo ka unwanted hissa kaatein.</p></div>
            <div class="card">
                <form method="POST" enctype="multipart/form-data" id="cropForm">
                    <input type="hidden" name="tool_type" value="crop">
                    <input type="hidden" name="x" id="cX"><input type="hidden" name="y" id="cY"><input type="hidden" name="width" id="cW"><input type="hidden" name="height" id="cH">
                    <div class="upload-zone" id="z-crop" onclick="document.getElementById('f-crop').click()">
                        <input type="file" id="f-crop" name="file" hidden required onchange="initCrop(this)">
                        <i class="fas fa-crop-alt" style="font-size:2.5rem; color:var(--accent);"></i><p>Select Photo</p>
                    </div>
                    <div id="c-wrapper" style="display:none;"><img id="i-crop" style="max-width:100%;"></div>
                    <button type="button" class="btn" onclick="doCrop()">Crop Now</button>
                </form>
            </div>
        </div>

        <div style="width:100%; max-width:1100px; margin-top:50px;">
            <h2 style="text-align:center;">User Reviews ⭐⭐⭐⭐⭐</h2>
            <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:15px;">
                <div class="testi-card">
                    <div class="testi-header"><img src="https://i.pravatar.cc/100?img=11" class="testi-avatar"><div><b>Ravi Sharma</b><br><small>Aspirant</small></div></div>
                    <p style="font-size:0.85rem; font-style:italic;">"Passport size ekdum perfect banti hai. Best app for students!"</p>
                </div>
                <div class="testi-card">
                    <div class="testi-header"><img src="https://i.pravatar.cc/100?img=5" class="testi-avatar"><div><b>Neha Verma</b><br><small>Student</small></div></div>
                    <p style="font-size:0.85rem; font-style:italic;">"Image to PDF feature marksheet ke liye bahut kaam aata hai."</p>
                </div>
            </div>
        </div>

        <div style="margin-top:40px; text-align:center; opacity:0.7;">
            <p>Built with ❤️ by <b>Vishal</b></p>
            <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" style="color:var(--accent); text-decoration:none; font-weight:bold;"><i class="fab fa-instagram"></i> Follow on Instagram</a>
        </div>
    </div>

    <div class="bottom-nav">
        <div class="nav-item active" onclick="switchTool('passport')" id="m-passport"><i class="fas fa-id-badge"></i><span>Passport</span></div>
        <div class="nav-item" onclick="switchTool('textpdf')" id="m-textpdf"><i class="fas fa-file-alt"></i><span>Notes</span></div>
        <div class="nav-item" onclick="switchTool('pdf')" id="m-pdf"><i class="fas fa-images"></i><span>Images</span></div>
        <div class="nav-item" onclick="switchTool('crop')" id="m-crop"><i class="fas fa-crop"></i><span>Crop</span></div>
    </div>

    <script>
        let cropper;
        function toggleTheme() { document.body.classList.toggle('light-mode'); document.body.classList.toggle('dark-mode'); }
        
        function switchTool(name) {
            const tools = ['passport', 'textpdf', 'pdf', 'crop'];
            tools.forEach(t => {
                document.getElementById('tool-'+t).classList.toggle('active', t === name);
                const mobItem = document.getElementById('m-'+t);
                if(mobItem) mobItem.classList.toggle('active', t === name);
            });
            window.scrollTo(0,0);
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
            div.innerText = input.files.length + " Photos Selected ✅";
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
            const data = cropper.getData(true);
            document.getElementById('cX').value = data.x;
            document.getElementById('cY').value = data.y;
            document.getElementById('cW').value = data.width;
            document.getElementById('cH').value = data.height;
            document.getElementById('cropForm').submit();
        }

        // PWA Install
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

@app.route('/')
def home(): return render_template_string(HTML)

@app.route('/manifest.json')
def manifest():
    return {
        "name": "Snapzo Pro AI App", "short_name": "SnapzoPro",
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
            c.setFont("Helvetica", 12)
            y = 800
            for line in text.split('\\n'):
                c.drawString(50, y, line)
                y -= 20
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

    except Exception as e: return f"Error: {str(e)}", 500
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
