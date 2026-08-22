#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重量换算逻辑测试：pct 优先 / 取整 / RPE 路径 / 缺 pct 报错"""
import pytest
from design_program import compute_lift

SQ = 145.0


def test_pct_priority_over_rpe():
    """pct 给了就忽略 rpe，直接按 %1RM。"""
    r = compute_lift("squat", SQ, reps=8, rpe=7, pct=69, plate_step=2.5)
    assert r["pct_1rm"] == 69
    # 145 * 0.69 = 100.05 -> 取整 100
    assert r["weight"] == 100.0


def test_pct_rounding_to_plate_step():
    """pct 路径按 plate_step 向下取整（round_weight 保守取整到可加载重量）。"""
    r = compute_lift("bench", 105.0, reps=8, pct=69, plate_step=2.5)
    # 105 * 0.69 = 72.45 -> 向下取整 70.0
    assert r["weight"] == 70.0


def test_rpe_path_uses_table():
    """无 pct 时走 RPE 表（rpe_to_percentage）。"""
    r = compute_lift("squat", SQ, reps=5, rpe=8, plate_step=2.5)
    # 5 次 @RPE8 应映射到某 %1RM；重量应为正整数/2.5 倍数
    assert r["weight"] is not None
    assert r["pct_1rm"] is not None
    assert r["weight"] % 2.5 == 0


def test_missing_pct_and_rpe_out_of_table_raises():
    """高次+RPE 表无对应（如 8 次 RPE7），且没给 pct → 明确报错。"""
    with pytest.raises(ValueError) as exc:
        compute_lift("squat", SQ, reps=8, rpe=7, pct=None, plate_step=2.5)
    assert "pct" in str(exc.value)


def test_no_weight_returns_null():
    """no_weight=True 不换算重量，weight=None，但仍记组数（MRV 用）。"""
    r = compute_lift("pullup", 0, reps=6, no_weight=True)
    assert r["weight"] is None
    assert r["no_weight"] is True
    assert r["pct_1rm"] is None
