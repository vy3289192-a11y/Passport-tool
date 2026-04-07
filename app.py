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
            --accent: #3b82f6; --border: #e2e8f0; --hover: #eff6ff;
        }
        body.dark-mode {
            --bg: #0f172a; --sidebar: #1e293b; --card: #1e293b; --text: #f1f5f9;
            --accent: #60a5fa; --border: #334155; --hover: #334155;
        }

        body { margin: 0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); display: flex; transition: 0.3s; }

        /* Sidebar */
        .sidebar { width: 250px; height: 100vh; background: var(--sidebar); border-right: 1px solid var(--border); position: fixed; padding: 20px; box-sizing: border-box; display: flex; flex-direction: column; }
        .logo { font-size: 1.5rem; font-weight: bold; margin-bottom: 40px; color: var(--accent); display: flex; align-items: center; gap: 10px; }
        .menu-item { padding: 12px 15px; border-radius: 8px; cursor: pointer; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; transition: 0.2s; font-weight: 500; }
        .menu-item:hover, .menu-item.active { background: var(--hover); color: var(--accent); }
        .theme-toggle { margin-top: auto; padding: 10px; border-radius: 8px; cursor: pointer; border: 1px solid var(--border); text-align: center; }

        /* Main Content */
        .content { margin-left: 250px; flex: 1; padding: 40px; display: flex; justify-content: center; }
        .tool-card { background: var(--card); padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.05); width: 100%; max-width: 500px; }

        /* Drag and Drop */
        .upload-box { border: 2px dashed var(--accent); border-radius: 15px; padding: 40px; text-align: center; cursor: pointer; transition: 0.3s; background: var(--hover); position: relative; }
        .upload-box:hover { background: transparent; }
        .upload-box i { font-size: 3rem; color: var(--accent); margin-bottom: 15px; }
        #preview { width: 150px; height: 180px; object-fit: cover; border-radius: 10px; display: none; margin: 20px auto; border: 3px solid var(--accent); }

        /* Form Elements */
        input[type="number"], select { width: 100%; padding: 12px; margin: 15px 0; border-radius: 10px; border: 1px solid var(--border); background: var(--bg); color: var(--text); box-sizing: border-box; font-size: 1rem; }
        button.btn-primary { width: 100%; padding: 15px; background: var(--accent); color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 1.1rem; cursor: pointer; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3); transition: 0.3s; }
        button.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4); }

        @media (max-width: 768px) {
            .sidebar { width: 70px; padding: 15px 5px; }
            .menu-item span, .logo span { display: none; }
            .content { margin-left: 70px; padding: 20px; }
        }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="logo"><i class="fas fa-camera-retro"></i> <span>Snapzo Pro</span></div>
        <div class="menu-item active" onclick="switchTool('passport')"><i class="fas fa-id-badge"></i> <span>Passport Maker</span></div>
        <div class="menu-item" onclick="alert('Coming Soon: AI Background Remover')"><i class="fas fa-magic"></i> <span>Remove BG</span></div>
        <div class="menu-item" onclick="location.reload()"><i class="fas fa-home"></i> <span>Home</span></div>
        
        <div class="theme-toggle" onclick="toggleTheme()">
            <i class="fas fa-moon" id="theme-icon"></i> <span id="theme-text">Dark Mode</span>
        </div>
    </div>

    <div class="content">
        <div class="tool-card" id="tool-passport">
            <h2 style="margin-top:0">Create Passport Photos</h2>
            <p style="opacity: 0.7; margin-bottom: 30px;">Upload image to generate professional grid</p>

            <form method="POST" enctype="multipart/form-data">
                <div class="upload-box" id="drop-area">
                    <input type="file" name="file" id="fileInput" accept="image/*" hidden required>
                    <div id="upload-prompt">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>Drag & Drop or <b>Browse</b></p>
                    </div>
                    <img id="preview">
                </div>

                <div style="display: flex; gap: 15px; margin-top: 10px;">
                    <div style="flex: 1;">
                        <label style="font-size: 0.8rem;">Count (1-12)</label>
                        <input type="number" name="count" value="8" min="1" max="12">
                    </div>
                    <div style="flex: 1;">
                        <label style="font-size: 0.8rem;">Format</label>
                        <select name="type">
                            <option value="jpg">JPG Image</option>
                            <option value="pdf">PDF File</option>
                        </select>
                    </div>
                </div>

                <button type="submit" class="btn-primary">Generate & Download</button>
            </form>
        </div>
    </div>

    <script>
        const dropArea = document.getElementById('drop-area');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');
        const prompt = document.getElementById('upload-prompt');

        // Theme Toggle Logic
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            document.getElementById('theme-icon').className = isDark ? 'fas fa-sun' : 'fas fa-moon';
            document.getElementById('theme-text').innerText = isDark ? 'Light Mode' : 'Dark Mode';
        }

        // Drag and Drop Logic
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }, false);
        });

        dropArea.onclick = () => fileInput.click();

        dropArea.addEventListener('drop', e => {
            const dt = e.dataTransfer;
            fileInput.files = dt.files;
            handleFiles(dt.files[0]);
        });

        fileInput.addEventListener('change', e => handleFiles(e.target.files[0]));

        function handleFiles(file) {
            if (file) {
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'block';
                prompt.style.display = 'none';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file: return "No file selected", 400

            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None: return "Invalid Image", 400

            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")

            # Core Logic (Safe from shape mismatch)
            face = cv2.resize(img, (413, 531))
            bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[220, 220, 220])
            bh, bw = bordered.shape[:2]

            canvas_img = np.ones((2000, 1500, 3), dtype=np.uint8) * 255

            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                y_start = r * (bh + 40) + 60
                x_start = c * (bw + 30) + 60
                canvas_img[y_start : y_start + bh, x_start : x_start + bw] = bordered

            if filetype == "jpg":
                _, encoded_img = cv2.imencode('.jpg', canvas_img)
                return send_file(io.BytesIO(encoded_img.tobytes()), mimetype='image/jpeg', as_attachment=True, download_name='passport_snapzo.jpg')
            else:
                pdf_io = io.BytesIO()
                c_pdf = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                _, encoded_img = cv2.imencode('.jpg', canvas_img)
                img_reader = ImageReader(io.BytesIO(encoded_img.tobytes()))
                c_pdf.drawImage(img_reader, 40, 100, width=520, height=680)
                c_pdf.showPage()
                c_pdf.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport_snapzo.pdf')

        except Exception as e:
            return f"Processing Error: {str(e)}", 500

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()
