"""Video input and frame extraction."""
import cv2


class VideoProcessor:
    def __init__(self, video_path):
        self.video_path = str(video_path)
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise IOError(f"Video acilamadi: {self.video_path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def extract_frames(self, fps=None):
        """Yield (frame_id, timestamp_sec, frame); fps ile kare atlanir."""
        step = max(1, round(self.fps / fps)) if fps else 1
        frame_id = 0
        while True:
            ok, frame = self.cap.read()
            if not ok:
                break
            if frame_id % step == 0:
                yield frame_id, frame_id / self.fps, frame
            frame_id += 1

    def close(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
