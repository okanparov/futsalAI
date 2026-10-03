"""Oyuncu takibi: hareket tahminli, mesafe tabanli, bagimsiz (ek kutuphane gerektirmez).

Koordinatlar kamera telafisiyle referans karede verilirse pan/donus eslesmeyi bozmaz.
Eslesme maliyeti: ayak noktasi mesafesi / kutu boyu. Ilk `min_hits` karede gorulmeyen
aday izler (hayalet tespitler) cikti uretmez ve kimlik tuketmez.
"""
import numpy as np


class MotionTracker:
    def __init__(self, max_age=30, min_hits=3, gate=1.0):
        self.max_age = max_age
        self.min_hits = min_hits
        self.gate = gate
        self._next_id = 1
        self._tracks = []

    @staticmethod
    def _foot(box):
        return np.array([(box[0] + box[2]) / 2, box[3]])

    def update(self, detections, frame=None):
        """detections: Nx5 [x1,y1,x2,y2,conf]. Dondurur: Nx6 [x1,y1,x2,y2,id,conf] (onayli izler)."""
        dets = np.asarray(detections, dtype=float).reshape(-1, 5)
        pairs = []
        for ti, t in enumerate(self._tracks):
            pred = t["pos"] + t["vel"] * min(t["lost"] + 1, 5)
            gate = self.gate * (1 + 0.15 * min(t["lost"], 10))
            for di, d in enumerate(dets):
                cost = np.linalg.norm(self._foot(d) - pred) / max(t["h"], d[3] - d[1], 1.0)
                if cost < gate:
                    pairs.append((cost, ti, di))
        pairs.sort()
        used_t, used_d, out = set(), set(), []
        for _, ti, di in pairs:
            if ti in used_t or di in used_d:
                continue
            used_t.add(ti)
            used_d.add(di)
            t, d = self._tracks[ti], dets[di]
            pos = self._foot(d)
            t["vel"] = 0.5 * t["vel"] + 0.5 * (pos - t["pos"]) / (t["lost"] + 1)
            t["pos"], t["h"], t["lost"], t["hits"] = pos, d[3] - d[1], 0, t["hits"] + 1
            if t["id"] is None and t["hits"] >= self.min_hits:
                t["id"], self._next_id = self._next_id, self._next_id + 1
            if t["id"] is not None:
                out.append([*d[:4], t["id"], d[4]])
        n_old = len(self._tracks)
        for di, d in enumerate(dets):
            if di not in used_d:
                t = {"pos": self._foot(d), "vel": np.zeros(2), "h": d[3] - d[1], "hits": 1, "lost": 0, "id": None}
                if self.min_hits <= 1:
                    t["id"], self._next_id = self._next_id, self._next_id + 1
                    out.append([*d[:4], t["id"], d[4]])
                self._tracks.append(t)
        kept = []
        for ti, t in enumerate(self._tracks):
            if ti >= n_old or ti in used_t:
                kept.append(t)  # bu karede eslesti ya da yeni acildi
                continue
            t["lost"] += 1
            if t["id"] is not None and t["lost"] <= self.max_age:  # aday izler kayipta hemen silinir
                kept.append(t)
        self._tracks = kept
        return np.array(out, dtype=float).reshape(-1, 6)


class PlayerTracker:
    def __init__(self, max_age=30, min_hits=3, gate=1.0):
        self._impl = MotionTracker(max_age=max_age, min_hits=min_hits, gate=gate)

    def update(self, detections, frame=None):
        return self._impl.update(detections, frame)
