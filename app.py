from flask import Flask, request, render_template_string, send_file
import cv2
import numpy as np
import io
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import json

app = Flask(__name__)

# 🔒 SECURITY FIX
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
ALLOWED_EXT = ('.png', '.jpg', '.jpeg', '.webp')

def is_valid(filename):
    return filename.lower().endswith(ALLOWED_EXT)

LOGO_URL = "https://i.ibb.co/Q73xvDmw/46658.jpg"

# ---------------- HTML ----------------

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{{ page_title }}</title>
<meta name="description" content="{{ page_desc }}">

<link rel="icon" href="''' + LOGO_URL + '''">

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

<style>
body { font-family: Arial; background:#f8fafc; margin:0; }
.nav { padding:15px; background:#2563eb; color:white; }
.container { padding:30px; text-align:center; }

.card {
    background:white;
    padding:25px;
    border-radius:15px;
    max-width:400px;
    margin:auto;
    box-shadow:0 10px 30px rgba(0,0,0,0.1);
}

.btn {
    padding:12px;
    width:100%;
    background:#2563eb;
    color:white;
    border:none;
    border-radius:10px;
    cursor:pointer;
}

.upload {
    border:2px dashed #2563eb;
    padding:20px;
    margin-bottom:15px;
    cursor:pointer;
}
</style>
</head>

<body>

<div class="nav">
    Snapzo Pro
</div>

<div class="container">

<div class="card">
<h2>Upload Image</h2>

<form method="POST" enctype="multipart/form-data">
<input type="hidden" name="tool_type" value="passport">

<div class="upload" onclick="document.getElementById('f').click()">
    Select Image
    <input type="file" id="f" name="file" hidden required>
</div>

<button class="btn">Generate</button>

</form>
</div>

</div>

</body>
</html>
'''

# ---------------- UTIL ----------------

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

# ---------------- ROUTE ----------------

@app.route('/', methods=['GET','POST'])
def home():

    if request.method == 'POST':
        try:
            tool_type = request.form.get('tool_type')
            file = request.files.get('file')

            # 🔒 VALIDATION FIX
            if not file or not is_valid(file.filename):
                return "Invalid file", 400

            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

            if tool_type == 'passport':
                face = cv2.resize(strict_passport_crop(img), (413, 531))

                _, buf = cv2.imencode('.jpg', face)

                return send_file(io.BytesIO(buf),
                                 mimetype='image/jpeg',
                                 as_attachment=True,
                                 download_name='passport.jpg')

        except Exception as e:
            print("ERROR:", e)
            return "Something went wrong", 500

    return render_template_string(HTML,
                                  page_title="Snapzo Pro",
                                  page_desc="Tool")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
  # ---------------- MORE TOOL LOGIC ----------------

def process_id_card(front_file, back_file):
    if not (is_valid(front_file.filename) and is_valid(back_file.filename)):
        return None

    img_f = cv2.imdecode(np.frombuffer(front_file.read(), np.uint8), cv2.IMREAD_COLOR)
    img_b = cv2.imdecode(np.frombuffer(back_file.read(), np.uint8), cv2.IMREAD_COLOR)

    pdf_io = io.BytesIO()
    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)

    _, buf_f = cv2.imencode('.jpg', img_f)
    _, buf_b = cv2.imencode('.jpg', img_b)

    c.drawImage(ImageReader(io.BytesIO(buf_f)), 150, 500, width=300, height=190)
    c.drawImage(ImageReader(io.BytesIO(buf_b)), 150, 290, width=300, height=190)

    c.showPage()
    c.save()
    pdf_io.seek(0)

    return pdf_io


def process_signature(file):
    if not is_valid(file.filename):
        return None

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    coords = cv2.findNonZero(255 - thresh)
    x, y, w, h = cv2.boundingRect(coords)

    cropped = thresh[y:y+h, x:x+w]
    cropped = cv2.copyMakeBorder(cropped, 20,20,20,20,
                                cv2.BORDER_CONSTANT, value=[255,255,255])

    _, buf = cv2.imencode('.png', cropped)

    return buf


def process_joiner(photo_file, sign_file):
    if not (is_valid(photo_file.filename) and is_valid(sign_file.filename)):
        return None

    img_p = cv2.imdecode(np.frombuffer(photo_file.read(), np.uint8), cv2.IMREAD_COLOR)
    img_s = cv2.imdecode(np.frombuffer(sign_file.read(), np.uint8), cv2.IMREAD_COLOR)

    face = cv2.resize(strict_passport_crop(img_p), (413, 531))
    sign = cv2.resize(img_s, (413, 150))

    merged = np.vstack((face, sign))

    _, buf = cv2.imencode('.jpg', merged)

    return buf


def process_pdf(files, magic=False):
    pdf_io = io.BytesIO()
    c = pdf_canvas.Canvas(pdf_io, pagesize=A4)

    for f in files:
        if not is_valid(f.filename):
            continue

        img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)

        if img is None:
            continue

        if magic:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, img = cv2.threshold(gray, 0, 255,
                                   cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        h, w = img.shape[:2]
        ratio = w / h
        new_w = 500
        new_h = int(new_w / ratio)

        _, buf = cv2.imencode('.jpg', img)

        c.drawImage(ImageReader(io.BytesIO(buf)),
                    50, 100, width=new_w, height=new_h)

        c.showPage()

    c.save()
    pdf_io.seek(0)

    return pdf_io


# ---------------- UPDATE MAIN ROUTE ----------------

# ADD inside your home() POST section:

elif tool_type == 'idcard':
    front = request.files.get('front')
    back = request.files.get('back')

    pdf = process_id_card(front, back)
    if pdf:
        return send_file(pdf,
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name='id_card.pdf')


elif tool_type == 'sign':
    file = request.files.get('file')

    buf = process_signature(file)
    if buf is not None:
        return send_file(io.BytesIO(buf),
                         mimetype='image/png',
                         as_attachment=True,
                         download_name='sign.png')


elif tool_type == 'joiner':
    photo = request.files.get('photo')
    sign = request.files.get('sign')

    buf = process_joiner(photo, sign)
    if buf is not None:
        return send_file(io.BytesIO(buf),
                         mimetype='image/jpeg',
                         as_attachment=True,
                         download_name='merged.jpg')


elif tool_type == 'pdf':
    files = request.files.getlist('file')
    magic = request.form.get('magic_scan') == 'yes'

    pdf = process_pdf(files, magic)
    return send_file(pdf,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name='output.pdf')
  # ---------------- REMAINING TOOLS ----------------

def process_crop(img, x, y, w, h):
    cropped = img[y:y+h, x:x+w]
    _, buffer = cv2.imencode('.jpg', cropped)
    return buffer


def process_compress(img, target_kb):
    target_bytes = target_kb * 1024

    quality = 90
    attempts = 0

    while attempts < 10:
        _, buffer = cv2.imencode('.jpg', img,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality])

        if len(buffer) <= target_bytes:
            return buffer

        quality -= 5
        attempts += 1

    # fallback resize
    scale = 0.9
    attempts = 0

    while attempts < 10:
        new_w = int(img.shape[1] * scale)
        new_h = int(img.shape[0] * scale)

        resized = cv2.resize(img, (new_w, new_h))

        _, buffer = cv2.imencode('.jpg', resized,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality])

        if len(buffer) <= target_bytes:
            return buffer

        scale -= 0.1
        attempts += 1

    return buffer


def process_social(img, platform):
    if platform == 'yt':
        dim = (1280, 720)
    elif platform == 'insta':
        dim = (1080, 1080)
    else:
        dim = (820, 312)

    res = cv2.resize(img, dim)
    _, buffer = cv2.imencode('.jpg', res)

    return buffer


def process_format(img, fmt):
    _, buffer = cv2.imencode(f'.{fmt}', img)
    return buffer


# ---------------- ADD IN MAIN ROUTE ----------------

# ADD inside POST section after previous parts:

elif tool_type == 'crop':
    file = request.files.get('file')

    if not file or not is_valid(file.filename):
        return "Invalid file", 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    x = int(request.form.get('x'))
    y = int(request.form.get('y'))
    w = int(request.form.get('width'))
    h = int(request.form.get('height'))

    buffer = process_crop(img, x, y, w, h)

    return send_file(io.BytesIO(buffer),
                     mimetype='image/jpeg',
                     as_attachment=True,
                     download_name='cropped.jpg')


elif tool_type == 'compress':
    file = request.files.get('file')

    if not file or not is_valid(file.filename):
        return "Invalid file", 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    target_kb = int(request.form.get('target_kb', 50))

    buffer = process_compress(img, target_kb)

    return send_file(io.BytesIO(buffer),
                     mimetype='image/jpeg',
                     as_attachment=True,
                     download_name='compressed.jpg')


elif tool_type == 'social':
    file = request.files.get('file')

    if not file or not is_valid(file.filename):
        return "Invalid file", 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    platform = request.form.get('platform', 'yt')

    buffer = process_social(img, platform)

    return send_file(io.BytesIO(buffer),
                     mimetype='image/jpeg',
                     as_attachment=True,
                     download_name='social.jpg')


elif tool_type == 'format':
    file = request.files.get('file')

    if not file or not is_valid(file.filename):
        return "Invalid file", 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    fmt = request.form.get('out_format', 'png')

    buffer = process_format(img, fmt)

    mime = f'image/{fmt}' if fmt != 'jpg' else 'image/jpeg'

    return send_file(io.BytesIO(buffer),
                     mimetype=mime,
                     as_attachment=True,
                     download_name=f'converted.{fmt}')
