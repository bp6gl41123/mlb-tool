"""
MLB Database Manager — SQLite backend for pitcher game logs and daily matchups.

Schema:
  pitchers     — unique pitcher registry (lottonavi ID as primary key)
  game_logs    — every regular-season appearance by any registered pitcher
  daily_matchups — per-game matchup data for prediction model input
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlb_data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pitchers (
    id          TEXT PRIMARY KEY,          -- lottonavi player ID (permanent, unique)
    name_en     TEXT NOT NULL,             -- English name (e.g. "Max Meyer")
    name_zh     TEXT,                      -- Chinese name (e.g. "梅耶爾")
    team        TEXT,                      -- current team abbreviation
    throws      TEXT,                      -- 'R' or 'L'
    first_seen  TEXT NOT NULL DEFAULT (date('now')),
    last_seen   TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS game_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pitcher_id  TEXT NOT NULL REFERENCES pitchers(id),
    game_date   TEXT NOT NULL,             -- ISO date YYYY-MM-DD
    opponent    TEXT NOT NULL,             -- opponent team abbreviation
    home_away   TEXT NOT NULL CHECK(home_away IN ('home','away')),
    innings     REAL,                      -- IP (e.g. 5.1)
    pitches     INTEGER,                   -- total pitches thrown
    hits        INTEGER,
    runs        INTEGER,
    earned_runs INTEGER,
    homers      INTEGER,
    walks       INTEGER,
    strikeouts  INTEGER,
    win         INTEGER DEFAULT 0,
    loss        INTEGER DEFAULT 0,
    save_val    INTEGER DEFAULT 0,
    era_after   REAL,                      -- ERA after this game
    team_score  INTEGER,                   -- pitcher's team runs scored
    opp_score   INTEGER,                   -- opponent runs scored
    is_regular  INTEGER DEFAULT 1,         -- 1=regular season, 0=spring training
    source_url  TEXT,                      -- lottonavi boxscore URL for traceability
    inserted_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(pitcher_id, game_date)
);

CREATE TABLE IF NOT EXISTS daily_matchups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_date       TEXT NOT NULL,
    away_team       TEXT NOT NULL,
    home_team       TEXT NOT NULL,
    away_starter_id TEXT REFERENCES pitchers(id),
    home_starter_id TEXT REFERENCES pitchers(id),
    line            TEXT,                   -- 亞洲讓分 (e.g. "1-05 讓1.5")
    total           REAL,                   -- 大小分
    away_score      INTEGER,
    home_score      INTEGER,
    away_starter_er INTEGER,
    home_starter_er INTEGER,
    status          TEXT DEFAULT 'scheduled',  -- scheduled|in_progress|final
    notes           TEXT,
    UNIQUE(game_date, away_team, home_team)
);

CREATE INDEX IF NOT EXISTS idx_game_logs_pitcher_date ON game_logs(pitcher_id, game_date DESC);
CREATE INDEX IF NOT EXISTS idx_game_logs_date ON game_logs(game_date DESC);
CREATE INDEX IF NOT EXISTS idx_game_logs_opponent ON game_logs(opponent);
CREATE INDEX IF NOT EXISTS idx_matchups_date ON daily_matchups(game_date DESC);
"""


