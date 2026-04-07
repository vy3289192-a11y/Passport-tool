from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro | Modern Editor</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --bg: #f8fafc; --sidebar: #ffffff; --card: #ffffff; --text: #1e293b;
            --accent: #3b82f6; --border: #e2e8f0; --hover: #eff6ff; --header: #ffffff;
        }
        body.dark-mode {
            --bg: #0f172a; --sidebar: #1e293b; --card: #1e293b; --text: #f1f5f9;
            --accent: #60a5fa; --border: #334155; --hover: #334155; --header: #111827;
        }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; flex-direction: column; transition: 0.3s; min-height: 100vh; }

        /* Mobile Header */
        .mobile-header { display: none; background: var(--header); padding: 15px 20px; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; align-items: center; justify-content: space-between; }
        .menu-toggle { font-size: 1.5rem; cursor: pointer; color: var(--text); }
        .mobile-logo { font-size: 1.3rem; font-weight: bold; color: var(--accent); }

        /* Sidebar */
        .sidebar { width: 260px; height: 100vh; background: var(--sidebar); border-right: 1px solid var(--border); position: fixed; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; z-index: 150; transition: transform 0.3s ease; }
        .logo { font-size: 1.5rem; font-weight: bold; margin-bottom: 40px; color: var(--accent); display: flex; align-items: center; gap: 10px; }
        .menu-item { padding: 12px 15px; border-radius: 8px; cursor: pointer; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; transition: 0.2s; font-weight: 500; color: var(--text); text-decoration: none; }
        .menu-item:hover, .menu-item.active { background: var(--hover); color: var(--accent); }
        .sidebar-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 140; }
        
        .theme-toggle-container { margin-top: auto; padding-top: 20px; border-top: 1px solid var(--border); }
        .theme-toggle { padding: 10px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); text-align: center; display: flex; align-items: center; justify-content: center; gap: 10px; }

        /* Main Content */
        .content { margin-left: 260px; flex: 1; padding: 40px; display: flex; justify-content: center; align-items: flex-start; margin-top: 0; }
        .tool-card { background: var(--card); padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.05); width: 100%; max-width: 500px; box-sizing: border-box; }

        /* Upload Area */
        .upload-box { border: 2px dashed var(--accent); border-radius: 15px; padding: 40px; text-align: center; cursor: pointer; transition: 0.3s; background: var(--hover); position: relative; overflow: hidden; min-height: 200px; display: flex; align-items: center; justify-content: center; }
        .upload-box:hover { border-color: var(--text); }
        .upload-box i { font-size: 3rem; color: var(--accent); margin-bottom: 15px; }
        #preview { max-width: 100%; max-height: 250px; object-fit: contain; border-radius: 10px; display: none; border: 3px solid var(--accent); }
        
        /* Forms & Buttons */
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.9rem; opacity: 0.8; }
        input[type="number"], select { width: 100%; padding: 12px 15px; border-radius: 10px; border: 1px solid var(--border); background: var(--card); color: var(--text); box-sizing: border-box; font-size: 1rem; }
        input[type="number"]:focus, select:focus { outline: none; border-color: var(--accent); ring: 2px var(--accent); }
        
        .btn-primary { width: 100%; padding: 16px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: bold; font-size: 1.1rem; cursor: pointer; transition: 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .btn-primary:hover { background: #2563eb; transform: translateY(-1px); }

        /* Mobile Responsiveness */
        @media (max-width: 768px) {
            .mobile-header { display: flex; }
            .sidebar { transform: translateX(-100%); height: 100%; }
            .sidebar.open { transform: translateX(0); }
            .sidebar-overlay.open { display: block; }
            .content { margin-left: 0; padding: 20px; }
            .tool-card { padding: 25px; border-radius: 15px; max-width: 100%; }
            .upload-box { padding: 30px; }
            .logo { margin-bottom: 30px; }
            .menu-item { padding: 15px; margin-bottom: 10px; font-size: 1.1rem; }
        }
    </style>
</head>
<body class="dark-mode"> <div class="mobile-header">
        <div class="mobile-logo"><i class="fas fa-camera-retro"></i> Snapzo Pro</div>
        <div class="menu-toggle" onclick="toggleSidebar()"><i class="fas fa-bars"></i></div>
    </div>

    <div class="sidebar-overlay" id="overlay" onclick="toggleSidebar()"></div>

    <div class="sidebar" id="sidebar">
        <div class="logo"><i class="fas fa-camera-retro"></i> <span>Snapzo Pro</span></div>
        
        <a href="#" class="menu-item active"><i class="fas fa-id-badge"></i> <span>Passport Maker</span></a>
        <a href="#" class="menu-item" onclick="alert('Coming Soon!')"><i class="fas fa-magic"></i> <span>Remove BG</span></a>
        <a href="#" class="menu-item"><i class="fas fa-home"></i> <span>Home</span></a>
        
        <div class="theme-toggle-container">
            <div class="theme-toggle" onclick="toggleTheme()">
                <i class="fas fa-sun" id="theme-icon"></i> <span id="theme-text">Light Mode</span>
            </div>
        </div>
    </div>

    <div class="content">
        <div class="tool-card">
            <h2 style="margin-top:0; font-size: 1.7rem;">Create Passport Photos</h2>
            <p style="opacity: 0.7; margin-bottom: 30px; font-size: 0.95rem;">Upload any image. We'll auto-crop and generate a professional grid.</p>

            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <div class="upload-box" id="drop-area">
                        <input type="file" name="file" id="fileInput" accept="image/*" hidden required>
                        <div id="upload-prompt">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <p style="margin: 5px 0 0;">Drag & Drop or <b style="color:var(--accent)">Browse</b></p>
                            <p style="font-size: 0.8rem; opacity: 0.6; margin-top: 5px;">Supports: JPG, PNG</p>
                        </div>
                        <img id="preview">
                    </div>
                </div>

                <div style="display: flex; gap: 15px;">
                    <div class="form-group" style="flex: 1;">
                        <label>Photos Count (1-12)</label>
                        <input type="number" name="count" value="8" min="1" max="12">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <label>Output Format</label>
                        <select name="type">
                            <option value="jpg">JPG Image</option>
                            <option value="pdf">PDF File</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="btn-primary">
                    <i class="fas fa-download"></i> Generate & Download
                </button>
            </form>
        </div>
    </div>

    <script>
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        const dropArea = document.getElementById('drop-area');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');
        const prompt = document.getElementById('upload-prompt');

        // Mobile Sidebar Toggle
        function toggleSidebar() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }

        // Theme Toggle Logic
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            
            // Setting for initial dark mode based on screenshots
            if(!isDark) {
                document.body.classList.remove('dark-mode');
                document.getElementById('theme-icon').className = 'fas fa-moon';
                document.getElementById('theme-text').innerText = 'Dark Mode';
            } else {
                document.body.classList.add('dark-mode');
                document.getElementById('theme-icon').className = 'fas fa-sun';
                document.getElementById('theme-text').innerText = 'Light Mode';
            }
        }
        
        // Ensure UI matches default dark mode state on load
        window.onload = function() {
            const isDark = document.body.classList.contains('dark-mode');
            document.getElementById('theme-icon').className = isDark ? 'fas fa-sun' : 'fas fa-moon';
            document.getElementById('theme-text').innerText = isDark ? 'Light Mode' : 'Dark Mode';
        }

        // Drag and Drop JavaScript Logic
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }, false);
        });

        // Add visual feedback on drag
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.style.borderColor = 'var(--text)', false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.style.borderColor = 'var(--accent)', false);
        });

        dropArea.onclick = () => fileInput.click();

        dropArea.addEventListener('drop', e => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if(files.length > 0) {
                fileInput.files = files; // Sync files to hidden input
                handleFiles(files[0]);
            }
        });

        fileInput.addEventListener('change', e => {
            if(e.target.files.length > 0) {
                handleFiles(e.target.files[0]);
            }
        });

        function handleFiles(file) {
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onloadend = function() {
                    preview.src = reader.result;
                    preview.style.display = 'block';
                    prompt.style.display = 'none';
                    dropArea.style.padding = '10px'; // Reduce padding when image is present
                }
            } else {
                alert("Please upload a valid image file.");
            }
        }
    </script>
