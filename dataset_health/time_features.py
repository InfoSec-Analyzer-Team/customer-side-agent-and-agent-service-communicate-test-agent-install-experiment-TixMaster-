
"""
共用時間特徵計算模組
====================
訓練端 (`feature_engineering.py`) 與線上推論端 (`processing/pipeline_utils.py`)
共用同一份時間戳正規化 / 時區換算邏輯，避免兩邊各自實作導致 training-serving skew。

只依賴標準庫（datetime / zoneinfo），刻意不 import pandas，讓沒有安裝 pandas 的
執行環境（例如 processing container）也能單獨 import 這個模組。

處理的邊界情況：
- 混合「不帶 offset 的 naive 字串」與「帶 offset 的字串」（'Z' / '+00:00' / '+0700' 等）
- 未知或無效的 IANA 時區名稱 → local_* 直接 fallback 成 UTC 版本，不中斷流程
- DST（日光節約時間）邊界 → 一律透過 zoneinfo 依實際日期換算，不是固定 offset 加減
- None / NaN / NaT / 空字串 → 全部特徵 fallback 為 0（等同 UTC 週一凌晨 0 點）
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

__all__ = ["parse_to_utc", "compute_time_features", "zone_lookup_failure_count", "check_tzdata_available"]

logger = logging.getLogger(__name__)

# ZoneInfo 在沒有系統 tzdata、也沒裝 tzdata PyPI 套件的環境（常見於 slim/minimal
# Docker base image）會對「幾乎每一個非 UTC 時區」拋出 ZoneInfoNotFoundError，讓
# local_* 特徵整批默默退化成 UTC 版本。這裡用一個計數器 + 「每個時區名稱只記一次
# log」的方式，讓這種系統性失敗在 log（進而在 Kibana）裡是看得到、可告警的，
# 而不是被 compute_time_features() 的 fallback 完全吞掉。
_zone_lookup_failures = 0
_zone_lookup_failed_names: set = set()

# Checked once on first failure so we can distinguish "tzdata package missing"
# (systemic — escalate to ERROR) from "bad timezone name" (per-event — WARNING).
_tzdata_available: Optional[bool] = None


def zone_lookup_failure_count() -> int:
    """目前為止 ZoneInfo 查詢失敗的累計次數，供呼叫端（例如 processing container
    的啟動自我檢查，或未來的 /health 端點）做觀測用。"""
    return _zone_lookup_failures


def _resolve_zoneinfo(tz_name: str) -> Optional[ZoneInfo]:
    global _zone_lookup_failures, _tzdata_available
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        _zone_lookup_failures += 1
        if tz_name not in _zone_lookup_failed_names:
            _zone_lookup_failed_names.add(tz_name)
            if _tzdata_available is None:
                _tzdata_available = check_tzdata_available()
            if not _tzdata_available:
                logger.error(
                    "tzdata package is missing from this environment — ALL timezone lookups "
                    "will silently fall back to UTC.  Add 'tzdata' to requirements.txt. "
                    "First failing tz_name=%r", tz_name,
                )
            else:
                logger.warning(
                    "Unknown timezone tz_name=%r; local_* features falling back to UTC. (%s)",
                    tz_name, exc,
                )
        return None
    except Exception as exc:
        _zone_lookup_failures += 1
        if tz_name not in _zone_lookup_failed_names:
            _zone_lookup_failed_names.add(tz_name)
            logger.warning(
                "ZoneInfo lookup error for tz_name=%r (%s); local_* features falling back to UTC.",
                tz_name, exc,
            )
        return None


def check_tzdata_available() -> bool:
    """啟動時的自我檢查：確認 IANA 時區資料庫實際可用（不管是系統內建還是靠 tzdata
    套件），而不是等到第一筆事件才發現 local_* 全部悄悄退化成 UTC。回傳 False 時
    應該在啟動 log 印出明顯的警告或錯誤。"""
    try:
        ZoneInfo("Asia/Taipei")
        return True
    except Exception:
        return False


def _time_period(hour: int) -> int:
    """0=night(0-5), 1=morning(6-11), 2=afternoon(12-17), 3=evening(18-23)。
    區間剛好是每 6 小時一段，整數除法等價於逐段判斷，更簡潔。"""
    return hour // 6


def _is_missing(value: Any) -> bool:
    """涵蓋 None / float('nan') / pandas NaT 的通用判斷，不需要 import pandas
    （NaN 與 NaT 都滿足 x != x 這個自我不相等的特性）。"""
    if value is None:
        return True
    try:
        return value != value
    except Exception:
        return False


def parse_to_utc(ts: Any, offset: Optional[str] = None) -> Optional[datetime]:
    """
    把原始時間戳正規化為 tz-aware 的 UTC datetime。

    ts: ISO 8601 字串（可帶或不帶 offset，接受 'Z' 結尾，也接受用空白分隔日期與時間），
        或已經是 datetime/pandas Timestamp 物件。
    offset: 當 ts 本身是 naive（不帶 offset）字串時，用這個補上原始時區 offset
            （例如某些歷史資料集把 offset 存在獨立欄位，如 apache log 的 "+0700"）。
            ts 已帶 offset，或已是 tz-aware datetime 時，這個參數會被忽略。

    解析失敗（None / 空字串 / 無法解析的格式）回傳 None，呼叫端應 fallback 成預設值，
    不要讓整筆事件因為一個壞掉的時間戳而中斷。
    """
    if _is_missing(ts):
        return None

    if isinstance(ts, datetime):
        dt = ts
    else:
        text = str(ts).strip()
        if not text or text.lower() in ("nan", "nat", "none"):
            return None
        text = text.replace("Z", "+00:00").replace("z", "+00:00")
        if " " in text and "T" not in text:
            text = text.replace(" ", "T", 1)
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None

    if dt.tzinfo is None:
        if offset:
            off_text = str(offset).strip()
            # 容錯：部分歷史資料集的 offset 欄位混有殘留字元（例如 "+0700]"）
            off_text = "".join(ch for ch in off_text if ch.isdigit() or ch in "+-:")
            off_text = off_text.replace("Z", "+00:00")
            try:
                probe = datetime.fromisoformat("2000-01-01T00:00:00" + off_text)
                dt = dt.replace(tzinfo=probe.tzinfo)
            except ValueError:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def compute_time_features(
    ts: Any,
    tz_name: Optional[str] = None,
    offset: Optional[str] = None,
) -> Dict[str, Any]:
    """
    計算一筆事件完整的時間特徵（UTC 版 + 當地時間版），訓練與線上推論共用同一份邏輯。

    ts: 原始時間戳（見 parse_to_utc）
    tz_name: agent 登記的 IANA 時區名稱（例如 'Asia/Taipei'）。None / 'UTC' / 未知或無效
             的時區名稱一律 fallback 成 UTC，此時 local_* 會等於 UTC 版特徵，不中斷流程。
    offset: 見 parse_to_utc，用於 ts 本身是 naive 但另有獨立 offset 欄位的情境。

    hour/day_of_week/is_odd_hour/time_period 一律以 UTC 為基準，跨 tenant/agent 可直接比較。
    local_hour/local_day_of_week/local_is_odd_hour/local_time_period 用 zoneinfo 依事件實際
    發生的日期換算，會自動套用當地當下是否為日光節約時間（DST），不是固定 offset 加減。
    """
    dt_utc = parse_to_utc(ts, offset=offset)

    if dt_utc is None:
        hour = dow = local_hour = local_dow = 0
    else:
        hour, dow = dt_utc.hour, dt_utc.weekday()
        local_hour, local_dow = hour, dow
        if tz_name and str(tz_name).upper() != "UTC":
            zone = _resolve_zoneinfo(str(tz_name))
            if zone is not None:
                dt_local = dt_utc.astimezone(zone)
                local_hour, local_dow = dt_local.hour, dt_local.weekday()
            # zone is None：未知/無效時區名稱，或系統缺少 tzdata（見 _resolve_zoneinfo
            # 的 log/計數器）——兩種情況都 fallback 成 UTC 版本，不中斷流程。

    return {
        "hour": hour,
        "day_of_week": dow,
        "is_odd_hour": int(1 <= hour <= 6),
        "time_period": _time_period(hour),
        "local_hour": local_hour,
        "local_day_of_week": local_dow,
        "local_is_odd_hour": int(1 <= local_hour <= 6),
        "local_time_period": _time_period(local_hour),
    }
