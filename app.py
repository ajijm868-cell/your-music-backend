"""
YOUR MUSIC - Backend Server
---------------------------
Run: python app.py
Endpoints:
  GET /search?q=<query>       -> list of tracks (title, artist, thumbnail, videoId)
  GET /stream/<video_id>      -> direct playable audio stream URL

Notes:
- Uses yt-dlp to talk to YouTube (no official API key needed).
- Keep this running on 127.0.0.1:5000 - frontend already expects this
  (see BACKEND_URL in script.js).
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # allows the HTML/JS frontend (different origin) to call this server


def search_youtube(query, limit=15):
    """Search YouTube and return a lightweight list of track dicts."""
    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",  # fast: don't fetch full info per video
        "noplaylist": True,
    }
    search_query = f"ytsearch{limit}:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get("entries", []) if info else []

    results = []
    for e in entries:
        if not e:
            continue
        video_id = e.get("id")
        results.append({
            "videoId": video_id,
            "title": e.get("title", "Unknown Title"),
            "artist": e.get("uploader") or e.get("channel") or "Unknown Artist",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "duration": e.get("duration"),
        })
    return results


def resolve_stream_url(video_id):
    """Given a YouTube video id, return a direct audio stream URL."""
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    url = f"https://www.youtube.com/watch?v={video_id}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("url") if info else None


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "missing query param 'q'"}), 400
    try:
        results = search_youtube(query)
        return jsonify({"results": results})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route("/stream/<video_id>")
def stream(video_id):
    try:
        url = resolve_stream_url(video_id)
        if not url:
            return jsonify({"error": "could not resolve stream"}), 404
        return jsonify({"streamUrl": url})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)