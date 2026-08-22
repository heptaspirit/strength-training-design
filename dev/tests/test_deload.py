#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""减载系数测试：phase=deload 默认 ×0.6；覆盖生效；非减载周系数 1.0"""
from conftest import make_week
from design_program import run_base


def test_deload_default_factor():
    """phase=deload 且未给 deload_factor → 默认 0.6。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "squat", "sets": 3, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
    ], intent={"phase": "deload"})
    res = run_base(wk)
    assert res["deload_factor"] == 0.6
    # 145 * 0.70 = 101.5 -> *0.6 = 60.9 -> 取整 60
    sq = [l for l in res["lifts"] if l["exercise"] == "squat"][0]
    assert sq["weight"] == 60.0


def test_deload_custom_factor():
    """phase=deload 且给 deload_factor=0.5 → 0.5 生效。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "squat", "sets": 3, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
    ], intent={"phase": "deload"}, deload_factor=0.5)
    res = run_base(wk)
    assert res["deload_factor"] == 0.5
    sq = [l for l in res["lifts"] if l["exercise"] == "squat"][0]
    # 101.5 * 0.5 = 50.75 -> 取整 50
    assert sq["weight"] == 50.0


def test_volume_phase_no_deload():
    """volume 周无减载系数 → 1.0。"""
    wk = make_week([
        {"day": "Mon", "lifts": [{"exercise": "squat", "sets": 3, "reps": 5,
                                   "pct": 70, "category": "primary"}]},
    ], intent={"phase": "volume"})
    res = run_base(wk)
    assert res["deload_factor"] == 1.0
