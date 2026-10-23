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
AU_DEGRADE_MAX = 2.0    # 分课型「AU ~ A」相对「AU ~ A + 时长」的样本外劣化倍数上限。
                        # 超过此值说明 A 缺的那部分信息正是时长 —— 换算表是残缺的，
                        # 使用者必须同时知道时长才敢用。
                        # 这是 L5 唯一新增的实质门：它测的是「A 缺不缺时长」，
                        # 与「课型内 k 极差」不重合（k = AU/A，k 极差与 AU~A
                        # 的残差是同一件事的两种说法，故不再另设相对误差门）。
MIN_FIT_SAMPLES = 5     # 课型内做样本外评估所需的最小样本数。
                        # 低于此数，每折剩不到 3 点拟合 2 参数，误差估计本身
                        # 没有精度 —— 那种课型的结论是「样本不足」，不是通过或不通过。
                        # 两个阈值都是工程约定，见 individual-calibration.md §4。


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


def ols_multi(cols, y):
    """多元最小二乘（含截距）。cols = [[x1_i], [x2_i], ...]，y = [y_i]。

    返回 (截距, [斜率...], R²)，不可算时返回 None。
    不可算的两种情形：样本量不足（自由度 ≤0）、或正规方程奇异（某列在样本内
    与其他列完全共线 —— 这在「A 随周次线性涨、时长也随周次线性涨」的合成数据里
    必然发生，所以必须有守卫而不是让它除零崩掉）。
    """
    n = len(y)
    k = len(cols)
    if n < k + 2:                     # 至少留 1 个自由度
        return None
    X = [[1.0] + [cols[j][i] for j in range(k)] for i in range(n)]
    m = k + 1
    A = [[sum(X[i][r] * X[i][c] for i in range(n)) for c in range(m)] for r in range(m)]
    b = [sum(X[i][r] * y[i] for i in range(n)) for r in range(m)]
    for c in range(m):
        piv = max(range(c, m), key=lambda r: abs(A[r][c]))
        if abs(A[piv][c]) < 1e-10:
            return None
        A[c], A[piv] = A[piv], A[c]
        b[c], b[piv] = b[piv], b[c]
        for r in range(m):
            if r == c:
                continue
            f = A[r][c] / A[c][c]
            for cc in range(c, m):
                A[r][cc] -= f * A[c][cc]
            b[r] -= f * b[c]
    beta = [b[r] / A[r][r] for r in range(m)]
    yhat = [sum(beta[r] * X[i][r] for r in range(m)) for i in range(n)]
    sse = sum((y[i] - yhat[i]) ** 2 for i in range(n))
    sst = sum((v - sum(y) / n) ** 2 for v in y)
    if sst <= 0:
        return None
    return beta[0], beta[1:], 1 - sse / sst


def loocv_rmse(cols, y):
    """留一法 RMSE：每折用其余样本拟合，预测留出的那一点。

    训练内 R² 会骗人 —— 加了变量几乎必然变好看。样本外误差才是模型有没有用的
    唯一证据。样本量不够（每折自由度不足）或某折奇异时返回 None。
    """
    n = len(y)
    if n < 4:
        return None
    errs = []
    for i in range(n):
        keep = [j for j in range(n) if j != i]
        res = ols_multi([[c[j] for j in keep] for c in cols], [y[j] for j in keep])
        if res is None:
            return None
        b0, bs, _ = res
        pred = b0 + sum(bs[j] * cols[j][i] for j in range(len(cols)))
        errs.append(y[i] - pred)
    return math.sqrt(sum(e * e for e in errs) / len(errs))


