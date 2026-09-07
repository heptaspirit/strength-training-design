#!/usr/bin/env python3
"""
strength-training-design skill — GPP / 体能处方计算器
Used by: 功能三步骤4「GPP 与体能模块」与功能五 conditioning-plan.md
提供: Karvonen 目标心率区间 / 间歇 work-rest 处方 / GPP 恢复预算审计 / 进阶 10% 表
来源: ACSM Guidelines for Exercise Testing and Prescription 12th ed.（FITT、强度分级、间歇协议）
      NSCA Essentials of Strength Training and Conditioning 5th ed.（work-to-rest、进阶）
      依据 references/methodology/gpp-framework.md 与 references/exercises/aerobic-training.md
Usage:
  python scripts/gpp_calculator.py hr --hr_max 192 --hr_rest 58 --zone moderate
  python scripts/gpp_calculator.py hr --hr_max 192 --hr_rest 58 --low 60 --high 89
  python scripts/gpp_calculator.py workrest --system glycolysis --work 20
  python scripts/gpp_calculator.py workrest --pct 85 --work 15
  python scripts/gpp_calculator.py budget --phase capacity --maintenance 2 --development 1
  python scripts/gpp_calculator.py progress --start 20 --weeks 8
"""

import argparse

# ACSM 强度分级对应的 %HRR（= %V̇O2R）区间
HRR_ZONES = {
    "very_light": (20, 30, "极轻 Very light"),
    "light": (30, 39, "轻 Light"),
    "moderate": (40, 59, "中等 Moderate"),
    "vigorous": (60, 89, "剧烈 Vigorous"),
    "near_max": (90, 100, "接近最大 Near-maximal"),
}

# 各强度档对应的 %HRmax 参考（ACSM 强度分级表第二列）
HRMAX_EQUIV = {
    "very_light": "<57",
    "light": "57-63",
    "moderate": "64-76",
    "vigorous": "77-95",
    "near_max": ">=96",
}

# 能量系统 → (功率%区间, 典型工作时长, work:rest 下限, 上限)
ENERGY_SYSTEMS = {
    "phosphagen": ((90, 100), "5-10 s", 12, 20, "磷酸原"),
    "glycolysis": ((75, 90), "15-30 s", 3, 5, "快糖酵解"),
    "mixed": ((30, 75), "1-3 min", 3, 4, "快糖酵解 + 氧化"),
    "oxidative": ((20, 30), ">3 min", 1, 3, "氧化"),
}

# GPP 三档疲劳分类账（gpp-framework.md §4）：每周单次占用的恢复预算中值
BUDGET_PER_SESSION = {
    "recovery": 0.0,      # 恢复性：不计入
    "maintenance": 7.5,   # 维持性：5-10%
    "development": 20.0,  # 发展性：15-25%
}

# 各周期阶段的恢复预算上限（超出即挤压主项）
BUDGET_CAP = {
    "capacity": 35.0,   # 容量期
    "deload": 30.0,     # 减载周
    "strength": 15.0,   # 力量期
    "peak": 10.0,       # 冲刺期
    "test": 5.0,        # 测试周
}

PHASE_LABEL = {
    "capacity": "容量期",
    "deload": "减载周",
    "strength": "力量期",
    "peak": "冲刺期",
    "test": "测试周",
}


def karvonen(hr_max: float, hr_rest: float, pct: float) -> float:
    """Karvonen 公式：目标心率 = (HRmax - HRrest) x 强度百分比 + HRrest"""
    return (hr_max - hr_rest) * (pct / 100.0) + hr_rest


