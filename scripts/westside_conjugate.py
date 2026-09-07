#!/usr/bin/env python3
"""
strength-training-design skill — Westside conjugate calculator
Used by: 共轭体系量化运算 — DE 波浪/平装载荷吨位/60% 法则/ME 轮换/带链虚拟力
来源: The Westside Barbell Book of Methods (Louie Simmons, 2007)
      量化出处见 references/westside/book-of-methods-core.md
Usage:
  python scripts/westside_conjugate.py wave    --lift squat --one_rm 150 --level intermediate --week 1
  python scripts/westside_conjugate.py tonnage --lift squat --target 150 [--one_rm 145]
  python scripts/westside_conjugate.py rotation --variants "暂停深蹲" "SSB 深蹲" "早安式" "低箱深蹲"
  python scripts/westside_conjugate.py band    --bar_pct 40 --band_top 25 --band_bottom 10   # 备注级
"""

import argparse

# DE 百分比按水平反向（官方表）：水平越高对杠施加的力越大，百分比可更低
LEVEL_WAVE_BASE = {
    "advanced": 40,      # 波: 40/45/50%
    "intermediate": 45,  # 波: 45/50/55%
    "novice": 50,        # 波: 50/55/60%
}

# DE 组数处方（L629；纯杠铃形态，无带/链）
DE_PRESCRIPTION = {
    "squat":    {"sets": "10-12", "reps": 2, "note": "组间 30-90s，杠速第一、百分比只是参考"},
    "bench":    {"sets": "8-10",  "reps": 3, "note": "三种握距；固定重量、不波浪"},
    "deadlift": {"sets": "5-6",   "reps": 1, "note": "速度硬拉 50-60%，不必每周做（L975）"},
}

DE_BENCH_PCT = (45, 50)  # 无装备 max（有装备 50%）


