import cv2
import numpy as np

from app import create_app
from src.database import Database
from src.pipeline import process_match


class FakeDetector:
    def __init__(self):
        self.i = 0

    def detect(self, frame):
        self.i += 1
        x = 10 + self.i * 5
        return np.array([[x, 20, x + 10, 60, .9]])


def make_video(path, n=12):
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (200, 100))
    for _ in range(n):
        w.write(np.zeros((100, 200, 3), dtype=np.uint8))
    w.release()


def test_pipeline_end_to_end(tmp_path):
    video = str(tmp_path / "m.avi")
    make_video(video)
    db = Database(":memory:")
    mid = db.add_match("A", "B", video_path=video)
    out = process_match(db, mid, FakeDetector())
    assert out["players"] == 1
    ratings = db.get_ratings(mid)
    assert len(ratings) == 1 and 0 <= ratings[0]["rating"] <= 99
    assert db.get_match(mid)["processed"] == 1


def test_process_endpoint(tmp_path):
    video = str(tmp_path / "m.avi")
    make_video(video)
    app = create_app(db_path=":memory:", upload_dir=str(tmp_path), detector_factory=FakeDetector)
    c = app.test_client()
    with open(video, "rb") as f:
        mid = c.post("/api/upload-video", data={"video": (f, "m.avi")}).get_json()["match_id"]
    r = c.post("/api/process-match", json={"match_id": mid})
    assert r.status_code == 200 and r.get_json()["players"] == 1
    assert len(c.get(f"/api/match/{mid}/ratings").get_json()) == 1
    assert c.post("/api/process-match", json={"match_id": 99}).status_code == 404


def test_pages_and_card_data(tmp_path):
    video = str(tmp_path / "m.avi")
    make_video(video)
    app = create_app(db_path=":memory:", upload_dir=str(tmp_path), detector_factory=FakeDetector)
    c = app.test_client()
    with open(video, "rb") as f:
        mid = c.post("/api/upload-video", data={"video": (f, "m.avi")}).get_json()["match_id"]
    c.post("/api/process-match", json={"match_id": mid})
    for url in ("/", f"/match/{mid}", "/player/1"):
        assert c.get(url).status_code == 200
    players = c.get(f"/api/match/{mid}/players").get_json()
    assert len(players) == 1
    stats = c.get(f"/api/player/{players[0]['player_id']}/stats").get_json()
    assert stats["player_name"] and len(stats["heatmap"]) == 4 and len(stats["heatmap"][0]) == 8
    assert c.get("/api/match/99/players").status_code == 404
