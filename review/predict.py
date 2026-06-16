#!/usr/bin/env python3
"""
智能預測引擎 v4 — 2026-06-16 全15場
"""
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init, save_game, get_stats

TEAMS = {
    "ARI":{"era":4.19,"ops":.689},"ATL":{"era":3.29,"ops":.749},"BAL":{"era":4.59,"ops":.728},
    "BOS":{"era":3.91,"ops":.697},"CHC":{"era":4.23,"ops":.727},"CIN":{"era":4.68,"ops":.704},
    "CLE":{"era":3.75,"ops":.689},"COL":{"era":5.64,"ops":.715},"CWS":{"era":4.29,"ops":.735},
    "DET":{"era":3.94,"ops":.705},"HOU":{"era":4.91,"ops":.733},"KC":{"era":4.44,"ops":.695},
    "LAA":{"era":4.62,"ops":.708},"LAD":{"era":3.37,"ops":.788},"MIA":{"era":4.07,"ops":.705},
    "MIL":{"era":3.45,"ops":.733},"MIN":{"era":4.86,"ops":.714},"NYM":{"era":3.85,"ops":.660},
    "NYY":{"era":3.32,"ops":.760},"OAK":{"era":4.85,"ops":.741},"PHI":{"era":4.11,"ops":.687},
    "PIT":{"era":4.22,"ops":.738},"SD":{"era":3.91,"ops":.658},"SEA":{"era":3.69,"ops":.718},
    "SF":{"era":4.52,"ops":.725},"STL":{"era":4.15,"ops":.724},"TB":{"era":3.95,"ops":.716},
    "TEX":{"era":3.79,"ops":.697},"TOR":{"era":4.12,"ops":.701},"WSH":{"era":4.66,"ops":.740},
}

PARK = {"COL":1.35,"CIN":1.10,"BOS":1.08,"ARI":1.06,"TEX":1.05,
        "LAD":0.95,"SF":0.90,"SEA":0.88,"SD":0.92,"NYM":0.93,
        "STL":0.97,"MIA":0.96,"TB":0.94,"OAK":0.95,"ATH":0.95}

MATCHUPS = [
    ("MIA","PHI","Tyler Phillips","Jesus Luzardo"),
    ("KC","WSH","Michael Wacha","Foster Griffin"),
    ("TOR","BOS","Dylan Cease","Payton Tolle"),
    ("CWS","NYY","Davis Martin","Gerrit Cole"),
    ("NYM","CIN","Kodai Senga","Brady Singer"),
    ("SF","ATL","Adrian Houser","Grant Holmes"),
    ("CLE","MIL","Slade Cecconi","Robert Gasser"),
    ("SD","STL","Michael King","Andre Pallante"),
    ("MIN","TEX","Zebby Matthews","Kumar Rocker"),
    ("COL","CHC","Ryan Feltner","Edward Cabrera"),
    ("DET","HOU","Framber Valdez","Hunter Brown"),
    ("PIT","ATH","Mitch Keller","Jack Perkins"),
    ("BAL","SEA","Brandon Young","Logan Gilbert"),
    ("LAA","ARI","Reid Detmers","Merrill Kelly"),
    ("TB","LAD","Drew Rasmussen","Justin Wrobleski"),
]

SP_ERA = {
    "Tyler Phillips":1.97,"Jesus Luzardo":4.52,"Michael Wacha":3.61,"Foster Griffin":3.97,
    "Dylan Cease":2.98,"Payton Tolle":3.10,"Davis Martin":2.98,"Gerrit Cole":2.55,
    "Kodai Senga":9.00,"Brady Singer":5.76,"Adrian Houser":5.91,"Grant Holmes":4.19,
    "Slade Cecconi":4.96,"Robert Gasser":6.46,"Michael King":3.56,"Andre Pallante":3.95,
    "Zebby Matthews":5.24,"Kumar Rocker":3.69,"Ryan Feltner":5.35,"Edward Cabrera":5.06,
    "Framber Valdez":4.48,"Hunter Brown":1.79,"Mitch Keller":5.14,"Jack Perkins":6.25,
    "Brandon Young":3.19,"Logan Gilbert":3.71,"Reid Detmers":4.17,"Merrill Kelly":5.54,
    "Drew Rasmussen":2.74,"Justin Wrobleski":2.99,
}

LEAGUE_ERA = 4.20
LEAGUE_OPS = .720

def predict_runs(batting, pitching, sp_name, is_home):
    bt = TEAMS.get(batting)
    pt = TEAMS.get(pitching)
    if not bt or not pt: return 4.0
    
    runs = 4.3
    runs += (pt['era'] - LEAGUE_ERA) * 0.6
    
    sp_era = SP_ERA.get(sp_name, LEAGUE_ERA)
    if isinstance(sp_era, tuple):
        era = sp_era[1] if not is_home else sp_era[2]
    else:
        era = sp_era
    runs += (era - LEAGUE_ERA) * 0.4
    
    runs += (bt['ops'] - LEAGUE_OPS) * 8
    
    park = PARK.get(pitching if is_home else batting, 1.0)
    runs *= park
    
    if is_home:
        runs += 0.5
    
    return round(max(runs, 1.0), 1)

def main():
    init()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print("智能預測 v4 — 2026-06-16 全15場")
    print(f"{'='*65}")
    print(f"{'對戰':18s} {'預測':>10s} {'讓分':>6s} {'總分':>5s} {'大小':>4s}")
    print(f"{'-'*65}")
    
    for away, home, ap, hp in MATCHUPS:
        away_r = predict_runs(away, home, hp, False)
        home_r = predict_runs(home, away, ap, True)
        spread = away_r - home_r
        winner = away if spread > 0 else home
        total = away_r + home_r
        ou = "大" if total > 8.5 else "小"
        diff = abs(spread)
        
        save_game({
            'game_date': today, 'matchup': f"{away} @ {home}",
            'away_team': away, 'home_team': home,
            'away_sp': ap, 'home_sp': hp,
            'away_sp_era': SP_ERA.get(ap, 0) if not isinstance(SP_ERA.get(ap, 0), tuple) else SP_ERA[ap][0],
            'home_sp_era': SP_ERA.get(hp, 0) if not isinstance(SP_ERA.get(hp, 0), tuple) else SP_ERA[hp][0],
            'away_runs_pred': away_r, 'home_runs_pred': home_r,
            'spread_pred': spread,
            'factors_used': ['TEAM_ERA','TEAM_OPS','SP_ERA','PARK','HOME'],
            'notes': f"估總分{total:.0f}"
        })
        
        fav = home if spread < 0 else away
        fav_r = home_r if spread < 0 else away_r
        dog_r = away_r if spread < 0 else home_r
        line = f"{fav}+{diff:.1f}"
        
        print(f"  {away} @ {home:4s}  {away_r}-{home_r:>4}  {winner}+{diff:.1f}  {total:.0f}   {ou}")
    
    stats = get_stats()
    if stats['total_games']:
        print(f"\n歷史: {stats['total_games']}場 | 方向: {stats['spread_accuracy']}% | 均誤: {stats['avg_error']}分")

if __name__ == "__main__":
    main()
