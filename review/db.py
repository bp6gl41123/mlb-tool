#!/usr/bin/env python3
"""
智能預測系統 v4 — 從零開始，僅用個人棒球知識與數據
核心原理: 預測得分 → 比較 → 學習誤差模式
v4: init() 改用 CREATE TABLE IF NOT EXISTS，永不刪資料
"""
import sqlite3, os, json
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_predict.db")

def init():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_date TEXT, matchup TEXT,
            away_team TEXT, home_team TEXT,
            away_sp TEXT, home_sp TEXT,
            away_sp_era REAL, home_sp_era REAL,
            away_runs_pred REAL, home_runs_pred REAL,
            away_runs_actual REAL, home_runs_actual REAL,
            spread_pred REAL, spread_actual REAL,
            error_margin REAL,
            factors_used TEXT,
            notes TEXT,
            created TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            error_type TEXT,
            error_value REAL,
            context TEXT
        );
        
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight TEXT,
            confidence REAL,
            evidence_count INTEGER,
            discovered TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def save_game(data):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""INSERT INTO games 
        (game_date,matchup,away_team,home_team,away_sp,home_sp,
         away_sp_era,home_sp_era,away_runs_pred,home_runs_pred,
         away_runs_actual,home_runs_actual,spread_pred,spread_actual,
         error_margin,factors_used,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data.get('game_date'), data.get('matchup'), data.get('away_team'), data.get('home_team'),
         data.get('away_sp'), data.get('home_sp'), data.get('away_sp_era'), data.get('home_sp_era'),
         data.get('away_runs_pred'), data.get('home_runs_pred'),
         data.get('away_runs_actual'), data.get('home_runs_actual'),
         data.get('spread_pred'), data.get('spread_actual'),
         data.get('error_margin'), json.dumps(data.get('factors_used',[])), data.get('notes')))
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid

def update_result(game_id, away_runs, home_runs):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT away_runs_pred, home_runs_pred FROM games WHERE id=?", (game_id,))
    row = cur.fetchone()
    if row:
        pred_away, pred_home = row
        spread_pred = pred_away - pred_home
        spread_actual = away_runs - home_runs
        error = abs(spread_pred - spread_actual)
        cur.execute("""UPDATE games SET 
            away_runs_actual=?, home_runs_actual=?, 
            spread_actual=?, error_margin=? WHERE id=?""",
            (away_runs, home_runs, spread_actual, error, game_id))
    conn.commit()
    conn.close()
    return error if row else None

def get_stats():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # 排除賽前換投場次
    cur.execute("SELECT COUNT(*), AVG(error_margin) FROM games WHERE error_margin IS NOT NULL AND (notes IS NULL OR notes NOT LIKE '%換投%')")
    total, avg_err = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM games WHERE spread_pred * spread_actual > 0 AND spread_actual IS NOT NULL AND spread_pred IS NOT NULL AND (notes IS NULL OR notes NOT LIKE '%換投%')")
    correct_spread = cur.fetchone()[0]
    conn.close()
    return {
        "total_games": total or 0,
        "avg_error": round(avg_err, 2) if avg_err else 0,
        "spread_direction_correct": correct_spread or 0,
        "spread_accuracy": round(correct_spread/total*100, 1) if total else 0
    }

def save_insight(insight, confidence, evidence):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO insights (insight, confidence, evidence_count) VALUES (?,?,?)",
                (insight, confidence, evidence))
    conn.commit()
    conn.close()

def get_insights():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT * FROM insights ORDER BY confidence DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_error_patterns():
    """找出預測誤差最大的模式"""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT matchup, away_sp_era, home_sp_era, spread_pred, spread_actual, error_margin, factors_used
        FROM games WHERE error_margin IS NOT NULL AND (notes IS NULL OR notes NOT LIKE '%換投%')
        ORDER BY error_margin DESC LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init()
    print("v2 資料庫已重置")
    print(get_stats())
