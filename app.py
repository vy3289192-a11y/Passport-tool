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
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro</title>
    <style>
        :root { --bg:#0f172a; --card:#1e293b; --text:#f1f5f9; --accent:#3b82f6; }
        body { margin:0; font-family:sans-serif; background:var(--bg); color:var(--text); text-align:center; }
        .navbar { padding:15px; background:#111827; font-weight:bold; font-size:1.2rem; }
        .card { background:var(--card); max-width:400px; margin:40px auto; padding:30px; border-radius:15px; box-shadow:0 10px 20px rgba(0,0,0,0.3); }
        input, select { width:100%; padding:10px; margin:10px 0; border-radius:8px; border:none; }
        button { width:100%; padding:12px; background:var(--accent); color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; }
        #preview { width:100px; display:none; margin:10px auto; border:2px solid var(--accent); }
    </style>
</head>
<body>
    <div class="navbar">📸 Snapzo Pro</div>
    <div class="card">
        <h2>Passport Photo Maker</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required onchange="document.getElementById('preview').src=URL.createObjectURL(this.files[0]);document.getElementById('preview').style.display='block'">
            <img id="preview">
            <label>Photos Count (1-12):</label>
            <input type="number" name="count" value="8" min="1" max="12">
            <label>Format:</label>
            <select name="type"><option value="jpg">JPG Image</option><option value="pdf">PDF Document</option></select>
            <button type="submit">Download Now</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file: return "No file uploaded"

        # Image ko memory mein read karna (File save nahi hogi)
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if img is None: return "Invalid Image"

        count = int(request.form.get("count", 8))
        filetype = request.form.get("type")

        # Passport size resize
        face = cv2.resize(img, (413, 531))
        # White Canvas (A4 Size Sheet)
        canvas_img = np.ones((1600, 1300, 3), dtype=np.uint8) * 255

        i = 0
        for r in range(4):
            for c in range(3):
                if i >= count: break
                y, x = r * 580 + 50, c * 430 + 30
                # Border
                bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[200, 200, 200])
                canvas_img[y:y+bordered.shape[0], x:x+bordered.shape[1]] = bordered
                i += 1

        # Response ko memory mein handle karna
        if filetype == "pdf":
            pdf_io = io.BytesIO()
            c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
            # Image ko temp save kiye bina PDF mein convert karna
            _, img_encoded = cv2.imencode('.jpg', canvas_img)
            img_reader = ImageReader(io.BytesIO(img_encoded.tobytes()))
            c.drawImage(img_reader, 50, 150, width=500, height=600)
            c.showPage()
            c.save()
            pdf_io.seek(0)
            return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='passport_photos.pdf')
        else:
            _, img_encoded = cv2.imencode('.jpg', canvas_img)
            return send_file(io.BytesIO(img_encoded.tobytes()), mimetype='image/jpeg', as_attachment=True, download_name='passport_photos.jpg')

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=False)
