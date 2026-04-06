from flask import Flask, request, render_template_string, send_file
import cv2
import os
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
from reportlab.lib.pagesizes import A4

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>Passport Tool</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body {
    background: linear-gradient(135deg,#667eea,#764ba2);
    margin:0;
    font-family:Arial;
    color:white;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}

.container {
    width:90%;
    max-width:400px;
    background: rgba(255,255,255,0.1);
    padding:20px;
    border-radius:15px;
    box-shadow:0 5px 15px rgba(0,0,0,0.3);
    text-align:center;
}

h1 {
    font-size:22px;
    margin-bottom:5px;
}

h2 {
    font-size:16px;
    margin-bottom:15px;
}

input, select {
    padding:12px;
    margin:8px 0;
    width:100%;
    border:none;
    border-radius:8px;
    font-size:14px;
}

button {
    padding:12px;
    width:100%;
    background:#ff758c;
    border:none;
    border-radius:10px;
    color:white;
    font-size:16px;
    margin-top:10px;
    cursor:pointer;
}

button:hover {
    background:#ff5c7a;
}

@media (max-width:500px) {
    h1 { font-size:20px; }
    h2 { font-size:14px; }
}
</style>
</head>

<body>

<div class="container">

<h1>Make Passport Size Photo</h1>
<h2>🔥 Passport Tool</h2>

<form method="POST" enctype="multipart/form-data">

<input type="file" name="file" required>

<label>Photos (1–99)</label>
<input type="number" name="count" min="1" max="99" value="8">

<label>Download Type</label>
<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select>

<button type="submit">Generate</button>

</form>

</div>

</body>
</html>
'''

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'POST':
        file = request.files['file']
        count = int(request.form.get("count"))
        filetype = request.form.get("type")

        file.save("input.jpg")
        img = cv2.imread("input.jpg")

        h, w, _ = img.shape
        ratio = 7/9

        crop_w = w
        crop_h = int(w / ratio)

        if crop_h > h:
            crop_h = h
            crop_w = int(h * ratio)

        x = (w - crop_w)//2
        y = (h - crop_h)//2

        face = img[y:y+crop_h, x:x+crop_w]
        face = cv2.resize(face, (413, 531))

        gap = 40
        border = 5

        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))

        cell_w = 413 + gap
        cell_h = 531 + gap

        canvas_w = cols * cell_w + gap
        canvas_h = rows * cell_h + gap

        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

        i = 0
        for r in range(rows):
            for c in range(cols):
                if i >= count:
                    break

                x_pos = gap + c * cell_w
                y_pos = gap + r * cell_h

                bordered = cv2.copyMakeBorder(
                    face, border, border, border, border,
                    cv2.BORDER_CONSTANT, value=[0,0,0]
                )

                h_b, w_b = bordered.shape[:2]
                canvas[y_pos:y_pos+h_b, x_pos:x_pos+w_b] = bordered

                i += 1

        os.makedirs("static", exist_ok=True)
        img_path = "static/output.jpg"
        cv2.imwrite(img_path, canvas)

        if filetype == "pdf":
            pdf_path = "static/output.pdf"
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            elements = [RLImage(img_path, width=500, height=700)]
            doc.build(elements)
            return send_file(pdf_path, as_attachment=True)

        return send_file(img_path, as_attachment=True)

    return render_template_string(HTML)


@app.route('/download')
def download():
    return send_file("static/output.jpg", as_attachment=True)


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
