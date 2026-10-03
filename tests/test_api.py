import io

from app import create_app


def test_endpoints(tmp_path):
    app = create_app(db_path=":memory:", upload_dir=str(tmp_path))
    c = app.test_client()
    r = c.post("/api/upload-video", data={"video": (io.BytesIO(b"x"), "m.mp4"), "team1": "A", "team2": "B"})
    assert r.status_code == 201
    mid = r.get_json()["match_id"]
    assert c.get(f"/api/match/{mid}").get_json()["team1"] == "A"
    assert c.get(f"/api/match/{mid}/ratings").get_json() == []
    assert c.get("/api/match/99").status_code == 404
    assert len(c.get("/api/dashboard").get_json()["matches"]) == 1
    assert c.post("/api/upload-video").status_code == 400
