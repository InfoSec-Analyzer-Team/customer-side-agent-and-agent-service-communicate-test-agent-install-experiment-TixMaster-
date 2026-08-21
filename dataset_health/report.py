"""dataset_health.report — 把 StageDiversityReport 序列化成 JSON / markdown。

供 run_stage.py（單一 stage）與未來的 run_all_stages.py（§8 步驟 4 後半，
依賴 config.STAGE_LOG_PATHS 先填好，目前還沒做）共用。對照規格 §4 輸出契約、
§6.2 CI artifact 格式。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .diversity import StageDiversityReport
from . import config as default_config

# markdown 裡不符合定義判準的樣本列表最多印這麼多筆，超過的用「...還有 N 筆」
# 收尾，避免一份混進太多其他 stage 樣本的 log 把報告拉到幾千行。JSON 輸出
# （to_json / StageDiversityReport.to_dict）上限寬鬆很多（見
# config.MAX_DEFINING_VIOLATIONS），但一樣不是無限——大型工具掃描（例如
# 15843 筆的 nikto scan）不截斷的話 JSON 報告會膨脹到 5+ MB。真實總數兩邊
# 都能從 defining_violations_total 拿到，不會因為截斷而失真。
_MAX_VIOLATIONS_IN_MARKDOWN = 20


def to_json(report: StageDiversityReport) -> str:
    """§4 輸出契約：StageDiversityReport 可被序列化成 JSON（供 CI artifact）。"""
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def to_markdown(report: StageDiversityReport, cfg=default_config) -> str:
    """§4 輸出契約：StageDiversityReport 可被序列化成 markdown（供人看）。"""
    stage_name = cfg.STAGE_NAMES.get(report.stage_id, f"stage {report.stage_id}")

    lines = [
        f"# Stage {report.stage_id} 多元度驗收報告 — {stage_name}",
        "",
        f"- 樣本數：{report.n_samples}"
        + ("（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）" if report.provisional else ""),
        f"- **Diversity_stage = {report.diversity_score:.4f}**",
        "",
    ]

    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in report.warnings:
            lines.append(f"- ⚠️ {w}")
        lines.append("")

    if report.defining_violations:
        lines.append("## 不符合定義判準的樣本")
        lines.append("")
        shown = report.defining_violations[:_MAX_VIOLATIONS_IN_MARKDOWN]
        columns = list(dict.fromkeys(k for v in shown for k in v.keys()))  # 保留第一次出現的順序
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
        for v in shown:
            lines.append("| " + " | ".join(str(v.get(c, "")) for c in columns) + " |")
        remaining = report.defining_violations_total - len(shown)
        if remaining > 0:
            lines.append("")
            lines.append(f"...還有 {remaining} 筆，明細見 JSON 輸出的 `defining_violations`"
                          + ("（JSON 也有截斷，見 config.MAX_DEFINING_VIOLATIONS）"
                             if report.defining_violations_total > len(report.defining_violations)
                             else ""))
        lines.append("")

    lines.append("## 支撐特徵明細")
    lines.append("")
    lines.append("| 特徵 | d(f) | coverage | missing |")
    lines.append("| --- | --- | --- | --- |")
    for feature, pf in report.per_feature.items():
        d = pf.to_dict()
        has_coverage = "coverage" in d
        cov_text = f"{d['coverage']:.2f}" if has_coverage else "—"
        missing_values = d.get("missing", []) if has_coverage else []
        missing_text = ", ".join(str(m) for m in missing_values) if missing_values else ("—" if has_coverage else "—")
        lines.append(f"| `{feature}` | {d['d']:.4f} | {cov_text} | {missing_text} |")
    lines.append("")

    return "\n".join(lines)


def write_report(report: StageDiversityReport, out_dir: Union[str, Path], cfg=default_config) -> dict:
    """寫出 <out_dir>/stage_<id>.json 與 <out_dir>/stage_<id>.md，回傳寫出的路徑。"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    json_path = out_path / f"stage_{report.stage_id}.json"
    md_path = out_path / f"stage_{report.stage_id}.md"

    json_path.write_text(to_json(report), encoding="utf-8")
    md_path.write_text(to_markdown(report, cfg=cfg), encoding="utf-8")

    return {"json": str(json_path), "markdown": str(md_path)}