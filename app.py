from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# Modern Responsive UI
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --accent: #3b82f6; --text: #f1f5f9; }
        body { margin: 0; font-family: sans-serif; background: var(--bg); color: var(--text); }
        .nav { background: #111827; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .main { padding: 20px; display: flex; justify-content: center; }
        .card { background: var(--card); padding: 30px; border-radius: 15px; width: 100%; max-width: 450px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .upload { border: 2px dashed var(--accent); padding: 30px; border-radius: 10px; cursor: pointer; text-align: center; background: rgba(59,130,246,0.05); }
        #preview { max-width: 100px; display: none; margin: 15px auto; border-radius: 5px; border: 2px solid var(--accent); }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; box-sizing: border-box; }
        button { background: var(--accent); color: white; font-weight: bold; cursor: pointer; }
        @media (max-width: 600px) { .card { padding: 20px; } }
    </style>
</head>
<body>
    <div class="nav">
        <div style="font-weight:bold; font-size:1.2rem;"><i class="fas fa-camera-retro"></i> Snapzo Pro</div>
        <i class="fas fa-bars" onclick="alert('Menu features coming soon!')" style="cursor:pointer"></i>
    </div>
    <div class="main">
        <div class="card">
            <h2 style="margin-top:0">Passport Maker</h2>
            <form method="POST" enctype="multipart/form-data">
                <div class="upload" onclick="document.getElementById('fileInput').click()">
                    <input type="file" name="file" id="fileInput" hidden required onchange="showPreview(this)">
                    <div id="msg"><i class="fas fa-upload" style="font-size:2rem"></i><p>Click or Drag Image</p></div>
                    <img id="preview">
                </div>
                <div style="display:flex; gap:10px; margin-top:10px">
                    <div style="flex:1"><label>Count</label><input type="number" name="count" value="8" min="1" max="12"></div>
                    <div style="flex:1"><label>Format</label><select name="type"><option value="jpg">JPG</option><option value="pdf">PDF</option></select></div>
                </div>
                <button type="submit">Download Photos</button>
            </form>
        </div>
    </div>
    <script>
        function showPreview(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('preview').src = e.target.result;
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('msg').style.display = 'none';
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
    </script>
</body>
</html>
'''

def auto_crop_passport(img):
    h, w = img.shape[:2]
    target_ratio = 413 / 531
    if (w / h) > target_ratio:
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        return img[:, offset:offset+new_w]
    else:
        new_h = int(w / target_ratio)
        offset = int((h - new_h) * 0.1) # Face area safety
        return img[offset:offset+new_h, :]

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file: return "File missing", 400
            
            # Read Image
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            
            # Crop & Resize
            cropped = auto_crop_passport(img)
            face = cv2.resize(cropped, (413, 531))
            
            # Border
            bordered = cv2.copyMakeBorder(face, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[225, 225, 225])
            bh, bw = bordered.shape[:2] # Dynamic size (bh=555, bw=437)

            # Canvas (Extra big for safety)
            canvas = np.ones((2000, 1500, 3), dtype=np.uint8) * 255
            count = int(request.form.get("count", 8))
            
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                # Dynamic Slice Placement (Ab error nahi aayega)
                y_pos = r * (bh + 40) + 60
                x_pos = c * (bw + 20) + 60
                canvas[y_pos : y_pos + bh, x_pos : x_pos + bw] = bordered

            # Output
            _, buffer = cv2.imencode('.jpg', canvas)
            final_io = io.BytesIO(buffer)

            if request.form.get("type") == "pdf":
                pdf_io = io.BytesIO()
                c_pdf = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                c_pdf.drawImage(ImageReader(final_io), 50, 100, width=500, height=650)
                c_pdf.showPage()
                c_pdf.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='photos.pdf')
            
            final_io.seek(0)
            return send_file(final_io, mimetype='image/jpeg', as_attachment=True, download_name='photos.jpg')

        except Exception as e:
            return f"Error: {str(e)}", 500
            
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
