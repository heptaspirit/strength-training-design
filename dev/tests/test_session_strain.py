#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""session_strain.py 测试：别名归一 / catalog 扩展 / 链条对齐 / 参数覆盖。

重点护住两类容易静默出错的地方：
  1. rows 与 blocks 的位置对齐——once a block lacks a chain profile, every later
     block's ratio would be read from the wrong row if rows were shorter than blocks.
  2. 别名与新增动作的边界——不允许"猜一个最像的动作"（会静默算错动作）。
"""
import pytest

from session_strain import (  # noqa: E402
    CATALOG, default_config, merge_config, normalize_key, spec_of, chain_analysis,
    simulate, parse_session,
)

BLOCK = {"sets": 3, "reps": 8}


def blk(exercise, **kw):
    d = dict(BLOCK)
    d.update(kw)
    d["exercise"] = exercise
    return d


# ── 别名归一 ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("name,key", [
    ("squat", "squat"),
    ("深蹲", "squat"),
    ("deadlift", "dl_conv"),
    ("相扑硬拉", "dl_sumo"),
    ("RDL", "rdl"),
    ("rdl", "rdl"),
    ("bench press", "bench"),
    ("窄距卧推", "cg_bench"),
    ("close-grip bench", "cg_bench"),
    ("引体", "pullup"),
    ("引体向上", "pullup"),
    ("pull up", "pullup"),
    ("实力推", "ohp"),
    ("挂片", None),          # 非别名 -> 抛错
])
def test_alias_resolution(name, key):
    cfg = default_config()
    if key is None:
        with pytest.raises(ValueError):
            normalize_key(name, cfg)
    else:
        assert normalize_key(name, cfg) == key


def test_unknown_name_does_not_guess():
    """错拼必须报错，不能静默取一个近似动作。"""
    with pytest.raises(ValueError) as e:
        normalize_key("squatt", default_config())
    assert "squat" in str(e.value)      # 候选里给出正确项
    assert "未知动作" in str(e.value)


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        normalize_key("   ", default_config())


# ── catalog：新增动作 ─────────────────────────────────────────────────
NEW = {"zh": "双力臂", "m": 0.45, "eff": 0.85, "td": 0.85,
       "chain": {"lats": 0.75, "biceps": 0.55}, "prime": "lats"}


def test_add_new_exercise():
    cfg = merge_config(default_config(), {"catalog": {"muscle_up": dict(NEW)}})
    assert "muscle_up" not in CATALOG          # 不动内置库
    spec = spec_of("muscle_up", cfg)
    assert spec["zh"] == "双力臂"
    assert spec["m"] == 0.45
    assert spec["rest"] == 90                  # EXTRA_DEFAULTS 兜底
    assert normalize_key("muscle_up", cfg) == "muscle_up"


def test_new_exercise_requires_m_and_td():
    with pytest.raises(ValueError) as e:
        merge_config(default_config(), {"catalog": {"dip": {"eff": 0.8}}})
    msg = str(e.value)
    assert "m" in msg and "td" in msg


def test_new_exercise_requires_ref_or_eff():
    with pytest.raises(ValueError) as e:
        merge_config(default_config(), {"catalog": {"dip": {"m": 0.4, "td": 0.5}}})
    assert "ref" in str(e.value) and "eff" in str(e.value)


def test_new_exercise_chain_and_prime_must_pair():
    with pytest.raises(ValueError):
        merge_config(default_config(),
                     {"catalog": {"dip": {"m": 0.4, "eff": 0.8, "td": 0.5, "prime": "chest"}}})
    with pytest.raises(ValueError):
        merge_config(default_config(),
                     {"catalog": {"dip": {"m": 0.4, "eff": 0.8, "td": 0.5,
                                          "chain": {"chest": 0.6}}}})


def test_builtin_tuning_needs_no_full_fields():
    """已登记动作只给一个字段即可调参。"""
    cfg = merge_config(default_config(), {"catalog": {"ohp": {"td": 0.9}}})
    assert spec_of("ohp", cfg)["td"] == 0.9
    assert spec_of("ohp", cfg)["m"] == CATALOG["ohp"]["m"]


def test_one_rm_accepts_alias():
    cfg = merge_config(default_config(), {"one_rm": {"深蹲": 150}})
    assert spec_of("squat", cfg)["ref"] == 150


def test_unknown_catalog_field_ignored():
    cfg = merge_config(default_config(), {"catalog": {"ohp": {"td": 0.9, "zzz": 1}}})
    assert "zzz" not in spec_of("ohp", cfg)


# ── 链条对齐（本轮修的 bug）────────────────────────────────────────────
def test_chain_rows_align_with_blocks():
    """中间插一个无档案动作，后面的协同比不能串位。"""
    cfg = merge_config(default_config(), {"catalog": {"dip": {"m": 0.4, "eff": 0.8, "td": 0.5}}})
    blocks = [blk("bench", weight=72.5), blk("dip"), blk("cg_bench", weight=57.5)]
    rows, accum, untracked = chain_analysis(blocks, cfg)
    assert len(rows) == len(blocks)        # 等长：位置可直接索引
    assert rows[1] is None                 # 无档案处为 None，不是被跳过
    assert rows[2] is not None
    assert rows[2]["exercise"] == "cg_bench"
    assert untracked == ["dip"]
    # 无档案动作不贡献等效组：只算 bench(3组) 与 cg_bench(3组)
    assert accum["chest"] == pytest.approx(3 * 0.62 + 3 * 0.38, abs=1e-9)
    assert accum["triceps"] == pytest.approx(3 * 0.38 + 3 * 0.72, abs=1e-9)


def test_chain_untracked_deduped():
    cfg = merge_config(default_config(), {"catalog": {"dip": {"m": 0.4, "eff": 0.8, "td": 0.5}}})
    _, _, untracked = chain_analysis([blk("dip"), blk("bench", weight=72.5), blk("dip")], cfg)
    assert untracked == ["dip"]


def test_new_exercise_joins_chain_when_profiled():
    cfg = merge_config(default_config(), {"catalog": {"muscle_up": dict(NEW)}})
    blocks = [blk("pullup", reps=6), blk("muscle_up")]
    rows, accum, untracked = chain_analysis(blocks, cfg)
    assert untracked == []
    assert rows[1]["prime"] == "lats"
    assert accum["lats"] == pytest.approx(3 * 0.78 + 3 * 0.75, abs=1e-9)


# ── 解析与参数覆盖 ────────────────────────────────────────────────────
def test_parse_session_normalizes_and_validates():
    cfg = default_config()
    s = parse_session({"name": "t", "blocks": [blk("深蹲", weight=100), blk("引体", reps=6)]}, 0, cfg)
    assert [b["exercise"] for b in s["blocks"]] == ["squat", "pullup"]
    with pytest.raises(ValueError) as e:
        parse_session({"name": "t", "blocks": [{"exercise": "squat", "reps": 8}]}, 0, cfg)
    assert "sets" in str(e.value) and "squat" in str(e.value)


def test_parse_empty_blocks():
    with pytest.raises(ValueError):
        parse_session({"name": "t", "blocks": []}, 0, default_config())


def test_selfweight_rejects_weight():
    from session_strain import _intensity
    with pytest.raises(ValueError):
        _intensity("pullup", 10, default_config())


def test_barbell_requires_weight():
    from session_strain import _intensity
    with pytest.raises(ValueError):
        _intensity("squat", None, default_config())


def test_params_override_unknown_key_raises():
    with pytest.raises(ValueError):
        merge_config(default_config(), {"params": {"nope": 1}})


def test_source_label_only_upgrades():
    cfg = merge_config(default_config(), {"source": "user"})
    cfg = merge_config(cfg, {"source": "estimate"})   # 低层不得把标签降回去
    assert cfg["source"] == "user"


# ── 回归：分辨率约定与顺序不变性 ───────────────────────────────────────
def test_order_invariance_within_resolution():
    """同一课换顺序，A 的变化必须在 1% 分辨率以内。"""
    from session_strain import RESOLUTION_PCT
    import itertools
    # 外部负重动作不再有内置参考 1RM，用例须自己给（示意整数即可）
    cfg = merge_config(default_config(),
                       {"one_rm": {"bench": 100, "cg_bench": 100}})
    base = [blk("bench", sets=5, weight=72.5), blk("cg_bench", weight=57.5),
            blk("pullup", sets=4, reps=6), blk("row", sets=4, reps=9)]
    vals = [simulate([dict(base[i]) for i in perm], cfg)["A"]
            for perm in itertools.permutations(range(len(base)))]
    assert (max(vals) - min(vals)) / min(vals) * 100 < RESOLUTION_PCT


def test_demo_numbers_stable():
    """样例文件的 A 值是回归基线，不应漂移。

    容差取模型自身的 1% 分辨率——比这更严的断言超出模型精度（见
    references/consultation/session-strain-modeling.md §7.0）。
    """
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    sample = os.path.join(here, "..", "..", "scripts", "examples",
                          "session_strain_sample.json")
    with open(sample, encoding="utf-8") as fh:
        data = json.load(fh)
    cfg = merge_config(default_config(), data)
    got = [simulate(parse_session(s, i, cfg)["blocks"], cfg)["A"]
           for i, s in enumerate(data["sessions"])]
    want = [14.59, 12.16, 8.71, 8.34]
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert abs(g - w) / w < 0.01, "样例 A 漂移：%.2f（基线 %.2f）" % (g, w)


def test_missing_one_rm_raises_actionable_error():
    """外部负重动作缺参考 1RM 时报错，且错误信息要说明怎么补。"""
    cfg = default_config()
    with pytest.raises(ValueError) as e:
        simulate([blk("squat", sets=5, reps=8, weight=100)], cfg)
    msg = str(e.value)
    assert "参考 1RM" in msg and "one_rm" in msg

    # 自重动作不受影响（靠 eff）
    simulate([blk("pullup", sets=4, reps=6)], cfg)
