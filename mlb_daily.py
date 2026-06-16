"""
MLB Daily Update — Pre-game pitcher registration + Post-game result updates.

Usage:
  python3.11 tools/mlb_daily.py pre     # Fetch today's starters, register, create matchups
  python3.11 tools/mlb_daily.py post    # Update today's games with actual results
"""

import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))

from mlb_db import (
    init_db, register_pitcher, get_pitcher, find_pitcher_by_name,
    insert_game_log, update_game_result, upsert_matchup,
    get_matchups_by_date, get_db_stats, get_pitcher_count
)
from datetime import date, timedelta


# ── Team slug mapping ─────────────────────────────────────────

TEAM_SLUG_MAP = {
    "arizona-diamondbacks": "ARI", "atlanta-braves": "ATL",
    "baltimore-orioles": "BAL", "boston-red-sox": "BOS",
    "chicago-cubs": "CHC", "cincinnati-reds": "CIN",
    "cleveland-guardians": "CLE", "colorado-rockies": "COL",
    "chicago-white-sox": "CWS", "detroit-tigers": "DET",
    "houston-astros": "HOU", "kansas-city-royals": "KC",
    "los-angeles-angels": "LAA", "los-angeles-dodgers": "LAD",
    "miami-marlins": "MIA", "milwaukee-brewers": "MIL",
    "minnesota-twins": "MIN", "new-york-mets": "NYM",
    "new-york-yankees": "NYY", "oakland-athletics": "OAK",
    "philadelphia-phillies": "PHI", "pittsburgh-pirates": "PIT",
    "san-diego-padres": "SD", "seattle-mariners": "SEA",
    "san-francisco-giants": "SF", "st.-louis-cardinals": "STL",
    "tampa-bay-rays": "TB", "texas-rangers": "TEX",
    "toronto-blue-jays": "TOR", "washington-nationals": "WSH",
}


def fetch_lineups_html():
    """Fetch today's lineups page HTML."""
    import subprocess
    import tempfile
    fpath = os.path.join(tempfile.gettempdir(), 'lineups_today.html')
    subprocess.run(
        ['curl', '-s', '-L', '-m', '15',
         'https://lottonavi.com/lineups/mlb/', '-o', fpath],
        check=False
    )
    with open(fpath, 'rb') as f:
        return f.read().decode('utf-8', errors='replace')


def parse_starters_from_html(html):
    """
    Parse starting pitchers from lottonavi lineups HTML.
    Returns list of dicts: {id, name_en, name_zh, throws}
    """
    # Pattern: <span>表定先發</span>...<a title="EN" href="...player/mlb/ID/slug/">ZH</a>...(R/L)
    pattern = r'表定先發</span>[^<]*<a title="([^"]+)"[^>]*player/mlb/(\d+)/([^/"]+)/"[^>]*>([^<]+)</a>[^)]*\((\w+)\)'
    matches = re.findall(pattern, html)
    
    starters = []
    for name_en, pid, slug, name_zh, throws_raw in matches:
        throws = 'R' if '右' in throws_raw else 'L'
        starters.append({
            'id': pid,
            'name_en': name_en,
            'name_zh': name_zh,
            'throws': throws,
        })
    return starters


def parse_matchups_from_html(html):
    """
    Parse game matchups from lineups HTML.
    Returns list of dicts: {away_team, home_team, away_starter_id, home_starter_id}
    Matches starters to teams by proximity in HTML.
    """
    # Find team sections with their starters
    # Each game block has: team names + two 表定先發 entries
    # Strategy: split by 表定先發, then look backward for team context
    
    matchups = []
    blocks = html.split('表定先發')
    
    # Collect all starter entries with positions
    starter_positions = []
    for m in re.finditer(r'表定先發</span>[^<]*<a title="([^"]+)"[^>]*player/mlb/(\d+)/', html):
        starter_positions.append({
            'pos': m.start(),
            'pid': m.group(2),
            'name_en': m.group(1),
        })
    
    # Find team names in the HTML near each starter
    # Team names appear in <a> tags with team/mlb/ URLs
    team_links = list(re.finditer(r'team/mlb/([^/"]+)"[^>]*>([^<]+)</a>', html))
    
    # For each pair of starters, find the closest team names
    for i in range(0, len(starter_positions) - 1, 2):
        away_starter = starter_positions[i]
        home_starter = starter_positions[i + 1]
        
        # Find team names closest to these starters
        away_team = home_team = None
        away_slug = home_slug = None
        
        for tm in team_links:
            slug = tm.group(1)
            name = tm.group(2)
            abbr = TEAM_SLUG_MAP.get(slug, slug[:3].upper())
            
            # Assign based on proximity
            dist_away = abs(tm.start() - away_starter['pos'])
            dist_home = abs(tm.start() - home_starter['pos'])
            
            if dist_away < 1500 and (away_slug is None or dist_away < abs(tm.start() - away_starter['pos'])):
                away_team = abbr
                away_slug = slug
            if dist_home < 1500 and (home_slug is None or dist_home < abs(tm.start() - home_starter['pos'])):
                home_team = abbr
                home_slug = slug
        
        if away_team and home_team:
            matchups.append({
                'away_team': away_team,
                'home_team': home_team,
                'away_starter_id': away_starter['pid'],
                'home_starter_id': home_starter['pid'],
            })
    
    return matchups


