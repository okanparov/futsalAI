"""Tek komutla video analizi.

Ornek:
  python analyze.py maç.mp4 --pick-points             # once saha koselerini sec
  python analyze.py maç.mp4 --calib "120,300,1800,310,1900,900,40,880" --max-seconds 120
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

from src.database import Database
from src.pipeline import process_match


def parse_calib(text):
    nums = [float(v) for v in text.split(",")]
    if len(nums) != 8:
        raise argparse.ArgumentTypeError("--calib 8 sayi olmali: x1,y1,x2,y2,x3,y3,x4,y4")
    return [[nums[i], nums[i + 1]] for i in range(0, 8, 2)]


def pick_points(video):
    """Ilk karede 4 saha kosesini tiklatir (sol-ust, sag-ust, sag-alt, sol-alt). Pencere gerektirir."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        sys.exit("Video acilamadi")
    pts = []

    def on_click(event, x, y, *_):
        if event == cv2.EVENT_LBUTTONDOWN and len(pts) < 4:
            pts.append((x, y))
            cv2.circle(frame, (x, y), 6, (0, 0, 255), -1)

    cv2.namedWindow("saha kosesi sec")
    cv2.setMouseCallback("saha kosesi sec", on_click)
    print("Sirayla tikla: sol-ust, sag-ust, sag-alt, sol-alt saha kosesi (ESC: iptal).")
    while len(pts) < 4:
        cv2.imshow("saha kosesi sec", frame)
        if cv2.waitKey(50) == 27:
            break
    cv2.imshow("saha kosesi sec", frame)
    cv2.waitKey(500)
    cv2.destroyAllWindows()
    if len(pts) == 4:
        print('--calib "' + ",".join(f"{x},{y}" for x, y in pts) + '"')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--team1", default="Takim 1")
    ap.add_argument("--team2", default="Takim 2")
    ap.add_argument("--fps", type=float, default=10, help="Islenecek kare/sn (varsayilan 10)")
    ap.add_argument("--max-seconds", type=float, help="Yalnizca ilk N saniyeyi isle")
    ap.add_argument("--court", default="40x20", help="Saha boyutu metre, ornek 40x20")
    ap.add_argument("--calib", type=parse_calib, help="Ilk karede saha koseleri (8 sayi)")
    ap.add_argument("--min-track-seconds", type=float, default=3.0,
                    help="Bundan kisa izler (hayalet/yanlis tespit) atilir (varsayilan 3)")
    ap.add_argument("--court-margin", type=float,
                    help="Saha disi tolerans (m): disindaki tespitler (seyirci/yedek) atilir; dogru --calib gerekir")
    ap.add_argument("--annotate", metavar="CIKTI.mp4",
                    help="Kutu ve oyuncu numaralari cizilmis kontrol videosu yaz")
    ap.add_argument("--debug", action="store_true", help="Takip/kamera tanilama bilgisini yazdir")
    ap.add_argument("--no-camera-motion", action="store_true", help="Sabit kamera: telafiyi kapat")
    ap.add_argument("--pick-points", action="store_true", help="Saha koselerini tiklayarak sec ve cik")
    ap.add_argument("--model", help="YOLO model yolu (config.yaml'daki yerine)")
    ap.add_argument("--db", help="Veritabani yolu")
    args = ap.parse_args()

    if not Path(args.video).exists():
        sys.exit(f"Dosya yok: {args.video}")
    if args.pick_points:
        return pick_points(args.video)

    cfg = yaml.safe_load(Path("config.yaml").read_text()) if Path("config.yaml").exists() else {}
    det_cfg = cfg.get("detection", {})
    cw, ch = (float(v) for v in args.court.lower().split("x"))

    if not args.calib:
        print("UYARI: --calib verilmedi. Kamera donuyorsa metre cinsinden degerler ANLAMSIZ olur; "
              "once --pick-points ile saha koselerini secin.", file=sys.stderr)

    from src.player_detector import PlayerDetector
    detector = PlayerDetector(args.model or det_cfg.get("model_path", "models/yolov8n.pt"),
                              det_cfg.get("confidence", 0.4))
    db = Database(args.db or cfg.get("database", {}).get("path", "data/matches.db"))
    match_id = db.add_match(args.team1, args.team2, video_path=str(Path(args.video).resolve()))
    result = process_match(db, match_id, detector, fps=args.fps, court_size_m=(cw, ch),
                           calibration=args.calib, camera_motion=not args.no_camera_motion,
                           max_seconds=args.max_seconds,
                           min_track_seconds=args.min_track_seconds, court_margin_m=args.court_margin, annotate_path=args.annotate)
    players = db.list_match_players(match_id)
    if args.debug:
        d = result["debug"]
        print("\n[DEBUG] kod surumu: kamera-telafili takipci, min_track_seconds=%s" % args.min_track_seconds)
        print(f"[DEBUG] kare={d['frames']}  kare basina ort. tespit={d['avg_detections_per_frame']:.1f}")
        print(f"[DEBUG] kamera hareketi kestirilemeyen kare={d['camera_failed_frames']}")
        print(f"[DEBUG] iz suresi (sn): medyan={d['track_seconds_median']:.1f}  maks={d['track_seconds_max']:.1f}  "
              f">=3sn olan iz={d['tracks_over_3s']}")

    print(f"\nMac #{match_id}: {result['players']} oyuncu izi tutuldu "
          f"({result['tracks_raw']} ham izden), {result['frames_processed']} kare")
    print(f"{'Oyuncu':<14}{'Puan':>6}{'Mesafe(m)':>12}{'Kapsam':>9}")
    for p in players:
        cov = "--" if p["coverage"] is None else f"{p['coverage']:.0%}"
        print(f"{p['player_name']:<14}{p['rating'] if p['rating'] is not None else '--':>6}"
              f"{p['distance_covered']:>12.0f}{cov:>9}")

    if args.annotate:
        print(f"Kontrol videosu: {args.annotate}")
    out = Path("data/exports")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"match_{match_id}.json").write_text(json.dumps(players, indent=2, ensure_ascii=False))
    with open(out / f"match_{match_id}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(players[0]) if players else ["player_id"])
        w.writeheader()
        w.writerows(players)
    print(f"\nDisa aktarim: data/exports/match_{match_id}.json / .csv")
    print("Arayuz icin: python app.py  ->  http://127.0.0.1:5000")


if __name__ == "__main__":
    main()
