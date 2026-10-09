#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strength-training-design skill — 个体校准报告（基线模型 → 使用者参数）

用训练者的 sRPE 日志判断：**这份数据现在能支撑到校准阶梯的第几级**，
以及**该不该继续拟合**。不自动写任何参数文件，只出报告与判定。

依据: references/consultation/individual-calibration.md（校准阶梯与判据）
      references/consultation/srpe-calibration.md（评分协议与拟合步骤）

校准阶梯（逐级升高，够到哪级用哪级，不要跳级）:
  L1 参考 1RM      —— 训练者实测 1RM 覆盖了多少个杠铃动作
  L2 时长口径      —— 实测时长 / 模型时长 是否稳定（>1.5 倍即不可靠）
  L3 课型 sRPE 基线 —— 按课型建基线表 + 漂移检测（n≥5 即可用，不需要拟合）
  L4 单次 AU 上限  —— 需「全」与「部分/未」两组都有样本
  L5 k 拟合         —— 可选。仅在隐含 k 极差 <1.5 倍时才允许

刻意不做的事:
  - 不写参数文件、不改基线代码。校准产物由使用者自己落到工作空间。
  - 不在 n 不足时硬凑拟合 —— 报告直接停在"数据不够"并说明还缺什么。
  - 不跨课型/跨周期外推。分组统计一律在课型内部做。

用法:
  python scripts/calibration_report.py --log srpe_log.csv
  python scripts/calibration_report.py --log srpe_log.csv --sessions c3_sessions.json --params my-params.json
  python scripts/calibration_report.py --log srpe_log.csv --json > report.json
