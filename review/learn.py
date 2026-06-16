#!/usr/bin/env python3
"""
智能學習 v2 — 從預測誤差中自我改進
不是套用已知分類，而是從數據中發現模式
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init, get_stats, get_error_patterns, get_insights, save_insight

def analyze():
    stats = get_stats()
    patterns = get_error_patterns()
    
    if not patterns:
        print("尚無足夠數據進行學習")
        return
    
    print("=" * 50)
    print("  智能學習 v2 — 從誤差中發現規律")
    print("=" * 50)
    print(f"  樣本: {stats['total_games']}場")
    print()
    
    # 分析1: 預測誤差與 SP ERA 的關係
    era_gap_errors = []
    for m, ae, he, sp, sa, err, fac in patterns:
        if ae and he:
            era_gap_errors.append((abs(ae-he), err))
    
    if era_gap_errors:
        # 分組分析
        small_gap = [e for g, e in era_gap_errors if g < 1.5]
        mid_gap = [e for g, e in era_gap_errors if 1.5 <= g < 3]
        large_gap = [e for g, e in era_gap_errors if g >= 3]
        
        print("  ERA差距 vs 預測誤差:")
        if small_gap:
            print(f"    小於1.5: 均誤差 {sum(small_gap)/len(small_gap):.1f}分 ({len(small_gap)}場)")
        if mid_gap:
            print(f"    1.5~3.0: 均誤差 {sum(mid_gap)/len(mid_gap):.1f}分 ({len(mid_gap)}場)")
        if large_gap:
            print(f"    大於3.0: 均誤差 {sum(large_gap)/len(large_gap):.1f}分 ({len(large_gap)}場)")
        
        # 自動結論
        if large_gap and small_gap:
            lg_avg = sum(large_gap)/len(large_gap)
            sg_avg = sum(small_gap)/len(small_gap)
            if lg_avg > sg_avg * 1.5:
                insight = f"ERA差距>3時預測誤差({lg_avg:.1f})比差距<1.5時({sg_avg:.1f})大{lg_avg/sg_avg:.1f}倍。大ERA差距需要額外調整因子"
                save_insight(insight, 0.75, len(large_gap))
                print(f"\n  💡 發現: {insight}")
    
    # 分析2: 預測偏向性（是否總是高估或低估）
    over_under = []
    for m, ae, he, sp, sa, err, fac in patterns:
        if sp and sa:
            over_under.append(sp - sa)  # 正=高估客隊, 負=低估客隊
    
    if over_under:
        avg_bias = sum(over_under) / len(over_under)
        print(f"\n  預測偏差: {avg_bias:+.2f}分 (正=高估客隊)")
        if abs(avg_bias) > 0.5:
            direction = "高估客隊" if avg_bias > 0 else "低估客隊"
            insight = f"模型系統性{direction}(偏差{avg_bias:+.1f}分)，需校正主客場權重"
            save_insight(insight, 0.6, len(over_under))
            print(f"  💡 發現: {insight}")
    
    # 現有規律
    existing = get_insights()
    if existing:
        print(f"\n  已累積規律 ({len(existing)}條):")
        for i in existing:
            pid, insight, conf, ev, disc = i
            print(f"  [{conf:.0%}] {insight[:100]}")

if __name__ == "__main__":
    init()
    analyze()
