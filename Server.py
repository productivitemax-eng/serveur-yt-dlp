from flask import Flask, request, jsonify, send_file
import yt_dlp, os, uuid, time, threading

app = Flask(__name__)
DIR = "/tmp/dl"
os.makedirs(DIR, exist_ok=True)

def cleanup():
    while True:
        time.sleep(600)
        now = time.time()
        for f in os.listdir(DIR):
            p = os.path.join(DIR, f)
            if now - os.path.getmtime(p) > 1800:
                try: os.remove(p)
                except: pass

threading.Thread(target=cleanup, daemon=True).start()

@app.route("/")
def health():
    return jsonify({"status": "ok"})

@app.route("/get_mp4", methods=["POST"])
def get_mp4():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL manquante"}), 400

    filename = f"{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(DIR, filename)

    try:
        with yt_dlp.YoutubeDL({
            "format": "best[ext=mp4][height<=1080]/best[ext=mp4]/best",
            "outtmpl": filepath,
            "quiet": True,
            "merge_output_format": "mp4",
        }) as ydl:
            info = ydl.extract_info(url, download=True)

        base = request.host_url.rstrip("/")
        return jsonify({
            "success": True,
            "mp4_url": f"{base}/files/{filename}",
            "title": info.get("title", ""),
            "duration": info.get("duration", 0)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/files/<name>")
def serve(name):
    p = os.path.join(DIR, os.path.basename(name))
    return send_file(p, mimetype="video/mp4") if os.path.exists(p) else ("", 404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
