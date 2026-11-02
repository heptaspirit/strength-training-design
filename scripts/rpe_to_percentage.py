#!/usr/bin/env python3
"""
strength-training-design skill — RPE to %1RM batch converter
Used by: 功能三 step 3 — converting RPE/reps to training weights
Usage: python scripts/rpe_to_percentage.py --reps <N> --rpe <RPE> --one_rm <PR>
"""

import argparse
from itertools import pairwise

# RPE 转 %1RM 表格（基于 JTS 数据）
# Key: (reps, rpe) -> %1RM
RPE_TABLE = {
    (1, 10): 100, (2, 10): 95, (3, 10): 92, (4, 10): 90, (5, 10): 87,
    (1, 9.5): 97, (2, 9.5): 92, (3, 9.5): 89, (4, 9.5): 87, (5, 9.5): 84,
    (1, 9): 95, (2, 9): 90, (3, 9): 87, (4, 9): 85, (5, 9): 82,
    (1, 8.5): 93, (2, 8.5): 88, (3, 8.5): 85, (4, 8.5): 82, (5, 8.5): 79,
    (1, 8): 90, (2, 8): 85, (3, 8): 82, (4, 8): 80, (5, 8): 77,
    (1, 7.5): 88, (2, 7.5): 83, (3, 7.5): 80, (4, 7.5): 77, (5, 7.5): 74,
    (1, 7): 85, (2, 7): 80, (3, 7): 77, (4, 7): 75, (5, 7): 72,
}

def rpe_to_percentage(reps: int, rpe: float) -> float:
    """查询 RPE 表格，返回 %1RM"""
    key = (reps, rpe)
    if key in RPE_TABLE:
        return RPE_TABLE[key]
    
    # 未找到精确匹配，尝试插值
    # 简化：返回最接近的 RPE 值
    closest_rpe = min([k[1] for k in RPE_TABLE.keys() if k[0] == reps], key=lambda x: abs(x - rpe))
    return RPE_TABLE.get((reps, closest_rpe), 80)

def calculate_1rm_from_rpe(weight: float, reps: int, rpe: float) -> float:
    """根据 RPE 反推 1RM"""
    percentage = rpe_to_percentage(reps, rpe)
    return weight / (percentage / 100)


# ── 组次与 %1RM 的可行域反查 ──────────────────────────────────────────
# 用途：处方里 (次数, %1RM) 是被当成两个自由参数填的，但两者不独立。
# 给定次数，%1RM 有上限（力竭点）；超过去就是「排了一组做不完的量」。

def pct_at_failure(reps: int):
    """该次数下做到力竭（RPE 10）对应的最高 %1RM。表只覆盖 1-5 次，其余返回 None。"""
    return RPE_TABLE.get((reps, 10))


def implied_rpe(reps: int, pct: float):
    """由 (次数, %1RM) 反查 RPE。返回 (rpe, 是否越界)：
    rpe > 10 表示该 %1RM 已超过该次数的力竭上限（不可能完成的处方）。
    次数不在表内（>5）或 %1RM 低于表下界时，返回 (None, False)——不判。
    """
    if (reps, 10) not in RPE_TABLE:
        return None, False
    pts = sorted((RPE_TABLE[(reps, r)], r)
                 for r in (7, 7.5, 8, 8.5, 9, 9.5, 10)
                 if (reps, r) in RPE_TABLE)
    if not pts:
        return None, False
    top_pct, top_rpe = pts[-1]
    if pct > top_pct:
        # 超力竭：按最后一档的斜率外推，仅用于排序与提示，不作精确值
        slope = (pts[-1][1] - pts[-2][1]) / (pts[-1][0] - pts[-2][0]) if len(pts) > 1 else 0
        return round(top_rpe + (pct - top_pct) * slope, 2), True
    if pct < pts[0][0]:
        return None, False
    for (p0, r0), (p1, r1) in pairwise(pts):
        if p0 <= pct <= p1:
            if p1 == p0:
                return r1, False
            return round(r0 + (pct - p0) / (p1 - p0) * (r1 - r0), 2), False
    return None, False


def calculate_weight_from_1rm(one_rm: float, reps: int, rpe: float) -> float:
    """根据 1RM 和 RPE 计算训练重量"""
    percentage = rpe_to_percentage(reps, rpe)
    return one_rm * (percentage / 100)

def main():
    parser = argparse.ArgumentParser(description='RPE 转 %1RM 计算')
    parser.add_argument('--reps', type=int, required=True, help='次数（1-10）')
    parser.add_argument('--rpe', type=float, required=True, help='RPE 值（6-10，支持 .5 步进）')
    parser.add_argument('--weight', type=float, help='使用的重量（用于反推 1RM）')
    parser.add_argument('--one_rm', type=float, help='1RM（用于计算训练重量）')
    
    args = parser.parse_args()
    
    percentage = rpe_to_percentage(args.reps, args.rpe)
    
    print(f"📊 RPE {args.rpe} @ {args.reps} 次 → {percentage}% 1RM")
    
    if args.weight:
        estimated_1rm = calculate_1rm_from_rpe(args.weight, args.reps, args.rpe)
        print(f"   使用重量 {args.weight}kg @ RPE {args.rpe} × {args.reps} 次")
        print(f"   → 估算 1RM: {estimated_1rm:.1f} kg")
    
    if args.one_rm:
        training_weight = calculate_weight_from_1rm(args.one_rm, args.reps, args.rpe)
        print(f"   1RM {args.one_rm}kg @ RPE {args.rpe} × {args.reps} 次")
        print(f"   → 训练重量: {training_weight:.1f} kg")
    
    # 输出 Markdown 表格行（用于 AI 生成计划）
    print(f"\n💡 AI 输出参考（Markdown 表格行）:")
    print(f"| RPE {args.rpe} | {args.reps} 次 | {percentage}% 1RM |")

if __name__ == '__main__':
    main()
