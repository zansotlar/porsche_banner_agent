"""
Porsche Banner Agent
Spletni vmesnik za samodejno posodabljanje "small print" besedila
(veljavnost akcije) na Meta banner kreativah.

Zagon:
    pip install -r requirements.txt
    python3 app.py
Nato odpri http://localhost:5000
"""
import os
import uuid
import shutil
import zipfile
from flask import Flask, request, render_template, send_file, jsonify

from fixer.fix_smallprint import fix_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
ALLOWED_EXT = {".png", ".jpg", ".jpeg"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    old_date = request.form.get("old_date", "30.9.2026").strip()
    new_date = request.form.get("new_date", "31.12.2026").strip()
    files = request.files.getlist("images")

    if not files:
        return jsonify({"error": "Ni naloženih slik."}), 400

    job_id = uuid.uuid4().hex[:10]
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    job_output_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)
    os.makedirs(job_output_dir, exist_ok=True)

    results = []
    for f in files:
        filename = f.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXT:
            results.append({"filename": filename, "ok": False, "message": "Nepodprt format datoteke."})
            continue

        in_path = os.path.join(job_upload_dir, filename)
        f.save(in_path)
        out_path = os.path.join(job_output_dir, filename)

        try:
            ok, msg = fix_image(in_path, out_path, old_date, new_date)
        except Exception as e:
            ok, msg = False, f"Napaka: {e}"

        if not ok:
            shutil.copy(in_path, out_path)

        results.append({"filename": filename, "ok": ok, "message": msg})

    zip_path = os.path.join(OUTPUT_DIR, f"{job_id}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(job_output_dir):
            zf.write(os.path.join(job_output_dir, fname), arcname=fname)

    return jsonify({"job_id": job_id, "results": results})


@app.route("/api/download/<job_id>")
def download(job_id):
    zip_path = os.path.join(OUTPUT_DIR, f"{job_id}.zip")
    if not os.path.isfile(zip_path):
        return "Paket ni najden ali je potekel.", 404
    return send_file(zip_path, as_attachment=True, download_name="popravljeni_bannerji.zip")


@app.route("/api/preview/<job_id>/<path:filename>")
def preview(job_id, filename):
    path = os.path.join(OUTPUT_DIR, job_id, filename)
    if not os.path.isfile(path):
        return "Ni najdeno.", 404
    return send_file(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