def per_type_fit_quality(rows):
    """逐课型评估 L5 的产出「AU = a + b·A」靠不靠得住。

    **必须在课型内做。** L5 的产物是分课型的换算表，那么「这张表靠不靠得住」
    只能在课型内回答。跨课型评估时，课型间的量级差会主导残差，把课型内
    的真实差异盖掉（实测：同样 n=4，卧推课型内相对误差 109%、深蹲 27%，
    差 4 倍纯属噪声）。

    每课型算：
        AU ~ A          L5 的产物本身：LOOCV RMSE、相对误差（参考信息）
        AU ~ A + 时长   参照模型：LOOCV RMSE。劣化倍数 = 前者 / 后者，
                        这是「A 缺不缺时长」的唯一判据
        样本量是否够做评估（n ≥ MIN_FIT_SAMPLES）

    返回 {课型: {...}}。样本不足的课型其 rel_err / degrade 为 None ——
    「样本不足」是第三种状态，不能当成通过。
    """
    out = {}
    for t in sorted({r["type"] for r in rows}):
        g = [r for r in rows if r["type"] == t]
        a = [r["A"] for r in g]
        dur = [r["dur"] for r in g]
        au = [r["srpe"] * r["dur"] for r in g]     # AU 自己算，不依赖调用方预先填
        m_a = ols_multi([a], au)
        m_both = ols_multi([a, dur], au)
        rec = {"n": len(g), "au_median": median(au)}
        if m_a is not None:
            rec["r2"] = m_a[2]
            rec["a_coef"] = m_a[1][0]
            rec["a_intercept"] = m_a[0]
        if m_both is not None:
            rec["r2_both"] = m_both[2]
        l_a = loocv_rmse([a], au)
        l_both = loocv_rmse([a, dur], au)
        rec["loocv"] = l_a
        rec["loocv_both"] = l_both
        if l_a is not None and rec["au_median"]:
            rec["rel_err"] = l_a / rec["au_median"]
        else:
            rec["rel_err"] = None
        if l_a is not None and l_both:
            rec["degrade"] = l_a / l_both
        else:
            rec["degrade"] = None
        # 可评估 = 样本量够 + 主判据（相对误差）算得出来。
        # 劣化倍数在 A 与时长共线时算不出来（参照模型奇异），那种情况下该门
        # 不参与判决 —— 共线本身说明「加时长」没有额外信息可加。
        rec["evaluable"] = (len(g) >= MIN_FIT_SAMPLES
                            and rec.get("rel_err") is not None)
        out[t] = rec
    return out


def ratio(vals):
    """正数的极差倍数（max/min）。min<=0 时返回 None。"""
    pos = [v for v in vals if v is not None and v > 0]
    if len(pos) < 2:
        return None
    return max(pos) / min(pos)


def duration_split(rows):
    """把「实测时长 / 模型时长」的离散拆成课型内与课型间两部分。

    两者含义完全不同，混在一起看会得出错误结论：
      课型内离散大 → **个人计时口径不稳**（同类型课都算不准），要改计时方式；
      课型间离散大 → **个人其实很稳**，是模型对某些课型的时长估计系统性偏，
                    要改的是「按课型给时长系数」，不是让使用者统一计时。

    返回 (within_max, between_range, per_type_median, per_type_within)。
    """
    per_type, per_type_within = {}, {}
    for r in rows:
        if not r.get("model_dur"):
            continue
        per_type.setdefault(r["type"], []).append(r["dur"] / r["model_dur"])
    for t, vals in per_type.items():
        per_type[t] = median(vals)
        per_type_within[t] = ratio(vals)
    within = [v for v in per_type_within.values() if v]
    return (max(within) if within else None,
            ratio(list(per_type.values())),
            per_type,
            per_type_within)


def within_type_agreement(rows):
    """课型内方向一致率：同一课型相邻两次，A 变化方向与 AU 变化方向是否相同。

    这是模型排序能力的**唯一有效检验**。跨课型 rho 低不代表模型坏了 ——
    A 与 AU 的跨课型刻度本就未经检验（不同课型的时长结构、局部代价占比不同），
    把它们混在一起算相关系数没有意义：测出的差距是刻度的，不是使用者的。
    课型内方向一致才是可解释的证据。

    「相邻」按时间排（用 date；无日期时退回按 A 排序）。方向以**时间在后的一节
    减时间在前的一节**为准，报出来的正负号与周的先后一致，不用心算。

    返回 (一致数, 总数, 明细列表)。
    """
    per_type = {}
    for r in rows:
        per_type.setdefault(r["type"], []).append(r)
    has_date = any(r.get("date") for r in rows)
    agree, total, detail = 0, 0, []
    for t in sorted(per_type):
        g = [r for r in per_type[t] if r.get("A") and r.get("AU") is not None]
        g.sort(key=(lambda r: (r.get("date") or "", r["session"])) if has_date
               else (lambda r: r["A"]))
        for i in range(len(g) - 1):
            lo, hi = g[i], g[i + 1]
            if hi["A"] == lo["A"]:
                continue
            total += 1
            dA = hi["A"] - lo["A"]
            dU = hi["AU"] - lo["AU"]
            ok = (dA > 0) == (dU > 0)
            agree += ok
            detail.append((t, lo["session"], hi["session"], dA, dU, ok))
    return agree, total, detail


