#!/usr/bin/env python3
"""
MLB 責失估算 v4 — 跨投手對照為核心，機械校正為輔助
用法:
  python3.11 tools/mlb_run_model.py             → 終端顯示
  python3.11 tools/mlb_run_model.py --js         → 輸出 mlb_data.js
  python3.11 tools/mlb_run_model.py --js > tools/mlb_data.js
"""

import json, sys


def calibrate(starts, today_opp_wins):
    """機械校正：勝場差 ÷ 5（僅供參考）"""
    vals = []
    for s in starts:
        diff = abs(s["wins"] - today_opp_wins)
        adj = diff / 5.0
        if s["wins"] >= today_opp_wins:
            vals.append(round(s["runs"] - adj, 1))
        else:
            vals.append(round(s["runs"] + adj, 1))
    return vals


def find_cross_pitcher_matches(today_starts, ref_starts):
    """
    找出兩組先發紀錄中的共同對手
    today_starts: 今天先發近三場 [{"opp": "費城", "wins": 38, "runs": 1, "venue": "away", "label": "上二場"}, ...]
    ref_starts:   昨天/參考投手近三場
    回傳: [{"opp": "費城", "today_er": 1, "ref_er": 2, "delta": -1, "venue_match": True}, ...]
    """
    matches = []
    for ts in today_starts:
        for rs in ref_starts:
            if ts["opp"] == rs["opp"]:
                matches.append({
                    "opp": ts["opp"],
                    "opp_wins": ts["wins"],
                    "today_er": ts["runs"],
                    "ref_er": rs["runs"],
                    "delta": ts["runs"] - rs["runs"],
                    "today_label": ts.get("label", ""),
                    "ref_label": rs.get("label", ""),
                    "today_venue": ts.get("venue", ""),
                    "ref_venue": rs.get("venue", ""),
                    "venue_match": ts.get("venue") == rs.get("venue"),
                })
    return matches


def is_extreme_last(start, today_venue=None):
    """
    判斷上一場是否大好大壞（市場信號，絕對值）
    大好：≤1 ER → 市場覺得投手正燙
    大壞：≥5 ER → 市場覺得投手爆了
    但如果大壞發生在客場、今天在主場 → 影響度降低
    """
    if start is None:
        return False, None
    runs = start["runs"]
    venue = start.get("venue", "")
    
    if runs <= 1:
        return True, "大好"
    if runs >= 5:
        # 客場大壞 + 今天主場 → 降級為「客場大壞(主場可望回穩)」
        if today_venue == "home" and venue == "away":
            return True, "客場大壞"
        return True, "大壞"
    return False, None


def venue_split(starts):
    """主客場分流：回傳 (home_starts, away_starts, home_avg, away_avg)"""
    home = [s for s in starts if s.get("venue") == "home"]
    away = [s for s in starts if s.get("venue") == "away"]
    home_avg = round(sum(s["runs"] for s in home) / len(home), 1) if home else None
    away_avg = round(sum(s["runs"] for s in away) / len(away), 1) if away else None
    return home, away, home_avg, away_avg


def compute_estimate(yesterday_starter_er, yesterday_bullpen_er, cross_delta, bullpen_adjustment=0):
    """
    今天估失 = 昨天先發對同一對手責失 + 跨投手 delta + 牛棚調整
    """
    starter = yesterday_starter_er + cross_delta
    bullpen = yesterday_bullpen_er + bullpen_adjustment
    return {
        "starter_est": max(starter, 0),
        "bullpen_est": bullpen,
        "total_est": max(starter, 0) + bullpen,
    }