"""
import argparse
import csv
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── 判据阈值（工程约定，见 individual-calibration.md §3）────────────────
K_RANGE_LIMIT = 1.5     # 隐含 k 极差上限（倍）。超过 → 停止拟合，转 L3
RHO_FIT_MIN = 0.7       # Spearman rho 达到此值才允许固化 k
DURATION_TOL = 1.5      # 实测时长 / 模型时长 极差上限（倍）。超过 → 时长口径不可靠
MIN_SAMPLES = 5         # 建立课型基线表的最小样本数（每课型）


# ── 统计小工具 ────────────────────────────────────────────────────────
def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def ols(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None, None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


def ratio(vals):
    """正数的极差倍数（max/min）。min<=0 时返回 None。"""
    pos = [v for v in vals if v is not None and v > 0]
    if len(pos) < 2:
        return None
    return max(pos) / min(pos)


def num(x):
    x = (x or "").strip()
    if not x:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def median(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


# ── 会话类型归类 ──────────────────────────────────────────────────────
# 日志的 session 列常写成「周一 深蹲日（W2）」这类。校准的分组必须按课型
# 做，不能跨课型混合，所以从名称里取课型关键词；取不到就退回整串（此时报告会
# 提示分组可能过细）。
TYPE_KEYS = ["深蹲", "卧推", "硬拉", "轻量", "推", "拉", "腿", "肩", "背", "核心"]


def session_type(name):
    """从课名抽课型关键词。日志写「卧推日」、会话 JSON 写「卧推」，都要归到同一个桶。

    只返回关键词本身（不带"日"），显示时再补后缀 —— 归一与显示分开，避免
    "卧推日 vs 卧推"这类拼写差异把同一课型拆成两组。
    """
    s = name.split("（")[0].split("(")[0]
    for k in TYPE_KEYS:
        if k in s:
            return k
    return s.strip() or "(未标注)"


# 日志与会话 JSON 的命名习惯不同（「周一 深蹲日（W2）」vs「W2 周一 深蹲+垂直推」），
# 所以按「周次 + 周几 + 课型」三个 token 匹配，而不是整串互为子串。
_DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日", "周天"]
_WEEK_RE = re.compile(r"[Ww]\s*(\d+)")


def name_tokens(name):
    s = name.split("（")[0].split("(")[0]
    day = next((d for d in _DAYS if d in s), None)
    mw = _WEEK_RE.search(name)
    week = int(mw.group(1)) if mw else None
    return {"day": day, "week": week, "type": session_type(name)}


def match_candidates(log_name, sess_names):
    """返回与日志行判为同一节课的候选课时列表。

    判据（全部满足）：课型一致 · 周几一致 · 周次一致。
    日志带周次而候选不带（如「锚点·C2 周一 深蹲日」）时视为**弱候选** ——
    弱候选只在没有强候选时启用，避免锚点课顶替当周实测课。
    """
    tl = name_tokens(log_name)
    strong, weak = [], []
    for name in sess_names:
        ts = name_tokens(name)
        if ts["type"] != tl["type"]:
            continue
        if tl["day"] and ts["day"] and tl["day"] != ts["day"]:
            continue
        if tl["week"] is not None and ts["week"] is not None:
            if tl["week"] != ts["week"]:
                continue
            strong.append(name)
        elif tl["week"] is not None and ts["week"] is None:
            weak.append(name)
        else:
            strong.append(name)
    return strong or weak


# ── 读日志 ────────────────────────────────────────────────────────────
LOG_COLUMNS = {
    "date": ["date", "日期"],
    "session": ["session", "训练日", "session_name", "name"],
    "session_type": ["session_type", "课型", "type"],
    "a_model": ["a_model", "A", "a", "A_model"],
    "duration": ["duration_min", "duration", "时长", "duration_min_actual"],
    "srpe": ["srpe", "srpe_score", "sRPE", "rpe_session"],
    "outcome": ["next_session", "outcome", "完成度", "completion"],
}


def pick(row, aliases):
    low = {(k or "").strip().lower(): v for k, v in row.items()}
    for a in aliases:
        v = low.get(a.lower())
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def read_log(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = []
        for i, r in enumerate(csv.DictReader(fh), 1):
            stype = pick(r, LOG_COLUMNS["session_type"]) or session_type(
                pick(r, LOG_COLUMNS["session"]))
            name = pick(r, LOG_COLUMNS["session"])
            date = pick(r, LOG_COLUMNS["date"])
            if not name:
                # 没有 session 列/值时用「日期 + 课型」标识该行，不能整行丢掉 ——
                # 日志只要有时长与 sRPE 就有校准价值，标识只是给人看的。
                if not date and stype in ("", "(未标注)"):
                    continue
                name = "%s %s" % (date or ("#%d" % i), stype)
            rows.append({
                "date": date,
                "session": name,
                "type": stype or "(未标注)",
                "A": num(pick(r, LOG_COLUMNS["a_model"])),
                "dur": num(pick(r, LOG_COLUMNS["duration"])),
                "srpe": num(pick(r, LOG_COLUMNS["srpe"])),
                "outcome": pick(r, LOG_COLUMNS["outcome"]),
                "note": (r.get("note") or r.get("备注") or "").strip(),
            })
    return rows


# ── 从会话 JSON 自动补 A ──────────────────────────────────────────────
def fill_A_from_sessions(rows, sessions_path, params_path):
    """按「周次 + 周几 + 课型」匹配把模型 A 填进日志。

    匹配不到就留空 —— 不用"猜一个最像的"，静默填错 A 比不填糟得多。
    同一行匹配到多节课时（同名周次重复）也留空，并在报告里点名。
    """
    import session_strain as ss

    cfg = ss.default_config()
    if params_path:
        with open(params_path, encoding="utf-8") as fh:
            cfg = ss.merge_config(cfg, json.load(fh))
    sessions, cfg, _anchor = ss.load_input(sessions_path, cfg)

    computed = []
    for s in sessions:
        r = ss.simulate(s["blocks"], cfg)
        computed.append((s["name"], r["A"], r["duration_min"]))

    filled, missed, ambiguous = 0, [], []
    by_name = {name: (a, m) for name, a, m in computed}
    names = [c[0] for c in computed]
    for row in rows:
        if row["A"] is not None:
            continue
        hits = match_candidates(row["session"], names)
        if len(hits) == 1:
            row["A"], row["model_dur"] = by_name[hits[0]]
            filled += 1
        elif len(hits) > 1:
            ambiguous.append("%s -> %s" % (row["session"], " / ".join(h[:24] for h in hits[:3])))
        else:
            missed.append(row["session"])
    return filled, missed, ambiguous, computed


# ── 报告 ──────────────────────────────────────────────────────────────
class Out(object):
    def __init__(self):
        self.lines = []

    def __call__(self, s=""):
        self.lines.append(str(s))

    def rule(self, ch="-", n=78):
        self(ch * n)


def build_report(rows, anchor, filled, missed, ambiguous, one_rm_keys, source_note):
    o = Out()
    o("=" * 78)
    o("个体校准报告 —— 基线模型 → 使用者参数")
    o("=" * 78)
    o()
    o("数据来源: %s" % source_note)
    if filled is not None:
        o("A 由会话 JSON 计算填入: %d 行；未匹配: %d 行；匹配到多节（留空）: %d 行%s"
          % (filled, len(missed), len(ambiguous),
             ("（%s）" % "; ".join(ambiguous[:3])) if ambiguous else ""))
        if missed:
            o("  未匹配: %s" % ", ".join(missed[:6]))
    o("日志行数: %d" % len(rows))
    if anchor:
        o("锚点 A = %.2f（A%% 刻度分母；未指定时只报原始 A）" % anchor)

    complete = [r for r in rows if r["A"] is not None and r["dur"] is not None
                and r["srpe"] is not None]
    o("有效样本 (A + 时长 + sRPE 齐备): %d / %d" % (len(complete), len(rows)))

    # ── 覆盖度 ────────────────────────────────────────────────────────
    o()
    o.rule()
    o("1  覆盖度与 L1（参考 1RM）")
    o.rule()
    types = {}
    for r in complete:
        types.setdefault(r["type"], []).append(r)
    o("%-14s %5s %8s %8s %8s %8s" % ("课型", "n", "A中位", "时长中位", "sRPE中位", "sRPE极差"))
    for t in sorted(types, key=lambda x: -len(types[x])):
        g = types[t]
        sr = [x["srpe"] for x in g]
        o("%-14s %5d %8s %8s %8s %8s"
          % (t, len(g),
             "%.2f" % median([x["A"] for x in g]) if median([x["A"] for x in g]) else "-",
             "%.0f" % median([x["dur"] for x in g]) if median([x["dur"] for x in g]) else "-",
             "%.1f" % median(sr) if median(sr) else "-",
             "%.1f" % (max(sr) - min(sr)) if len(sr) > 1 else "-"))
    o()
    if not types:
        o("⚠ 没有任何有效样本。先补 A（--sessions 自动匹配，或手填日志 A 列）与 sRPE。")
    elif len(types) < 2:
        o("⚠ 只出现 1 种课型。校准必须在课型内部做（跨课型混合会把周期形状"
          "当成个人特征），单课型只能建该课型的基线。")
    for t in sorted(types):
        if len(types[t]) < MIN_SAMPLES:
            o("· %s 仅 n=%d（<%d）：够记基线，不够谈拟合。"
              % (t, len(types[t]), MIN_SAMPLES))

    if one_rm_keys is not None:
        o()
        o("L1 参考 1RM：会话涉及的杠铃动作中，已给 1RM 的 key ——")
        o("  %s" % (", ".join(one_rm_keys) if one_rm_keys else "（无）"))

    # ── L2 时长口径 ──────────────────────────────────────────────────
    o()
    o.rule()
    o("2  L2 时长口径（拟合前必须先过这一关）")
    o.rule()
    with_mdur = [r for r in complete if r.get("model_dur")]
    if with_mdur:
        rr = [r["dur"] / r["model_dur"] for r in with_mdur if r["model_dur"]]
        r_range = ratio(rr)
        o("实测时长 / 模型时长：n=%d  中位 %.2f  极差 %.1f 倍"
          % (len(rr), median(rr), r_range if r_range else float("nan")))
        if r_range and r_range > DURATION_TOL:
            o("判定: ✗ 超过 %.1f 倍 —— **时长口径不一致**，AU 的离散主要来自这里，"
              "不是 A 与 AU 不线性。" % DURATION_TOL)
            o("      先统一口径（同一计时起止点）再谈拟合；此时禁止进入 L5。")
        else:
            o("判定: ✓ 口径稳定（极差 ≤ %.1f 倍），AU 的变化不能只怪时长。" % DURATION_TOL)
    else:
        o("未提供会话 JSON，无法算模型时长 —— 本级跳过。")
        o("补法：加 --sessions <会话.json> [--params <参数.json>]，本脚本会按名称匹配填 A 并同算模型时长。")

    # ── Step 1 诊断 ──────────────────────────────────────────────────
    o()
    o.rule()
    o("3  Step 1 诊断：AU = sRPE × 实际时长  vs  模型 A")
    o.rule()
    for r in complete:
        r["AU"] = r["srpe"] * r["dur"]
    xs = [r["A"] for r in complete]
    ys = [r["AU"] for r in complete]
    ks = [r["AU"] / r["A"] for r in complete if r["A"] > 0]
    k_range = ratio(ks)
    rho = pearson(ranks(xs), ranks(ys)) if len(complete) >= 3 else None
    r_lin = pearson(xs, ys) if len(complete) >= 3 else None
    dur_rho = pearson(ranks([r["dur"] for r in complete]), ranks(ys)) if len(complete) >= 3 else None

    o("%-26s %4s %8s %8s %8s %9s %8s" % ("训练日", "课型", "A", "时长", "sRPE", "AU", "完成度"))
    for r in sorted(complete, key=lambda x: x["AU"]):
        o("%-26s %-8s %8.2f %8.0f %8.1f %9.0f %8s"
          % (r["session"][:26], r["type"][:8], r["A"], r["dur"], r["srpe"], r["AU"],
             r["outcome"] or "-"))
    o()
    o("AU 与模型 A 的关系：")
    o("  Pearson  r     = %s" % ("%.3f" % r_lin if r_lin is not None else "n/a"))
    o("  Spearman rho   = %s   ← 主看这个（排序是否一致）"
      % ("%.3f" % rho if rho is not None else "n/a"))
    o("  AU 与实际时长的 rho = %s   ← 对照项：它更高说明 AU 被时长支配"
      % ("%.3f" % dur_rho if dur_rho is not None else "n/a"))
    o("  隐含 k = AU/A 极差 = %s 倍（上限 %.1f）"
      % ("%.2f" % k_range if k_range else "n/a", K_RANGE_LIMIT))

    # ── L3 课型基线 ──────────────────────────────────────────────────
    o()
    o.rule()
    o("4  L3 课型基线表 + 漂移检测（不需要拟合）")
    o.rule()
    o("%-14s %5s %8s %8s %8s   %s" % ("课型", "n", "时长中位", "sRPE中位", "sRPE基线带宽", "漂移"))
    baselines = {}
    for t in sorted(types, key=lambda x: -len(types[x])):
        g = types[t]
        sr = [x["srpe"] for x in g]
        base = median(sr)
        baselines[t] = base
        drift = []
        if len(g) >= 3 and base is not None:
            for x in g:
                if abs(x["srpe"] - base) > 1.0:
                    drift.append("%s(%s)" % (x["session"][:14], x["srpe"]))
        if len(sr) < 2:
            note = "样本不足（n=%d）" % len(sr)
        elif drift:
            note = "漂移: " + "; ".join(drift)
        else:
            note = "无"
        o("%-14s %5d %8s %8s %8s   %s"
          % (t, len(g),
             "%.0f" % median([x["dur"] for x in g]) if median([x["dur"] for x in g]) else "-",
             "%.1f" % base if base is not None else "-",
             "%.1f" % (max(sr) - min(sr)) if len(sr) > 1 else "-",
             note))
    o()
    o("用法：同课型固定结构下 sRPE 偏离基线 >1 档 = 有变化（换动作、加量、"
      "减重、睡眠差）。此时先怀疑计划改动，不要先怀疑模型。")
    o("⚠ 基线只在**同一课型 + 同一周期结构**内可比。容量期与力量期、测试周与"
      "常规周的 sRPE 不在同一基线上，换阶段要重建。")

    # ── L4 单次上限 ──────────────────────────────────────────────────
    o()
    o.rule()
    o("5  L4 单次 AU 上限（需要后果变量分组）")
    o.rule()
    ok = [r for r in complete if r["outcome"] in ("全", "完成", "ok")]
    bad = [r for r in complete if r["outcome"] in ("部分", "未", "部分/未")]
    if ok and bad:
        hi_ok = max(r["AU"] for r in ok)
        lo_bad = min(r["AU"] for r in bad)
        if lo_bad > hi_ok:
            o("✓ 单次上限落在 AU %.0f – %.0f 之间" % (hi_ok, lo_bad))
            if anchor:
                o("  对应 A%%：%.0f – %.0f（锚点 A=%.2f）"
                  % (min(r["A"] for r in ok) / anchor * 100,
                     max(r["A"] for r in bad) / anchor * 100, anchor))
            o("  这是「这次练过了」的可执行定义。补齐区间内样本能把线画实。")
        else:
            o("✗ 两组 AU 区间重叠（完成组最高 %.0f，未完成组最低 %.0f）——"
              "AU 单独解释不了后果。" % (hi_ok, lo_bad))
            o("  处置：引入外部变量（睡眠 / 周次位置 / 前一日量），或按周期阶段分开看。")
    else:
        o("画不了线：需要「全」与「部分/未」两组各有样本（当前：完成 %d / 未完成 %d）。"
          % (len(ok), len(bad)))
        o("  这一列不能省 —— sRPE 只测代价，测不出后果。")

    # ── L5 判定 ──────────────────────────────────────────────────────
    o()
    o.rule()
    o("6  L5 拟合判定（可选级）")
    o.rule()
    # 判定顺序：先报**最强的停止信号**。k 极差超限比"样本不足"更有指导意义 ——
    # 两者都指向"别拟合"，但前者指出了具体原因（口径或非线性），可以直接去修。
    verdict = None
    if not complete:
        verdict = ("skip",
                   "没有有效样本：先补 A（--sessions 自动匹配或手填）与 sRPE。")
    elif k_range is not None and k_range > K_RANGE_LIMIT:
        extra = "（n=%d 同时偏小，n 达标后重测）" % len(complete) if len(complete) < 10 else ""
        verdict = ("stop",
                   "隐含 k 极差 %.1f 倍 > %.1f：**停止拟合**。不要靠加变量救，"
                   "改用 L3 查表 + 漂移检测。%s" % (k_range, K_RANGE_LIMIT, extra))
    elif len(types) < 2:
        msg = ("只有 1 种课型：回归无法跨课型验证（系数只对这一课型成立）。"
               "建该课型基线即可。")
        verdict = ("stop", msg)
    elif rho is not None and rho < RHO_FIT_MIN:
        verdict = ("stop",
                   "rho %.3f < %.1f：排序都不一致，A 不能当 AU 的代理。"
                   "先查时长口径与课型混合，再考虑拆两项回归。"
                   % (rho, RHO_FIT_MIN))
    elif len(complete) < 10:
        verdict = ("skip",
                   "n=%d < 10：样本量不足，拟合出的曲线往往是这个周期的形状，"
                   "不是这个人的特征。停在 L3/L4。" % len(complete))
    else:
        verdict = ("ok",
                   "rho %.3f、隐含 k 极差 %.2f 倍、跨 %d 种课型 —— 可以固化 k = b，"
                   "但仍禁止外推到其他周期结构。"
                   % (rho, k_range, len(types)))
    o("判定: %s" % verdict[1])
    o()
    if verdict[0] == "ok":
        a0, b = ols(xs, ys)
        if b:
            o("  AU = %+.1f + %.1f·A" % (a0, b))
            o("  单次上限 AU → A = (AU - %.1f) / %.1f" % (a0, b))
            if anchor:
                for au in (300, 400, 500, 600, 700, 800):
                    a_val = (au - a0) / b
                    o("    AU %4d -> A %7.2f -> A%% %6.1f" % (au, a_val, a_val / anchor * 100))
    o()
    o("=" * 78)
    return o.lines, verdict


def main():
    ap = argparse.ArgumentParser(description="个体校准报告：判断 sRPE 日志能支撑到校准阶梯第几级")
    ap.add_argument("--log", required=True, help="sRPE 日志 CSV")
    ap.add_argument("--sessions", help="会话 JSON（用于按名称匹配补 A 与模型时长）")
    ap.add_argument("--params", help="参数 JSON（与 --sessions 配合）")
    ap.add_argument("--anchor", type=float, help="锚点 A（A%% 刻度分母）")
    ap.add_argument("--out", help="报告输出路径（默认打印到 stdout）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args()

    if not os.path.exists(args.log):
        print("找不到日志: %s" % args.log, file=sys.stderr)
        return 1

    rows = read_log(args.log)
    filled = missed = ambiguous = None
    one_rm_keys = None
    source_note = args.log
    if args.sessions:
        if not os.path.exists(args.sessions):
            print("找不到会话文件: %s" % args.sessions, file=sys.stderr)
            return 1
        try:
            filled, missed, ambiguous, _ = fill_A_from_sessions(rows, args.sessions, args.params)
            source_note = "%s + %s" % (args.log, args.sessions)
        except Exception as e:                      # noqa: BLE001 — 报告工具不该因数据问题崩掉
            print("读取会话文件失败（继续，只用日志里已有的 A）: %s" % e, file=sys.stderr)
            filled, missed, ambiguous = 0, [], []
        if args.params:
            try:
                with open(args.params, encoding="utf-8") as fh:
                    pj = json.load(fh)
                one_rm_keys = sorted(k for k, v in (pj.get("one_rm") or {}).items() if v)
            except Exception:                        # noqa: BLE001
                one_rm_keys = None

    lines, verdict = build_report(rows, args.anchor, filled, missed, ambiguous,
                                  one_rm_keys, source_note)
    text = "\n".join(lines)

    if args.json:
        complete = [r for r in rows if r["A"] is not None and r["dur"] is not None
                    and r["srpe"] is not None]
        payload = {
            "source": source_note,
            "rows": len(rows),
            "complete": len(complete),
            "anchor": args.anchor,
            "a_filled": filled,
            "a_unmatched": missed,
            "sessions": complete,
            "one_rm_keys": one_rm_keys,
            "verdict": verdict[0],
            "verdict_text": verdict[1],
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("报告已写出 -> %s" % args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