def k_by_type(rows):
    """隐含 k = AU/A 的课型内极差与课型间极差，分开报。"""
    per_type = {}
    for r in rows:
        if r.get("A") and r["A"] > 0 and r.get("AU") is not None:
            per_type.setdefault(r["type"], []).append(r["AU"] / r["A"])
    within = {t: ratio(v) for t, v in per_type.items()}
    within = {t: v for t, v in within.items() if v}
    flat = [x for v in per_type.values() for x in v]
    return within, (max(flat) / min(flat) if len(flat) > 1 and min(flat) > 0 else None)


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
    within_range, between_range, per_type_med, per_type_within = duration_split(complete)
    with_mdur = [r for r in complete if r.get("model_dur")]
    if with_mdur:
        rr = [r["dur"] / r["model_dur"] for r in with_mdur if r["model_dur"]]
        r_range = ratio(rr)
        o("实测时长 / 模型时长：n=%d  中位 %.2f  全体极差 %.1f 倍"
          % (len(rr), median(rr), r_range if r_range else float("nan")))
        o()
        o("%-14s %6s %8s   %s" % ("课型", "n", "比值中位", "课型内极差"))
        for t in sorted(per_type_med):
            g = [x for x in with_mdur if x["type"] == t]
            wr = per_type_within[t]
            o("%-14s %6d %8.2f   %s"
              % (t, len(g), per_type_med[t],
                 "%.2f 倍" % wr if wr else "n=1，无法判断"))
        o()
        o("→ 读法：两个数字指向完全不同的处置，别混为一谈。")
        if within_range and within_range > DURATION_TOL and between_range \
                and between_range > DURATION_TOL:
            o("⚠ **课型内 %.1f 倍 + 课型间 %.1f 倍都超限** —— 先修计时口径，"
              "课型间差异在计时修好后重测。" % (within_range, between_range))
        elif within_range and within_range > DURATION_TOL:
            o("判定: ✗ 课型内 %.1f 倍 > %.1f —— **个人计时口径不稳**（同类型课"
              "之间都算不准）。先统一计时起止点；此时禁止进入 L5。"
              % (within_range, DURATION_TOL))
        elif between_range and between_range > DURATION_TOL:
            # 比值 = 实测 / 模型。比值 < 1 = 实际用时比模型短 = 模型高估。
            over = min(per_type_med, key=lambda t: per_type_med[t]) \
                if per_type_med else "?"
            under = max(per_type_med, key=lambda t: per_type_med[t]) \
                if per_type_med else "?"
            o("判定: △ 课型内 %.2f 倍（稳）但课型间 %.1f 倍 > %.1f —— "
              "**个人计时是稳的**，是模型对不同课型的时长估计有系统性偏差。"
              % (within_range, between_range, DURATION_TOL))
            o("      处置不是让使用者统一计时，而是**按课型给时长系数**："
              "模型高估最多的是「%s」（实测只有模型估的 %.0f%%），"
              "低估最多的是「%s」（实测是模型估的 %.0f%%）。"
              % (over, per_type_med.get(over, 0) * 100,
                 under, per_type_med.get(under, 0) * 100))
            o("      这不构成停止 L5 的理由 —— 校准层的做法是把课型系数写进"
              "使用者的参数文件（见 individual-calibration.md §5），基线不动。")
        else:
            o("判定: ✓ 课型内 %.2f 倍、课型间 %.2f 倍，都 ≤ %.1f 倍，口径稳定。"
              % (within_range or 1.0, between_range or 1.0, DURATION_TOL))
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
    o("  Spearman rho   = %s   ← 跨课型混合，仅供参考" % ("%.3f" % rho if rho is not None else "n/a"))
    o("  AU 与实际时长的 rho = %s   ← 对照项：它更高说明 AU 被时长支配"
      % ("%.3f" % dur_rho if dur_rho is not None else "n/a"))
    o()
    o("※ 上面的 rho 把不同课型混在一起算，**不能当判据**。不同课型的时长结构与"
      "局部代价占比不同，A 与 AU 的跨课型刻度本就未经检验，")
    o("  把它们混算得到一个低 rho，既不能证明模型坏，也不能证明 A 能用。")
    o("  有判据的是下面两项 —— 都只在课型内部成立。")
    o()
    w_agree, w_total, w_detail = within_type_agreement(complete)
    if w_total:
        o("① 课型内方向一致率 = %d/%d（同一课型相邻两次，A 与 AU 变化同向）"
          % (w_agree, w_total))
        for t, s1, s2, dA, dU, ok in w_detail:
            o("   %-8s A %+5.2f → AU %+5.0f   %-18s %s  %s"
              % (t, dA, dU, s1[:18], s2[:18], "同向" if ok else "背离"))
        o("   （箭头 = 后一次减前一次；课型内检验里这条才是判据）")
    else:
        o("① 课型内方向一致率：数据不足（每课型需要 ≥2 次实测）。")
    o()
    k_within, k_between = k_by_type(complete)
    o("② 隐含 k = AU/A（课型内 vs 课型间）")
    for t in sorted(k_within, key=lambda x: -k_within[x]):
        o("   %-10s 课型内极差 %s"
          % (t, "%.2f 倍" % k_within[t] if k_within[t] else "n=1，样本不足"))
    o("   课型间极差 = %s"
      % ("%.2f 倍" % k_between if k_between else "n/a"))
    o("   课型间大是**正常且预期**的：A 的课型间刻度本就没校准过。"
      "把课型系数写进个人参数文件即可消掉，不是不许模型用。")
    if k_within:
        worst_k = max(k_within, key=lambda t: k_within[t])
        if k_within[worst_k] and k_within[worst_k] > K_RANGE_LIMIT:
            o("   ⚠ 「%s」课型内 k 极差 %.2f 倍 > %.1f —— 单节课型内部就对不上，"
              "课型系数也救不了。查该课型内是否存在计划改动或计时口径变化。"
              % (worst_k, k_within[worst_k], K_RANGE_LIMIT))

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
    # 判定顺序：先报**最强的停止信号**。
    #
    # 判据只用**课型内**证据。跨课型混算的 rho 与课型间 k 极差都不作判据 ——
    # A 的课型间刻度本就没有校准过，拿它当判据等于用一把没刻度的尺子量东西，
    # 测出的差距是尺子的，不是使用者的。跨课型差异的正确处置见 Step 1 的 ②。
    within_k_bad = [t for t, v in k_within.items() if v and v > K_RANGE_LIMIT]
    verdict = None
    if not complete:
        verdict = ("skip",
                   "没有有效样本：先补 A（--sessions 自动匹配或手填）与 sRPE。")
    elif within_k_bad:
        t = max(within_k_bad, key=lambda x: k_within[x])
        verdict = ("stop",
                   "「%s」课型内隐含 k 极差 %.2f 倍 > %.1f：**停止拟合**。"
                   "单节课型内部就对不上，课型系数也救不了——"
                   "先查该课型内是否有计划改动或计时口径变化。"
                   "课型间 %.1f 倍的差异不算理由，那由课型系数处理。"
                   % (t, k_within[t], K_RANGE_LIMIT, k_between or 0.0))
    elif w_total and w_agree / w_total < RHO_FIT_MIN:
        verdict = (
            "stop",
            "课型内方向一致率 %d/%d = %.2f < %.1f：**停止拟合**。"
            "同一课型内 A 涨了而 AU 没涨（只涨 %d/%d），"
            "课型系数救不了这种——它按课型缩放，不改课型内的排序。"
            "先查该课型内是否有时长口径外的变化（自主改组间休息、动作顺序、组数），"
            "再考虑模型。" % (w_agree, w_total, w_agree / w_total,
                              RHO_FIT_MIN, w_agree, w_total))
    elif len(types) < 2:
        verdict = (
            "stop",
            "只有 1 种课型：回归无法跨课型验证（系数只对这一课型成立）。"
            + "建该课型基线即可。",
        )
    elif len(complete) < 10:
        extra = ""
        if between_range and between_range > DURATION_TOL and \
                within_range and within_range <= DURATION_TOL:
            extra = ("（注意：课型间时长比值 %.1f 倍偏大，但课型内 %.2f 倍稳定——"
                     "这是模型对某类课的时长估计偏，个人计时没问题）"
                     % (between_range, within_range))
        verdict = ("skip",
                   "n=%d < 10：样本量不足，拟合出的曲线往往是这个周期的形状，"
                   "不是这个人的特征。停在 L3/L4。%s" % (len(complete), extra))
    else:
        # 竞争模型检验 + 样本外门槛 —— 放在 ok 之前，因为它们比任何训练内指标都强。
        quality = per_type_fit_quality(complete)
        evaluable = {t: q for t, q in quality.items() if q["evaluable"]}
        not_eval = {t: q for t, q in quality.items() if not q["evaluable"]}
        if not_eval:
            # **所有**课型都必须可评估才算放行 —— L5 的产物是「一整张分课型换算表」，
            # 缺一个课型的表就等于这张表有洞，用它反解会静默漏掉那个课型。
            need = ", ".join("%s(需 %d，现 %d)" % (t, MIN_FIT_SAMPLES, q["n"])
                             for t, q in sorted(not_eval.items()))
            verdict = ("skip",
                       "**样本量不足，无法评估完整的换算表。**"
                       "样本外的误差估计要求课型内 n≥%d（每折至少留 3 点拟合 2 参数），"
                       "当前不足的课型：%s。n 不足时结论只能是「样本不足」，"
                       "不能算通过也不能算不通过。"
                       "补齐这些课型的样本（或删掉它们）后重跑。停在 L3。"
                       % (MIN_FIT_SAMPLES, need))
        else:
            bad_deg = [(t, q) for t, q in evaluable.items()
                       if q.get("degrade") is not None and q["degrade"] > AU_DEGRADE_MAX]
            if bad_deg:
                t, q = max(bad_deg, key=lambda x: x[1]["degrade"])
                verdict = (
                    "stop",
                    "**「A → AU」的换算缺了时长那一半：停止拟合。**"
                    "「%s」课型内样本外误差：只用 A 时 %.0f AU，加上时长后 %.0f AU —— "
                    "差 %.1f 倍（门槛 %.1f 倍）。AU = sRPE × 时长，"
                    "A 缺的那部分正是时长，固化出来的表是残缺的。"
                    "处置：改用 L3 查表（按课型记时长中位 + sRPE 中位 + 带宽）。"
                    % (t, q["loocv"], q["loocv_both"], q["degrade"], AU_DEGRADE_MAX))
            else:
                degs = [(t, q) for t, q in evaluable.items() if q.get("degrade") is not None]
                if degs:
                    worst_d = max(degs, key=lambda x: x[1]["degrade"])
                    deg_txt = "、劣化倍数最差 %.1f 倍（门槛 %.1f）" % (
                        worst_d[1]["degrade"], AU_DEGRADE_MAX)
                else:
                    deg_txt = "、劣化倍数不可评估（A 与时长共线，参照模型奇异）"
                verdict = ("ok",
                           "课型内方向一致 %d/%d、课型内 k 极差 ≤%.1f、"
                           "可评估课型 %d 个%s—— **分课型**固化系数可用。"
                           % (w_agree, w_total, K_RANGE_LIMIT, len(evaluable), deg_txt))
    o("判定: %s" % verdict[1])
    o()

    # 竞争模型检验的明细 —— 无论是否 ok 都报，它本身就是结论的一部分
    quality = per_type_fit_quality(complete) if complete else {}
    if quality:
        o("  -- 换算表可用性检验（逐课型）--")
        o("  L5 的产物是**一张只用 A 的分课型换算表**（反解时手上只有 A），")
        o("  所以检验在**课型内**做：课型间的量级差会盖掉课型内的真实差异。")
        o()
        o("    %-10s%4s%8s%10s%10s%10s%8s"
          % ("课型", "n", "R²", "LOOCV", "相对误差", "劣化倍数", "可评估"))
        o("    " + "-" * 66)
        for t in sorted(quality):
            q = quality[t]
            note = "是" if q["evaluable"] else "n<%d" % MIN_FIT_SAMPLES
            o("    %-10s%4d%8s%10s%10s%10s%8s"
              % (t, q["n"],
                 "%.3f" % q["r2"] if q.get("r2") is not None else "-",
                 "%.0f" % q["loocv"] if q.get("loocv") is not None else "-",
                 "%.0f%%" % (q["rel_err"] * 100) if q.get("rel_err") is not None else "-",
                 "%.1f" % q["degrade"] if q.get("degrade") is not None else "共线",
                 note))
        o()
        o("    劣化倍数门槛 %.1f　可评估需课型内 n≥%d" % (AU_DEGRADE_MAX, MIN_FIT_SAMPLES))
        o("    n 不足的课型：**样本不足**，既不算通过也不算不通过。")
        o("    「共线」= A 与时长在课型内共线，「AU ~ A + 时长」参照模型奇异，")
        o("      劣化倍数算不出来 —— 这时该门不参与判决，且共线本身说明"
          "「加时长」没有额外信息可加。")
        o("    相对误差一列是参考信息：它与「课型内 k 极差」测的是同一件事"
          "（k = AU/A），故不另设门槛。")
        o()

    if verdict[0] == "ok":
        o("  -- 分课型系数（**这就是可用的产出**）--")
        o("  每课型单独拟合 AU = a + b·A。跨课型不共用一根线：")
        o()
        o("  %-10s%5s%16s%8s%8s%14s"
          % ("课型", "n", "AU = a + b·A", "R²", "b", "AU300 -> A"))
        o("  " + "-" * 68)
        for t in sorted(types):
            g = [x for x in complete if x["type"] == t]
            if len(g) < 3:
                o("  %-10s%5d%s" % (t, len(g), "样本不足（需 >=3）"))
                continue
            ax = [x["A"] for x in g]
            au = [x["AU"] for x in g]
            a0, b = ols(ax, au)
            if b is None:
                o("  %-10s%5d%s" % (t, len(g), "A 无变异，无法拟合"))
                continue
            yh = [a0 + b * v for v in ax]
            sse = sum((au[i] - yh[i]) ** 2 for i in range(len(au)))
            sst = sum((v - sum(au) / len(au)) ** 2 for v in au)
            r2 = 1 - sse / sst if sst > 0 else float("nan")
            inv = "A %.1f" % ((300 - a0) / b) if b else "-"
            o("  %-10s%5d%16s%8.3f%8.1f%14s"
              % (t, len(g), "%.1f %+.1f·A" % (a0, b), r2, b, inv))
        o()
        o("  用法：拿到那节课的 A，先查它属于哪个课型，用**该课型**的 a、b 反解 AU。")
        o("  ! 只在**同一课型 + 同一周期结构**内成立。容量期与力量期、减载周与"
          "常规周的结构不同，系数不能跨阶段搬。")
        o("  ! n<5 的课型上表只是示意，不足以固化。")
        o("  ! AU = sRPE x 时长，缺时长就不能把 A 换算成 AU —— "
          "反解时必须同时知道那节课的实测时长。")
        o()
        # 全局回归只作描述，明确不给它反解资格
        a0g, bg = ols(xs, ys)
        if bg:
            o("  -- 跨课型全局回归（**仅描述，不用于反解**）--")
            o("  AU = %.1f %+.1f·A" % (a0g, bg))
            o("  它把若干条不同的线压成一个平均：分课型的 b 彼此可差 2 倍以上，")
            o("  用它反解阈值会系统性错。列出来只为了让人看清「为什么不能这么用」。")
            o()
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
