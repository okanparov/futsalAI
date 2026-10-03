"""Flask backend."""
from pathlib import Path

import yaml
from flask import Flask, jsonify, request

from src.database import Database


def create_app(db_path=None, upload_dir="data/videos"):
    cfg = {}
    if Path("config.yaml").exists():
        cfg = yaml.safe_load(Path("config.yaml").read_text()) or {}
    app = Flask(__name__)
    db = Database(db_path or cfg.get("database", {}).get("path", "data/matches.db"))
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    @app.post("/api/upload-video")
    def upload_video():
        f = request.files.get("video")
        if not f or not f.filename:
            return jsonify(error="video dosyasi gerekli"), 400
        dest = Path(upload_dir) / Path(f.filename).name
        f.save(dest)
        match_id = db.add_match(request.form.get("team1", ""), request.form.get("team2", ""),
                                request.form.get("venue", ""), str(dest))
        return jsonify(match_id=match_id, video_path=str(dest)), 201

    @app.post("/api/process-match")
    def process_match():
        match_id = (request.get_json(silent=True) or {}).get("match_id")
        if not db.get_match(match_id):
            return jsonify(error="mac bulunamadi"), 404
        # TODO(Sprint 2): pipeline'i (detect -> track -> stats) calistir.
        return jsonify(error="isleme henuz uygulanmadi"), 501

    @app.get("/api/match/<int:match_id>")
    def match(match_id):
        m = db.get_match(match_id)
        return (jsonify(m), 200) if m else (jsonify(error="mac bulunamadi"), 404)

    @app.get("/api/player/<int:player_id>/stats")
    def player_stats(player_id):
        s = db.get_player_stats(player_id)
        return (jsonify(s), 200) if s else (jsonify(error="istatistik yok"), 404)

    @app.get("/api/match/<int:match_id>/ratings")
    def ratings(match_id):
        if not db.get_match(match_id):
            return jsonify(error="mac bulunamadi"), 404
        return jsonify(db.get_ratings(match_id))

    @app.get("/api/dashboard")
    def dashboard():
        return jsonify(matches=db.list_matches())

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
