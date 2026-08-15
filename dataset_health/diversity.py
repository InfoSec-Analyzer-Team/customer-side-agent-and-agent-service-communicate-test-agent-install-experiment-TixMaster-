"""dataset_health.diversity — per-stage 多元度驗收公式與模組介面實作。

對照 Verify_doc/log_per_stage_verify_diversity_module_design_instruments.md
§2（公式）、§4（介面契約）、§5（邊界情況）。所有 stage 專屬常數一律從
`config.py` 讀，這裡不得硬編。
"""

from __future__ import annotations

import dataclasses
import math
import re
import warnings
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

# ============================================================
# §4 — load_stage_log：純 I/O + parsing，不算任何特徵
# ============================================================
#
# 這個正則刻意跟 agent/parser.py 的 _COMBINED_RE 同一套錨點結構（同樣的
# ident/auth/optional-referer/optional-UA 寫法），避免兩邊對同一份 nginx
# combined log format 各自維護一份會漂移的 parsing 邏輯。唯一差異：這裡把
# 整個 "METHOD URL PROTO" 當一個 group 原樣保留（不像 agent/parser.py 拆開
# method/url 後丟棄 proto），因為 feature_engineering.extract_request_features()
# 本來就要對這個原始字串自己 regex 出 method/url/version 三者——丟給它同一份
# 原始字串，而不是重新组装,才不會有第二份平行的 method/url/proto 拆解邏輯。
_LOG_LINE_RE = re.compile(
    r'^(\S+)'                    # remote_addr
    r' \S+ \S+'                  # ident, auth（通常都是 "-"）
    r' \[([^\]]+)\]'             # [time_local]
    r' "([^"]*)"'                # "METHOD URL PROTO"（原樣保留，交給 feature_engineering 解析）
    r' (\d{3})'                  # status
    r' (\d+|-)'                  # bytes sent（"-" = 0）
    r'(?: "([^"]*)")?'           # optional referer
    r'(?: "([^"]*)")?'           # optional user_agent
)

# 跟 agent/parser.py 的 _TIME_FMT 一致：nginx/apache combined log 的
# time_local 格式（例如 "26/Jul/2026:00:41:55 +0000"）。
_TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


def _parse_time_local(raw: str) -> str:
    """把 combined log 的 time_local 轉成帶 offset 的 ISO 字串。

    time_features.compute_time_features() 依 §1.4 設計為逐列解析原始時間
    字串，能吃「帶 offset 的字串」；轉不動就回傳原始字串讓它自己 fallback。
    """
    try:
        return datetime.strptime(raw, _TIME_FMT).isoformat()
    except ValueError:
        return raw


def load_stage_log(log_path: str, stage_id: int, cfg) -> pd.DataFrame:
    """讀一份 stage 的裸 access.log，parse 成 create_all_features() 需要的
    原始欄位 DataFrame（ip, request, referer, status, size, browser, datetime）。

    純 I/O + parsing，不算任何特徵。`stage_id`/`cfg` 目前不影響 parsing 本身
    （介面依 §4 契約保留，供未來需要依 stage 調整 parsing 規則時使用）。
    """
    rows = []
    n_unparsed = 0

    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            m = _LOG_LINE_RE.match(line)
            if not m:
                n_unparsed += 1
                continue

            ip, time_local, request, status, size, referer, browser = m.groups()
            rows.append({
                "ip": ip,
                "datetime": _parse_time_local(time_local),
                "request": request,
                "status": status,
                "size": 0 if size == "-" else size,
                "referer": referer if referer is not None else "-",
                "browser": browser if browser is not None else "",
            })

    if n_unparsed:
        warnings.warn(
            f"load_stage_log: stage {stage_id}: {n_unparsed} line(s) in "
            f"{log_path!r} failed to parse against combined log format and "
            f"were skipped"
        )

    return pd.DataFrame(rows)


def extract_stage_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """呼叫 feature_engineering.create_all_features(df_raw)，回傳 31 欄特徵
    （28 欄程式碼內固定映射的整數特徵 + 3 欄尚未 LabelEncoding 的原始字串
    ip_type/request_method/request_version）。

    必須直接 import 並呼叫 feature_engineering 的函式，不得自己重寫一份平行
    邏輯——否則又是 training-serving skew（見 §3.5）。
    """
    from . import feature_engineering  # noqa: PLC0415 — 延後 import，見 feature_engineering.py 頂部說明

    return feature_engineering.create_all_features(df_raw.copy(), verbose=False)


# ============================================================
# §2.1 — 標準化 Shannon 熵（類別型特徵）
# ============================================================

