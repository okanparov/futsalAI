"""detect -> track -> stats -> rating -> database."""
import cv2
import numpy as np

from src.camera_motion import CameraMotionEstimator, warp_boxes
from src.court import court_homography
from src.rating_system import RatingSystem
from src.stats_calculator import StatsCalculator
from src.tracker import PlayerTracker
from src.video_processor import VideoProcessor


def process_match(db, match_id, detector, tracker=None, fps=None, court_size_m=(40.0, 20.0),
                  calibration=None, camera_motion=False, max_seconds=None,
                  min_track_seconds=0.0, court_margin_m=None, annotate_path=None):
    """calibration: referans (ilk) karede sahanin 4 kosesi [sol-ust, sag-ust, sag-alt, sol-alt] piksel.
    camera_motion: donen/pan yapan kamera icin telafiyi acar."""
    match = db.get_match(match_id)
    if not match:
        raise ValueError(f"mac bulunamadi: {match_id}")
    tracker = tracker or PlayerTracker()
    estimator = CameraMotionEstimator() if camera_motion else None
    court_hom = court_homography(calibration, court_size_m) if calibration else None
    det_rows = []
    det_total = frames_n = 0
    writer = None
    with VideoProcessor(match["video_path"]) as vp:
        stats = StatsCalculator((vp.width, vp.height), court_size_m, court_hom=court_hom,
                               bounds_margin_m=court_margin_m)
        for frame_id, ts, frame in vp.extract_frames(fps=fps):
            if max_seconds is not None and ts > max_seconds:
                break
            dets = detector.detect(frame)
            det_total += len(dets)
            frames_n += 1
            cam = estimator.update(frame, dets) if estimator else None
            # takip referans (kamera-telafili) koordinatta yapilir; pan eslesmeyi bozmaz
            tracks = tracker.update(warp_boxes(cam, dets) if cam is not None else dets, frame)
            stats.add_frame(ts, tracks)
            if annotate_path:
                writer = writer or _open_writer(annotate_path, vp, fps)
                _write_annotated(writer, frame, tracks, cam, frame_id, ts)
            for x1, y1, x2, y2, tid, conf in tracks:
                det_rows.append((frame_id, int(tid), (x1 + x2) / 2, y2, float(conf), ts))
    if writer:
        writer.release()
    raw_tracks = len(stats.track_ids())
    keep = [tid for tid in stats.track_ids() if stats.duration(tid) >= min_track_seconds]
    # track_id -> players.id (kisa/hayalet izler atilir)
    player_ids = {tid: db.add_player(match_id, f"Oyuncu {tid}") for tid in keep}
    db.add_detections([(f, player_ids[t], x, y, c, ts) for f, t, x, y, c, ts in det_rows if t in player_ids])
    rater = RatingSystem()
    for tid, summary in ((t, stats.summary(t)) for t in keep):
        db.save_match_stats(match_id, player_ids[tid], summary["distance_covered"],
                            rater.from_match_stats(summary), summary["coverage"], summary["heatmap"])
    db.mark_processed(match_id)
    durations = sorted(stats.duration(t) for t in stats.track_ids())
    debug = {
        "frames": frames_n,
        "avg_detections_per_frame": det_total / frames_n if frames_n else 0.0,
        "camera_failed_frames": estimator.failed if estimator else None,
        "track_seconds_median": durations[len(durations) // 2] if durations else 0.0,
        "track_seconds_max": durations[-1] if durations else 0.0,
        "tracks_over_3s": sum(d >= 3 for d in durations),
    }
    return {"players": len(player_ids), "tracks_raw": raw_tracks, "debug": debug,
            "frames_processed": len({r[0] for r in det_rows})}


OUT_WIDTH = 1280


def _open_writer(path, vp, fps):
    scale = OUT_WIDTH / vp.width
    size = (OUT_WIDTH, int(vp.height * scale))
    codec = "mp4v" if str(path).lower().endswith(".mp4") else "MJPG"
    return cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*codec), fps or vp.fps, size)


def _write_annotated(writer, frame, tracks, cam, frame_id, ts):
    """Izleri (referans koordinatta) kare koordinatina geri tasiyip numarali kutu cizer."""
    img = cv2.resize(frame, (OUT_WIDTH, int(frame.shape[0] * OUT_WIDTH / frame.shape[1])))
    k = OUT_WIDTH / frame.shape[1]
    boxes = warp_boxes(np.linalg.inv(cam), tracks) if cam is not None and len(tracks) else tracks
    for x1, y1, x2, y2, tid, _ in boxes:
        tid = int(tid)
        color = ((tid * 67) % 200 + 55, (tid * 131) % 200 + 55, (tid * 29) % 200 + 55)
        p1, p2 = (int(x1 * k), int(y1 * k)), (int(x2 * k), int(y2 * k))
        cv2.rectangle(img, p1, p2, color, 2)
        cv2.putText(img, f"#{tid}", (p1[0], max(12, p1[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(img, f"t={ts:5.1f}s  izler={len(tracks)}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    writer.write(img)