def build_data():
    # ═══════════════ 輸入區 ═══════════════
    # 今天先發（教士 Buehler）
    team_a = {
        "abbr": "SD", "name": "教士", "starter": "Walker Buehler",
        "record": "3-3, 4.33 ERA", "era": 4.33,
        # ── 昨天團隊 ──
        "y_team": 3, "y_starter": 2,  # Vásquez 5.0IP 2ER
        "y_bullpen": 1,                # 牛棚 3.0IP 1ER
        "y_pitcher": "Vásquez",
        "today_venue": "away",         # 今天在客場（@金鶯）
        # ── 今天先發近三場（最新在前） ──
        "starts": [
            {"opp": "紅人",  "wins": 33, "runs": 1, "venue": "home", "label": "上一場"},
            {"opp": "費城",  "wins": 38, "runs": 1, "venue": "away", "label": "上二場"},
            {"opp": "費城",  "wins": 38, "runs": 2, "venue": "home", "label": "上三場"},
        ],
        "today_opp_wins": 34,  # 金鶯
        # ── 參考投手（昨天先發）近三場 ──
        "ref_starts": [
            {"opp": "金鶯",  "wins": 34, "runs": 2, "venue": "away", "label": "昨(今對手)"},
            {"opp": "大都",  "wins": 31, "runs": 4, "venue": "home", "label": "上二場"},
            {"opp": "費城",  "wins": 38, "runs": 2, "venue": "away", "label": "上三場"},
        ],
        "ref_era": 3.63,
        "bullpen_adj": 0,
        "opp_runs_yesterday": 3,
        "opp_runs_note": "金鶯昨得 3（對教士 Vásquez 2ER + 牛棚 1ER）",
    }

    # 今天先發（金鶯 Rogers）
    team_b = {
        "abbr": "BAL", "name": "金鶯", "starter": "Trevor Rogers",
        "record": "3-6, 6.15 ERA", "era": 6.15,
        # ── 昨天團隊 ──
        "y_team": 9, "y_starter": 6,  # Gibson 4.1IP 6ER
        "y_bullpen": 3,                # 牛棚 4.2IP 3ER
        "y_pitcher": "Gibson",
        # ── 今天先發近三場 ──
        "starts": [
            {"opp": "水手",  "wins": 37, "runs": 3, "venue": "home", "label": "上一場"},
            {"opp": "紅襪",  "wins": 29, "runs": 1, "venue": "away", "label": "上二場"},
            {"opp": "藍鳥",  "wins": 34, "runs": 4, "venue": "home", "label": "上三場"},
        ],
        "today_opp_wins": 36,  # 教士
        # ── 參考投手（昨天先發）近三場 ──
        "ref_starts": [
            {"opp": "教士",  "wins": 36, "runs": 6, "venue": "home", "label": "昨(今對手)"},
            {"opp": "水手",  "wins": 37, "runs": 3, "venue": "home", "label": "上二場"},
            {"opp": "光芒",  "wins": 40, "runs": 1, "venue": "home", "label": "上三場"},
        ],
        "ref_era": 4.24,
        "bullpen_adj": 0,
        "opp_runs_yesterday": 9,
        "opp_runs_note": "教士昨得 9（對金鶯 Gibson 6ER + 牛棚 3ER）",
    }

    # ═══════════════ 計算 ═══════════════
    for t in [team_a, team_b]:
        # 機械校正
        vals = calibrate(t["starts"], t["today_opp_wins"])
        t["mech_vals"] = [{"opp": s["opp"], "wins": s["wins"], "runs": s["runs"], "cal": v}
                          for s, v in zip(t["starts"], vals)]
        t["mech_avg"] = round(sum(vals) / len(vals), 1) if vals else 0

        # 標記上一場是否大好大壞（市場信號）
        t_last = t["starts"][0] if t["starts"] else None
        t["last_extreme"], t["last_extreme_dir"] = is_extreme_last(t_last, t.get("today_venue"))
        ref_last = t["ref_starts"][0] if t["ref_starts"] else None
        _, _ = is_extreme_last(ref_last)

        # 主客場分流
        h, a, h_avg, a_avg = venue_split(t["starts"])
        t["venue_home_avg"] = h_avg
        t["venue_away_avg"] = a_avg
        t["venue_split_note"] = ""
        if h_avg is not None and a_avg is not None:
            diff = a_avg - h_avg
            if abs(diff) >= 2:
                t["venue_split_note"] = f"主客場差 {diff:+.1f}（主{a_avg:.1f}/客{h_avg:.1f}）⚠"

        # 跨投手對照：找共同對手
        matches = find_cross_pitcher_matches(t["starts"], t["ref_starts"])
        t["cross_matches"] = matches

        # 最佳配對（優先：場地相同 > 上二場 > 同venue優先）
        # 如果主客場差大 → 場地相同加權更高
        venue_bonus = 5 if t["venue_split_note"] else 3
        best = None
        for m in matches:
            score = 0
            if m["venue_match"]: score += venue_bonus
            # 同venue（跟今天場地一致）
            if m["today_venue"] == t.get("today_venue", ""): score += 2
            if m["ref_venue"] == t.get("today_venue", ""): score += 1
            # 上二場優先（default 策略）
            if "上二" in m["today_label"]: score += 2
            if "上二" in m["ref_label"]: score += 2
            # 上一場大好大壞 → 如果有上一場配對，強制優先
            if t["last_extreme"] and "上一場" in m["today_label"]:
                score += 10
            if best is None or score > best[0]:
                best = (score, m)
        t["best_match"] = best[1] if best else None

        # 如果有配對，用跨投手 delta 計算估失
        if t["best_match"]:
            est = compute_estimate(
                t["y_starter"], t["y_bullpen"],
                t["best_match"]["delta"], t["bullpen_adj"]
            )
        else:
            # 無配對 → 退守機械校正
            est = {
                "starter_est": t["mech_avg"],
                "bullpen_est": t["y_bullpen"] + t["bullpen_adj"],
                "total_est": t["mech_avg"] + t["y_bullpen"] + t["bullpen_adj"],
            }
        t["computed"] = est
        t["starter_est"] = est["starter_est"]
        t["total_lo"] = max(est["total_est"] - 1, 0)
        t["total_hi"] = est["total_est"] + 1

        # 牛棚債
        t["bp_debt"] = t["y_team"] - t["y_starter"]

    # 結論
    diff = team_a["computed"]["total_est"] - team_b["computed"]["total_est"]
    spread_note = f"差距 {abs(diff):.1f} 分"

    return {
        "matchup": f"{team_a['name']} @ {team_b['name']}",
        "pitchers": f"{team_a['starter']} vs {team_b['starter']}",
        "spread_note": spread_note,
        "ref_note": "",
        "extra_note": "",
        "team_a": team_a,
        "team_b": team_b,
    }


