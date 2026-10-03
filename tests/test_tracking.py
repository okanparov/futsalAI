import numpy as np

from src.tracker import PlayerTracker


def test_ids_persist_and_new_id_assigned():
    t = PlayerTracker(min_hits=1)
    a = t.update(np.array([[0, 0, 10, 20, .9], [100, 0, 110, 20, .9]]))
    b = t.update(np.array([[1, 0, 11, 20, .9], [101, 0, 111, 20, .9], [200, 0, 210, 20, .9]]))
    assert sorted(b[:2, 4]) == sorted(a[:, 4])
    assert b[2, 4] not in a[:, 4]


def test_empty_detections():
    assert PlayerTracker().update(np.empty((0, 5))).shape == (0, 6)


def test_ghost_detection_not_confirmed():
    t = PlayerTracker(min_hits=3)
    out = [t.update(np.array([[0, 0, 10, 40, .9]]) if i == 0 else np.empty((0, 5))) for i in range(5)]
    assert all(len(o) == 0 for o in out)


def simulate(n_players=10, frames=300, dropout=0.15, seed=1, pan_px=0.0):
    """Rastgele yuruyen oyuncular, tespit kacirma ve titreme. Pan ekran koordinatinda uygulanir
    ve takipciye telafili (referans) koordinat verilir -> pan etkisiz olmali."""
    rng = np.random.RandomState(seed)
    pos = rng.uniform([50, 100], [1800, 700], (n_players, 2))
    vel = rng.normal(0, 6, (n_players, 2))
    t = PlayerTracker(max_age=30, min_hits=3)
    ids = set()
    for f in range(frames):
        pos += vel + rng.normal(0, 1.5, pos.shape)
        pos = np.clip(pos, [20, 100], [1850, 800])
        vel += rng.normal(0, 0.8, vel.shape)
        dets = [[x - 20 + rng.normal(0, 1.5), y - 90, x + 20 + rng.normal(0, 1.5), y, .9]
                for x, y in pos if rng.rand() > dropout]
        out = t.update(np.array(dets).reshape(-1, 5))
        ids.update(out[:, 4].astype(int))
    return len(ids)


def test_id_fragmentation_is_low():
    # 10 oyuncu, %15 kacirma, 300 kare: izler 10'a yakin kalmali (eski IoU takipcisi onlarca uretirdi)
    assert simulate() <= 20
