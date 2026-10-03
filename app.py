"""Flask backend."""
from pathlib import Path

import yaml
from flask import Flask, jsonify, render_template, request

from src.database import Database
from src.pipeline import process_match as run_pipeline


def create_app(db_path=None, upload_dir="data/videos", detector_factory=None):
    cfg = {}
    if Path("config.yaml").exists():
        cfg = yaml.safe_load(Path("config.yaml").read_text()) or {}
    app = Flask(__name__)
    db = Database(db_path or cfg.get("database", {}).get("path", "data/matches.db"))
    Path(upload_dir).mkdir(parents=True, exist_ok=True)

    @app.get("/")
    def index_page():
        return render_template("index.html")

    @app.get("/match/<int:match_id>")
    def match_page(match_id):
        return render_template("match_stats.html", match_id=match_id)

    @app.get("/player/<int:player_id>")
    def player_page(player_id):
        return render_template("player_card.html", player_id=player_id)

    @app.get("/api/match/<int:match_id>/players")
    def match_players(match_id):
        if not db.get_match(match_id):
            return jsonify(error="mac bulunamadi"), 404
        return jsonify(db.list_match_players(match_id))

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
        try:
            if detector_factory:
                detector = detector_factory()
            else:
                from src.player_detector import PlayerDetector
                det_cfg = cfg.get("detection", {})
                detector = PlayerDetector(det_cfg.get("model_path", "models/yolov8n.pt"),
                                          det_cfg.get("confidence", 0.4))
        except ImportError as e:
            return jsonify(error=f"dedektor yuklenemedi: {e}"), 503
        return jsonify(run_pipeline(db, match_id, detector))

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
