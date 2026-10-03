"""Kamera hareketi telafisi (donen/pan yapan sabit kamera, zoom yok).

Her karenin koordinatini ilk karenin (referans) koordinatina tasiyan 3x3 homografi
hesaplanir. Oyuncu kutulari ozellik secimi disinda tutulur ki oyuncu hareketi
kamera hareketi sanilmasin. Hata zamanla birikir (drift); kisa/orta klipler icin uygundur.
"""
import cv2
import numpy as np


class CameraMotionEstimator:
    def __init__(self, scale=0.5, max_corners=400, min_points=12):
        self.scale = scale
        self.max_corners = max_corners
        self.min_points = min_points
        self._prev_gray = None
        self._prev_pts = None
        self.to_ref = np.eye(3)  # guncel kare -> referans kare
        self.frames = 0
        self.failed = 0  # hareket kestirilemeyen kare sayisi (onceki donusum korunur)

    def _prep(self, frame, boxes):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        gray = cv2.resize(gray, None, fx=self.scale, fy=self.scale)
        mask = np.full(gray.shape, 255, np.uint8)
        for b in boxes:
            x1, y1, x2, y2 = [int(v * self.scale) for v in b[:4]]
            pad = 4
            mask[max(0, y1 - pad):y2 + pad, max(0, x1 - pad):x2 + pad] = 0
        return gray, mask

    def _features(self, gray, mask):
        return cv2.goodFeaturesToTrack(gray, self.max_corners, 0.01, 7, mask=mask)

    def update(self, frame, boxes=()):
        """Guncel kareyi isle; kare->referans homografisini (3x3) dondurur."""
        gray, mask = self._prep(frame, boxes)
        self.frames += 1
        updated = self._prev_gray is None
        if self._prev_gray is not None and self._prev_pts is not None and len(self._prev_pts) >= self.min_points:
            cur_pts, status, _ = cv2.calcOpticalFlowPyrLK(self._prev_gray, gray, self._prev_pts, None)
            ok = status.ravel() == 1
            p0, p1 = self._prev_pts[ok], cur_pts[ok]
            # simdiki karede oyuncu kutusuna dusen noktalari at
            keep = np.array([mask[int(np.clip(p[0][1], 0, mask.shape[0] - 1)),
                                  int(np.clip(p[0][0], 0, mask.shape[1] - 1))] > 0 for p in p1], bool)
            p0, p1 = p0[keep], p1[keep]
            if len(p0) >= self.min_points:
                H, inl = cv2.findHomography(p1.reshape(-1, 2) / self.scale, p0.reshape(-1, 2) / self.scale,
                                            cv2.RANSAC, 3.0)
                if H is not None and inl is not None and inl.sum() >= self.min_points:
                    self.to_ref = self.to_ref @ H  # cur->prev, prev->ref ile birlestirilir
                    updated = True
        if not updated:
            self.failed += 1
        self._prev_gray = gray
        self._prev_pts = self._features(gray, mask)
        return self.to_ref.copy()


def apply_homography(H, x, y):
    p = H @ np.array([x, y, 1.0])
    return p[0] / p[2], p[1] / p[2]


def warp_boxes(H, dets):
    """Nx(>=4) kutulari H ile donusturur (koseler donusturulup sinirlayici kutu alinir)."""
    dets = np.asarray(dets, dtype=float)
    if H is None or len(dets) == 0:
        return dets
    out = dets.copy()
    for i, d in enumerate(dets):
        xs, ys = zip(*[apply_homography(H, x, y) for x, y in ((d[0], d[1]), (d[2], d[1]), (d[2], d[3]), (d[0], d[3]))])
        out[i, :4] = [min(xs), min(ys), max(xs), max(ys)]
    return out
