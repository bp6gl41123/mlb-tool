#!/usr/bin/env python3
"""MLB 兩日投手對照工具 — 計算合理盤口偏離值

資料來源：VIP 預測端 (盤口+先發) + lottonavi (陣容)
用法：python3.11 tools/mlb_pitcher_diff.py
"""

import json
import ssl
import urllib.request
from datetime import datetime

VIP_API = "https://script.google.com/macros/s/AKfycbxQS5sbzVYvfgcTKQnvOhIbcn94Js16pel-l1zPP8_3SRIgA8dZVAcigM9J1TMldH7g/exec?action=getData"


def fetch_vip_games() -> list[dict]:
    """從 VIP 預測端拉 MLB 賽程"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = VIP_API + "&t=" + str(int(datetime.now().timestamp()))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.loads(resp.read())
    inner = json.loads(data["data"])
    return [g for g in inner.get("games", [])
            if g.get("sport") == "mlb" and not g.get("locked")]


def asian_to_am(spread: str) -> float:
    """亞洲讓分(1+50/1平/2+100) → 美式賠率(-125/-150/-200)"""
    s = spread.strip()
    if s == "PK" or s == "1平":
        return -150.0
    is_under = s.startswith("受讓")
    s = s.replace("受讓", "")
    # 解析 1+50, 1-50, 2+100, 2-36
    if "+" in s:
        base_str, juice_str = s.split("+")
        base = float(base_str)
        juice = float(juice_str)
        am = -(150 if base == 1 else 200) + juice / 2
    elif "-" in s:
        base_str, juice_str = s.split("-")
        base = float(base_str)
        juice = float(juice_str)
        am = -(150 if base == 1 else 200) - juice / 2
    else:
        return -150.0
    return am if not is_under else -am


def am_to_asian(am: float) -> str:
    """美式賠率 → 亞洲讓分"""
    if abs(am) <= 110:
        return "PK"
    if am < 0:
        a = abs(am)
    else:
        return f"受讓{am_to_asian(-am)}"

    if a >= 200:
        base = 2
        ref = 200
    else:
        base = 1
        ref = 150

    diff = a - ref
    if diff >= 0:
        return f"{base}-{int(diff * 2)}"
    else:
        juice = int(50 + abs(diff) * 2)
        return f"{base}+{juice}"


def parse_era(stats: str) -> float | None:
    """從 '6-0(2.85)' 格式抽出 ERA"""
    try:
        return float(stats.split("(")[1].rstrip(")"))
    except (IndexError, ValueError):
        return None


def main():
    print("=" * 62)
    print("  ⚾ MLB 兩日投手對照．合理盤口估算")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  來源：VIP預測端")
    print("=" * 62)

    games = fetch_vip_games()
    if not games:
        print("  ❌ 無 MLB 賽程資料")
        return

    print(f"\n  📋 共 {len(games)} 場\n")

    for g in games:
        away = g.get("away", "?")
        home = g.get("home", "?")
        t = g.get("gametime", "?:??")
        spread = g.get("spread", "?")
        total = g.get("total", "?")
        p_away = g.get("pitcherAway", "?")
        p_home = g.get("pitcherHome", "?")
        s_away = g.get("pitcherAwayStats", "?")
        s_home = g.get("pitcherHomeStats", "?")

        era_a = parse_era(s_away)
        era_h = parse_era(s_home)

        # ── 模型推估 ──
        est = None
        if era_a and era_h:
            diff_era = era_h - era_a  # 正值 = 主隊ERA較差
            est_am = -150 + diff_era * 25
            est = am_to_asian(est_am)

        # ── 偏離 ──
        dev = ""
        if est and spread and spread != "尚未開盤":
            try:
                actual_am = asian_to_am(spread)
                est_am = asian_to_am(est)
                gap = actual_am - est_am
                if abs(gap) > 30:
                    direction = "輕讓" if gap > 0 else "深讓"
                    dev = f" ⚠️ 偏離{gap:+.0f}點→{direction}"
                else:
                    dev = " ✓"
            except Exception:
                dev = ""

        # ── 輸出 ──
        print(f"  {t}  {away} @ {home}")
        print(f"    先發: {p_away} {s_away}  vs  {p_home} {s_home}")
        print(f"    實際: {spread}  大小{total}  |  模型: {est or 'N/A'}{dev}")
        print()

    print("=" * 62)
    print("  備註：建議搭配昨日box score取得前日責失")
    print("        公式：era_h - era_a 每差1分 ≒ 讓分±25美式點")
    print("=" * 62)


if __name__ == "__main__":
    main()
