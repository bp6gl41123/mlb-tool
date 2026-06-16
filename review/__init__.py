#!/usr/bin/env python3
"""
智能預測系統 v1 — 獨立於 MLB 工具，自成一套
├── predict:  每日預測（先發對比 + 後期影響 + 強弱轉換）
├── review:   賽後覆盤（預測 vs 實際 → 死因分類）
├── learn:    規律提取（從錯誤中學模式）
├── db:       獨立 SQLite 資料庫

用法:
  python3.11 review/predict.py            → 今日預測
  python3.11 review/review.py 2026-06-14  → 覆盤指定日
  python3.11 review/learn.py              → 從歷史學規律
"""
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "smart_predict.db")
