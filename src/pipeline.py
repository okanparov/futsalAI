"""detect -> track -> stats -> rating -> database."""
from src.camera_motion import CameraMotionEstimator, warp_boxes
from src.court import court_homography
from src.rating_system import RatingSystem
from src.stats_calculator import StatsCalculator
from src.tracker import PlayerTracker
from src.video_processor import VideoProcessor


def process_match(db, match_id, detector, tracker=None, fps=None, court_size_m=(40.0, 20.0),
                  calibration=None, camera_motion=False, max_seconds=None,
                  min_track_seconds=0.0, court_margin_m=None):
    """calibration: referans (ilk) karede sahanin 4 kosesi [sol-ust, sag-ust, sag-alt, sol-alt] piksel.
    camera_motion: donen/pan yapan kamera icin telafiyi acar."""
    match = db.get_match(match_id)
    if not match:
        raise ValueError(f"mac bulunamadi: {match_id}")
    tracker = tracker or PlayerTracker()
    estimator = CameraMotionEstimator() if camera_motion else None
    court_hom = court_homography(calibration, court_size_m) if calibration else None
    det_rows = []
    with VideoProcessor(match["video_path"]) as vp:
        stats = StatsCalculator((vp.width, vp.height), court_size_m, court_hom=court_hom,
                               bounds_margin_m=court_margin_m)
        for frame_id, ts, frame in vp.extract_frames(fps=fps):
            if max_seconds is not None and ts > max_seconds:
                break
            dets = detector.detect(frame)
            cam = estimator.update(frame, dets) if estimator else None
            # takip referans (kamera-telafili) koordinatta yapilir; pan eslesmeyi bozmaz
            tracks = tracker.update(warp_boxes(cam, dets) if cam is not None else dets, frame)
            stats.add_frame(ts, tracks)
            for x1, y1, x2, y2, tid, conf in tracks:
                det_rows.append((frame_id, int(tid), (x1 + x2) / 2, y2, float(conf), ts))
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
    return {"players": len(player_ids), "tracks_raw": raw_tracks,
            "frames_processed": len({r[0] for r in det_rows})}
