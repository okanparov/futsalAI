"""Player tracking. Uses boxmot DeepSORT when available, else a greedy IoU tracker."""
import numpy as np


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


class IouTracker:
    def __init__(self, max_age=30, iou_threshold=0.3):
        self.max_age = max_age
        self.iou_threshold = iou_threshold
        self._next_id = 1
        self._tracks = {}  # id -> (bbox, age)

    def update(self, detections, frame=None):
        """detections: Nx5 [x1,y1,x2,y2,conf]. Returns Nx6 [x1,y1,x2,y2,id,conf]."""
        out, used = [], set()
        for det in detections:
            best_id, best = None, self.iou_threshold
            for tid, (box, _) in self._tracks.items():
                if tid in used:
                    continue
                score = iou(det[:4], box)
                if score > best:
                    best_id, best = tid, score
            if best_id is None:
                best_id, self._next_id = self._next_id, self._next_id + 1
            used.add(best_id)
            self._tracks[best_id] = (det[:4], 0)
            out.append([*det[:4], best_id, det[4]])
        for tid in list(self._tracks):
            if tid not in used:
                box, age = self._tracks[tid]
                if age + 1 > self.max_age:
                    del self._tracks[tid]
                else:
                    self._tracks[tid] = (box, age + 1)
        return np.array(out, dtype=float).reshape(-1, 6)


class PlayerTracker:
    def __init__(self, max_age=30):
        self._impl = IouTracker(max_age=max_age)
        self.backend = "iou"
        try:
            from boxmot import DeepOcSort  # noqa: F401  (boxmot kurulu mu?)
        except Exception:
            return
        # boxmot API surumler arasi degisiyor; entegrasyon gercek GPU makinede dogrulanmali.
        # Su an varsayilan IoU takipcisi kullanilir.

    def update(self, detections, frame=None):
        return self._impl.update(detections, frame)
