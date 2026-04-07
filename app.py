from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from rembg import remove  # <--- NEW IMPORT FOR BG REMOVAL

app = Flask(__name__)

# Aapka Direct Image Link
LOGO_URL = "https://i.ibb.co/Cp1Dzh0t/46596.png"

HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro | AI Passport Maker</title>
    
    <link rel="icon" type="image/png" href="''' + LOGO_URL + '''">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>

    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; --border: #334155; }
        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); overflow-x: hidden; }
        
        .nav { background: #111827; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; }
        .nav-brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: white; }
        .nav-brand img { height: 35px; border-radius: 5px; }
        .nav-brand span { font-weight: bold; font-size: 1.3rem; letter-spacing: 0.5px; }

        .desktop-menu { display: flex; gap: 10px; align-items: center; }
        .desktop-menu .menu-btn { padding: 10px 15px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-weight: 500; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; }
        .desktop-menu .menu-btn:hover, .desktop-menu .active-menu { background: var(--accent); color: white; }
        .mobile-toggle { display: none; font-size: 1.4rem; cursor: pointer; }

        .sidebar { width: 250px; height: 100vh; background: #111827; position: fixed; left: -250px; top: 0; transition: 0.3s; z-index: 2000; padding: 20px; box-sizing: border-box; }
        .sidebar.active { left: 0; }
        .sidebar .menu-btn { padding: 15px; display: flex; align-items: center; gap: 15px; color: var(--text); border-radius: 8px; margin-bottom: 10px; transition: 0.2s; cursor: pointer; }
        .sidebar .menu-btn:hover, .sidebar .active-menu { background: var(--accent); }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1500; }
        .overlay.active { display: block; }

        .main { padding: 40px 20px; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; min-height: 85vh; }
        .card { background: var(--card); padding: 35px; border-radius: 24px; width: 100%; max-width: 500px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid var(--border); margin-bottom: 30px; }
        
        h2 { margin-top: 0; font-size: 1.8rem; text-align: center; background: linear-gradient(to right, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .upload-zone { border: 2px dashed var(--accent); padding: 40px 20px; border-radius: 18px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.03); transition: 0.3s; }
        .upload-zone:hover { background: rgba(59,130,246,0.08); border-color: white; }
        .preview-img { max-width: 100%; max-height: 250px; border-radius: 12px; display: none; margin-top: 15px; border: 2px solid var(--accent); }

        .row { display: flex; gap: 15px; margin: 20px 0; }
        .group { flex: 1; }
        label { display: block; font-size: 0.85rem; margin-bottom: 8px; opacity: 0.8; }
        input, select { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; box-sizing: border-box; font-size: 1rem; }
        input[type="color"] { padding: 5px; height: 50px; cursor: pointer; }
        
        .btn { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4); }
        .btn:hover { background: #2563eb; transform: translateY(-2px); }

        .footer { max-width: 480px; width: 100%; text-align: center; padding: 20px 0; border-top: 1px solid var(--border); }
        .footer-desc { font-size: 0.9rem; opacity: 0.7; margin-bottom: 20px; line-height: 1.5; }
        .footer-founder { font-size: 1.05rem; font-weight: 500; margin-bottom: 15px; }
        .insta-btn { display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; padding: 10px 20px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 0.9rem; transition: 0.3s; box-shadow: 0 4px 15px rgba(220, 39, 67, 0.3); }
        .insta-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(220, 39, 67, 0.5); }

        .img-container { max-height: 400px; display: none; margin-top: 15px; }
        .img-container img { max-width: 100%; display: block; }

        @media (max-width: 850px) {
            .desktop-menu { display: none; }
            .mobile-toggle { display: block; }
            .card { padding: 25px; }
        }
        
        /* Loading Overlay */
        #loader { display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.9); z-index: 9999; justify-content: center; align-items: center; flex-direction: column; color: white; }
        .spinner { border: 5px solid rgba(255,255,255,0.1); border-top: 5px solid var(--accent); border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin-bottom: 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <div id="loader">
        <div class="spinner"></div>
        <h3>Processing AI Magic...</h3>
        <p>Please wait.</p>
    </div>

    <div class="nav">
        <a href="/" class="nav-brand">
            <img src="''' + LOGO_URL + '''" alt="Logo">
            <span>Snapzo Pro</span>
        </a>
        <div class="desktop-menu">
            <div class="menu-btn active-menu" onclick="switchTool('passport')" id="desk-passport"><i class="fas fa-id-card"></i> Passport Maker</div>
            <div class="menu-btn" onclick="switchTool('crop')" id="desk-crop"><i class="fas fa-crop-alt"></i> Manual Crop</div>
            <div class="menu-btn" onclick="switchTool('pdf')" id="desk-pdf"><i class="fas fa-file-pdf"></i> Photo to PDF</div>
            <div class="menu-btn" onclick="switchTool('compress')" id="desk-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</div>
            <div class="menu-btn" onclick="switchTool('bg')" id="desk-bg"><i class="fas fa-magic"></i> Remove BG</div> </div>
        <i class="fas fa-bars mobile-toggle" onclick="toggleMenu()"></i>
    </div>

    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="sidebar" id="sidebar">
        <h3 style="color:var(--accent); margin-top:0;">Menu</h3>
        <div class="menu-btn active-menu" onclick="switchTool('passport')" id="mob-passport"><i class="fas fa-id-card"></i> Passport Maker</div>
        <div class="menu-btn" onclick="switchTool('crop')" id="mob-crop"><i class="fas fa-crop-alt"></i> Manual Crop</div>
        <div class="menu-btn" onclick="switchTool('pdf')" id="mob-pdf"><i class="fas fa-file-pdf"></i> Photo to PDF</div>
        <div class="menu-btn" onclick="switchTool('compress')" id="mob-compress"><i class="fas fa-compress-arrows-alt"></i> Compress</div>
        <div class="menu-btn" onclick="switchTool('bg')" id="mob-bg"><i class="fas fa-magic"></i> Remove BG</div> </div>

    <div class="main">
        
        <div class="card" id="tool-passport">
            <h2>AI Passport Studio</h2>
            <form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
                <input type="hidden" name="tool_type" value="passport">
                <div class="upload-zone" onclick="document.getElementById('fileInputPass').click()">
                    <input type="file" name="file" id="fileInputPass" hidden required onchange="handlePreview(this, 'preview-pass', 'drop-text-pass')">
                    <div id="drop-text-pass">
                        <i class="fas fa-cloud-upload-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                        <p style="margin:0"><b>Click to upload</b> or drag image</p>
                    </div>
                    <img id="preview-pass" class="preview-img">
                </div>
                <div class="row">
                    <div class="group"><label>Quantity</label><input type="number" name="count" value="8" min="1" max="12"></div>
                    <div class="group"><label>Format</label><select name="type"><option value="jpg">Image (JPG)</option><option value="pdf">Document (PDF)</option></select></div>
                </div>
                <button type="submit" class="btn"><i class="fas fa-bolt"></i> Generate & Download</button>
            </form>
        </div>

        <div class="card" id="tool-crop" style="display: none;">
            <h2>Manual Crop Studio</h2>
            <form method="POST" enctype="multipart/form-data" id="cropForm" onsubmit="showLoader()">
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

        <div class="card" id="tool-pdf" style="display: none;">
            <h2>Photo to PDF Converter</h2>
            <form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
                <input type="hidden" name="tool_type" value="pdf">
                <div class="upload-zone" onclick="document.getElementById('fileInputPdf').click()">
                    <input type="file" name="file" id="fileInputPdf" hidden required onchange="handlePreview(this, 'preview-pdf', 'drop-text-pdf')">
                    <div id="drop-text-pdf"><i class="fas fa-file-pdf" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i><p style="margin:0"><b>Upload Image</b> to convert</p></div>
                    <img id="preview-pdf" class="preview-img">
                </div>
                <button type="submit" class="btn" style="margin-top: 20px;"><i class="fas fa-download"></i> Download PDF</button>
            </form>
        </div>

        <div class="card" id="tool-compress" style="display: none;">
            <h2>Image Compressor</h2>
            <form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
                <input type="hidden" name="tool_type" value="compress">
                <div class="upload-zone" onclick="document.getElementById('fileInputCompress').click()">
                    <input type="file" name="file" id="fileInputCompress" hidden required onchange="handlePreview(this, 'preview-compress', 'drop-text-compress')">
                    <div id="drop-text-compress"><i class="fas fa-compress-arrows-alt" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i><p style="margin:0"><b>Upload Image</b> to compress</p></div>
                    <img id="preview-compress" class="preview-img">
                </div>
                <div class="row">
                    <div class="group"><label>Quality (10% to 100%)</label><input type="number" name="quality" value="60" min="10" max="100"></div>
                </div>
                <button type="submit" class="btn"><i class="fas fa-compress"></i> Compress & Download</button>
            </form>
        </div>

        <div class="card" id="tool-bg" style="display: none;">
            <h2>AI Background Remover</h2>
            <form method="POST" enctype="multipart/form-data" onsubmit="showLoader()">
                <input type="hidden" name="tool_type" value="bg">
                
                <div class="upload-zone" onclick="document.getElementById('fileInputBg').click()">
                    <input type="file" name="file" id="fileInputBg" hidden required onchange="handlePreview(this, 'preview-bg', 'drop-text-bg')">
                    <div id="drop-text-bg">
                        <i class="fas fa-user-slash" style="font-size: 3.5rem; color: var(--accent); margin-bottom: 10px;"></i>
                        <p style="margin:0"><b>Upload Image</b> to remove BG</p>
                    </div>
                    <img id="preview-bg" class="preview-img">
                </div>

                <div class="row">
                    <div class="group">
                        <label>Background Options</label>
                        <select name="bg_type" id="bgTypeSelector" onchange="toggleBgOptions()">
                            <option value="transparent">Transparent (PNG)</option>
                            <option value="color">Solid Color</option>
                            <option value="custom_image">Custom Background Image</option>
                        </select>
                    </div>
                </div>

                <div class="row" id="colorPickerRow" style="display: none;">
                    <div class="group">
                        <label>Choose Color</label>
                        <input type="color" name="bg_color" value="#ffffff">
                    </div>
                </div>

                <div class="upload-zone" id="customImgRow" style="display: none; padding: 20px; min-height: auto;" onclick="document.getElementById('fileInputCustomBg').click()">
                    <input type="file" name="custom_bg" id="fileInputCustomBg" hidden accept="image/*" onchange="handlePreview(this, 'preview-custom-bg', 'drop-text-custom-bg')">
                    <div id="drop-text-custom-bg"><i class="fas fa-image" style="font-size: 2rem; color: var(--text);"></i><p style="margin:5px 0 0;">Upload Background Image</p></div>
                    <img id="preview-custom-bg" class="preview-img" style="max-height: 100px;">
                </div>

                <button type="submit" class="btn" style="margin-top: 20px;">
                    <i class="fas fa-magic"></i> Remove BG & Download
                </button>
            </form>
        </div>


        <div class="footer">
            <div class="footer-desc"><strong>Snapzo Pro Suite:</strong> Create passport photos, crop precisely, compress sizes, remove backgrounds or convert to PDF - all in one place.</div>
            <div class="footer-founder">Built with ❤️ by <span style="color: var(--accent);">Vishal</span><br><span style="font-size: 0.85rem; opacity: 0.7;">Founder, Snapzo Pro</span></div>
            <a href="https://www.instagram.com/rry.vishal?igsh=YnhweDR6eDhoNXV3" target="_blank" class="insta-btn"><i class="fab fa-instagram" style="font-size: 1.2rem;"></i> Follow me on Instagram</a>
        </div>
    </div>

    <script>
        let cropper = null;

        function showLoader() { document.getElementById('loader').style.display = 'flex'; }
        
        function toggleMenu() {
            document.getElementById('sidebar').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function switchTool(toolName) {
            const tools = ['passport', 'crop', 'pdf', 'compress', 'bg'];
            tools.forEach(t => {
                document.getElementById('tool-' + t).style.display = (t === toolName) ? 'block' : 'none';
                document.getElementById('desk-' + t).classList.toggle('active-menu', t === toolName);
                document.getElementById('mob-' + t).classList.toggle('active-menu', t === toolName);
            });
            if(window.innerWidth <= 850) { toggleMenu(); }
        }

        // Generic Preview Function
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
            showLoader();
            const cropData = cropper.getData(true);
            document.getElementById('cropX').value = cropData.x;
            document.getElementById('cropY').value = cropData.y;
            document.getElementById('cropWidth').value = cropData.width;
            document.getElementById('cropHeight').value = cropData.height;
            document.getElementById('cropForm').submit();
        }

        // BG Remove Options Toggle
        function toggleBgOptions() {
            const val = document.getElementById('bgTypeSelector').value;
            document.getElementById('colorPickerRow').style.display = (val === 'color') ? 'flex' : 'none';
            document.getElementById('customImgRow').style.display = (val === 'custom_image') ? 'block' : 'none';
        }
    </script>
</body>
</html>
'''

# --- PYTHON LOGIC ---

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

            # ================= 1. PASSPORT (UNTOUCHED) =================
            if tool_type == 'passport':
                face = cv2.resize(auto_crop_passport(img), (413, 531))
                bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[235, 235, 235])
                bh, bw = bordered.shape[:2]

                canvas = np.ones((2000, 1500, 3), dtype=np.uint8) * 255
                count = int(request.form.get("count", 8))
                
                for i in range(min(count, 12)):
                    r, c = i // 3, i % 3
                    y_p, x_p = r*(bh+45)+70, c*(bw+30)+70
                    canvas[y_p:y_p+bh, x_p:x_p+bw] = bordered

                _, buffer = cv2.imencode('.jpg', canvas)
                io_buf = io.BytesIO(buffer)

                if request.form.get("type") == "pdf":
                    pdf_io = io.BytesIO()
                    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                    c.drawImage(ImageReader(io_buf), 45, 100, width=505, height=680)
                    c.showPage()
                    c.save()
                    pdf_io.seek(0)
                    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_photos.pdf')
                
                io_buf.seek(0)
                return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='snapzo_photos.jpg')

            # ================= 2. CROP (UNTOUCHED) =================
            elif tool_type == 'crop':
                x, y = int(request.form.get('x', 0)), int(request.form.get('y', 0))
                w, h = int(request.form.get('width', img.shape[1])), int(request.form.get('height', img.shape[0]))
                x, y = max(0, x), max(0, y)
                w, h = min(w, img.shape[1] - x), min(h, img.shape[0] - y)

                cropped_img = img[y:y+h, x:x+w]
                _, buffer = cv2.imencode('.jpg', cropped_img)
                io_buf = io.BytesIO(buffer)
                return send_file(io_buf, mimetype='image/jpeg', as_attachment=True, download_name='snapzo_cropped.jpg')

            # ================= 3. PDF (UNTOUCHED) =================
            elif tool_type == 'pdf':
                _, buffer = cv2.imencode('.jpg', img)
                io_buf = io.BytesIO(buffer)
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                
                img_h, img_w = img.shape[:2]
                a4_w, a4_h = A4
                margin = 50
                ratio = min((a4_w - 2*margin) / img_w, (a4_h - 2*margin) / img_h)
                new_w, new_h = img_w * ratio, img_h * ratio
                pos_x, pos_y = (a4_w - new_w) / 2, (a4_h - new_h) / 2
                
                c.drawImage(ImageReader(io_buf), pos_x, pos_y, width=new_w, height=new_h)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_document.pdf')

            # ================= 4. COMPRESS (UNTOUCHED) =================
            elif tool_type == 'compress':
                quality = max(5, min(100, int(request.form.get("quality", 60))))
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                _, buffer = cv2.imencode('.jpg', img, encode_param)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_compressed.jpg')

            # ================= 5. NEW: BG REMOVER =================
            elif tool_type == 'bg':
                bg_type = request.form.get('bg_type', 'transparent')
                
                # Use rembg to remove background (returns bytes of PNG with transparency)
                output_bytes = remove(file_bytes)
                
                if bg_type == 'transparent':
                    return send_file(io.BytesIO(output_bytes), mimetype='image/png', as_attachment=True, download_name='snapzo_nobg.png')
                
                # If color or custom image, composite the image using OpenCV
                fg = cv2.imdecode(np.frombuffer(output_bytes, np.uint8), cv2.IMREAD_UNCHANGED) # Load with Alpha channel
                
                # Extract alpha and RGB channels
                alpha = fg[:, :, 3] / 255.0
                fg_rgb = fg[:, :, :3]
                H, W = fg_rgb.shape[:2]
                
                bg_rgb = np.zeros_like(fg_rgb, dtype=np.uint8)
                
                if bg_type == 'color':
                    hex_color = request.form.get('bg_color', '#ffffff').lstrip('#')
                    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    bg_rgb[:] = [b, g, r] # OpenCV uses BGR
                    
                elif bg_type == 'custom_image':
                    custom_bg_file = request.files.get('custom_bg')
                    if custom_bg_file and custom_bg_file.filename != '':
                        custom_bg = cv2.imdecode(np.frombuffer(custom_bg_file.read(), np.uint8), cv2.IMREAD_COLOR)
                        bg_rgb = cv2.resize(custom_bg, (W, H))
                    else:
                        bg_rgb[:] = [255, 255, 255] # Default to white if no image uploaded
                
                # Alpha compositing math
                final_img = (fg_rgb * alpha[..., None] + bg_rgb * (1 - alpha[..., None])).astype(np.uint8)
                
                _, buffer = cv2.imencode('.jpg', final_img)
                return send_file(io.BytesIO(buffer), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_newbg.jpg')

        except Exception as e:
            return f"Server Error: {str(e)}", 500
            
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
