"""dataset_health.run_stage — CLI：單一 stage 的裸 access.log → 多元度報告。

用法：
    python -m dataset_health.run_stage --stage 1 --log nginx/logs/access2_Dicurigai_sensitive_path.log --out report/

--log 可以逗號分隔多個路徑，跟 stage_log_map.txt 的多檔語法一致，一次合併多份
log 一起評多元度。

對照規格 §6.2 / §8 步驟 4。手動指定路徑（--log）優先於 config.STAGE_LOG_PATHS
查表，兩者可以獨立存在（見 config.py 對 STAGE_LOG_PATHS 待補的說明）。
"""

from __future__ import annotations

import argparse
import sys

from . import config as cfg
from .diversity import extract_stage_features, load_stage_logs, stage_diversity
from .report import to_markdown, write_report


def _resolve_log_paths(stage: int, log_arg: str | None) -> list[str]:
    if log_arg:
        return [p.strip() for p in log_arg.split(",") if p.strip()]
    paths = cfg.STAGE_LOG_PATHS.get(stage)
    if not paths:
        raise SystemExit(
            f"stage {stage} 沒有指定 --log，config.STAGE_LOG_PATHS 也還沒填"
            f"（§3.7 待團隊拍板 log 檔案命名慣例），無法自動找到 log 檔案；"
            f"請用 --log 手動指定路徑"
        )
    return paths


def _force_utf8_console() -> None:
    """Windows 終端機的預設 codepage（例如 cp950）編不出 ⚠️ 等符號，印報告時
    會直接 UnicodeEncodeError 崩潰。這裡把 stdout/stderr 重設成 UTF-8，跟主控台
    實際 codepage 無關；reconfigure 在極舊 Python 才可能沒有，包一層防呆。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_console()
    parser = argparse.ArgumentParser(description="跑單一 stage 的 per-stage 多元度驗收（§2/§4）")
    parser.add_argument("--stage", type=int, required=True, help="stage id（見 config.SUPPORT_FEATURES）")
    parser.add_argument("--log", type=str, default=None, help="裸 access.log 路徑（逗號分隔可多份）；省略則查 config.STAGE_LOG_PATHS")
    parser.add_argument("--out", type=str, default="report", help="輸出目錄，預設 report/")
    args = parser.parse_args(argv)

    if args.stage not in cfg.SUPPORT_FEATURES:
        parser.error(f"未知的 stage {args.stage}（合法範圍：{sorted(cfg.SUPPORT_FEATURES)}）")

    log_paths = _resolve_log_paths(args.stage, args.log)

    df_raw = load_stage_logs(log_paths, stage_id=args.stage, cfg=cfg)
    if df_raw.empty:
        print(f"[run_stage] {log_paths!r} 沒有解析出任何一行 log，中止", file=sys.stderr)
        return 1

    df = extract_stage_features(df_raw)
    report = stage_diversity(df, stage_id=args.stage, cfg=cfg)

    paths = write_report(report, args.out, cfg=cfg)

    print(to_markdown(report, cfg=cfg))
    print(f"[run_stage] wrote {paths['json']}")
    print(f"[run_stage] wrote {paths['markdown']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())