#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRV 审计 + 合规红绿灯测试：MRV 边界 / 硬拉容量 / 48h / gap_rules 顺向"""
from conftest import make_week
from design_program import run_base, DEADLIFT_FULL_WEEKLY_CAP


def test_mrv_at_boundary_green():
    """squat 18 组 = MRV 上限(100%)。

    注意：calculate_mrv_status 的契约是 percentage < 100 才安全、< 80 安全；
    恰好 == 100 走 else 分支返回 '超过 MRV'（这是被复用脚本的既有定义，
    设计器不修改其语义）。此处断言跟随真实行为。
    """
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "squat", "sets": 9, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
        {"day": "Thu", "lifts": [{"exercise": "squat", "sets": 9, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
    ])
    res = run_base(wk)
    mrv = res["mrv"]["squat"]
    assert mrv["weekly_sets"] == 18
    assert mrv["status"] == "超过 MRV"  # 100% 恰好临界（calculate_mrv 契约）


def test_mrv_over_red():
    """squat 19 组 > MRV(18) → 超过 MRV。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "squat", "sets": 10, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
        {"day": "Thu", "lifts": [{"exercise": "squat", "sets": 9, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
    ])
    res = run_base(wk)
    assert res["mrv"]["squat"]["weekly_sets"] == 19
    assert res["mrv"]["squat"]["status"] == "超过 MRV"


def test_deadlift_capacity_error():
    """全程硬拉 7 组 > 上限 6 → error。
    注意：硬拉容量约束只数 'deadlift' 键（全程硬拉本身），
    pause_deadlift 等变式是独立键、不计入全程硬拉容量。
    """
    wk = make_week([
        {"day": "Thu", "lifts": [
            {"exercise": "deadlift", "sets": 4, "reps": 3, "pct": 80, "category": "primary"},
        ]},
        {"day": "Mon", "lifts": [
            {"exercise": "deadlift", "sets": 3, "reps": 3, "pct": 80, "category": "primary"},
        ]},
    ])
    res = run_base(wk)
    dl_total = res["mrv"].get("deadlift", {}).get("weekly_sets", 0)
    assert dl_total > DEADLIFT_FULL_WEEKLY_CAP
    assert any("硬拉" in e for e in res["compliance"]["errors"])


def test_deadlift_48h_violation():
    """硬拉周四+周五（间隔 1 天 < 3）→ error。"""
    wk = make_week([
        {"day": "Thu", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
        {"day": "Fri", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
    ])
    res = run_base(wk)
    assert any("48h" in e for e in res["compliance"]["errors"])


def test_deadlift_48h_ok():
    """硬拉周四+周一（间隔 4 天）→ 不报 48h error。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
        {"day": "Thu", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
    ])
    res = run_base(wk)
    assert not any("48h" in e for e in res["compliance"]["errors"])


def test_gap_rules_forward_pass():
    """RDL 周一距周四硬拉 3 天（顺向）→ 放行（无 warning）。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "rdl", "sets": 3, "reps": 8,
                                   "pct": 50, "category": "assistance"}]},
        {"day": "Thu", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
    ], gap_rules=[{"after": "deadlift", "before": ["rdl"], "min_gap_days": 3}])
    res = run_base(wk)
    assert not any("rdl" in w for w in res["compliance"]["warnings"])


def test_gap_rules_forward_violation():
    """RDL 周五距周四硬拉 1 天（顺向）→ warning。"""
    wk = make_week([
        {"day": "Thu", "lifts": [{"exercise": "deadlift", "sets": 3, "reps": 3,
                                   "pct": 80, "category": "primary"}]},
        {"day": "Fri", "lifts": [{"exercise": "rdl", "sets": 3, "reps": 8,
                                   "pct": 50, "category": "assistance"}]},
    ], gap_rules=[{"after": "deadlift", "before": ["rdl"], "min_gap_days": 3}])
    res = run_base(wk)
    assert any("rdl" in w for w in res["compliance"]["warnings"])
