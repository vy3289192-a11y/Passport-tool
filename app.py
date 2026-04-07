from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# Simple Modern UI
HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snapzo Pro</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 350px; text-align: center; }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: none; box-sizing: border-box; }
        button { background: #3b82f6; color: white; font-weight: bold; cursor: pointer; }
        button:hover { background: #2563eb; }
        #preview { width: 100px; height: 120px; object-fit: cover; display: none; margin: 10px auto; border: 2px solid #3b82f6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📸 Snapzo Pro</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required onchange="const img=document.getElementById('preview'); img.src=URL.createObjectURL(this.files[0]); img.style.display='block';">
            <img id="preview">
            <input type="number" name="count" value="8" min="1" max="12" placeholder="Photos Count">
            <select name="type">
                <option value="jpg">Download as JPG</option>
                <option value="pdf">Download as PDF</option>
            </select>
            <button type="submit">Download Now</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file: return "Error: No file selected", 400

            # Memory mein image load karna
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if img is None: return "Error: Could not decode image", 400

            count = int(request.form.get("count", 8))
            filetype = request.form.get("type")

            # Passport Photo Resize
            face = cv2.resize(img, (413, 531))
            canvas_img = np.ones((1600, 1300, 3), dtype=np.uint8) * 255

            # Simple grid logic
            for i in range(min(count, 12)):
                r, c = i // 3, i % 3
                y, x = r * 580 + 50, c * 430 + 30
                bordered = cv2.copyMakeBorder(face, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[200, 200, 200])
                h, w = bordered.shape[:2]
                canvas_img[y:y+h, x:x+w] = bordered

            # JPG Return
            if filetype == "jpg":
                success, encoded_img = cv2.imencode('.jpg', canvas_img)
                if not success: return "Error: Encoding failed", 500
                return send_file(io.BytesIO(encoded_img.tobytes()), mimetype='image/jpeg', as_attachment=True, download_name='snapzo_passport.jpg')

            # PDF Return
            else:
                pdf_io = io.BytesIO()
                c = pdf_canvas.Canvas(pdf_io, pagesize=A4)
                success, encoded_img = cv2.imencode('.jpg', canvas_img)
                img_reader = ImageReader(io.BytesIO(encoded_img.tobytes()))
                c.drawImage(img_reader, 50, 150, width=500, height=600)
                c.showPage()
                c.save()
                pdf_io.seek(0)
                return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='snapzo_photos.pdf')

        except Exception as e:
            # Ye line Render logs mein asli error dikhayegi
            return f"Server Error: {str(e)}", 500

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run()
