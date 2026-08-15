"""Tier 1 單元測試：測公式實作對不對，不碰真實資料，完全決定性。

對照 Verify_doc/log_per_stage_verify_diversity_module_design_instruments.md §6.1。
"""

import math

import pandas as pd
import pytest

from dataset_health import config as cfg
from dataset_health.diversity import (
    coverage,
    numeric_dispersion,
    feature_diversity,
    normalized_entropy,
    stage_diversity,
)


# ============================================================
# normalized_entropy — §2.1
# ============================================================

def test_normalized_entropy_uniform_distribution_is_one():
    series = pd.Series([0, 1, 2, 3] * 50)  # 均勻分佈在全部 4 個理論取值上
    assert normalized_entropy(series, n_theoretical=4) == pytest.approx(1.0)


def test_normalized_entropy_single_value_is_zero():
    series = pd.Series([1] * 100)
    assert normalized_entropy(series, n_theoretical=4) == 0.0


def test_normalized_entropy_denominator_uses_theoretical_cardinality_not_nunique():
    # 只觀察到 2 個取值，但理論基數是 8（例如 os_type）——分母該用 ln(8)，
    # 不是 ln(nunique())=ln(2)，所以即使這 2 個值均勻分佈，結果也要 < 1。
    series = pd.Series([0, 1] * 50)
    result = normalized_entropy(series, n_theoretical=8)
    expected = math.log(2) / math.log(8)
    assert result == pytest.approx(expected)
    assert result < 1.0


def test_normalized_entropy_n_theoretical_one_is_zero():
    series = pd.Series([0] * 10)
    assert normalized_entropy(series, n_theoretical=1) == 0.0


def test_normalized_entropy_ignores_nan():
    series = pd.Series([0, 1, None, 0, 1])
    result = normalized_entropy(series, n_theoretical=2)
    assert result == pytest.approx(1.0)


# ============================================================
# coverage — §2.2
# ============================================================

def test_coverage_reports_missing_set():
    series = pd.Series([0, 1, 0, 1])
    cov, missing = coverage(series, expected_values=[0, 1, 2, 3])
    assert cov == pytest.approx(0.5)
    assert missing == {2, 3}


def test_coverage_full_is_one_with_no_missing():
    series = pd.Series([0, 1, 2])
    cov, missing = coverage(series, expected_values=[0, 1, 2])
    assert cov == pytest.approx(1.0)
    assert missing == set()


def test_coverage_ignores_values_outside_expected_set():
    # 觀察到 expected 集合以外的值不該讓 cov > 1，也不該出現在 missing 裡
    series = pd.Series([0, 1, 99])
    cov, missing = coverage(series, expected_values=[0, 1])
    assert cov == pytest.approx(1.0)
    assert missing == set()


# ============================================================
# numeric_dispersion — §2.3 QCD
# ============================================================

def test_numeric_dispersion_all_zero_is_zero():
    series = pd.Series([0] * 20)
    assert numeric_dispersion(series) == 0.0


def test_numeric_dispersion_mostly_zero_q1_q3_zero_is_zero():
    # 超過 75% 為 0 → Q1=Q3=0 → 依規格顯式回 0，不可讓除法拋錯
    series = pd.Series([0] * 80 + [5] * 20)
    assert numeric_dispersion(series) == 0.0


def test_numeric_dispersion_known_quartiles_matches_manual_formula():
    series = pd.Series(range(1, 101))  # 1..100
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    expected = (q3 - q1) / (q3 + q1)
    assert numeric_dispersion(series) == pytest.approx(expected)


def test_numeric_dispersion_robust_to_outlier():
    base = list(range(1, 101))
    with_outlier = base + [1_000_000]
    d_base = numeric_dispersion(pd.Series(base))
    d_outlier = numeric_dispersion(pd.Series(with_outlier))
    # QCD 用 Q1/Q3，不看極端值，加一個離群值不該讓分數劇烈跳動
    assert d_outlier == pytest.approx(d_base, abs=0.05)


# ============================================================
# feature_diversity — 分派
# ============================================================

def test_feature_diversity_dispatches_categorical_to_entropy():
    series = pd.Series([1, 1, 1, 1])
    assert feature_diversity(series, "os_type", cfg) == 0.0


def test_feature_diversity_dispatches_numeric_to_qcd():
    series = pd.Series([0] * 20)
    assert feature_diversity(series, "url_length", cfg) == 0.0


def test_feature_diversity_unknown_feature_raises():
    with pytest.raises(ValueError):
        feature_diversity(pd.Series([1, 2, 3]), "not_a_real_feature", cfg)


# ============================================================
# stage_diversity — §2.5 / §4 / §5
# ============================================================

