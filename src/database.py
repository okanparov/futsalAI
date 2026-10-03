"""SQLite operations."""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY, date TIMESTAMP, team1 TEXT, team2 TEXT,
    venue TEXT, video_path TEXT, processed BOOLEAN DEFAULT 0);
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY, match_id INTEGER, team_id INTEGER, player_name TEXT,
    position TEXT, jersey_number INTEGER, player_color TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(id));
CREATE TABLE IF NOT EXISTS detections (
    id INTEGER PRIMARY KEY, frame_id INTEGER, player_id INTEGER,
    bbox_x REAL, bbox_y REAL, confidence REAL, timestamp REAL);
CREATE TABLE IF NOT EXISTS match_stats (
    id INTEGER PRIMARY KEY, match_id INTEGER, player_id INTEGER,
    distance_covered REAL, pass_attempts INTEGER, pass_success INTEGER,
    ball_touches INTEGER, tackles INTEGER, interceptions INTEGER, rating REAL);
"""


class Database:
    def __init__(self, path="data/matches.db"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def add_match(self, team1, team2, venue="", video_path="", date=None):
        cur = self.conn.execute(
            "INSERT INTO matches (date, team1, team2, venue, video_path) "
            "VALUES (COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?)",
            (date, team1, team2, venue, video_path))
        self.conn.commit()
        return cur.lastrowid

    def get_match(self, match_id):
        row = self.conn.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
        return dict(row) if row else None

    def mark_processed(self, match_id):
        self.conn.execute("UPDATE matches SET processed=1 WHERE id=?", (match_id,))
        self.conn.commit()

    def add_detections(self, rows):
        """rows: iterable of (frame_id, player_id, bbox_x, bbox_y, confidence, timestamp)."""
        self.conn.executemany(
            "INSERT INTO detections (frame_id, player_id, bbox_x, bbox_y, confidence, timestamp) "
            "VALUES (?,?,?,?,?,?)", rows)
        self.conn.commit()

    def get_player_stats(self, player_id):
        row = self.conn.execute(
            "SELECT * FROM match_stats WHERE player_id=?", (player_id,)).fetchone()
        return dict(row) if row else None

    def get_ratings(self, match_id):
        rows = self.conn.execute(
            "SELECT player_id, rating FROM match_stats WHERE match_id=?", (match_id,)).fetchall()
        return [dict(r) for r in rows]

    def list_matches(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM matches ORDER BY id DESC")]

    def add_player(self, match_id, name, team_id=None, position=None):
        cur = self.conn.execute(
            "INSERT INTO players (match_id, team_id, player_name, position) VALUES (?,?,?,?)",
            (match_id, team_id, name, position))
        self.conn.commit()
        return cur.lastrowid

    def save_match_stats(self, match_id, player_id, distance_covered, rating):
        self.conn.execute(
            "INSERT INTO match_stats (match_id, player_id, distance_covered, rating) VALUES (?,?,?,?)",
            (match_id, player_id, distance_covered, rating))
        self.conn.commit()