@contextmanager
def get_db():
    """Get a database connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema if not exists."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
    print(f"Database initialized: {DB_PATH}")


# ── Pitcher CRUD ──────────────────────────────────────────────

def register_pitcher(pitcher_id: str, name_en: str, name_zh: str = None,
                     team: str = None, throws: str = None) -> bool:
    """
    Register a new pitcher. Returns True if inserted, False if already exists.
    Always updates last_seen date.
    """
    with get_db() as conn:
        cur = conn.execute("SELECT id FROM pitchers WHERE id = ?", (pitcher_id,))
        exists = cur.fetchone()
        if exists:
            conn.execute(
                "UPDATE pitchers SET last_seen = date('now'), team = COALESCE(?, team) WHERE id = ?",
                (team, pitcher_id)
            )
            return False
        conn.execute(
            """INSERT INTO pitchers (id, name_en, name_zh, team, throws)
               VALUES (?, ?, ?, ?, ?)""",
            (pitcher_id, name_en, name_zh, team, throws)
        )
        return True


def find_pitcher_by_name(name_en: str) -> list:
    """Search pitchers by English name (fuzzy)."""
    with get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM pitchers WHERE name_en LIKE ?",
            (f"%{name_en}%",)
        )
        return [dict(r) for r in cur.fetchall()]


def get_pitcher(pitcher_id: str) -> dict | None:
    """Get a single pitcher by ID."""
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM pitchers WHERE id = ?", (pitcher_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_pitchers(team: str = None) -> list:
    """List all pitchers, optionally filtered by team."""
    with get_db() as conn:
        if team:
            cur = conn.execute("SELECT * FROM pitchers WHERE team = ? ORDER BY name_en", (team,))
        else:
            cur = conn.execute("SELECT * FROM pitchers ORDER BY name_en")
        return [dict(r) for r in cur.fetchall()]


def get_pitcher_count() -> int:
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM pitchers").fetchone()[0]


# ── Game Log CRUD ─────────────────────────────────────────────

def insert_game_log(pitcher_id: str, game_date: str, opponent: str,
                    home_away: str, innings: float = None, pitches: int = None,
                    hits: int = None, runs: int = None, earned_runs: int = None,
                    homers: int = None, walks: int = None, strikeouts: int = None,
                    win: int = 0, loss: int = 0, save_val: int = 0,
                    era_after: float = None, team_score: int = None,
                    opp_score: int = None, is_regular: int = 1,
                    source_url: str = None) -> bool:
    """
    Insert a game log entry. Returns True if inserted, False if duplicate (same pitcher+date).
    Uses INSERT OR IGNORE to handle duplicates gracefully.
    """
    with get_db() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO game_logs
               (pitcher_id, game_date, opponent, home_away, innings, pitches,
                hits, runs, earned_runs, homers, walks, strikeouts,
                win, loss, save_val, era_after, team_score, opp_score,
                is_regular, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pitcher_id, game_date, opponent, home_away, innings, pitches,
             hits, runs, earned_runs, homers, walks, strikeouts,
             win, loss, save_val, era_after, team_score, opp_score,
             is_regular, source_url)
        )
        return cur.rowcount > 0


def update_game_result(pitcher_id: str, game_date: str,
                       earned_runs: int, innings: float = None,
                       team_score: int = None, opp_score: int = None) -> bool:
    """Update a game log after the game is played. Used in daily update flow."""
    with get_db() as conn:
        fields = ["earned_runs = ?"]
        params = [earned_runs]
        if innings is not None:
            fields.append("innings = ?")
            params.append(innings)
        if team_score is not None:
            fields.append("team_score = ?")
            params.append(team_score)
        if opp_score is not None:
            fields.append("opp_score = ?")
            params.append(opp_score)
        params.extend([pitcher_id, game_date])
        cur = conn.execute(
            f"UPDATE game_logs SET {', '.join(fields)} WHERE pitcher_id = ? AND game_date = ?",
            params
        )
        return cur.rowcount > 0


def get_recent_starts(pitcher_id: str, limit: int = 5) -> list:
    """Get the most recent regular-season starts for a pitcher."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT * FROM game_logs
               WHERE pitcher_id = ? AND is_regular = 1
               ORDER BY game_date DESC LIMIT ?""",
            (pitcher_id, limit)
        )
        return [dict(r) for r in cur.fetchall()]


def get_pitcher_season_stats(pitcher_id: str) -> dict:
    """Get aggregated season stats for a pitcher (regular season only)."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT
                 COUNT(*) as games,
                 SUM(win) as wins,
                 SUM(loss) as losses,
                 ROUND(SUM(innings), 1) as total_ip,
                 SUM(hits) as total_h,
                 SUM(runs) as total_r,
                 SUM(earned_runs) as total_er,
                 SUM(homers) as total_hr,
                 SUM(walks) as total_bb,
                 SUM(strikeouts) as total_k
               FROM game_logs
               WHERE pitcher_id = ? AND is_regular = 1""",
            (pitcher_id,)
        )
        row = cur.fetchone()
        if not row or not row["games"]:
            return {}
        d = dict(row)
        if d["total_ip"] and d["total_er"] is not None and d["total_ip"] > 0:
            d["era"] = round((d["total_er"] * 9) / d["total_ip"], 2)
        else:
            d["era"] = None
        return d


# ── Matchup CRUD ──────────────────────────────────────────────

def upsert_matchup(game_date: str, away_team: str, home_team: str,
                   away_starter_id: str = None, home_starter_id: str = None,
                   line: str = None, total: float = None,
                   status: str = 'scheduled', notes: str = None) -> None:
    """Create or update a daily matchup."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO daily_matchups
               (game_date, away_team, home_team, away_starter_id, home_starter_id,
                line, total, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(game_date, away_team, home_team) DO UPDATE SET
               away_starter_id = COALESCE(excluded.away_starter_id, daily_matchups.away_starter_id),
               home_starter_id = COALESCE(excluded.home_starter_id, daily_matchups.home_starter_id),
               line = COALESCE(excluded.line, daily_matchups.line),
               total = COALESCE(excluded.total, daily_matchups.total),
               status = COALESCE(excluded.status, daily_matchups.status),
               notes = COALESCE(excluded.notes, daily_matchups.notes)""",
            (game_date, away_team, home_team, away_starter_id, home_starter_id,
             line, total, status, notes)
        )


def get_matchups_by_date(game_date: str) -> list:
    """Get all matchups for a given date."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT m.*, a.name_en as away_starter_name, h.name_en as home_starter_name
               FROM daily_matchups m
               LEFT JOIN pitchers a ON m.away_starter_id = a.id
               LEFT JOIN pitchers h ON m.home_starter_id = h.id
               WHERE m.game_date = ?
               ORDER BY m.id""",
            (game_date,)
        )
        return [dict(r) for r in cur.fetchall()]


# ── Cross-Pitcher Queries (for prediction model) ───────────────

def find_common_opponents(pitcher_a_id: str, pitcher_b_id: str) -> list:
    """Find common opponents between two pitchers. Returns paired game logs."""
    with get_db() as conn:
        cur = conn.execute(
            """SELECT a.game_date as date_a, b.game_date as date_b,
                      a.opponent, a.home_away as venue_a, b.home_away as venue_b,
                      a.earned_runs as er_a, b.earned_runs as er_b,
                      a.innings as ip_a, b.innings as ip_b
               FROM game_logs a
               JOIN game_logs b ON a.opponent = b.opponent
               WHERE a.pitcher_id = ? AND b.pitcher_id = ?
                 AND a.is_regular = 1 AND b.is_regular = 1
               ORDER BY a.game_date DESC""",
            (pitcher_a_id, pitcher_b_id)
        )
        return [dict(r) for r in cur.fetchall()]


# ── Stats ─────────────────────────────────────────────────────

def get_db_stats() -> dict:
    """Return summary stats for the database."""
    with get_db() as conn:
        pitchers = conn.execute("SELECT COUNT(*) FROM pitchers").fetchone()[0]
        games = conn.execute("SELECT COUNT(*) FROM game_logs").fetchone()[0]
        regular = conn.execute(
            "SELECT COUNT(*) FROM game_logs WHERE is_regular = 1"
        ).fetchone()[0]
        matchups = conn.execute("SELECT COUNT(*) FROM daily_matchups").fetchone()[0]
        date_range = conn.execute(
            "SELECT MIN(game_date), MAX(game_date) FROM game_logs WHERE is_regular = 1"
        ).fetchone()
        return {
            "pitchers": pitchers,
            "total_game_logs": games,
            "regular_season_logs": regular,
            "matchups": matchups,
            "date_range": f"{date_range[0]} → {date_range[1]}" if date_range[0] else "N/A",
        }


if __name__ == "__main__":
    init_db()
    stats = get_db_stats()
    print(f"\n📊 DB Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