</body>
</html>
'''

# Helper function for Auto-Cropping to Passport Ratio
def auto_crop_to_passport_ratio(img):
    h, w = img.shape[:2]
    
    # Target Passport Aspect Ratio (Width:Height ≈ 3.5:4.5 ≈ 0.777)
    target_ratio = 413 / 531  # Using your target pixel dimensions ratio
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        # Image is too wide (landscape), crop width from center
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        cropped_img = img[:, offset:offset+new_w]
    elif current_ratio < target_ratio:
        # Image is too tall (portrait), crop height from center (keeping top part mostly)
        new_h = int(w / target_ratio)
        # Shift crop slightly upwards for faces (15% from top instead of pure center)
        offset = int((h - new_h) * 0.15) 
        cropped_img = img[offset:offset+new_h, :]
    else:
        # Ratio is already perfect
        cropped_img = img
        
    return cropped_img

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file or file.filename == '':
                return "Error: No file selected", 400

            # Memory mein image load karna
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if img is None:
                return "Error: Invalid Image format", 400

            # 1. NEW: Auto-Crop to Passport Aspect Ratio first
            cropped_face = auto_crop_to_passport_ratio(img)

            # 2. Resize the cropped face to final dimensions (Safe from distortion now)
            final_face = cv2.resize(cropped_face, (413, 531))
            
            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")

            # 3. Add Border (Grayish professional border)
            bordered = cv2.copyMakeBorder(final_face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[225, 225, 225])
            bh, bw = bordered.shape[:2] # Dynamic (approx 437x555)

            # 4. Create Canvas (Larger to avoid overflow)
            canvas_img = np.ones((2200, 1600, 3), dtype=np.uint8) * 255

            # Simple grid logic: 3 photos per row
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                # Adjust spacing based on dynamic bordered size
                y_start = r * (bh + 50) + 80
                x_start = c * (bw + 40) + 80
                
                # Double check safety against canvas bounds
                if y_start + bh < canvas_img.shape[0] and x_start + bw < canvas_img.shape[1]:
                    canvas_img[y_start : y_start + bh, x_start : x_start + bw] = bordered

            # 5. Return result
            if filetype == "jpg":
                success, encoded_img = cv2.imencode('.jpg', canvas_img)
                if not success: return "Error: Image encoding failed", 500
                return send_file(io.BytesIO(encoded_img.tobytes()), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_passport_grid.jpg')

            # PDF Return
            else:
                pdf_io = io.BytesIO()
                c_pdf = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                success, encoded_img = cv2.imencode('.jpg', canvas_img)
                img_reader = ImageReader(io.BytesIO(encoded_img.tobytes()))
                # Position image on A4 page nicely
                c_pdf.drawImage(img_reader, 45, 120, width=505, height=660)
                c_pdf.showPage()
                c_pdf.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_passport_sheet.pdf')

        except Exception as e:
            return f"Server Error during processing: {str(e)}", 500

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()
