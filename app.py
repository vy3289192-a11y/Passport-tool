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
<style>
body {
    background: linear-gradient(135deg,#667eea,#764ba2);
    text-align:center;
    font-family:Arial;
    color:white;
}
input, select {
    padding:10px;
    margin:8px;
    width:250px;
}
button {
    padding:12px;
    background:#ff758c;
    border:none;
    border-radius:10px;
    color:white;
}
</style>
</head>
<body>

<h2>🔥 Passport Tool</h2>

<form method="POST" enctype="multipart/form-data">

<input type="file" name="file" required><br>

<label>Photos (1–99)</label><br>
<input type="number" name="count" min="1" max="99" value="8"><br>

<label>Download Type</label><br>
<select name="type">
<option value="jpg">JPG</option>
<option value="pdf">PDF</option>
</select><br>

<button type="submit">Generate</button>

</form>

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

        # GRID SETTINGS
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