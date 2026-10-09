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
    """隐含 k 极差 >1.5 倍 → 必须 stop，不允许固化 k。"""
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


def test_verdict_allows_fit_when_all_gates_pass():
    """n≥10、跨课型、k 极差小、rho 高 → ok。"""
    pairs = []
    for i in range(12):
        a = 8.0 + i * 0.5
        dur = 50.0 + i * 2
        srpe = 5.0 + (i % 3) * 0.5
        oc = "全" if i < 10 else "部分"
        pairs.append((a, dur, srpe, oc))
    rows = []
    for i, (a, d, s, oc) in enumerate(pairs):
        rows.append({"date": "", "session": "s%d" % i,
                     "type": "深蹲" if i % 2 == 0 else "卧推", "A": a, "dur": d,
                     "srpe": s, "outcome": oc, "note": ""})
    _lines, verdict = cr.build_report(rows, 12.0, None, [], [], None, "test")
    assert verdict[0] == "ok", verdict[1]


# ── L2 时长口径门 ─────────────────────────────────────────────────────
def test_duration_mismatch_blocks_calibration_message():
    """实测/模型时长极差 >1.5 倍 → 报告必须点明"口径不一致"且禁止进入 L5。"""
    rows = _rows_specs([(10.0, 50, 5, "全"), (10.0, 90, 6, "全"), (10.0, 60, 5, "全"),
                        (10.0, 55, 5, "全"), (10.0, 65, 6, "全")])
    rows[0]["model_dur"] = 50.0
    rows[1]["model_dur"] = 90.0
    rows[2]["model_dur"] = 30.0     # 实测 60 / 模型 30 = 2 倍
    rows[3]["model_dur"] = 55.0
    rows[4]["model_dur"] = 65.0
    lines, _v = cr.build_report(rows, 10.0, 0, [], [], None, "test")
    text = "\n".join(lines)
    assert "时长口径不一致" in text
    assert "禁止进入 L5" in text


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