def _stage2_fixture(n=300, sql_flag_all_one=True):
    """Stage 2 = SQLi。定義 flag `has_sql_injection` 排除在 F 之外。"""
    return pd.DataFrame({
        "has_sql_injection": [1] * n if sql_flag_all_one else ([1] * (n - 5) + [0] * 5),
        "os_type": [i % 8 for i in range(n)],
        "ua_length": [50 + (i % 30) for i in range(n)],
        "url_length": [20 + (i % 40) for i in range(n)],
        "url_special_chars": [i % 5 for i in range(n)],
        "url_param_count": [i % 3 for i in range(n)],
        "request_method": ["GET" if i % 2 == 0 else "POST" for i in range(n)],
        "url_encoding_count": [i % 4 for i in range(n)],
    })


def test_stage_diversity_excludes_defining_flag_from_support_set():
    df = _stage2_fixture()
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert "has_sql_injection" not in report.per_feature
    assert set(report.per_feature.keys()) == set(cfg.SUPPORT_FEATURES[2])


def test_stage_diversity_small_sample_is_provisional():
    df = _stage2_fixture(n=50)
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert report.provisional is True
    assert any("provisional" in w or "MIN_SAMPLES" in w for w in report.warnings)


def test_stage_diversity_large_sample_not_provisional():
    df = _stage2_fixture(n=300)
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert report.provisional is False


def test_stage_diversity_full_collapse_warns():
    df = _stage2_fixture(n=300)
    df["os_type"] = 1  # 支撐特徵完全無變異
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert report.per_feature["os_type"].d == 0.0
    assert any("os_type" in w and "塌縮" in w for w in report.warnings)


def test_stage_diversity_defining_flag_violation_warns():
    df = _stage2_fixture(n=300, sql_flag_all_one=False)
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert any("不符合定義判準" in w for w in report.warnings)


def test_stage_diversity_weighted_average_matches_manual_calc():
    df = _stage2_fixture(n=300)
    report = stage_diversity(df, stage_id=2, cfg=cfg)

    manual = [d.d for d in report.per_feature.values()]
    assert report.diversity_score == pytest.approx(sum(manual) / len(manual))


def test_stage_diversity_unknown_stage_raises_keyerror():
    df = _stage2_fixture()
    with pytest.raises(KeyError):
        stage_diversity(df, stage_id=999, cfg=cfg)


def test_stage_diversity_stage8_numeric_defining_predicate():
    # Stage 8：定義不是 0/1 flag，而是 url_encoding_count > 0（§3.4）
    n = 300
    df = pd.DataFrame({
        "url_encoding_count": [1] * n,  # 全部符合 > 0
        "url_length": [20 + (i % 40) for i in range(n)],
        "url_special_chars": [i % 5 for i in range(n)],
        "os_type": [i % 8 for i in range(n)],
        "ua_length": [50 + (i % 30) for i in range(n)],
    })
    report = stage_diversity(df, stage_id=8, cfg=cfg)
    assert not any("不符合定義判準" in w for w in report.warnings)


def test_stage_diversity_stage11_keeps_request_method_in_support_set():
    # Stage 11：異常 HTTP 方法。request_method 是「定義判準」的一部分，
    # 但規格 §3.1/§3.5 刻意把它留在支撐特徵集裡（例外，見 config.py 註解）。
    n = 300
    methods = ["PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]
    df = pd.DataFrame({
        "request_method": [methods[i % len(methods)] for i in range(n)],
        "url_length": [20 + (i % 40) for i in range(n)],
        "os_type": [i % 8 for i in range(n)],
        "ua_length": [50 + (i % 30) for i in range(n)],
    })
    report = stage_diversity(df, stage_id=11, cfg=cfg)
    assert "request_method" in report.per_feature
    # 全部是非 GET/POST 方法 → 不該觸發定義判準違反警告
    assert not any("不符合定義判準" in w for w in report.warnings)


def test_stage_diversity_stage11_defining_violation_when_get_post_present():
    n = 300
    df = pd.DataFrame({
        "request_method": ["GET"] * n,
        "url_length": [20] * n,
        "os_type": [1] * n,
        "ua_length": [50] * n,
    })
    report = stage_diversity(df, stage_id=11, cfg=cfg)
    assert any("不符合定義判準" in w for w in report.warnings)


def test_stage_diversity_missing_column_warns_and_is_skipped():
    df = _stage2_fixture(n=300).drop(columns=["os_type"])
    report = stage_diversity(df, stage_id=2, cfg=cfg)
    assert "os_type" not in report.per_feature
    assert any("os_type" in w and "不在輸入" in w for w in report.warnings)