def cmd_hr(args):
    """目标心率区间换算（ACSM）"""
    if args.hr_max <= args.hr_rest:
        raise SystemExit("错误: 最大心率必须大于静息心率")
    if args.zone and (args.low is not None or args.high is not None):
        raise SystemExit("错误: --zone 与 --low/--high 不能同时使用")
    if not args.zone and (args.low is None or args.high is None):
        raise SystemExit("错误: 需指定 --zone，或同时指定 --low 与 --high")
    if args.low is not None and args.high is not None and args.low >= args.high:
        raise SystemExit("错误: --low 必须小于 --high")

    if args.zone:
        low, high, label = HRR_ZONES[args.zone]
        hrmax_equiv = HRMAX_EQUIV[args.zone]
    else:
        low, high, label = args.low, args.high, "自定义区间"
        hrmax_equiv = "—"

    thr_low = karvonen(args.hr_max, args.hr_rest, low)
    thr_high = karvonen(args.hr_max, args.hr_rest, high)

    print("=" * 56)
    print("目标心率区间（Karvonen / %HRR 法）")
    print("=" * 56)
    print(f"  最大心率 HRmax : {args.hr_max:g} bpm")
    print(f"  静息心率 HRrest: {args.hr_rest:g} bpm")
    print(f"  强度档        : {label}（{low:g}-{high:g}% HRR）")
    print(f"  等价 %HRmax   : {hrmax_equiv}")
    print("-" * 56)
    print(f"  >> 目标心率区间: {thr_low:.0f} - {thr_high:.0f} bpm")
    print("=" * 56)
    print("  公式: THR = (HRmax - HRrest) x 强度百分比 + HRrest")
    print("  注: ACSM 12th 不推荐使用 220 - 年龄估算 HRmax（误差 10-15 bpm）")


