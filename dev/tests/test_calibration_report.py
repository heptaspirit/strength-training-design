#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calibration_report.py 测试：课名归一 / 匹配优先级 / 拟合门限。

重点护住三类容易静默出错的地方：
  1. 课名归一——「卧推日」与「卧推」必须落进同一个课型桶，否则同一课型被拆成两组，
     校准基线表就变成两行 n=1 的垃圾。
  2. 匹配歧义——锚点课（无周次）不得顶替当周实测课；匹配到多节必须留空并点名，
     不能"猜一个最像的"。
  3. 拟合门限——n 不足 / 隐含 k 极差超限时必须拒绝固化 k，这是 L5 的全部意义。
"""
import csv
import os
import sys

import pytest

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import calibration_report as cr


# ── 课型归一 ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("name,typ", [
    ("周一 深蹲日（C3 W2）", "深蹲"),
    ("C3 W1 周一 深蹲+垂直推", "深蹲"),
    ("周三 卧推日（C3 W1）", "卧推"),
    ("C3 W2 周三 卧推", "卧推"),
    ("周六 轻量/表现", "轻量"),
    ("周六 轻量日（C3 W1）", "轻量"),
    ("周五 硬拉+爆发", "硬拉"),
])
def test_session_type_unifies_day_suffix(name, typ):
    """带"日"与不带"日"、带周次与不带周次，都要归到同一个课型。"""
    assert cr.session_type(name) == typ


def test_type_keys_do_not_collide_on_prefix():
    """"推"不能吃掉"卧推"—— TYPE_KEYS 顺序必须让更长（更具体）的关键词先命中。"""
    assert cr.session_type("周三 卧推日") == "卧推"
    assert cr.session_type("推举日") == "推"


# ── 名称 token 与匹配 ─────────────────────────────────────────────────
def test_name_tokens_extracts_week_and_day():
    t = cr.name_tokens("周一 深蹲日（C3 W2）")
    assert t["day"] == "周一" and t["week"] == 2 and t["type"] == "深蹲"


def test_anchor_lesson_never_wins_over_current_week():
    """锚点课无周次，属弱候选；当周实测课存在时必须选当周那节。"""
    names = ["锚点·C2 周一 深蹲日", "C3 W2 周一 深蹲+垂直推"]
    hits = cr.match_candidates("周一 深蹲日（C3 W2）", names)
    assert hits == ["C3 W2 周一 深蹲+垂直推"]


def test_anchor_used_only_when_no_week_specific_match():
    """日志没有周次信息时，锚点课可以作为唯一候选被采用。"""
    names = ["锚点·C2 周一 深蹲日", "C3 W2 周一 深蹲+垂直推"]
    hits = cr.match_candidates("周一 深蹲日", names)
    assert "锚点·C2 周一 深蹲日" in hits


def test_different_day_never_matches():
    assert cr.match_candidates("周一 深蹲日（C3 W2）", ["C3 W2 周三 卧推"]) == []


def test_ambiguous_match_returns_all_candidates():
    """同名两节（如两个周期都叫"周一 深蹲日"且日志无周次）→ 返回多候选，由调用方留空。"""
    hits = cr.match_candidates("周一 深蹲日", ["C3 W1 周一 深蹲+垂直推",
                                             "C3 W2 周一 深蹲+垂直推"])
    assert len(hits) == 2


# ── 统计小工具 ────────────────────────────────────────────────────────
def test_ratio_is_max_over_min():
    assert cr.ratio([2.0, 5.0, 10.0]) == pytest.approx(5.0)
    assert cr.ratio([3.0]) is None


def test_ratio_ignores_nonpositive():
    """k = AU/A，A<=0 的点不能进极差计算（否则极差被符号污染）。"""
    assert cr.ratio([2.0, 5.0, 0.0, -1.0]) == pytest.approx(2.5)


def test_median_even_and_odd():
    assert cr.median([1.0, 2.0, 3.0]) == pytest.approx(2.0)
    assert cr.median([1.0, 2.0, 3.0, 4.0]) == pytest.approx(2.5)


def test_ranks_handles_ties():
    assert cr.ranks([5.0, 5.0, 9.0]) == [1.5, 1.5, 3.0]


# ── 日志读取（列名别名）────────────────────────────────────────────────
def _write_log(tmp_path, rows, header):
    p = tmp_path / "log.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return str(p)


def test_read_log_accepts_chinese_columns(tmp_path):
    p = _write_log(tmp_path, [{"日期": "2026-01-05", "课型": "深蹲", "时长": "55",
                             "sRPE": "5.5", "完成度": "全"}],
                   ["日期", "课型", "时长", "sRPE", "完成度"])
    rows = cr.read_log(p)
    assert len(rows) == 1
    assert rows[0]["dur"] == 55.0 and rows[0]["srpe"] == 5.5
    assert rows[0]["outcome"] == "全"


def test_read_log_skips_blank_session_rows(tmp_path):
    p = _write_log(tmp_path, [{"session": "周一 深蹲日（C3 W1）", "duration_min": "55",
                             "srpe": "5.5"},
                            {"session": "", "duration_min": "", "srpe": ""}],
                   ["session", "duration_min", "srpe"])
    rows = cr.read_log(p)
    assert len(rows) == 1


def test_num_rejects_garbage():
    assert cr.num("abc") is None and cr.num("") is None and cr.num(" 5.5 ") == 5.5


# ── L5 拟合门限 ───────────────────────────────────────────────────────
def _rows_specs(pairs):
    """pairs: [(A, dur, srpe, outcome)] → 日志行字典。"""
    out = []
    for a, d, s, oc in pairs:
        out.append({"date": "", "session": "x", "type": "深蹲", "A": a, "dur": d,
                    "srpe": s, "outcome": oc, "note": ""})
    return out


def test_verdict_blocks_fit_when_k_range_too_wide():
    """同一课型内隐含 k 极差 >1.5 倍 → 必须 stop，不允许固化 k。"""
    rows = _rows_specs([(10.0, 50, 5, "全"), (10.0, 70, 7, "全"), (10.0, 60, 6, "全"),
                        (10.0, 55, 5, "全"), (10.0, 65, 6, "全")])
    _lines, verdict = cr.build_report(rows, 10.0, None, [], [], None, "test")
    assert verdict[0] == "stop"
    assert "极差" in verdict[1]


def test_verdict_blocks_fit_when_n_too_small():
    """n<10（但 k 极差与课型数都达标）→ skip：曲线是周期形状，不是个人特征。"""
    rows = []
    for i in range(8):
        rows.append({"date": "", "session": "s%d" % i,
                     "type": "深蹲" if i % 2 == 0 else "卧推",
                     "A": 10.0, "dur": 50.0 + i, "srpe": 5.0, "outcome": "全",
                     "note": ""})
    _lines, verdict = cr.build_report(rows, 10.0, None, [], [], None, "test")
    assert verdict[0] == "skip"
    assert "n=8" in verdict[1]


def test_verdict_blocks_fit_with_single_session_type():
    """只有 1 种课型 → 回归无法跨课型验证，系数只对该课型成立。"""
    rows = _rows_specs([(10.0, 50 + i, 5, "全") for i in range(12)])
    _lines, verdict = cr.build_report(rows, 10.0, None, [], [], None, "test")
    assert verdict[0] == "stop"
    assert "课型" in verdict[1]


def _synthetic_rows(t_scales=(1.0, 4.0), n_per_type=8, a_step=0.3):
    """造一份跨课型的合成样本，用于检验「ok」路径。

    四处必须真实，否则检验测不到该测的东西：

    1. **A 与时长不共线** —— 时长带非单调扰动。否则「A + 时长」的正规方程
       奇异，样本外评估直接算不出来。
    2. **sRPE 随 A 涨** —— 真实数据里 AU = sRPE × 时长，而 sRPE 由训练量决定。
       若把 sRPE 设成「只由时长决定」，换算表当然不准 —— 那是夹具不真实。
    3. **每课型 n ≥ 5** —— 样本外误差估计要求课型内 n≥5（每折留 3 点拟合 2 参数）。
    4. **AU 随 A 单调涨** —— 课型内 AU~A 的 R² 要够高，且残差要小。

    课型系数 k_scale 让课型间的隐含 k 差 4 倍，用来确认「课型间差不是停止理由」。
    """
    jitter = (0.0, 3.0, 1.0, 4.0, 2.0, 5.0, 1.5, 2.5)
    rows = []
    for t_i, (t, k_scale) in enumerate(zip(["深蹲", "卧推"], t_scales)):
        for i in range(n_per_type):
            a = 9.0 + i * a_step
            dur = 50.0 + i * 2 + jitter[i % len(jitter)] * 0.05
            # sRPE 主要随 A 涨（训练量决定代价），时长只带轻微扰动
            srpe = (2.0 + a * 0.12 + dur * 0.002) * k_scale
            rows.append({"date": "2026-01-%02d" % (t_i * n_per_type + i + 1),
                         "session": "%s s%d" % (t, i), "type": t, "A": a,
                         "dur": dur, "srpe": srpe, "outcome": "全", "note": ""})
    return rows


def test_verdict_allows_fit_when_all_gates_pass():
    """n≥10、跨课型、课型内 k 极差小、课型内方向一致、A 有独立贡献 → ok。

    夹具必须满足**课型内** A 与 AU 同向（这才是判据）；跨课型怎么排都无所谓 ——
    旧版这里只查跨课型 rho，是个真 bug。
    """
    rows = _synthetic_rows()
    rows[5]["outcome"] = "部分"          # 留一组「未完成」供 L4 分组
    _lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "ok", verdict[1]


def test_verdict_blocks_when_within_type_direction_disagrees():
    """课型内方向一致率 <70% → stop，且理由必须指向课型内而非课型间。"""
    rows = []
    # 每个课型内 A 单调上升但 AU 来回摆 —— 课型系数救不了这种
    for t_i, t in enumerate(["深蹲", "卧推"]):
        for i in range(6):
            rows.append({"date": "2026-01-%02d" % (t_i * 6 + i + 1),
                         "session": "%s s%d" % (t, i), "type": t,
                         "A": 9.0 + i * 0.5, "dur": 50.0 + i * 2,
                         "srpe": 5.0 + (0.9 if i % 2 else 0.0),
                         "outcome": "全", "note": ""})
    _lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "stop"
    assert "方向一致率" in verdict[1]


def test_between_type_k_range_alone_does_not_block_fit():
    """课型间 k 极差大**不是**停止信号 —— 那由课型系数处理。

    这是本轮最关键的修正：旧版拿全体 k 极差当判据，把「A 的课型间刻度没校准过」
    误报成「使用者数据不可信」。
    """
    rows = _synthetic_rows()
    _lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "ok", verdict[1]
    # 课型间 k 极差大不是停止理由 —— 报告里不该把它说成理由
    assert "课型间" not in verdict[1] or "不算理由" in verdict[1]


# ── 新门限：换算表可用性（逐课型评估）──────────────────────────────
def test_skips_when_no_type_has_enough_samples_for_out_of_sample_eval():
    """课型内 n 不足 → 判「样本不足」，不得假装能评估。

    n=4 时每折只剩 3 点拟合 2 参数，误差估计本身没有精度。
    「样本不足」是第三种状态，不能当成通过，也不能当成不通过。
    """
    # 「深蹲」8 点（够评估）、「卧推」3 点（不够）→ 至少一个课型不可评估
    jitter = (0.0, 3.0, 1.0, 4.0, 2.0, 5.0, 1.5, 2.5)
    rows = []
    for t_i, (t, n) in enumerate([("深蹲", 8), ("卧推", 3)]):
        for i in range(n):
            rows.append({"date": "2026-01-%02d" % (t_i * 10 + i + 1),
                         "session": "%s s%d" % (t, i), "type": t,
                         "A": 9.0 + i * 0.3, "dur": 50.0 + i * 2 + jitter[i] * 0.3,
                         "srpe": 3.0 + i * 0.12 + (50.0 + i * 2) * 0.002,
                         "outcome": "全", "note": ""})
    _lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "skip", verdict[1]
    assert "样本量不足" in verdict[1]
    assert "不能算通过也不能算不通过" in verdict[1]
    # 必须指名是哪个课型不够、还差多少
    assert "卧推" in verdict[1] and "需 5" in verdict[1]


def test_stops_when_A_alone_cannot_predict_AU():
    """单用 A 预测 AU 远差于「A + 时长」→ 换算缺了时长那一半 → stop。

    AU = sRPE × 时长，A 缺的那部分正是时长。固化 a、b 得到的阈值会系统性错。
    这道门与「课型内 k 极差」不重合 —— k = AU/A，k 极差与 AU~A 的残差是同一件事，
    而这里测的是「加进时长后能改善多少」。
    """
    jitter = (0.0, 3.0, 1.0, 4.0, 2.0, 5.0, 1.5, 2.5)
    rows = []
    for t_i, t in enumerate(["深蹲", "卧推"]):
        for i in range(8):
            a = 9.0 + i * 0.2
            dur = 50.0 + i * 2 + jitter[i] * 0.3
            # sRPE 主要是时长的函数 → AU 的散布来自时长，A 解释不了
            srpe = 3.0 + i * 0.02 + dur * 0.02
            rows.append({"date": "2026-01-%02d" % (t_i * 8 + i + 1),
                         "session": "%s s%d" % (t, i), "type": t,
                         "A": a, "dur": dur, "srpe": srpe,
                         "outcome": "全", "note": ""})
    _lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "stop", verdict[1]
    assert "时长" in verdict[1] or "换算" in verdict[1]
    assert "L3" in verdict[1]


def test_ok_verdict_outputs_per_type_coefficients_not_one_global_line():
    """放行后必须给**分课型**系数；跨课型全局直线只能作描述，不给反解资格。

    旧版给的是一根跨课型的全局线，而课型间 b 可差 2 倍以上 ——
    用它反解阈值会系统性错。这是本轮修掉的真漏洞。
    """
    rows = _synthetic_rows()
    lines, verdict = cr.build_report(rows, 11.0, None, [], [], None, "test")
    assert verdict[0] == "ok", verdict[1]
    text = "\n".join(lines)
    assert "分课型系数" in text
    assert "仅描述，不用于反解" in text
    # 每个课型各自一条线
    assert text.count("·A") >= 2
    # 且必须提示缺时长就不能换算
    assert "缺时长" in text


def test_report_always_shows_competing_model_check():
    """竞争模型检验的明细必须出现在报告里 —— 无论判决 ok 还是 stop。

    它本身就是结论的一部分：读者要能看到「A 的增量只有多少」，
    而不只是看到一个结论词。
    """
    rows = _synthetic_rows()
    lines, _v = cr.build_report(rows, 11.0, None, [], [], None, "test")
    text = "\n".join(lines)
    assert "换算表可用性检验" in text
    assert "逐课型" in text


# ── L2 时长口径门：课型内 vs 课型间 ────────────────────────────────────
def test_duration_mismatch_blocks_calibration_message():
    """同一课型内实测/模型时长极差 >1.5 倍 → 个人计时不稳，必须明说。"""
    rows = _rows_specs([(10.0, 50, 5, "全"), (10.0, 90, 6, "全"), (10.0, 60, 5, "全"),
                        (10.0, 55, 5, "全"), (10.0, 65, 6, "全")])
    rows[0]["model_dur"] = 50.0
    rows[1]["model_dur"] = 90.0
    rows[2]["model_dur"] = 30.0     # 实测 60 / 模型 30 = 2 倍
    rows[3]["model_dur"] = 55.0
    rows[4]["model_dur"] = 65.0
    lines, _v = cr.build_report(rows, 10.0, 0, [], [], None, "test")
    text = "\n".join(lines)
    assert "计时口径不稳" in text
    assert "禁止进入 L5" in text


def test_between_type_duration_bias_is_not_a_personal_problem():
    """课型内稳、课型间偏 → 必须说「个人计时是稳的」，且指向课型系数而非统一计时。"""
    rows = []
    for t_i, (t, actual) in enumerate([("深蹲", 60.0), ("卧推", 60.0), ("轻量", 36.0)]):
        for i in range(2):
            idx = t_i * 2 + i
            rows.append({"date": "2026-01-%02d" % (idx + 1),
                         "session": "%s s%d" % (t, i), "type": t,
                         "A": 10.0, "dur": actual, "srpe": 5.0,
                         "model_dur": 60.0, "outcome": "全", "note": ""})
    lines, _v = cr.build_report(rows, 10.0, None, [], [], None, "test")
    text = "\n".join(lines)
    assert "个人计时是稳的" in text
    assert "按课型给时长系数" in text
    # 且不得把它当成停止 L5 的理由
    assert "不构成停止 L5 的理由" in text


def test_duration_split_detects_systematic_per_type_bias():
    """课型内比值稳、课型中位相差大 → between_range 大而 within 小。"""
    rows = []
    for t_i, (t, ratio_val) in enumerate([("深蹲", 1.0), ("轻量", 0.7)]):
        for i in range(2):
            rows.append({"type": t, "dur": 50.0 * ratio_val * (1 + i * 0.02),
                         "model_dur": 50.0, "A": 10.0, "srpe": 5.0, "AU": 250.0})
    within, between, per_type, _per_within = cr.duration_split(rows)
    assert within < 1.1
    assert between > 1.3
    assert set(per_type) == {"深蹲", "轻量"}


def test_within_type_agreement_uses_date_order():
    """方向一致率按时间排，不按 A 排序 —— 否则「哪一次在变重」会读反。"""
    rows = [
        {"type": "深蹲", "session": "w1", "date": "2026-01-01", "A": 10.0, "AU": 300.0},
        {"type": "深蹲", "session": "w2", "date": "2026-01-08", "A": 10.1, "AU": 320.0},
    ]
    agree, total, _detail = cr.within_type_agreement(rows)
    assert total == 1
    assert agree == 1


# ── L4 后果分组 ───────────────────────────────────────────────────────
def test_single_session_ceiling_requires_both_outcome_groups():
    """只有"全"没有"部分/未" → 画不了线，报告必须明说缺什么。"""
    rows = _rows_specs([(10.0, 50, 5, "全"), (11.0, 60, 6, "全")])
    lines, _v = cr.build_report(rows, 10.0, None, [], [], None, "test")
    assert "画不了线" in "\n".join(lines)


def test_single_session_ceiling_drawn_when_groups_separate():
    rows = _rows_specs([(10.0, 50, 5, "全"), (10.5, 55, 5, "全"),
                        (14.0, 80, 7, "部分")])
    lines, _v = cr.build_report(rows, 10.0, None, [], [], None, "test")
    text = "\n".join(lines)
    assert "单次上限落在 AU" in text


def test_overlapping_outcome_groups_refuse_to_draw_line():
    """"完成"组的最高 AU 高于"未完成"组的最低 AU → 区间重叠，必须拒绝画线。"""
    rows = _rows_specs([(14.0, 80, 7, "全"), (10.0, 50, 5, "部分")])
    lines, _v = cr.build_report(rows, 10.0, None, [], [], None, "test")
    assert "区间重叠" in "\n".join(lines)


# ── 空数据不崩 ────────────────────────────────────────────────────────
def test_report_on_empty_log_does_not_crash():
    rows = []
    lines, verdict = cr.build_report(rows, None, None, [], [], None, "empty")
    assert verdict[0] == "skip"
    assert "没有任何有效样本" in "\n".join(lines)


def test_report_with_missing_srpe_column_lists_gap():
    rows = [{"date": "", "session": "周一 深蹲日", "type": "深蹲", "A": 10.0,
             "dur": 55.0, "srpe": None, "outcome": "", "note": ""}]
    lines, _v = cr.build_report(rows, None, None, [], [], None, "test")
    assert "有效样本 (A + 时长 + sRPE 齐备): 0 / 1" in "\n".join(lines)
