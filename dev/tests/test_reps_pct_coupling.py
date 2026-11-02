#!/usr/bin/env python3
"""
组次 × %1RM 耦合校验（check_reps_pct / implied_rpe / pct_at_failure）。

背景：设计器允许同一条 lift 同时给 reps 与 pct，两者此前互不校验。
结果是可以排出「5 次 @ 88% 1RM」这种物理上做不完的组——表现是 TS 在最后 1-2 次失败，
而计划表里看起来完全正常（RPE 列还写着 8.5）。
"""
import pytest
from design_program import check_reps_pct, compute_lift
from rpe_to_percentage import implied_rpe, pct_at_failure


def test_failure_ceiling_is_rep_dependent():
    """力竭上限随次数下降：1 次 100% / 3 次 92% / 5 次 87%。"""
    assert pct_at_failure(1) == 100
    assert pct_at_failure(3) == 92
    assert pct_at_failure(5) == 87
    assert pct_at_failure(8) is None  # 表只覆盖 1-5 次


def test_implied_rpe_matches_table_grid():
    """落在表格网点上时必须精确复现 RPE。"""
    assert implied_rpe(5, 79) == (8.5, False)
    assert implied_rpe(5, 82) == (9.0, False)
    assert implied_rpe(3, 85) == (8.5, False)
    assert implied_rpe(3, 87) == (9.0, False)


def test_implied_rpe_interpolates_between_grid_points():
    """网点之间线性插值，3 次 88.3% 应落在 RPE 9 与 9.5 之间。"""
    ir, beyond = implied_rpe(3, 88.3)
    assert 9.0 < ir < 9.5
    assert beyond is False


def test_over_failure_is_flagged_and_extrapolated():
    """超过力竭上限要标 beyond=True，且 RPE 外推到 10 以上。"""
    ir, beyond = implied_rpe(5, 88)
    assert beyond is True
    assert ir > 10


def test_check_reps_pct_levels():
    assert check_reps_pct("squat", 5, 88)[1] == "impossible"
    assert check_reps_pct("squat", 3, 88.3)[1] == "over_cap"
    assert check_reps_pct("squat", 5, 79)[1] is None
    # 次数超出表范围（>5）不判，避免对高次/辅助动作误报
    assert check_reps_pct("squat", 8, 69) == (None, None)


def test_compute_lift_raises_on_impossible_prescription():
    with pytest.raises(ValueError, match="超过该次数的力竭上限"):
        compute_lift("squat", 150.0, reps=5, rpe=8.5, pct=88)


def test_compute_lift_keeps_feasible_prescription_working():
    r = compute_lift("squat", 150.0, reps=3, pct=88.3)
    assert r["weight"] is not None
    r5 = compute_lift("squat", 150.0, reps=5, pct=79)
    assert r5["pct_1rm"] == 79