def normalized_entropy(series: pd.Series, n_theoretical: int) -> float:
    """§2.1。`n_theoretical` 來自 config.CARDINALITY，不得用 series.nunique()。

    N_f = 1 時定義為 0（無變異空間）。
    """
    if n_theoretical <= 1:
        return 0.0

    counts = series.dropna().value_counts()
    total = counts.sum()
    if total == 0:
        return 0.0

    probs = counts / total
    h = -float((probs * np.log(probs)).sum())
    # 0.0 + ... 把單一取值情況下可能出現的 -0.0 正規化成 0.0，避免 JSON/報告裡
    # 出現視覺上易誤解的負零。
    return 0.0 + h / math.log(n_theoretical)


# ============================================================
# §2.2 — 類別涵蓋率（類別型特徵）
# ============================================================

def coverage(series: pd.Series, expected_values: list) -> tuple[float, set]:
    """§2.2。回傳 (cov, missing_set)。"""
    expected = set(expected_values)
    if not expected:
        return 0.0, set()

    observed = set(series.dropna().unique().tolist())
    missing = expected - observed
    cov = len(observed & expected) / len(expected)
    return cov, missing


# ============================================================
# §2.3 — 四分位離散係數 QCD（數值型特徵）
# ============================================================

def numeric_dispersion(series: pd.Series) -> float:
    """§2.3 QCD。Q3+Q1==0 時回 0.0（超過 75% 樣本為 0 的正確反映，不可拋錯）。"""
    s = series.dropna()
    if s.empty:
        return 0.0

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    denom = q3 + q1
    if denom == 0:
        return 0.0
    return float((q3 - q1) / denom)


# ============================================================
# §2.4 — 尾部涵蓋旗標（數值型，歸屬 realism 側，不進 diversity）
# ============================================================

def tail_reach(series: pd.Series, baseline_p95: Optional[float]) -> Optional[float]:
    """§2.4。baseline_p95 來自 baseline 資料；無 baseline 時回 None（不計入）。"""
    if baseline_p95 is None:
        return None

    s = series.dropna()
    if s.empty:
        return None
    return float((s > baseline_p95).mean())


# ============================================================
# 依 FEATURE_TYPE 分派
# ============================================================

def feature_diversity(series: pd.Series, feature: str, cfg) -> float:
    """依 FEATURE_TYPE 分派到 normalized_entropy 或 numeric_dispersion，回 d(f)。"""
    ftype = cfg.FEATURE_TYPE.get(feature)
    if ftype == "categorical":
        n_theoretical = cfg.CARDINALITY[feature]
        return normalized_entropy(series, n_theoretical)
    if ftype == "numeric":
        return numeric_dispersion(series)
    raise ValueError(
        f"feature_diversity: 特徵 {feature!r} 不在 cfg.FEATURE_TYPE 裡"
        f"（既不是 categorical 也不是 numeric）"
    )


# ============================================================
# §3.4 / §4 — 定義判準（DEFINING_FLAG / DEFINING_PREDICATE）驗證
# ============================================================

_PREDICATE_OPS = {
    "eq": lambda s, v: s == v,
    "ne": lambda s, v: s != v,
    "gt": lambda s, v: s > v,
    "ge": lambda s, v: s >= v,
    "lt": lambda s, v: s < v,
    "le": lambda s, v: s <= v,
    "in": lambda s, v: s.isin(v),
    "not_in": lambda s, v: ~s.isin(v),
}


def _eval_condition(df: pd.DataFrame, condition: dict) -> pd.Series:
    feature = condition["feature"]
    if feature not in df.columns:
        raise KeyError(
            f"defining predicate 用到的欄位 {feature!r} 不在輸入 DataFrame 裡"
        )
    op = _PREDICATE_OPS[condition["op"]]
    return op(df[feature], condition["value"])


def _defining_conditions(stage_id: int, cfg) -> list:
    """統一把 DEFINING_FLAG（單一 0/1 flag）跟 DEFINING_PREDICATE（複合/數值
    條件）攤平成同一種 condition list，方便 _validate_defining 統一處理。"""
    flag = cfg.DEFINING_FLAG.get(stage_id)
    if flag is not None:
        return [{"feature": flag, "op": "eq", "value": 1, "exclude_from_support": True}]
    return cfg.DEFINING_PREDICATE.get(stage_id, [])


def _validate_defining(df: pd.DataFrame, stage_id: int, cfg) -> list[str]:
    """步驟 1：用 cfg.DEFINING_FLAG / DEFINING_PREDICATE 驗證這批確實屬於此
    stage（不符 → warn）。stage 10/12 這種「目標即多樣性」型沒有判準，略過。
    """
    conditions = _defining_conditions(stage_id, cfg)
    if not conditions:
        return []

    n = len(df)
    if n == 0:
        return []

    mask = pd.Series(True, index=df.index)
    for cond in conditions:
        try:
            mask &= _eval_condition(df, cond)
        except KeyError as exc:
            return [f"stage {stage_id}: {exc}"]

    n_bad = int((~mask).sum())
    if n_bad == 0:
        return []
    return [
        f"stage {stage_id}: {n_bad}/{n} 筆樣本不符合定義判準 {conditions!r}，"
        f"可能混入其他 stage 的樣本，或定義判準本身設錯"
    ]


