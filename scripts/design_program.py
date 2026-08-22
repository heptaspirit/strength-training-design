#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strength-training-design skill — design_program.py
架构 B：通用重复运算器 + 合规检查器（非编排器）

职责（脚本做 = 对任何动作都一样的确定性算术）：
  - 消费 AI 在功能三 step1 生成的 YAML 草稿（含主项/辅助/奥举/核心，每个 lift 带重量意图）
  - 复用现有 4 脚本的确定性计算（RPE→% / 重量取整 / MRV 审计 / 疲劳加权）
  - 对每个 lift 做：重量换算（RPE→% 或直给 pct → 取整）+ MRV 周容量审计
  - 执行硬约束合规校验（频率 / 48h 间隔 / 后侧链距硬拉间隔 / 硬拉容量上限）
  - 输出 JSON（结构化数据）+ Markdown（周报骨架）给 AI 消费

不负责（留给 AI 编排 = 选择/排布/主观判断）：
  - 动作选择：排不排 OHP / 高翻 / 高拉 / 拉伸 / 有氧 / 核心 / 引体 / 孤立
  - 排布：同日肌群怎么组合（周一深蹲+引体、周五硬拉+高翻…）
  - 弱点变式选择、减载切分、块间过渡、退阶决策、双进阶递增、RPE 主观记录
  - 最终计划文档编排

v1 支持模板：full_body(3) / upper_lower(4) / ppl(5)
v1 不做：6/7 天自动生成（有氧日不进设计器）

边界红线（用户原话）：脚本充其量做的是重复性运算的工作。

用法：
  python scripts/design_program.py --input plan.yaml --out-json out.json --out-md week.md
  python scripts/design_program.py --input plan.json   # 自动识别 json/yaml
