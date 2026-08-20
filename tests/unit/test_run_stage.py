"""CLI 層級測試：真的呼叫 `python -m dataset_health.run_stage`，用真實 log
（config.STAGE_LOG_PATHS，來自 nginx/logs/stage_log_CHECK/stage_log_map.txt
自動查表）跑一次，把審查結果寫進 repo 的 report/ 目錄——這份輸出是給人看的
實際報告，不是拋棄式的暫存檔。

跟 test_diversity.py 的公式單元測試不同：這裡故意吃真實、持續在變動的資料，
所以只做結構性斷言（exit code、JSON schema、分數落在合理範圍），不釘死
具體數字——log 內容本來就會隨時間變。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from dataset_health import config as cfg

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_OUT_DIR = _REPO_ROOT / "report"


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "dataset_health.run_stage", *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",  # run_stage.py 強制 UTF-8 輸出（見它的 _force_utf8_console），
        errors="replace",  # 這裡也要用 UTF-8 解碼，不然預設走系統 codepage（cp950）會 UnicodeDecodeError
    )


def test_stage_log_paths_has_at_least_one_real_entry_to_test_against():
    assert cfg.STAGE_LOG_PATHS, (
        "config.STAGE_LOG_PATHS 是空的——下面的真實資料 CLI 測試會被 "
        "parametrize 悄悄跳過 0 筆。去 nginx/logs/stage_log_CHECK/"
        "stage_log_map.txt 補一筆 <檔名>==<stage id> 再跑"
    )


@pytest.mark.parametrize("stage_id", sorted(cfg.STAGE_LOG_PATHS.keys()))
def test_run_stage_cli_real_log_produces_valid_report(stage_id):
    """對每個目前有真實 log 對應的 stage，實際跑 CLI（不手動指定 --log，
    走 stage_log_map.txt 的自動查表），確認：
      1. CLI 正常結束（exit code 0）
      2. report/stage_<id>.json 是合法 JSON，欄位跟 StageDiversityReport.to_dict() 一致
      3. diversity_score 落在 [0,1]，per_feature 是這個 stage 支撐特徵集的子集
      4. report/stage_<id>.md 也寫出來了
    """
    result = _run_cli("--stage", str(stage_id), "--out", str(_OUT_DIR))
    assert result.returncode == 0, result.stderr

    json_path = _OUT_DIR / f"stage_{stage_id}.json"
    assert json_path.exists()

    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["stage_id"] == stage_id
    assert report["n_samples"] > 0
    assert 0.0 <= report["diversity_score"] <= 1.0
    assert set(report["per_feature"].keys()) <= set(cfg.SUPPORT_FEATURES[stage_id])
    assert isinstance(report["warnings"], list)
    assert isinstance(report["defining_violations"], list)

    md_path = _OUT_DIR / f"stage_{stage_id}.md"
    assert md_path.exists()
    assert "Diversity_stage" in md_path.read_text(encoding="utf-8")


def test_run_stage_cli_unknown_stage_exits_nonzero():
    result = _run_cli("--stage", "999")
    assert result.returncode != 0
    assert "未知的 stage" in result.stderr


def test_run_stage_cli_missing_log_and_no_config_mapping_exits_nonzero():
    unmapped_stage = next(
        (s for s in cfg.SUPPORT_FEATURES if s not in cfg.STAGE_LOG_PATHS), None
    )
    if unmapped_stage is None:
        pytest.skip("所有 stage 都已經在 stage_log_map.txt 裡有對應的 log，沒有未對應的 stage 可測")

    result = _run_cli("--stage", str(unmapped_stage))
    assert result.returncode != 0
    assert "STAGE_LOG_PATHS" in result.stderr
