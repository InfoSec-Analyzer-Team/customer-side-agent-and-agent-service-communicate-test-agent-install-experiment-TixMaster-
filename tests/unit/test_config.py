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
    p = _write(tmp_path, "access1_Aman.log==0\naccess2_Dicurigai_sensitive_path.log==1\n")
    result = _load_stage_log_map(p)
    assert result[0].endswith("nginx/logs/access1_Aman.log")
    assert result[1].endswith("nginx/logs/access2_Dicurigai_sensitive_path.log")


def test_skips_blank_lines_and_comments(tmp_path):
    p = _write(tmp_path, "\n# just a comment\n\naccess1_Aman.log==0\n")
    result = _load_stage_log_map(p)
    assert result == {0: result[0]}  # 只有那一筆有效條目


def test_skips_line_without_equals_and_warns(tmp_path):
    p = _write(tmp_path, "not_a_valid_line\naccess1_Aman.log==0\n")
    with pytest.warns(UserWarning, match="=="):
        result = _load_stage_log_map(p)
    assert result == {0: result[0]}


def test_skips_non_integer_stage_id_and_warns(tmp_path):
    p = _write(tmp_path, "foo.log==notanumber\naccess1_Aman.log==0\n")
    with pytest.warns(UserWarning, match="stage id"):
        result = _load_stage_log_map(p)
    assert result == {0: result[0]}


def test_stage_log_paths_only_covers_attack_stages():
    # 真正的 config module-level STAGE_LOG_PATHS/NON_DIVERSITY_LOG_PATHS 是
    # import 時就從 nginx/logs/stage_log_CHECK/stage_log_map.txt 解析好的；
    # 這裡驗證「1-12 進 STAGE_LOG_PATHS、其他（例如 0=benign）進
    # NON_DIVERSITY_LOG_PATHS」這條過濾規則本身，不依賴那份 log 檔案地圖
    # 目前實際填了哪些內容。
    from dataset_health import config as cfg

    assert set(cfg.STAGE_LOG_PATHS.keys()) <= set(SUPPORT_FEATURES.keys())
    assert set(cfg.NON_DIVERSITY_LOG_PATHS.keys()).isdisjoint(SUPPORT_FEATURES.keys())