"""

import argparse
import json
import os
import sys

# ── 复用现有 4 脚本的函数层（不重写 RPE_TABLE/MRV_TABLE）────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from rpe_to_percentage import calculate_weight_from_1rm  # noqa: E402
from round_weight import round_weight  # noqa: E402
from calculate_mrv import calculate_mrv_status  # noqa: E402

# ── 模板定义（v1：3/4/5 天经典）──────────────────────────────────────
# 每个主项出现日（用于频率 / 48h 间隔校验）
TEMPLATES = {
    "full_body": {
        "days": ["Mon", "Wed", "Fri"],
        "main_lifts": {  # 每日主项顺序（category 标 primary/olympic）
            "Mon": [("squat", "primary"), ("bench", "primary")],
            "Wed": [("deadlift", "primary"), ("ohp", "primary")],
            "Fri": [("squat", "primary"), ("bench", "primary")],  # 周五变式或轻量由 AI 决定
        },
        "label": "全身 3 天",
    },
    "upper_lower": {
        "days": ["Mon", "Tue", "Thu", "Fri"],
        "main_lifts": {
            "Mon": [("squat", "primary")],
            "Tue": [("bench", "primary")],
            "Thu": [("deadlift", "primary")],
            "Fri": [("bench", "primary")],  # 或 OHP，AI 决定
        },
        "label": "上/下分化 4 天",
    },
    "ppl": {
        "days": ["Mon", "Tue", "Wed", "Fri", "Sat"],
        "main_lifts": {
            "Mon": [("squat", "primary")],    # Push
            "Tue": [("bench", "primary")],    # Pull
            "Wed": [("deadlift", "primary")], # Legs
            "Fri": [("squat", "primary")],    # Push 变式
            "Sat": [("bench", "primary")],    # Pull 变式
        },
        "label": "推/拉/腿 5 天",
    },
}

# 动作 → MRV 周组数区间（自然中级，来源：skill references 的 MRV/MEV/MAV 表）
# AI 可在 YAML mrv_overrides 覆盖；辅助动作不在此表则仅做重量换算不强制审计
MRV_DEFAULTS = {
    "squat":    {"mev": 10, "mav": 16, "mrv": 18},
    "bench":    {"mev": 8,  "mav": 14, "mrv": 20},
    "deadlift": {"mev": 4,  "mav": 6,  "mrv": 6},     # 全程硬拉专项期上限 ≤6 组/周（硬约束）
    "ohp":      {"mev": 8,  "mav": 14, "mrv": 16},
    "hang_power_clean": {"mev": 3, "mav": 6, "mrv": 9},   # 高翻（爆发力，容量低）
    "hang_high_pull":   {"mev": 3, "mav": 6, "mrv": 9},  # 高拉
    "pause_squat":      {"mev": 6, "mav": 10, "mrv": 12},  # 弱点变式按间接刺激计
    "front_squat":      {"mev": 6, "mav": 10, "mrv": 14},
    "pause_deadlift":   {"mev": 2, "mav": 4,  "mrv": 6},
    "rdl":              {"mev": 4, "mav": 8,  "mrv": 12},
    "good_morning":     {"mev": 3, "mav": 6,  "mrv": 10},
    "pullup":           {"mev": 10, "mav": 18, "mrv": 22},
}

# 硬拉容量强约束（见 deadlift-volume-management.md）
DEADLIFT_FULL_WEEKLY_CAP = 6
DEADLIFT_MIN_GAP_DAYS = 3  # 硬拉→下一后侧链刺激 ≥48h（3 天间隔为安全值）

# 需要 48h 间隔约束的主项类别（任何被标为需间隔的主项都数）
INTERVAL_CONSTRAINED_CATEGORIES = {"primary", "olympic"}

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _day_idx(day):
    return DAY_ORDER.index(day)


def compute_lift(exercise, one_rm, reps, rpe=None, pct=None, plate_step=2.5,
                 deload_factor=1.0, tm=None, no_weight=False):
    """计算单个 lift：RPE→%→重量→取整，或直接 pct→重量→取整。
    - 优先用 pct（直接 %1RM，适合高次/奥举/不在 RPE 表的动作）
    - 否则用 RPE 表（rpe_to_percentage，仅支持 1-5 次精确组合）
    - tm 可选：若提供则用 TM 锚定（而非 1RM）做 % 基准
    - no_weight=True：自重/次数导向动作（如引体），不换算重量，仅审计组数
    """
    if no_weight or (rpe is None and pct is None):
        # 自重/次数导向动作：只记录组数，重量标 null（MRV 审计仍做）
        return {
            "exercise": exercise,
            "reps": reps,
            "rpe": rpe,
            "pct_1rm": None,
            "raw_weight": None,
            "weight": None,
            "no_weight": True,
        }
    base = tm if tm is not None else one_rm
    if pct is not None:
        raw_pct = base * (pct / 100.0)
        rounded = round_weight(raw_pct * deload_factor, plate_step)
        return {
            "exercise": exercise,
            "reps": reps,
            "rpe": rpe,
            "pct_1rm": pct,
            "raw_weight": round(raw_pct * deload_factor, 2),
            "weight": rounded,
        }
    # RPE 路径（1-5 次，RPE 表只覆盖精确组合）
    try:
        raw_val = calculate_weight_from_1rm(base, reps, rpe)
    except ValueError:
        raise ValueError(
            f"动作 {exercise}：RPE 表无 reps={reps}/rpe={rpe} 组合，且未提供 pct。"
            f"高次(>5)或奥举/辅助动作请直接给 pct 字段（如 pct: 68 表示 68% 1RM），"
            f"或自重动作设 no_weight: true。"
        )
    rounded = round_weight(raw_val * deload_factor, plate_step)
    return {
        "exercise": exercise,
        "reps": reps,
        "rpe": rpe,
        "pct_1rm": round(raw_val / base * 100, 1),
        "raw_weight": round(raw_val * deload_factor, 2),
        "weight": rounded,
    }


def run_base(yaml_data):
    """base_rpe_pct 模块：计算所有 lift + MRV 审计 + 合规校验"""
    one_rm = yaml_data["one_rm"]
    intent = yaml_data.get("intent", {})
    phase = intent.get("phase", "volume")
    template = yaml_data["template"]
    plate_step = yaml_data.get("plate_step", 2.5)
    deload_factor = yaml_data.get("deload_factor", 0.6 if phase == "deload" else 1.0)

    # TM 锚定：默认 = 1RM；若 amrap_reestimate 且提供了 tm_anchor，用锚定值
    tm_mode = yaml_data.get("tm_mode", "amrap_reestimate")
    tm_overrides = yaml_data.get("tm_overrides", {})
    tm = {}
    for ex in one_rm:
        if tm_mode == "amrap_reestimate":
            anchor = tm_overrides.get(ex, {}).get("tm_anchor")
            tm[ex] = anchor if anchor is not None else one_rm[ex]
        else:
            tm[ex] = one_rm[ex]

    # MRV 表：内置默认 + AI 覆盖
    mrv_table = dict(MRV_DEFAULTS)
    mrv_table.update(yaml_data.get("mrv_overrides", {}))

    tpl = TEMPLATES[template]
    out_lifts = []
    compliance = {"errors": [], "warnings": []}

    # 周组数统计（用于 MRV 审计 + 频率校验）
    weekly_sets = {}        # exercise -> total sets
    primary_days = {}       # exercise(需间隔) -> [day, ...]
    dl_days = []            # 硬拉出现日

    # 读 week_structure（list of {day, lifts:[...]}）
    week_struct = yaml_data.get("week_structure", [])
    for day_block in week_struct:
        day = day_block["day"]
        for spec in day_block.get("lifts", []):
            ex = spec["exercise"]
            reps = spec.get("reps", 5)
            rpe = spec.get("rpe", 7.5)
            sets = spec.get("sets", 3)
            pct = spec.get("pct", None)
            category = spec.get("category", "assistance")
            no_weight = spec.get("no_weight", False)
            # 奥举/主项用 TM 锚定（若提供了 tm）；辅助用 1RM
            use_tm = ex in tm and category in INTERVAL_CONSTRAINED_CATEGORIES
            lift = compute_lift(
                ex, one_rm.get(ex, one_rm.get("deadlift")), reps, rpe, pct,
                plate_step, deload_factor, tm=tm.get(ex) if use_tm else None,
                no_weight=no_weight
            )
            lift.update({"day": day, "sets": sets, "category": category})
            out_lifts.append(lift)
            weekly_sets[ex] = weekly_sets.get(ex, 0) + sets
            if category in INTERVAL_CONSTRAINED_CATEGORIES:
                primary_days.setdefault(ex, []).append(day)
            if ex == "deadlift":
                dl_days.append(day)

    # MRV 审计（仅对 mrv_table 中有的动作）
    mrv_report = {}
    for ex, total in weekly_sets.items():
        if ex in mrv_table:
            cap = mrv_table[ex]["mrv"]
            st = calculate_mrv_status(total, cap)
            mrv_report[ex] = {"weekly_sets": total, "mrv": cap, **st}
        else:
            mrv_report[ex] = {"weekly_sets": total, "mrv": None,
                              "status": "unaudited", "note": "未在 MRV 表，仅做重量换算"}

    # 合规校验
    # 1) 硬拉容量上限（全程硬拉 ≤6 组/周）
    dl_sets = weekly_sets.get("deadlift", 0)
    if dl_sets > DEADLIFT_FULL_WEEKLY_CAP:
        compliance["errors"].append(
            f"硬拉全程组数 {dl_sets} > 上限 {DEADLIFT_FULL_WEEKLY_CAP} 组/周"
        )
    # 2) 硬拉间隔 ≥48h（相邻硬拉日间隔）
    if len(dl_days) >= 2:
        for i in range(len(dl_days) - 1):
            gap = _day_idx(dl_days[i + 1]) - _day_idx(dl_days[i])
            if gap < DEADLIFT_MIN_GAP_DAYS:
                compliance["errors"].append(
                    f"硬拉间隔 {gap} 天 < {DEADLIFT_MIN_GAP_DAYS} 天（48h 约束）"
                )
    # 3) 每主项频率 ≤3 次/周（48h 派生）
    for ex, days in primary_days.items():
        if len(days) > 3:
            compliance["warnings"].append(
                f"{ex} 刺激 {len(days)} 天/周 > 3（压缩单次日容量风险）"
            )
    # 4) 后侧链距硬拉间隔规则（可配置 gap_rules）
    # 语义：硬拉日之后，第一个出现的后侧链刺激动作应间隔 ≥ min_gap_days（顺向，不取环形最短）
    for rule in yaml_data.get("gap_rules", []):
        after = rule["after"]
        before_list = rule["before"]
        min_gap = rule.get("min_gap_days", 3)
        after_days = sorted(primary_days.get(after, []), key=_day_idx)
        for b_ex in before_list:
            b_days = sorted(
                [d["day"] for d in week_struct if any(
                    l["exercise"] == b_ex for l in d.get("lifts", []))],
                key=_day_idx
            )
            if not b_days or not after_days:
                continue
            for b_day in b_days:
                # 找 b_day 之前最近的硬拉日（顺向间隔，不跨周回绕）
                prior_dl = [d for d in after_days if _day_idx(d) < _day_idx(b_day)]
                if not prior_dl:
                    continue  # 该后侧链在当周第一个硬拉之前，不查（如周一 RDL 在周四硬拉前）
                gap = _day_idx(b_day) - _day_idx(prior_dl[-1])
                if gap < min_gap:
                    compliance["warnings"].append(
                        f"{b_ex} 在 {b_day} 距硬拉 {prior_dl[-1]} 仅 {gap} 天 < {min_gap} 天（后侧链间隔规则）"
                    )

    return {
        "module": "base_rpe_pct",
        "phase": phase,
        "deload_factor": deload_factor,
        "lifts": out_lifts,
        "mrv": mrv_report,
        "compliance": compliance,
    }


# ── 可选模块函数（由 enabled_modules 白名单控制，默认不启用）──────────
# 来源：v0.9.6 吸收的 SBS / SSPT / Mag-Ort / YSY 机制

def tm_adjust(tm_anchor, mode="amrap_reestimate", last_rir_deviation=None):
    """TM 自动调节（SBS RIR 版 7 档逻辑）。
    amrap_reestimate 模式：直接返回锚定 TM（计划末 AMRAP→Epley 算出，整段固定）
    weekly_rir 模式：根据上周末组 RIR 偏离调节（±）
    """
    if mode == "amrap_reestimate":
        return tm_anchor
    if mode == "weekly_rir" and last_rir_deviation is not None:
        d = last_rir_deviation
        if d <= -2:
            adj = -5.0
        elif d < 0:
            adj = -2.0
        elif d == 0:
            adj = 0.0
        elif d == 1:
            adj = 0.5
        elif d == 2:
            adj = 1.0
        elif d == 3:
            adj = 1.5
        elif d == 4:
            adj = 2.0
        else:
            adj = 3.0
        return round(tm_anchor * (1 + adj / 100.0), 2)
    return tm_anchor


def single_at_8_to_weight(one_rm, rep_target=1):
    """Single@8 当日锚（SBS）：1 次 @RPE8 ≈ 90% 1RM。"""
    pct = calculate_weight_from_1rm(one_rm, 1, 8) / one_rm * 100
    return round_weight(one_rm * (pct / 100.0))


def rir_target(pct_1rm):
    """Last Set RIR 目标表查询（SBS RIR 版）。"""
    if pct_1rm <= 72.5:
        return 3
    elif pct_1rm <= 82.5:
        return 2
    elif pct_1rm <= 95:
        return 1
    else:
        return 0


def run_modules(yaml_data, result, tm):
    """按 enabled_modules 白名单执行可选模块，原地更新 result。"""
    enabled = yaml_data.get("enabled_modules", ["base_rpe_pct"])
    extras = {}

    if "tm_autoregulation" in enabled:
        mode = yaml_data.get("tm_mode", "amrap_reestimate")
        overrides = yaml_data.get("tm_overrides", {})
        tm_after = {}
        for ex, anchor in tm.items():
            ov = overrides.get(ex, {})
            if mode == "weekly_rir":
                dev = ov.get("last_rir_deviation")
                tm_after[ex] = tm_adjust(anchor, mode, dev)
            else:
                tm_after[ex] = tm_adjust(ov.get("tm_anchor", anchor), mode)
        extras["tm_autoregulation"] = {"mode": mode, "tm_after_adjust": tm_after}

    if "single_at_8" in enabled:
        sa8 = {ex: single_at_8_to_weight(tm[ex]) for ex in tm}
        extras["single_at_8"] = sa8

    if "rir_target_table" in enabled:
        for l in result["lifts"]:
            l["rir_target"] = rir_target(l["pct_1rm"])

    if "long_cycle_blocking" in enabled:
        wk = yaml_data.get("meta", {}).get("week")
        extras["long_cycle_blocking"] = {
            "note": "YSY 9×4 周块分块逻辑由 AI 编排；脚本仅标记 week 用于波浪判断",
            "week": wk,
        }

    if "deadlift_single_mode" in enabled:
        extras["deadlift_single_mode"] = {
            "note": "SSPT/Ort 硬拉单次高质量模式由 AI 编排 day 结构；脚本仅放宽 MRV 审计中的硬拉专项期上限",
        }

    if "tempo_rps" in enabled:
        extras["tempo_rps"] = {
            "note": "TUT 节奏码 + RPS 休息由 AI 在辅助动作表填写（见 tempo-and-rest.md）；脚本不自动生成",
        }

    if extras:
        result["modules"] = extras
    return result


def build_markdown(yaml_data, result):
    """生成周报骨架（给 AI 直接读 + 续写编排）"""
    tpl = TEMPLATES[yaml_data["template"]]
    lines = [f"# 训练周计划骨架（{tpl['label']} · phase={result['phase']}）", ""]
    if result["phase"] == "deload":
        lines.append(f"> 减载周：权重系数 ×{result['deload_factor']}")
        lines.append("")
    # 按日分组
    by_day = {}
    for l in result["lifts"]:
        by_day.setdefault(l["day"], []).append(l)
    # 读原始 week_structure 顺序
    for day_block in yaml_data.get("week_structure", []):
        day = day_block["day"]
        lines.append(f"## {day}")
        for l in by_day.get(day, []):
            line = (
                f"- **{l['exercise']}** ({l['category']}): "
                f"{l['sets']}×{l['reps']}"
            )
            if l["rpe"] is not None:
                line += f" @ RPE {l['rpe']}"
            if l["weight"] is not None:
                line += f" → {l['weight']}kg ({l['pct_1rm']}% 1RM)"
            else:
                line += " （自重/次数导向，不换算重量）"
            lines.append(line)
        if day not in by_day:
            lines.append("- （辅助/有氧，由 AI 编排）")
        lines.append("")
    # MRV 状态
    lines.append("## MRV 审计")
    for ex, m in result["mrv"].items():
        if m.get("status") == "unaudited":
            lines.append(f"- ⚪ {ex}: {m['weekly_sets']} 组（未在 MRV 表，仅重量换算）")
        else:
            flag = "⚠️" if m.get("status") in ("over", "near") else "✅"
            lines.append(f"- {flag} {ex}: {m['weekly_sets']}/{m['mrv']} 组 ({m.get('status')})")
    lines.append("")
    # 合规红绿灯
    lines.append("## 合规校验")
    if result["compliance"]["errors"]:
        for e in result["compliance"]["errors"]:
            lines.append(f"- 🔴 {e}")
    if result["compliance"]["warnings"]:
        for w in result["compliance"]["warnings"]:
            lines.append(f"- 🟡 {w}")
    if not result["compliance"]["errors"] and not result["compliance"]["warnings"]:
        lines.append("- 🟢 全部通过")
    lines.append("")
    lines.append("> 以下由 AI 编排：动作选择、排布、弱点变式、同日肌群组合、减载切分、退阶、双进阶、RPE 记录。")
    return "\n".join(lines)


def load_input(path):
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    if path.endswith(".json"):
        return json.loads(txt)
    # YAML：优先用 PyYAML（系统 Python 已预装 6.0.3）
    try:
        import yaml  # type: ignore
        return yaml.safe_load(txt)
    except ImportError:
        raise RuntimeError(
            "未找到 PyYAML。请使用已预装 PyYAML 的 Python 运行本脚本"
            "（如系统 Python：C:/Users/boyang/AppData/Local/Python/bin/python.exe）。"
        )


def main():
    ap = argparse.ArgumentParser(description="训练计划通用重复运算器（架构 B）")
    ap.add_argument("--input", "-i", required=True, help="YAML/JSON 输入路径")
    ap.add_argument("--out-json", "-j", help="输出 JSON 路径")
    ap.add_argument("--out-md", "-m", help="输出 Markdown 周报路径")
    args = ap.parse_args()

    data = load_input(args.input)
    result = run_base(data)
    # 按 enabled_modules 白名单执行可选模块（默认仅 base_rpe_pct）
    result = run_modules(data, result, {ex: data["one_rm"][ex] for ex in data["one_rm"]})

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON → {args.out_json}")
    if args.out_md:
        md = build_markdown(data, result)
        with open(args.out_md, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"✅ Markdown → {args.out_md}")

    # 终端摘要
    print(f"\n📋 {data['template']} · phase={result['phase']} · deload×{result['deload_factor']}")
    for l in result["lifts"]:
        rpe_s = f"@RPE{l['rpe']}" if l["rpe"] is not None else ""
        print(f"  {l['day']} {l['exercise']} ({l['category']}): {l['sets']}×{l['reps']} {rpe_s} → {l['weight']}kg")
    c = result["compliance"]
    if c["errors"]:
        print("🔴 合规错误:", c["errors"])
    if c["warnings"]:
        print("🟡 合规警告:", c["warnings"])
    if not c["errors"] and not c["warnings"]:
        print("🟢 合规通过")
    # 退出码：有 error 则非 0（可 gate CI / 提醒 AI）
    sys.exit(1 if c["errors"] else 0)


if __name__ == "__main__":
    main()
