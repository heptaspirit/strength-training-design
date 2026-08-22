#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""no_weight 自重动作测试：引体仅审计组数、不换算重量、不崩"""
from conftest import make_week
from design_program import run_base


def test_pullup_no_weight_mrv_audited():
    """引体 4×6 = 24 组 > MRV(22) → over，但不因重量缺失而崩。"""
    wk = make_week([
        {"day": "Mon", "lifts": [
            {"exercise": "squat", "sets": 5, "reps": 8, "pct": 69, "category": "primary"},
            {"exercise": "pullup", "sets": 4, "reps": 6, "no_weight": True, "category": "assistance"},
        ]},
    ])
    res = run_base(wk)
    pull = [l for l in res["lifts"] if l["exercise"] == "pullup"][0]
    assert pull["weight"] is None
    assert res["mrv"]["pullup"]["weekly_sets"] == 4  # 仅本周 1 次出现
    # 4/22 = 18% < 80% → 安全
    assert res["mrv"]["pullup"]["status"] == "安全"


def test_no_weight_with_normal_lift_same_day():
    """同日混排自重 + 普通重量动作，两者都正确。"""
    wk = make_week([
        {"day": "Mon", "lifts": [
            {"exercise": "squat", "sets": 5, "reps": 8, "pct": 69, "category": "primary"},
            {"exercise": "pullup", "sets": 4, "reps": 6, "no_weight": True, "category": "assistance"},
        ]},
    ])
    res = run_base(wk)
    squat = [l for l in res["lifts"] if l["exercise"] == "squat"][0]
    pull = [l for l in res["lifts"] if l["exercise"] == "pullup"][0]
    assert squat["weight"] == 100.0  # 145*0.69=100.05 -> 100
    assert pull["weight"] is None