def cmd_pre(game_date=None):
    """
    Pre-game: fetch today's starters, register new pitchers, create matchups.
    """
    if game_date is None:
        game_date = date.today().isoformat()
    
    init_db()
    html = fetch_lineups_html()
    starters = parse_starters_from_html(html)
    matchups = parse_matchups_from_html(html)
    
    if not starters:
        print("❌ No starters found. The lineups page may not be updated yet.")
        return
    
    print(f"📋 Found {len(starters)} starting pitchers, {len(matchups)} matchups\n")
    
    # Register pitchers
    new_count = 0
    for s in starters:
        existing = get_pitcher(s['id'])
        if not existing:
            # Check by name to avoid duplicates
            by_name = find_pitcher_by_name(s['name_en'])
            if by_name:
                print(f"  ⚠ {s['name_en']} ({s['name_zh']}) — name match found with ID {by_name[0]['id']}, using existing")
                continue
            
            # New pitcher — need team info. Try to find from matchup context
            team = None
            for m in matchups:
                if m['away_starter_id'] == s['id']:
                    team = m['away_team']
                elif m['home_starter_id'] == s['id']:
                    team = m['home_team']
            
            register_pitcher(s['id'], s['name_en'], s['name_zh'], team, s['throws'])
            new_count += 1
            print(f"  ✅ NEW: {s['name_en']} ({s['name_zh']}) — ID {s['id']}")
    
    if new_count:
        print(f"\n  {new_count} new pitchers registered")
    else:
        print("  (all pitchers already registered)")
    
    # Create matchups
    m_count = 0
    for m in matchups:
        upsert_matchup(
            game_date=game_date,
            away_team=m['away_team'],
            home_team=m['home_team'],
            away_starter_id=m['away_starter_id'],
            home_starter_id=m['home_starter_id'],
            status='scheduled'
        )
        m_count += 1
    
    print(f"\n  {m_count} matchups created for {game_date}")
    print(f"  DB total: {get_pitcher_count()} pitchers, {get_db_stats()['regular_season_logs']} RS games")


def cmd_post(game_date=None):
    """
    Post-game: update today's games with actual results.
    
    This requires the user to provide results, since lottonavi scoreboard
    may not have structured data easily parsable.
    
    Reads from stdin a simple format:
      MIA @ PIT: Meyer 5.1IP 2ER (MIA 3-5 PIT)
      SD @ BAL: Buehler 6.0IP 1ER (SD 2-3 BAL)
    
    Or can be called per-game:
      python3.11 tools/mlb_daily.py post --game "MIA@PIT" --er 2 --ip 5.1
    """
    if game_date is None:
        game_date = date.today().isoformat()
    
    init_db()
    
    # Check if called with --game flag
    if '--game' in sys.argv:
        game_idx = sys.argv.index('--game')
        game_str = sys.argv[game_idx + 1]
        er = int(sys.argv[sys.argv.index('--er') + 1]) if '--er' in sys.argv else None
        ip_val = float(sys.argv[sys.argv.index('--ip') + 1]) if '--ip' in sys.argv else None
        
        # Parse "MIA@PIT" format
        parts = game_str.split('@')
        away = parts[0].strip()
        home = parts[1].strip()
        
        matchups = get_matchups_by_date(game_date)
        for m in matchups:
            if m['away_team'] == away and m['home_team'] == home:
                # Update both starters' game logs
                if er is not None and m['away_starter_id']:
                    update_game_result(m['away_starter_id'], game_date, er, ip_val)
                if er is not None and m['home_starter_id']:
                    update_game_result(m['home_starter_id'], game_date, er, ip_val)
                print(f"✅ Updated {away}@{home}")
                return
        
        print(f"❌ Matchup {away}@{home} not found for {game_date}")
        return
    
    # Interactive mode: show matchups and ask for results
    matchups = get_matchups_by_date(game_date)
    if not matchups:
        print(f"❌ No matchups found for {game_date}. Run 'pre' first.")
        return
    
    print(f"📋 Matchups for {game_date}:\n")
    for m in matchups:
        away_name = m.get('away_starter_name', '?')
        home_name = m.get('home_starter_name', '?')
        print(f"  {m['away_team']} @ {m['home_team']} | {away_name} vs {home_name} | {m['status']}")


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('pre', 'post'):
        print("Usage: python3.11 tools/mlb_daily.py pre [YYYY-MM-DD]")
        print("       python3.11 tools/mlb_daily.py post [YYYY-MM-DD] [--game MIA@PIT --er 2 --ip 5.1]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    dt = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    
    if cmd == 'pre':
        cmd_pre(dt)
    elif cmd == 'post':
        cmd_post(dt)
