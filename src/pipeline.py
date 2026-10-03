"""detect -> track -> stats -> rating -> database."""
from src.rating_system import RatingSystem
from src.stats_calculator import StatsCalculator
from src.tracker import PlayerTracker
from src.video_processor import VideoProcessor


def process_match(db, match_id, detector, tracker=None, fps=None, court_size_m=(40.0, 20.0)):
    match = db.get_match(match_id)
    if not match:
        raise ValueError(f"mac bulunamadi: {match_id}")
    tracker = tracker or PlayerTracker()
    det_rows = []
    with VideoProcessor(match["video_path"]) as vp:
        stats = StatsCalculator((vp.width, vp.height), court_size_m)
        for frame_id, ts, frame in vp.extract_frames(fps=fps):
            tracks = tracker.update(detector.detect(frame), frame)
            stats.add_frame(ts, tracks)
            for x1, y1, x2, y2, tid, conf in tracks:
                det_rows.append((frame_id, int(tid), (x1 + x2) / 2, y2, float(conf), ts))
    # track_id -> players.id
    player_ids = {tid: db.add_player(match_id, f"Oyuncu {tid}") for tid in stats.track_ids()}
    db.add_detections([(f, player_ids[t], x, y, c, ts) for f, t, x, y, c, ts in det_rows])
    rater = RatingSystem()
    for tid, summary in stats.process_all().items():
        db.save_match_stats(match_id, player_ids[tid], summary["distance_covered"],
                            rater.from_match_stats(summary), summary["coverage"], summary["heatmap"])
    db.mark_processed(match_id)
    return {"players": len(player_ids), "frames_processed": len({r[0] for r in det_rows})}
