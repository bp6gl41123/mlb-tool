// MLB 責失估算數據 — 由 mlb_run_model.py 自動產生
window.MLB_DATA = {
  "matchup": "教士 @ 金鶯",
  "pitchers": "Walker Buehler vs Trevor Rogers",
  "spread_note": "差距 7.0 分",
  "ref_note": "",
  "extra_note": "",
  "team_a": {
    "abbr": "SD",
    "name": "教士",
    "starter": "Walker Buehler",
    "record": "3-3, 4.33 ERA",
    "era": 4.33,
    "y_team": 3,
    "y_starter": 2,
    "y_bullpen": 1,
    "y_pitcher": "Vásquez",
    "today_venue": "away",
    "starts": [
      {
        "opp": "紅人",
        "wins": 33,
        "runs": 1,
        "venue": "home",
        "label": "上一場"
      },
      {
        "opp": "費城",
        "wins": 38,
        "runs": 1,
        "venue": "away",
        "label": "上二場"
      },
      {
        "opp": "費城",
        "wins": 38,
        "runs": 2,
        "venue": "home",
        "label": "上三場"
      }
    ],
    "today_opp_wins": 34,
    "ref_starts": [
      {
        "opp": "金鶯",
        "wins": 34,
        "runs": 2,
        "venue": "away",
        "label": "昨(今對手)"
      },
      {
        "opp": "大都",
        "wins": 31,
        "runs": 4,
        "venue": "home",
        "label": "上二場"
      },
      {
        "opp": "費城",
        "wins": 38,
        "runs": 2,
        "venue": "away",
        "label": "上三場"
      }
    ],
    "ref_era": 3.63,
    "bullpen_adj": 0,
    "opp_runs_yesterday": 3,
    "opp_runs_note": "金鶯昨得 3（對教士 Vásquez 2ER + 牛棚 1ER）",
    "mech_vals": [
      {
        "opp": "紅人",
        "wins": 33,
        "runs": 1,
        "cal": 1.2
      },
      {
        "opp": "費城",
        "wins": 38,
        "runs": 1,
        "cal": 0.2
      },
      {
        "opp": "費城",
        "wins": 38,
        "runs": 2,
        "cal": 1.2
      }
    ],
    "mech_avg": 0.9,
    "last_extreme": true,
    "last_extreme_dir": "大好",
    "venue_home_avg": 1.5,
    "venue_away_avg": 1.0,
    "venue_split_note": "",
    "cross_matches": [
      {
        "opp": "費城",
        "opp_wins": 38,
        "today_er": 1,
        "ref_er": 2,
        "delta": -1,
        "today_label": "上二場",
        "ref_label": "上三場",
        "today_venue": "away",
        "ref_venue": "away",
        "venue_match": true
      },
      {
        "opp": "費城",
        "opp_wins": 38,
        "today_er": 2,
        "ref_er": 2,
        "delta": 0,
        "today_label": "上三場",
        "ref_label": "上三場",
        "today_venue": "home",
        "ref_venue": "away",
        "venue_match": false
      }
    ],
    "best_match": {
      "opp": "費城",
      "opp_wins": 38,
      "today_er": 1,
      "ref_er": 2,
      "delta": -1,
      "today_label": "上二場",
      "ref_label": "上三場",
      "today_venue": "away",
      "ref_venue": "away",
      "venue_match": true
    },
    "computed": {
      "starter_est": 1,
      "bullpen_est": 1,
      "total_est": 2
    },
    "starter_est": 1,
    "total_lo": 1,
    "total_hi": 3,
    "bp_debt": 1
  },
  "team_b": {
    "abbr": "BAL",
    "name": "金鶯",
    "starter": "Trevor Rogers",
    "record": "3-6, 6.15 ERA",
    "era": 6.15,
    "y_team": 9,
    "y_starter": 6,
    "y_bullpen": 3,
    "y_pitcher": "Gibson",
    "starts": [
      {
        "opp": "水手",
        "wins": 37,
        "runs": 3,
        "venue": "home",
        "label": "上一場"
      },
      {
        "opp": "紅襪",
        "wins": 29,
        "runs": 1,
        "venue": "away",
        "label": "上二場"
      },
      {
        "opp": "藍鳥",
        "wins": 34,
        "runs": 4,
        "venue": "home",
        "label": "上三場"
      }
    ],
    "today_opp_wins": 36,
    "ref_starts": [
      {
        "opp": "教士",
        "wins": 36,
        "runs": 6,
        "venue": "home",
        "label": "昨(今對手)"
      },
      {
        "opp": "水手",
        "wins": 37,
        "runs": 3,
        "venue": "home",
        "label": "上二場"
      },
      {
        "opp": "光芒",
        "wins": 40,
        "runs": 1,
        "venue": "home",
        "label": "上三場"
      }
    ],
    "ref_era": 4.24,
    "bullpen_adj": 0,
    "opp_runs_yesterday": 9,
    "opp_runs_note": "教士昨得 9（對金鶯 Gibson 6ER + 牛棚 3ER）",
    "mech_vals": [
      {
        "opp": "水手",
        "wins": 37,
        "runs": 3,
        "cal": 2.8
      },
      {
        "opp": "紅襪",
        "wins": 29,
        "runs": 1,
        "cal": 2.4
      },
      {
        "opp": "藍鳥",
        "wins": 34,
        "runs": 4,
        "cal": 4.4
      }
    ],
    "mech_avg": 3.2,
    "last_extreme": false,
    "last_extreme_dir": null,
    "venue_home_avg": 3.5,
    "venue_away_avg": 1.0,
    "venue_split_note": "主客場差 -2.5（主1.0/客3.5）⚠",
    "cross_matches": [
      {
        "opp": "水手",
        "opp_wins": 37,
        "today_er": 3,
        "ref_er": 3,
        "delta": 0,
        "today_label": "上一場",
        "ref_label": "上二場",
        "today_venue": "home",
        "ref_venue": "home",
        "venue_match": true
      }
    ],
    "best_match": {
      "opp": "水手",
      "opp_wins": 37,
      "today_er": 3,
      "ref_er": 3,
      "delta": 0,
      "today_label": "上一場",
      "ref_label": "上二場",
      "today_venue": "home",
      "ref_venue": "home",
      "venue_match": true
    },
    "computed": {
      "starter_est": 6,
      "bullpen_est": 3,
      "total_est": 9
    },
    "starter_est": 6,
    "total_lo": 8,
    "total_hi": 10,
    "bp_debt": 3
  }
};
