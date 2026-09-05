#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonymize_log.py
-----------------
把 Apache/Nginx combined log 依「秒數間隔」切成多個 session，
對每個 session 重新指派一個像正常外網使用者的公開 IP，並把整個
session 的時間平移到過去 N 天內隨機分散的時間點 (session 內部各
請求的相對間隔保持不變，只整體平移)。

同時支援關鍵字黑名單：任何一行只要命中黑名單子字串 (不分大小寫)，
整行直接捨棄，不會出現在輸出檔中 (例如歧視字樣、明顯的路徑掃描字串)。

用法:
    python3 anonymize_log.py <輸入log路徑> <輸出log路徑>

只依賴 Python 標準函式庫，不需要額外安裝套件。
"""

import re
import sys
import random
from datetime import datetime, timedelta, timezone

# ============ 可調整設定 ============

# 是否自動根據資料本身的間隔分佈判斷「一般動作間隔」與「換 session」的分界，
# 而不是用單一固定秒數。像 Playwright 這種自動化測試常常每個動作只間隔 1~2 秒，
# 但緊接著換了另一個模擬使用者 (不同 UA / referer 從頭開始)，固定門檻會誤判成同一個 session。
AUTO_SESSION_GAP = True

# AUTO_SESSION_GAP=False 時，退回用這個固定秒數判斷 session 邊界
SESSION_GAP_SECONDS = 20 * 60  # 20 分鐘

# 自動門檻的安全範圍 (秒)：不管統計結果算出什麼，都夾在這個區間內，
# 避免資料太規律 (全部等間隔) 或太雜訊時算出離譜的門檻。
AUTO_GAP_MIN_SECONDS = 60          # 最少 1 分鐘才會被視為「換 session」
AUTO_GAP_MAX_SECONDS = 4 * 60 * 60  # 最多 4 小時

# 除了時間間隔，另外兩個「一定切 session」的訊號：
# 1) 連續兩筆請求的 User-Agent 不同 -> 換了不同使用者/裝置，不管間隔多短都切開
BREAK_ON_UA_CHANGE = True
# 2) 請求的 Referer 是 "-" (代表使用者直接輸入網址/開新分頁，不是從站內某頁點過來的)
#    -> 視為一次新的造訪起點，不管間隔多短都切開 (但同一筆本身不算，只看非第一筆的情況)
BREAK_ON_FRESH_REFERER = True

# 把 session 的起始時間重新分散到「現在」往前推這麼多天的範圍內
TIME_SPREAD_DAYS = 7

# 黑名單子字串 (不分大小寫)：整行只要包含其中任何一個，就整行移除
BLOCKLIST_SUBSTRINGS = [
    "nig",
    # 可依需求繼續加，例如常見探測/攻擊字串：
    # "/etc/passwd", "<script>", "../../",
]

# 偽裝成正常外網使用者的公開 IP 池 (示意用途，涵蓋北美/歐洲/亞太多個網段)
EXTERNAL_IP_POOL = [
    "73.162.44.201", "24.5.130.87",
    "86.145.22.9", "82.34.191.63",
    "203.0.113.45", "121.54.33.201",
    "1.34.201.55", "36.239.10.174",
    "112.104.55.201", "175.98.23.11",
    "185.199.108.153", "104.28.31.5",
    "58.115.6.201", "220.135.44.9",
    "142.250.72.14", "20.205.243.166",
]

# 若原本 referer / log 內容含有內部測試網域，可選擇替換成外部網域，讓資料更像正式環境流量。
# 設成 None 代表不做替換，原樣保留。
REWRITE_HOST = "https://example-ticketing.app"
ORIGINAL_HOST_PATTERN = re.compile(r"https?://localhost(:\d+)?", re.IGNORECASE)

RANDOM_SEED = 42  # 固定 seed 方便重現；要每次都不同就刪掉這行相關程式碼

# ============ 解析用的正則 ============

LOG_LINE_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) (?P<proto>[^"]+)" '
    r'(?P<status>\d+) (?P<size>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)
TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_line(raw_line):
    """把一行 log 解析成 dict；解析不出來就回傳 None。"""
    m = LOG_LINE_RE.match(raw_line.strip())
    if not m:
        return None
    d = m.groupdict()
    try:
        d["dt"] = datetime.strptime(d["time"], TIME_FORMAT)
    except ValueError:
        return None
    d["raw"] = raw_line.rstrip("\n")
    return d


def is_blocked(raw_line):
    """整行只要命中黑名單子字串就回傳 True。

    純英文字母的詞用 word-boundary 比對，避免像 "nig" 這種詞誤中
    "night"/"sign"/"design" 等剛好包含該子字串的正常英文單字（純子字串比對
    曾經把含 "night" 的合法 log 行整行刪掉）。含特殊符號的黑名單項目
    （例如 "/etc/passwd"、"<script>"）維持子字串比對——這類 pattern 本來就
    不會出現在一般英文單字中間，不需要邊界保護，而且 `\\b` 前後接的是
    `/`、`<` 這類標點符號時邊界判定不穩定，反而可能比對不到。
    """
    lower = raw_line.lower()
    for bad in BLOCKLIST_SUBSTRINGS:
        bad_lower = bad.lower()
        if bad_lower.isalpha():
            if re.search(rf"\b{re.escape(bad_lower)}\b", lower):
                return True
        elif bad_lower in lower:
            return True
    return False


def load_entries(path):
    """讀檔、逐行解析，套用黑名單過濾，回傳依時間排序的 entry list。"""
    entries = []
    skipped_blocked = 0
    skipped_unparsed = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            if is_blocked(raw_line):
                skipped_blocked += 1
                continue
            entry = parse_line(raw_line)
            if entry is None:
                skipped_unparsed += 1
                continue
            entries.append(entry)
    entries.sort(key=lambda e: e["dt"])
    print(f"讀取完成: 保留 {len(entries)} 行；因黑名單移除 {skipped_blocked} 行；"
          f"格式無法解析而略過 {skipped_unparsed} 行。")
    return entries


def otsu_threshold_seconds(gaps):
    """
    對一串秒數間隔做 Otsu 二分法 (取自影像處理找前景/背景分界的經典演算法，
    這裡拿來找「同一 session 內的正常間隔」跟「換 session 的大間隔」之間的
    自然分界)。在 log(秒數+1) 空間上做，這樣不管間隔是秒級還是小時級都適用。

    回傳分界值 (秒)。資料點太少時回傳 None，交由呼叫端 fallback 成固定門檻。
    """
    if len(gaps) < 8:
        return None

    import math
    logs = [math.log(g + 1.0) for g in gaps]
    lo, hi = min(logs), max(logs)
    if hi - lo < 1e-9:
        return None  # 所有間隔幾乎一樣，沒有「自然分界」可言

    bins = 128
    width = (hi - lo) / bins
    hist = [0] * bins
    for v in logs:
        idx = min(bins - 1, int((v - lo) / width))
        hist[idx] += 1

    total = len(logs)
    sum_all = sum(i * hist[i] for i in range(bins))

    best_score = -1.0
    best_idx = 0
    w_bg = 0
    sum_bg = 0
    for i in range(bins):
        w_bg += hist[i]
        if w_bg == 0:
            continue
        w_fg = total - w_bg
        if w_fg == 0:
            break
        sum_bg += i * hist[i]
        mean_bg = sum_bg / w_bg
        mean_fg = (sum_all - sum_bg) / w_fg
        # between-class variance；越大代表這個切點把資料分成兩群的效果越好
        score = w_bg * w_fg * (mean_bg - mean_fg) ** 2
        if score > best_score:
            best_score = score
            best_idx = i

    threshold_log = lo + (best_idx + 1) * width
    threshold_seconds = math.exp(threshold_log) - 1.0
    return threshold_seconds


def compute_auto_threshold(entries):
    gaps = [
        (entries[i]["dt"] - entries[i - 1]["dt"]).total_seconds()
        for i in range(1, len(entries))
    ]
    gaps = [g for g in gaps if g > 0]
    threshold = otsu_threshold_seconds(gaps)
    if threshold is None:
        print("資料量太少或間隔太一致，無法自動判斷，改用固定門檻。")
        return SESSION_GAP_SECONDS
    threshold = max(AUTO_GAP_MIN_SECONDS, min(AUTO_GAP_MAX_SECONDS, threshold))
    print(f"自動判斷出的 session 間隔門檻：約 {threshold:.0f} 秒 "
          f"({threshold / 60:.1f} 分鐘)。")
    return threshold


def split_into_sessions(entries):
    """
    切分 session 的規則 (符合任一即視為新 session 起點):
      1. 與上一筆的秒數間隔超過門檻 (AUTO_SESSION_GAP 時用自動算出的值，否則用固定值)
      2. User-Agent 跟上一筆不同 (BREAK_ON_UA_CHANGE)
      3. Referer 是 "-"，代表這是一次新的直接造訪 (BREAK_ON_FRESH_REFERER)
    這樣即使像 Playwright 產生的流量前後間隔只有 1~2 秒，只要是不同模擬使用者
    (UA 換了、或 referer 從頭開始)，還是會被正確切成不同 session，不會被
    小間隔誤判成同一個人連續瀏覽。
    """
    if not entries:
        return []

    gap_threshold = (
        compute_auto_threshold(entries) if AUTO_SESSION_GAP else SESSION_GAP_SECONDS
    )

    sessions = []
    current = [entries[0]]
    for prev, e in zip(entries, entries[1:]):
        gap = (e["dt"] - prev["dt"]).total_seconds()
        new_session = False
        reason = None

        if gap > gap_threshold:
            new_session, reason = True, f"間隔 {gap:.0f}s > 門檻"
        elif BREAK_ON_UA_CHANGE and e["ua"] != prev["ua"]:
            new_session, reason = True, "User-Agent 改變"
        elif BREAK_ON_FRESH_REFERER and e["referer"] == "-":
            new_session, reason = True, "Referer 重新開始 (直接造訪)"

        if new_session:
            sessions.append(current)
            current = []
        current.append(e)
    if current:
        sessions.append(current)

    return sessions


def reassign_sessions(sessions, rng):
    """
    對每個 session:
      - 指派一個隨機外網 IP (整個 session 內共用同一個 IP，符合單一使用者的行為)
      - 計算一個隨機時間位移量，套用到該 session 所有請求上 (相對秒數間隔不變)
    回傳攤平後、依新時間排序好的 entry list。
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=TIME_SPREAD_DAYS)
    window_seconds = TIME_SPREAD_DAYS * 24 * 3600

    out = []
    for session in sessions:
        ip = rng.choice(EXTERNAL_IP_POOL)
        new_start = window_start + timedelta(seconds=rng.randint(0, window_seconds))
        offset = new_start - session[0]["dt"]

        for e in session:
            new_dt = e["dt"] + offset
            new_referer = e["referer"]
            if REWRITE_HOST and new_referer not in ("-", ""):
                new_referer = ORIGINAL_HOST_PATTERN.sub(REWRITE_HOST, new_referer)

            size_field = e["size"]  # 保持原樣 (可能是 "0" 或實際 byte 數)
            new_line = (
                f'{ip} - - [{new_dt.strftime(TIME_FORMAT)}] '
                f'"{e["method"]} {e["path"]} {e["proto"]}" '
                f'{e["status"]} {size_field} '
                f'"{new_referer}" "{e["ua"]}"'
            )
            out.append((new_dt, new_line))
    out.sort(key=lambda t: t[0])
    return [line for _, line in out]


def main():
    if len(sys.argv) != 3:
        print("用法: python3 anonymize_log.py <輸入log路徑> <輸出log路徑>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    rng = random.Random(RANDOM_SEED)

    entries = load_entries(input_path)
    sessions = split_into_sessions(entries)
    print(f"共切出 {len(sessions)} 個 session。")

    output_lines = reassign_sessions(sessions, rng)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"完成，寫入 {len(output_lines)} 行 -> {output_path}")


if __name__ == "__main__":
    main()