def cmd_workrest(args):
    """间歇训练 work:rest 处方（NSCA）"""
    if args.system:
        key = args.system
    else:
        key = next(
            (k for k, v in ENERGY_SYSTEMS.items() if v[0][0] <= args.pct <= v[0][1]),
            None,
        )
    if key is None:
        raise SystemExit(f"错误: 功率百分比 {args.pct:g} 未落在任何能量系统区间（20-100）")

    (pct_lo, pct_hi), typical, r_lo, r_hi, cn_name = ENERGY_SYSTEMS[key]
    work = args.work
    rest_lo = work * r_lo
    rest_hi = work * r_hi
    cycle_lo = work + rest_lo
    cycle_hi = work + rest_hi

    # 目标总做功时间（不含休息）：发展性 GPP 单次 10-20 min
    total_work = args.total_work if args.total_work else 600
    sets = int(total_work // cycle_hi)
    sets = max(sets, 1)

    print("=" * 56)
    print("间歇训练 work:rest 处方（NSCA）")
    print("=" * 56)
    print(f"  主导能量系统  : {cn_name}（{key}）")
    print(f"  对应功率区间  : {pct_lo}-{pct_hi}% 最大功率")
    print(f"  典型工作时长  : {typical}")
    print(f"  本次工作时长  : {work:g} s")
    print("-" * 56)
    print(f"  work:rest 比  : 1:{r_lo} - 1:{r_hi}")
    print(f"  >> 休息时长   : {rest_lo:.0f} - {rest_hi:.0f} s")
    print(f"  单轮周期      : {cycle_lo:.0f} - {cycle_hi:.0f} s")
    print(f"  建议组数      : {sets} 组（按总做功 {total_work // 60:g} min 计）")
    print(f"  预计净时长    : 约 {sets * cycle_hi / 60:.1f} min（含休息）")
    print("=" * 56)
    print("  注: NSCA 指出该表基于代谢系统参与的理论时间进程，")
    print("      目前仍缺乏最优 work:rest 的循证金标准，视为工程近似。")
    if key == "phosphagen":
        print("  注: 磷酸原完全再合成需 3-5 min（可达 8 min），休息不足即练错系统。")


def cmd_budget(args):
    """GPP 恢复预算审计（gpp-framework.md §4 三档分类账）"""
    maint = BUDGET_PER_SESSION["maintenance"] * args.maintenance
    dev = BUDGET_PER_SESSION["development"] * args.development
    total = maint + dev
    cap = BUDGET_CAP[args.phase]

    print("=" * 56)
    print("GPP 恢复预算审计")
    print("=" * 56)
    print(f"  周期阶段      : {PHASE_LABEL[args.phase]}（上限 {cap:g}%）")
    print("-" * 56)
    print(f"  恢复性 x{args.recovery:<2d}     : 0.0%（不计入预算）")
    print(f"  维持性 x{args.maintenance:<2d}     : {maint:.1f}%（5-10%/次）")
    print(f"  发展性 x{args.development:<2d}     : {dev:.1f}%（15-25%/次）")
    print("-" * 56)
    print(f"  >> 合计占用   : {total:.1f}% / {cap:g}%")
    print("=" * 56)

    if args.development > 0 and args.phase in ("strength", "peak", "test"):
        print("  [违规] 发展性 GPP 仅允许容量期与减载周，当前阶段禁用。")
    if total > cap:
        print(f"  [超限] 超出 {total - cap:.1f} 个百分点 —— 优先砍发展性，其次维持性。")
        print("         硬约束：主项容量与强度不动，只砍 GPP。")
    elif total > cap * 0.8:
        print("  [警戒] 已用掉八成以上预算，主项疲劳上升时需先减 GPP。")
    else:
        print("  [通过] 在预算内。")


def cmd_progress(args):
    """有氧进阶表（NSCA 进阶原则：每周增幅 <=10%，一次只动一个变量）"""
    rate = args.rate / 100.0
    print("=" * 56)
    print(f"有氧进阶表（起始 {args.start:g} {args.unit}，周增幅 {args.rate:g}%）")
    print("=" * 56)
    value = float(args.start)
    for week in range(1, args.weeks + 1):
        if week == 1:
            print(f"  W{week:<2d} {value:8.1f} {args.unit}  （基线）")
        else:
            value *= (1 + rate)
            print(f"  W{week:<2d} {value:8.1f} {args.unit}")
    print("-" * 56)
    print(f"  {args.weeks} 周后: {args.start:g} -> {value:.1f} {args.unit}"
          f"（累计 +{(value / args.start - 1) * 100:.0f}%）")
    print("=" * 56)
    print("  规则: 一次只增加一个变量（频率/强度/时长三选一）")
    print("        用时长而非距离设定（距离忽略地形与环境）")
    print("        超过 10% 属功能性过度负荷，须配套过度训练监控")
    if args.rate > 10:
        print(f"  [提示] 当前 {args.rate:g}% 已超过 NSCA 建议的 10% 上限。")


def main():
    parser = argparse.ArgumentParser(
        description="GPP / 体能处方计算器（strength-training-design skill）"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_hr = sub.add_parser("hr", help="Karvonen 目标心率区间换算")
    p_hr.add_argument("--hr_max", type=float, required=True, help="最大心率（实测优先）")
    p_hr.add_argument("--hr_rest", type=float, required=True, help="静息心率")
    p_hr.add_argument("--zone", choices=list(HRR_ZONES.keys()),
                      help="强度档: very_light/light/moderate/vigorous/near_max")
    p_hr.add_argument("--low", type=float, help="自定义强度下限（百分比数值）")
    p_hr.add_argument("--high", type=float, help="自定义强度上限（百分比数值）")
    p_hr.set_defaults(func=cmd_hr)

    p_wr = sub.add_parser("workrest", help="间歇训练 work:rest 处方")
    p_wr.add_argument("--system", choices=list(ENERGY_SYSTEMS.keys()),
                      help="能量系统: phosphagen/glycolysis/mixed/oxidative")
    p_wr.add_argument("--pct", type=float, help="功率百分比数值（用于自动判定系统）")
    p_wr.add_argument("--work", type=float, required=True, help="单组工作时长（秒）")
    p_wr.add_argument("--total_work", type=float,
                      help="目标总做功时间（秒，默认 600 即 10 分钟）")
    p_wr.set_defaults(func=cmd_workrest)

    p_bg = sub.add_parser("budget", help="GPP 恢复预算审计")
    p_bg.add_argument("--phase", choices=list(BUDGET_CAP.keys()), required=True,
                      help="周期阶段: capacity/deload/strength/peak/test")
    p_bg.add_argument("--recovery", type=int, default=0, help="恢复性次数/周（默认 0）")
    p_bg.add_argument("--maintenance", type=int, default=0, help="维持性次数/周（默认 0）")
    p_bg.add_argument("--development", type=int, default=0, help="发展性次数/周（默认 0）")
    p_bg.set_defaults(func=cmd_budget)

    p_pg = sub.add_parser("progress", help="有氧进阶表（10%% 规则）")
    p_pg.add_argument("--start", type=float, required=True, help="起始值")
    p_pg.add_argument("--weeks", type=int, required=True, help="周数")
    p_pg.add_argument("--rate", type=float, default=10.0, help="周增幅百分比数值（默认 10）")
    p_pg.add_argument("--unit", default="min", help="单位显示（默认 min）")
    p_pg.set_defaults(func=cmd_progress)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