# ============================================================
# 報告結構
# ============================================================

@dataclasses.dataclass
class PerFeatureDiversity:
    d: float
    coverage: Optional[float] = None
    missing: Optional[set] = None

    def to_dict(self) -> dict:
        out: dict[str, Any] = {"d": self.d}
        if self.coverage is not None:
            out["coverage"] = self.coverage
            out["missing"] = sorted(self.missing) if self.missing else []
        return out


@dataclasses.dataclass
class StageDiversityReport:
    stage_id: int
    n_samples: int
    diversity_score: float
    per_feature: dict  # feature -> PerFeatureDiversity
    warnings: list
    provisional: bool

    def to_dict(self) -> dict:
        """供 report.py 序列化成 JSON（§4 輸出契約）。"""
        return {
            "stage_id": self.stage_id,
            "n_samples": self.n_samples,
            "diversity_score": self.diversity_score,
            "provisional": self.provisional,
            "per_feature": {f: pf.to_dict() for f, pf in self.per_feature.items()},
            "warnings": list(self.warnings),
        }


# ============================================================
# §2.5 / §4 — stage_diversity：主入口
# ============================================================

def stage_diversity(df: pd.DataFrame, stage_id: int, cfg) -> StageDiversityReport:
    """§2.5。df = extract_stage_features() 的輸出（31 欄 + label）。

    步驟：
      1. 用 cfg.DEFINING_FLAG / DEFINING_PREDICATE 驗證這批確實屬於此 stage（不符 → warn）。
      2. F = cfg.SUPPORT_FEATURES[stage_id]。
      3. 對每個 f 算 d(f)；類別型另算 coverage。
      4. 加權平均得 Diversity_stage。
      5. 組裝 per-feature 明細 + 缺漏診斷 + 樣本數警告。
    """
    if stage_id not in cfg.SUPPORT_FEATURES:
        raise KeyError(f"stage_diversity: 未知的 stage_id {stage_id!r}（不在 cfg.SUPPORT_FEATURES 裡）")

    warnings_list: list[str] = _validate_defining(df, stage_id, cfg)

    if (
        stage_id == 9
        and getattr(cfg, "SPECIAL_CHARS_DENSE_THRESHOLD", None) is None
    ):
        warnings_list.append(
            "stage 9: config.SPECIAL_CHARS_DENSE_THRESHOLD 尚未由團隊拍板，"
            "目前定義判準只驗證 has_xss==1，未驗 url_special_chars 密集門檻"
        )

    n_samples = len(df)
    provisional = n_samples < cfg.MIN_SAMPLES
    if provisional:
        warnings_list.append(
            f"stage {stage_id}: n_samples={n_samples} < MIN_SAMPLES={cfg.MIN_SAMPLES}，"
            f"熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻"
        )

    support_features = cfg.SUPPORT_FEATURES[stage_id]
    weights = cfg.STAGE_WEIGHTS.get(stage_id, {f: 1.0 for f in support_features})

    # 定義判準特徵不該混進支撐集，除非明確標 exclude_from_support=False
    # （唯一已知例外是 stage 11 的 request_method，見 config.py 註解與 §3.5）。
    for cond in _defining_conditions(stage_id, cfg):
        feature = cond["feature"]
        if cond.get("exclude_from_support", True) and feature in support_features:
            warnings_list.append(
                f"stage {stage_id}: 定義判準特徵 {feature!r} 出現在支撐特徵集 F 中，"
                f"違反 §1.2「多元度只評支撐特徵,不評定義 flag」的原則"
            )

    per_feature: dict[str, PerFeatureDiversity] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for feature in support_features:
        if feature not in df.columns:
            warnings_list.append(f"stage {stage_id}: 支撐特徵 {feature!r} 不在輸入 DataFrame 欄位中，跳過")
            continue

        series = df[feature]
        d = feature_diversity(series, feature, cfg)

        cov = None
        missing = None
        if cfg.FEATURE_TYPE.get(feature) == "categorical":
            expected = cfg.EXPECTED_VALUES.get(feature)
            if expected is not None:
                cov, missing = coverage(series, expected)

        per_feature[feature] = PerFeatureDiversity(d=d, coverage=cov, missing=missing)

        if d == 0.0:
            warnings_list.append(f"stage {stage_id}: 支撐特徵 {feature!r} 完全塌縮（d=0）")

        w = weights.get(feature, 1.0)
        weighted_sum += w * d
        weight_total += w

    diversity_score = weighted_sum / weight_total if weight_total > 0 else 0.0

    return StageDiversityReport(
        stage_id=stage_id,
        n_samples=n_samples,
        diversity_score=diversity_score,
        per_feature=per_feature,
        warnings=warnings_list,
        provisional=provisional,
    )