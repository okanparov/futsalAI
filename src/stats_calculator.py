"""Per-player metrics from tracked positions.

Konum, bbox'in alt-orta noktasindan (ayaklar) alinir ve kareden sahaya dogrusal
olcekle metreye cevrilir (perspektif duzeltmesi YOK, yaklasik deger).
Top verisi olmadigindan pas/top temasi/tackle/interception su an hesaplanmaz.
"""
import math
from collections import defaultdict

import numpy as np

MAX_SPEED_MS = 12.0  # bunun ustundeki adimlar takip sicramasi sayilir


class StatsCalculator:
    def __init__(self, frame_size, court_size_m=(40.0, 20.0), grid=(8, 4)):
        self.frame_w, self.frame_h = frame_size
        self.court_w, self.court_h = court_size_m
        self.grid = grid
        self._pos = defaultdict(list)  # track_id -> [(t, x_m, y_m)]

    def to_court(self, x, y):
        return x / self.frame_w * self.court_w, y / self.frame_h * self.court_h

    def add_frame(self, timestamp, tracks):
        """tracks: Nx6 [x1,y1,x2,y2,id,conf]."""
        for x1, y1, x2, y2, tid, _ in tracks:
            self._pos[int(tid)].append((timestamp, *self.to_court((x1 + x2) / 2, y2)))

    def track_ids(self):
        return list(self._pos)

    def distance(self, tid):
        pts, total = self._pos[tid], 0.0
        for (t0, x0, y0), (t1, x1, y1) in zip(pts, pts[1:]):
            d, dt = math.hypot(x1 - x0, y1 - y0), t1 - t0
            if dt > 0 and d / dt <= MAX_SPEED_MS:
                total += d
        return total

    def heatmap(self, tid):
        gx, gy = self.grid
        h = np.zeros((gy, gx))
        for _, x, y in self._pos[tid]:
            i = min(gx - 1, max(0, int(x / self.court_w * gx)))
            j = min(gy - 1, max(0, int(y / self.court_h * gy)))
            h[j, i] += 1
        return h

    def coverage(self, tid):
        """Ziyaret edilen saha hucresi orani (0-1)."""
        return float((self.heatmap(tid) > 0).mean())

    def summary(self, tid):
        pts = self._pos[tid]
        return {
            "distance_covered": self.distance(tid),
            "frames_seen": len(pts),
            "coverage": self.coverage(tid),
            "heatmap": self.heatmap(tid).tolist(),
        }

    def process_all(self):
        return {tid: self.summary(tid) for tid in self._pos}
