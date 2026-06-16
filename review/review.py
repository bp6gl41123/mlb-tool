#!/usr/bin/env python3
"""
智能覆盤 v2 — 比對預測得分 vs 實際得分，自動發現誤差模式
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init, update_result, get_stats, get_error_patterns, save_insight

def review_game(game_id, actual_away, actual_home):
    """更新一場的實際結果，計算誤差"""
    err = update_result(game_id, actual_away, actual_home)
    return err

def discover_insights():
    """從誤差模式中自動發現規律"""
    patterns = get_error_patterns()
    if not patterns:
        return []
    
    discoveries = []
    
    # 分析: 高 ERA 差是否對應高誤差？
    high_era_gap_errors = []
    for m, ae, he, sp, sa, err, fac in patterns:
        if ae and he:
            gap = abs(ae - he)
            if gap > 2.0:
                high_era_gap_errors.append(err)
    
    if len(high_era_gap_errors) >= 2 and sum(high_era_gap_errors)/len(high_era_gap_errors) > 3:
        insight = f"ERA差距>2的比賽，預測誤差偏大(均{round(sum(high_era_gap_errors)/len(high_era_gap_errors),1)}分)，ERA差可能不是線性關係"
        save_insight(insight, 0.7, len(high_era_gap_errors))
        discoveries.append(insight)
    
    # 分析: 誤差是否集中在特定球場？
    return discoveries

def print_summary():
    stats = get_stats()
    patterns = get_error_patterns()
    
    print("=" * 50)
    print("  智能覆盤 v2")
    print("=" * 50)
    print(f"  總場次: {stats['total_games']}")
    print(f"  方向正確: {stats['spread_direction_correct']}/{stats['total_games']} ({stats['spread_accuracy']}%)")
    print(f"  平均預測誤差: {stats['avg_error']} 分")
    print()
    
    if patterns:
        print("  最大誤差場次:")
        for m, ae, he, sp, sa, err, fac in patterns[:5]:
            sp_str = f"{sp:+.1f}" if sp else "?"
            sa_str = f"{sa:+.1f}" if sa else "?"
            print(f"  {m}: 估{sp_str} 實{sa_str} 誤差{err:.1f}分")
    
    discoveries = discover_insights()
    if discoveries:
        print(f"\n  新發現規律 ({len(discoveries)}條):")
        for d in discoveries:
            print(f"  💡 {d[:100]}")

if __name__ == "__main__":
    init()
    print_summary()