def terminal_display(d):
    a, b = d["team_a"], d["team_b"]
    W = 64

    def team_block(t, cls):
        lines = []
        lines.append(f"  {t['name']} ({t['starter']})  {t['record']}")

        # 昨天
        lines.append(f"  昨 {t['y_pitcher']} {t['y_starter']}ER | 牛棚 {t['y_bullpen']}ER | 全隊 {t['y_team']}")

        # 今天先發近況
        lines.append(f"  今天{'主' if t.get('today_venue')=='home' else '客'}場先發近況：")
        for s in t["starts"]:
            venue_tag = " ✓" if s["venue"] == t.get("today_venue", "") else ""
            lines.append(f"    {s['label']} vs {s['opp']}({s['wins']}W) {s['runs']}ER @{s['venue']}{venue_tag}")
        # 主客場分流
        if t["venue_home_avg"] is not None and t["venue_away_avg"] is not None:
            lines.append(f"  主場均 {t['venue_home_avg']}ER / 客場均 {t['venue_away_avg']}ER")
            if t["venue_split_note"]:
                lines.append(f"  ⚡ {t['venue_split_note']}")
        # 上一場大好大壞標記
        if t["last_extreme"]:
            label = t["last_extreme_dir"]
            note = ""
            if label == "客場大壞":
                note = "（今天主場 → 影響降低）"
            lines.append(f"  ⚡ 上一場{label}（{t['starts'][0]['runs']}ER @{t['starts'][0]['venue']}）{note}")

        # 參考投手近況
        lines.append(f"  參考投手({t['y_pitcher']})近況：")
        for s in t["ref_starts"]:
            lines.append(f"    {s['label']} vs {s['opp']}({s['wins']}W) {s['runs']}ER @{s['venue']}")

        # 共同對手配對
        if t["cross_matches"]:
            lines.append(f"  跨投手對照（共同對手）：")
            for m in t["cross_matches"]:
                venue_ok = "✓同場地" if m["venue_match"] else "⚠場地不同"
                lines.append(f"    {m['opp']}({m['opp_wins']}W) → {t['y_pitcher']} {m['ref_er']}ER / {t['starter'].split()[-1]} {m['today_er']}ER  delta={m['delta']:+d} {venue_ok}")
        else:
            lines.append(f"  ⚠ 無共同對手，退守機械校正")

        # 選用哪一場
        if t["best_match"]:
            m = t["best_match"]
            lines.append(f"  → 選用：{m['opp']}({m['today_label']}/{m['ref_label']}) delta={m['delta']:+d}")
        if t["last_extreme"]:
            lines.append(f"  ⚡ 上一場{t['last_extreme_dir']}（{t['starts'][0]['runs']}ER），若上一場有共同對手應優先採用")

        # 計算
        est = t["computed"]
        lines.append(f"  機械校正平均: {t['mech_avg']}")
        lines.append(f"  跨投手估失: 先發 {est['starter_est']} + 牛棚 {est['bullpen_est']} = {est['total_est']}")
        return lines

    print("═" * W)
    print(f"  ⚾  {d['matchup']}  —  兩日責失對照")
    print(f"  {d['pitchers']}")
    print("═" * W)

    a_lines = team_block(a, "mia")
    b_lines = team_block(b, "pit")

    for i in range(max(len(a_lines), len(b_lines))):
        left = a_lines[i] if i < len(a_lines) else ""
        right = b_lines[i] if i < len(b_lines) else ""
        print(f"{left:<40s} │ {right}")

    print("─" * W)
    print(f"  結論：教士估失 {a['total_lo']}-{a['total_hi']} | 金鶯估失 {b['total_lo']}-{b['total_hi']}")
    print(f"  {d['spread_note']}")
    print("═" * W)


if __name__ == "__main__":
    d = build_data()
    if "--js" in sys.argv:
        print("// MLB 責失估算數據 — 由 mlb_run_model.py 自動產生")
        print(f"window.MLB_DATA = {json.dumps(d, ensure_ascii=False, indent=2)};")
    else:
        terminal_display(d)
