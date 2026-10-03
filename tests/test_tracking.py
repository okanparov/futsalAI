import numpy as np

from src.tracker import PlayerTracker


def test_ids_persist_and_new_id_assigned():
    t = PlayerTracker()
    a = t.update(np.array([[0, 0, 10, 20, .9], [100, 0, 110, 20, .9]]))
    b = t.update(np.array([[1, 0, 11, 20, .9], [101, 0, 111, 20, .9], [200, 0, 210, 20, .9]]))
    assert list(b[:2, 4]) == list(a[:, 4])
    assert b[2, 4] not in a[:, 4]


def test_empty_detections():
    assert PlayerTracker().update(np.empty((0, 5))).shape == (0, 6)
