import cv2
import numpy as np

from src.video_processor import VideoProcessor


def test_video_processor_reads_frames(tmp_path):
    path = str(tmp_path / "t.avi")
    w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for _ in range(10):
        w.write(np.zeros((48, 64, 3), dtype=np.uint8))
    w.release()
    with VideoProcessor(path) as vp:
        frames = list(vp.extract_frames(fps=5))
    assert len(frames) == 5 and frames[0][2].shape == (48, 64, 3)