def round_weight(weight: float, plate_step: float = 2.5) -> float:
    """向下取整到哑铃片步进（与 round_weight.py 同规则）"""
    return (weight // plate_step) * plate_step


def wave_week_pct(level: str, week: int) -> float:
    """三周钟摆波: base/base+5/base+10，按水平反向"""
    base = LEVEL_WAVE_BASE[level]
    return base + (week - 1) * 5


def cmd_wave(args):
    """DE 波浪课处方生成"""
    lift = args.lift
    pres = DE_PRESCRIPTION[lift]
    one_rm = args.one_rm

    print(f"📊 DE 动态努力日 — {lift}（{args.level}）")

    if lift == "bench":
        # 卧推 DE 固定重量不波浪
        lo = round_weight(one_rm * DE_BENCH_PCT[0] / 100)
        hi = round_weight(one_rm * DE_BENCH_PCT[1] / 100)
        print(f"   固定重量（不波浪）: {lo}-{hi} kg（45-50% 无装备 max）")
        print(f"   组数: {pres['sets']}×{pres['reps']}，三种握距（窄/中/宽）")
        print(f"   要点: {pres['note']}")
    else:
        week = args.week
        pct = wave_week_pct(args.level, week)
        weight = round_weight(one_rm * pct / 100)
        print(f"   Week {week}/3 钟摆波: {pct}% → {weight} kg × {pres['sets']}×{pres['reps']}")
        print(f"   要点: {pres['note']}")
        if week == 3:
            print("   ⚠️ W3 为波顶点，下一周回 W1 重新开始（三周后人无法更快或更强）")

    # AI 输出参考
    print(f"\n💡 AI 输出参考:")
    if lift == "bench":
        print(f"| DE 卧推 | {DE_PRESCRIPTION['bench']['sets']}×3 | 45-50% 固定重量 | 三握距 |")
    else:
        pct = wave_week_pct(args.level, args.week)
        weight = round_weight(one_rm * pct / 100)
        print(f"| DE {lift} W{args.week} | {DE_PRESCRIPTION[lift]['sets']}×{DE_PRESCRIPTION[lift]['reps']} | {weight}kg ({pct}%) | 杠速优先 |")


def cmd_tonnage(args):
    """平装载荷吨位 + 60% 法则"""
    target = args.target
    lift = args.lift
    pres = DE_PRESCRIPTION[lift]

    # 平装载荷: 单日 DE 总吨位 = 目标成绩 × 12
    de_tonnage = target * 12
    print(f"📊 平装载荷（flat loading）— {lift}")
    print(f"   目标成绩: {target} kg → 单日 DE 吨位 = 目标 × 12 = {de_tonnage:.0f} kg")

    # 按波位反推组数: sets = tonnage / (pct × 1RM × reps)
    one_rm = args.one_rm if args.one_rm else target
    reps = pres["reps"]
    print(f"\n   三周波内总吨位恒定（波内不加重，达成新 PR 后整体上调）:")
    print(f"   {'周':<6} {'%':<5} {'重量':<10} {'组数':<12}")
    for week in (1, 2, 3):
        pct = wave_week_pct(args.level, week)
        weight = round_weight(one_rm * pct / 100)
        per_set = weight * reps
        sets = de_tonnage / per_set if per_set else 0
        print(f"   W{week:<5} {pct:<5} {weight:<10} {sets:.1f} 组（×{reps} 次）")
    print(f"\n   要点: {pres['note']}")

    # 60% 法则
    me_tonnage = de_tonnage * 0.6
    print(f"\n📐 60% 法则: ME 日总吨位 ≈ DE 的 60% = {me_tonnage:.0f} kg")
    print(f"   （Westside 实际操作约 45-50%；此值为举重来源的理论锚点）")

    print(f"\n💡 AI 输出参考: DE {lift} 目标 {target}kg → 日吨位 {de_tonnage:.0f}kg，ME 日吨位 ≈{me_tonnage:.0f}kg")


def cmd_rotation(args):
    """ME 变式轮换计划：4-5 个变式每两周轮换一个 → 10 周大周期（标准处方）"""
    variants = args.variants
    n = len(variants)
    if not 3 <= n <= 5:
        print("⚠️ 建议选 4-5 个核心变式（最少 3 个才成完整大周期）")

    weeks_total = n * 2
    print(f"📊 ME 轮换大周期（{weeks_total} 周，每变式 2 周）")
    print(f"   标准处方：选 4-5 个核心变式、每两周轮换一个；最强/最产出的动作排在最后一轮接比赛/测试周")
    print(f"\n   {'周':<8} {'ME 变式':<20}")
    for i, v in enumerate(variants):
        tag = " ← 最产出动作收尾" if i == n - 1 else ""
        print(f"   W{i*2+1}-{i*2+2:<4} {v}{tag}")

    print(f"\n   轮换规则:")
    print(f"   - 90%+ 持续不超过 3 周（CNS 保护核心规则）→ 换动作即规避")
    print(f"   - 课内 >90% 次数上限 2-3 次: 90% → 95-98% → 冲纪录（或 92-95% 直接跳冲）")
    print(f"   - 追'当天的极限'，不是旧纪录；不必每周都做 ME（可插 rest 周）")
    print(f"   - 配件（reverse hyper/pull-through/GHR）按'效力下降就换'独立轮换，不受此表约束")

    print(f"\n💡 AI 输出参考: ME 轮换 {weeks_total} 周 — " + " → ".join(f"{v}×2周" for v in variants))


def cmd_band(args):
    """带/链虚拟力计算 — 备注级（用户环境不常备，默认不引入）"""
    top = args.bar_pct + args.band_top
    bottom = args.bar_pct + args.band_bottom
    print(f"📊 虚拟力计算（备注级 — 设备不常备，仅背景储备）")
    print(f"   杠 {args.bar_pct}% + 顶部带 {args.band_top}% / 底部带 {args.band_bottom}%")
    print(f"   → 顶部总负荷 {top}% / 底部总负荷 {bottom}%")

    # 65/35 规则提示
    bar_share = args.bar_pct / top * 100 if top else 0
    print(f"   杠占比: {bar_share:.0f}%（速度力量目标 65% 杠/35% 带；力量-速度反转 65% 带/35% 杠）")
    if args.band_top > 40:
        print(f"   ⚠️ 带张力 >40%: 离心相位缩至 ~0.5s，overspeed eccentric——带大张力组后不要卸带做纯杠大重量")
    print(f"\n💡 门槛: plyo/过速离心需深蹲 ≥2× 体重；circa-max 需 ≥3.5× 体重")


def main():
    parser = argparse.ArgumentParser(description='Westside 共轭体系量化运算（一手来源）')
    sub = parser.add_subparsers(dest='command', required=True)

    p_wave = sub.add_parser('wave', help='DE 波浪课处方（钟摆波 / 卧推固定重量）')
    p_wave.add_argument('--lift', choices=['squat', 'bench', 'deadlift'], required=True)
    p_wave.add_argument('--one_rm', type=float, required=True, help='当前 1RM（kg）')
    p_wave.add_argument('--level', choices=['novice', 'intermediate', 'advanced'], default='intermediate')
    p_wave.add_argument('--week', type=int, choices=[1, 2, 3], default=1, help='波内第几周（卧推忽略）')
    p_wave.set_defaults(func=cmd_wave)

    p_ton = sub.add_parser('tonnage', help='平装载荷吨位 + 60 法则')
    p_ton.add_argument('--lift', choices=['squat', 'bench', 'deadlift'], required=True)
    p_ton.add_argument('--target', type=float, required=True, help='目标成绩（kg）')
    p_ton.add_argument('--one_rm', type=float, help='当前 1RM（kg，用于波内重量；默认=目标）')
    p_ton.add_argument('--level', choices=['novice', 'intermediate', 'advanced'], default='intermediate')
    p_ton.set_defaults(func=cmd_tonnage)

    p_rot = sub.add_parser('rotation', help='ME 变式轮换计划（两周小周期）')
    p_rot.add_argument('--variants', nargs='+', required=True, help='变式列表（按轮换顺序，最强放最后）')
    p_rot.set_defaults(func=cmd_rotation)

    p_band = sub.add_parser('band', help='带/链虚拟力（备注级）')
    p_band.add_argument('--bar_pct', type=float, required=True, help='杠重（1RM 百分比数值）')
    p_band.add_argument('--band_top', type=float, required=True, help='顶部带张力（百分比数值）')
    p_band.add_argument('--band_bottom', type=float, required=True, help='底部带张力（百分比数值）')
    p_band.set_defaults(func=cmd_band)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
