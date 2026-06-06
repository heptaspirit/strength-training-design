#!/usr/bin/env python3
"""
strength-training-design skill — weighted fatigue + CNS fatigue calculator
Used by: 功能三 step 5 — weighted fatigue audit
Usage: python scripts/calculate_fatigue.py --sets <N> --fc <coeff> --rpe <RPE> [--cns]
"""

import argparse

# 疲劳系数表（fatigue coefficient, FC）
# 参考 JTS 和 Renaissance Periodization 数据
FC_TABLE = {
    'squat': 0.75,        # 深蹲
    'bench': 0.55,        # 卧推
    'deadlift': 0.85,     # 硬拉（传统）
    'ohp': 0.60,          # 实力推
    'row': 0.45,          # 划船
    'rdl': 0.65,          # 罗马尼亚硬拉
    'front_squat': 0.70,  # 前蹲
    'sumo_deadlift': 0.80,# 相扑硬拉
}

# CNS 疲劳系数表
CNS_FC_TABLE = {
    'squat': 0.12,
    'bench': 0.08,
    'deadlift': 0.15,
    'ohp': 0.09,
    'row': 0.06,
    'rdl': 0.10,
    'front_squat': 0.11,
    'sumo_deadlift': 0.14,
}

def get_fc(exercise: str) -> float:
    """查询疲劳系数"""
    for key, value in FC_TABLE.items():
        if key in exercise.lower():
            return value
    return 0.50  # 默认

def get_cns_fc(exercise: str) -> float:
    """查询 CNS 疲劳系数"""
    for key, value in CNS_FC_TABLE.items():
        if key in exercise.lower():
            return value
    return 0.08  # 默认


def calculate_weighted_fatigue(sets: int, fc: float, rpe: float, rpe_mod: float = 0.85) -> dict:
    """
    计算加权疲劳

    Formula: Weighted Fatigue = sets × FC × (RPE / 10) × RPE_mod

    Args:
        sets: 训练组数
        fc: 动作疲劳系数（0-1）
        rpe: RPE 值（6-10）
        rpe_mod: RPE 修正系数（默认 0.85，用于校准）

    Returns:
        dict: 含计算结果和建议
    """
    fatigue = sets * fc * (rpe / 10) * rpe_mod
    fatigue = round(fatigue, 2)

    if fatigue < 4:
        status = "✅ 安全"
        advice = "疲劳在可控范围，无需调整"
    elif fatigue < 8:
        status = "⚠️ 中等"
        advice = "注意监控恢复指标（睡眠、情绪、力量下降），必要时降 BO 组"
    else:
        status = "❌ 偏高"
        advice = "建议减少 BO 组数 1-2 组，或降低 RPE 目标 0.5-1"

    return {
        'fatigue': fatigue,
        'status': status,
        'advice': advice,
        'sets': sets,
        'fc': fc,
        'rpe': rpe,
        'rpe_mod': rpe_mod,
    }


def calculate_cns_fatigue(sets: int, cns_fc: float, rpe: float) -> dict:
    """
    计算 CNS 疲劳

    Formula: CNS Fatigue = sets × CNS_FC × (RPE / 10)

    Args:
        sets: 训练组数
        cns_fc: CNS 疲劳系数（0-1）
        rpe: RPE 值（6-10）

    Returns:
        dict: 含计算结果和建议
    """
    cns = sets * cns_fc * (rpe / 10)
    cns = round(cns, 2)

    if cns < 2.0:
        status = "✅ 安全（CNS < 2.0）"
    elif cns < 3.0:
        status = "⚠️ 接近上限（CNS 2.0-3.0）"
    else:
        status = "❌ 超标（CNS > 3.0）"

    return {
        'cns_fatigue': cns,
        'status': status,
        'sets': sets,
        'cns_fc': cns_fc,
        'rpe': rpe,
    }


def main():
    parser = argparse.ArgumentParser(description='加权疲劳 + CNS 疲劳计算')
    parser.add_argument('--sets', type=int, required=True, help='训练组数')
    parser.add_argument('--fc', type=float, help='动作疲劳系数（0-1），不提供则从表中查询')
    parser.add_argument('--exercise', type=str, help='动作名称（如 squat, deadlift），用于自动查询 FC')
    parser.add_argument('--rpe', type=float, required=True, help='RPE 值（6-10）')
    parser.add_argument('--rpe_mod', type=float, default=0.85, help='RPE 修正系数（默认 0.85）')
    parser.add_argument('--cns', action='store_true', help='同时计算 CNS 疲劳')

    args = parser.parse_args()

    # 确定 FC
    fc = args.fc
    if fc is None and args.exercise:
        fc = get_fc(args.exercise)
        print(f"ℹ️  动作 '{args.exercise}' 的疲劳系数 FC = {fc}")
    elif fc is None:
        print("❌ 必须提供 --fc 或 --exercise")
        return

    # 加权疲劳
    result = calculate_weighted_fatigue(args.sets, fc, args.rpe, args.rpe_mod)

    print(f"\n📊 加权疲劳计算:")
    print(f"   组数: {args.sets}")
    print(f"   FC: {result['fc']}")
    print(f"   RPE: {result['rpe']}")
    print(f"   RPE 修正: {result['rpe_mod']}")
    print(f"   → 加权疲劳: {result['fatigue']} units {result['status']}")
    print(f"   💡 建议: {result['advice']}")

    # CNS 疲劳
    if args.cns:
        cns_fc = args.fc if args.fc else 0.08
        if args.exercise:
            cns_fc = get_cns_fc(args.exercise)
        cns_result = calculate_cns_fatigue(args.sets, cns_fc, args.rpe)
        print(f"\n🧠 CNS 疲劳计算:")
        print(f"   CNS FC: {cns_result['cns_fc']}")
        print(f"   → CNS 疲劳: {cns_result['cns_fatigue']} units {cns_result['status']}")

    # Markdown 输出
    print(f"\n💡 AI 输出参考 (Markdown):")
    print(f"| 动作 | 组数 | FC | RPE | 加权疲劳 | 状态 |")
    print(f"|------|------|-----|-----|---------|------|")
    print(f"| {args.exercise or '指定动作'} | {args.sets} | {fc} | {args.rpe} | {result['fatigue']} | {result['status']} |")


if __name__ == '__main__':
    main()
