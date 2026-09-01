"""單元測試：dataset_health.config 的 stage_log_map.txt 解析與過濾邏輯。

對照 nginx/logs/stage_log_CHECK/README.md 的格式規則。
"""

import warnings

import pytest

from dataset_health.config import _load_stage_log_map, SUPPORT_FEATURES


def _write(tmp_path, text):
    p = tmp_path / "stage_log_map.txt"
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_file_returns_empty_dict(tmp_path):
    result = _load_stage_log_map(tmp_path / "does_not_exist.txt")
    assert result == {}


def test_parses_valid_lines(tmp_path):
    p = _write(tmp_path, "logs/access1_Aman.log==0\nlogs/access2_Dicurigai_sensitive_path.log==1\n")
    result = _load_stage_log_map(p)
    assert result[0] == ["nginx/logs/access1_Aman.log"]
    assert result[1] == ["nginx/logs/access2_Dicurigai_sensitive_path.log"]


def test_parses_comma_separated_multiple_paths_on_one_line(tmp_path):
    p = _write(tmp_path, "logs/access2_Dicurigai_sensitive_path.log,collected/nikto.log==1\n")
    result = _load_stage_log_map(p)
    assert result[1] == [
        "nginx/logs/access2_Dicurigai_sensitive_path.log",
        "nginx/collected/nikto.log",
    ]


def test_multiple_lines_for_same_stage_accumulate_not_overwrite(tmp_path):
    p = _write(tmp_path, "logs/a.log==1\nlogs/b.log==1\n")
    result = _load_stage_log_map(p)
    assert result[1] == ["nginx/logs/a.log", "nginx/logs/b.log"]


def test_skips_blank_lines_and_comments(tmp_path):
    p = _write(tmp_path, "\n# just a comment\n\nlogs/access1_Aman.log==0\n")
    result = _load_stage_log_map(p)
    assert result == {0: result[0]}  # 只有那一筆有效條目


def test_skips_line_without_equals_and_warns(tmp_path):
    p = _write(tmp_path, "not_a_valid_line\nlogs/access1_Aman.log==0\n")
    with pytest.warns(UserWarning, match="=="):
        result = _load_stage_log_map(p)
    assert result == {0: result[0]}


def test_skips_non_integer_stage_id_and_warns(tmp_path):
    p = _write(tmp_path, "foo.log==notanumber\nlogs/access1_Aman.log==0\n")
    with pytest.warns(UserWarning, match="stage id"):
        result = _load_stage_log_map(p)
    assert result == {0: result[0]}


def test_skips_line_with_no_path_before_equals_and_warns(tmp_path):
    p = _write(tmp_path, "==1\nlogs/access1_Aman.log==0\n")
    with pytest.warns(UserWarning, match="沒有檔名"):
        result = _load_stage_log_map(p)
    assert result == {0: result[0]}


def test_every_support_feature_has_a_registered_feature_type():
    # 迴歸測試：has_double_encoding 曾經出現在 SUPPORT_FEATURES[4] 裡，卻沒登記
    # 進 CARDINALITY/EXPECTED_VALUES（進而沒進 FEATURE_TYPE），拿真實
    # nginx/collected/nginx01_batch_path_traversal_001.log 跑 stage 4 時
    # 直接 ValueError。這裡把「SUPPORT_FEATURES 用到的每個特徵，FEATURE_TYPE
    # 都要有」這條隱性契約直接斷言出來，之後同類遺漏會在單元測試就炸，不用
    # 等到真實資料才發現。
    from dataset_health import config as cfg

    used_features = {f for features in cfg.SUPPORT_FEATURES.values() for f in features}
    missing = used_features - set(cfg.FEATURE_TYPE.keys())
    assert not missing, f"這些特徵出現在 SUPPORT_FEATURES 裡，但沒登記進 FEATURE_TYPE: {missing}"


def test_every_categorical_support_feature_has_expected_values():
    # 同上，但斷言 EXPECTED_VALUES（coverage 診斷用）也要有，不能只顧
    # entropy 那一半。
    from dataset_health import config as cfg

    used_features = {f for features in cfg.SUPPORT_FEATURES.values() for f in features}
    used_categorical = {f for f in used_features if cfg.FEATURE_TYPE.get(f) == "categorical"}
    missing = used_categorical - set(cfg.EXPECTED_VALUES.keys())
    assert not missing, f"這些類別型特徵出現在 SUPPORT_FEATURES 裡，但沒登記進 EXPECTED_VALUES: {missing}"


def test_stage_log_paths_only_covers_attack_stages():
    # 真正的 config module-level STAGE_LOG_PATHS/NON_DIVERSITY_LOG_PATHS 是
    # import 時就從 nginx/logs/stage_log_CHECK/stage_log_map.txt 解析好的；
    # 這裡驗證「1-12 進 STAGE_LOG_PATHS、其他（例如 0=benign）進
    # NON_DIVERSITY_LOG_PATHS」這條過濾規則本身，不依賴那份 log 檔案地圖
    # 目前實際填了哪些內容。
    from dataset_health import config as cfg

    assert set(cfg.STAGE_LOG_PATHS.keys()) <= set(SUPPORT_FEATURES.keys())
    assert set(cfg.NON_DIVERSITY_LOG_PATHS.keys()).isdisjoint(SUPPORT_FEATURES.keys())
