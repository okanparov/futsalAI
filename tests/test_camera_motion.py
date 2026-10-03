import cv2
import numpy as np

from src.camera_motion import CameraMotionEstimator, apply_homography
from src.court import court_homography
from src.database import Database
from src.pipeline import process_match

W, H, STEP, N = 400, 300, 5, 30
PLAYER_WORLD_X = 300


def world():
    rng = np.random.RandomState(0)
    img = np.full((H, 1000, 3), 90, np.uint8)
    for _ in range(600):
        c = tuple(int(v) for v in rng.randint(0, 255, 3))
        cv2.circle(img, (int(rng.randint(0, 1000)), int(rng.randint(0, H))), int(rng.randint(2, 7)), c, -1)
    return img


def frames():
    w = world()
    for i in range(N):
        yield w[:, i * STEP:i * STEP + W].copy()


class WorldFixedDetector:
    """Dunyada sabit duran bir oyuncu: kare icinde kamera ile ters yonde kayar."""
    def __init__(self):
        self.i = 0

    def detect(self, frame):
        x = PLAYER_WORLD_X - self.i * STEP
        self.i += 1
        return np.array([[x, 150, x + 10, 190, .9]])


def test_estimator_recovers_pan():
    est = CameraMotionEstimator()
    for i, f in enumerate(frames()):
        h = est.update(f)
    x, y = apply_homography(h, 0, 0)
    assert abs(x - (N - 1) * STEP) < 4 and abs(y) < 4


def test_pipeline_pan_compensation(tmp_path):
    path = str(tmp_path / "pan.avi")
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (W, H))
    for f in frames():
        w.write(f)
    w.release()
    calib = [[0, 0], [W, 0], [W, H], [0, H]]
    dist = {}
    for use_cam in (False, True):
        db = Database(":memory:")
        mid = db.add_match("A", "B", video_path=path)
        process_match(db, mid, WorldFixedDetector(), court_size_m=(40.0, 30.0),
                      calibration=calib, camera_motion=use_cam)
        dist[use_cam] = db.list_match_players(mid)[0]["distance_covered"]
    # telafisiz: oyuncu kamerayla ters kayiyor gibi gorunur (~14 m); telafili: neredeyse duruyor
    assert dist[False] > 8
    assert dist[True] < 2


def test_court_homography_corners():
    from src.camera_motion import apply_homography as ap
    hom = court_homography([[10, 10], [110, 12], [120, 80], [5, 78]], (40, 20))
    assert np.allclose(ap(hom, 10, 10), (0, 0), atol=1e-3)
    assert np.allclose(ap(hom, 120, 80), (40, 20), atol=1e-3)
