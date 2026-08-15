"""
特徵工程模組
============
從原始 Apache Log 資料提取可泛化的機器學習特徵

特徵類別：
- IP 特徵：IP 類型、網段分類
- 時間特徵：小時、星期、時段（週期性特徵）
- URL 特徵：長度、深度、攻擊模式檢測
- Referrer 特徵：來源類型、長度
- Status 特徵：狀態碼分類
- Size 特徵：回應大小分類
- Browser 特徵：作業系統、Bot 檢測
"""

import pandas as pd
import numpy as np
import re

try:
    from .time_features import compute_time_features
    from .attack_patterns import (
        SQL_PATTERNS, XSS_PATTERNS, PATH_TRAVERSAL_PAT, CMD_PATTERNS, FILE_INCLUSION_PAT,
    )
except ImportError:  # 以獨立 script 執行，或非套件 context 匯入時（例如 api.py）
    from time_features import compute_time_features
    from attack_patterns import (
        SQL_PATTERNS, XSS_PATTERNS, PATH_TRAVERSAL_PAT, CMD_PATTERNS, FILE_INCLUSION_PAT,
    )


# ============================================================
# IP 特徵
# ============================================================

def extract_ip_features(df):
    """
    從 IP 提取抽象特徵

    產生欄位：
    - ip_type: IP 類型（public, private_class_a/b/c, loopback, invalid, unknown）
    - ip_first_octet: IP 第一個 octet（網段分類，0-255）
    """

    def classify_ip_type(ip):
        if pd.isna(ip):  # is NA => true
            return 'unknown'

        ip_str = str(ip)
        parts = ip_str.split('.')

        if len(parts) != 4:
            return 'invalid'

        try:
            first = int(parts[0])
            second = int(parts[1])

            # 私有 IP 範圍
            if first == 10:
                return 'private_class_a'  # 10.0.0.0 - 10.255.255.255
            elif first == 172 and 16 <= second <= 31:
                return 'private_class_b'  # 172.16.0.0 - 172.31.255.255
            elif first == 192 and second == 168:
                return 'private_class_c'  # 192.168.0.0 - 192.168.255.255
            elif first == 127:
                return 'loopback'  # 127.0.0.0 - 127.255.255.255
            else:
                return 'public'
        except:
            return 'invalid'

    df['ip_type'] = df['ip'].apply(classify_ip_type)

    # IP 第一個 octet（網段分類）
    df['ip_first_octet'] = df['ip'].apply(
        lambda x: int(str(x).split('.')[0]) if pd.notna(x) and '.' in str(x) else 0
    )

    return df


# ============================================================
# 時間特徵
# ============================================================
#
# hour/day_of_week/is_odd_hour/time_period（以及 local_* 版本）一律透過
# time_features.compute_time_features() 計算 —— 跟 processing/pipeline_utils.py
# 線上推論用的是同一份函式，避免離線訓練與線上推論各自實作導致 training-serving skew。

def _row_time_features(ts, tz_name=None, offset=None):
    return compute_time_features(ts, tz_name=tz_name, offset=offset)


def extract_datetime_features(df):  # df=dataframe
    """
    提取時間的週期性特徵（不依賴具體日期，可泛化）。實際計算委派給
    time_features.compute_time_features()，逐列 apply，確保跟線上推論
    （processing/pipeline_utils.py）算出來的結果一致。

    產生欄位：
    - hour: 小時 (0-23)，以 UTC 為基準，跨 tenant/agent 可直接比較
    - day_of_week: 星期幾 (0=週一, 6=週日)，以 UTC 為基準
    - is_weekend: 是否為週末 (0/1)
    - is_odd_hour: 是否為異常時段，UTC 凌晨 1-6 點 (0/1)
    - time_period: 時段分類 (0=night, 1=morning, 2=afternoon, 3=evening)，以 UTC 為基準

    `df['datetime']` 可以是 naive 字串、帶 offset 的字串，或混合兩者——每一列各自
    獨立解析（不像 pandas 向量化 to_datetime 那樣，naive 列會被整批以 UTC 假設處理，
    也不會因為同一批混有不同格式而整批出錯）。無法解析的值 fallback 為 hour=0。
    """

    if 'datetime' in df.columns:
        computed = pd.DataFrame(
            list(df['datetime'].apply(_row_time_features)), index=df.index
        )
        df['hour'] = computed['hour']
        df['day_of_week'] = computed['day_of_week']
        df['is_odd_hour'] = computed['is_odd_hour']
        df['time_period'] = computed['time_period']
    else:
        if 'hour' not in df.columns: df['hour'] = 0
        if 'day_of_week' not in df.columns: df['day_of_week'] = 0
        df['is_odd_hour'] = ((df['hour'] >= 1) & (df['hour'] <= 6)).astype(int)
        # 區間剛好是每 6 小時一段（0-5/6-11/12-17/18-23），整數除法取代 .apply()，
        # 向量化操作在大型 DataFrame 上比逐列呼叫 Python 函式快很多。
        df['time_period'] = (df['hour'] // 6).astype(int)

    # 是否為週末
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

    # 週期性 sin/cos 編碼（供 SVM 使用，消除線性距離問題）
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['dow_sin']  = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos']  = np.cos(2 * np.pi * df['day_of_week'] / 7)

    return df


def extract_local_datetime_features(df, tz_column: str = 'timezone'):
    """
    衍生「當地時間」版本的時間特徵，跟 extract_datetime_features() 算出的 UTC 版
    分開存放，不共用欄位名稱。同樣委派給 time_features.compute_time_features()。

    需求：
    - df 必須有 'datetime' 欄位（原始時間戳字串）。
    - df[tz_column] 是每一列對應的 IANA 時區名稱（例如 'Asia/Taipei'），通常由呼叫端
      用 agent_id/tenant_id join agents.timezone 取得；缺少該欄位時全部視為 'UTC'。

    用 zoneinfo 依「該筆事件實際發生的日期」換算時區，會自動套用該地區當下是否處於
    日光節約時間（DST）的規則，不是用固定 offset 加減——同一個時區在夏令、冬令時間
    換算出來的 local_hour 才會正確。未知/無效的時區名稱會 fallback 成 UTC 版本。

    產生欄位：
    - local_hour, local_day_of_week: 當地時間版的 hour / day_of_week
    - local_is_odd_hour: 當地時間是否為凌晨 1-6 點 (0/1)
    - local_time_period: 當地時間的時段分類
    """
    if 'datetime' not in df.columns:
        raise ValueError("df 必須有 'datetime' 欄位才能計算 local_* 特徵")

    if tz_column not in df.columns:
        df[tz_column] = 'UTC'
    tz_series = df[tz_column].fillna('UTC')

    computed = pd.DataFrame(
        list(df['datetime'].combine(tz_series, _row_time_features)), index=df.index
    )

    df['local_hour'] = computed['local_hour']
    df['local_day_of_week'] = computed['local_day_of_week']
    df['local_is_odd_hour'] = computed['local_is_odd_hour']
    df['local_time_period'] = computed['local_time_period']

    return df


# ============================================================
# Request 特徵
# ============================================================

def extract_request_features(df):
    """
    從 Request 提取方法和版本特徵

    產生欄位：
    - request_method: HTTP 方法 (GET, POST, PUT, DELETE, etc.)
    - request_version: HTTP 版本 (HTTP/1.0, HTTP/1.1, HTTP/2.0)
    - url: 從 request 中提取的 URL 路徑
    """

    # Request Method（使用正則表達式提取第一個單字）
    df['request_method'] = df['request'].str.extract(r'^(\w+)', expand=False)

    # Request Version（提取 HTTP/x.x 格式）
    df['request_version'] = df['request'].str.extract(r'(HTTP/\d\.\d)$', expand=False)

    # 提取 URL（方法和版本之間的部分）
    df['url'] = df['request'].str.extract(r'^\w+\s+(.+?)\s+HTTP', expand=False)

    return df


# ============================================================
# URL 特徵（攻擊模式檢測）
# ============================================================

def extract_url_features(df):
    """
    從 URL 提取攻擊模式特徵（核心特徵，可泛化到不同網站）

    產生欄位：
    - url_length: URL 長度
    - url_depth: 路徑深度（/ 的數量）
    - url_param_count: 參數數量（? 和 & 的數量）
    - url_special_chars: 特殊字元數量
    - has_sql_injection: 是否包含 SQL Injection 模式 (0/1)
    - has_xss: 是否包含 XSS 模式 (0/1)
    - has_path_traversal: 是否包含路徑遍歷攻擊 (0/1)
    - has_command_injection: 是否包含命令注入 (0/1)
    - has_file_inclusion: 是否包含檔案包含攻擊 (0/1)
    - url_encoding_count: URL 編碼數量
    - has_double_encoding: 是否有雙重編碼（繞過過濾）(0/1)
    - accesses_sensitive_path: 是否訪問敏感路徑 (0/1)
    - url_file_type: 請求的檔案類型分類
    """

    # URL 長度（異常長的 URL 可能是攻擊）
    df['url_length'] = df['url'].str.len().fillna(0).astype(int)

    # 路徑深度（/ 的數量）
    df['url_depth'] = df['url'].str.count('/').fillna(0).astype(int)

    # 參數數量
    df['url_param_count'] = df['url'].str.count(r'[?&]').fillna(0).astype(int)
    # url_param_count = url 中 '?' 和 '&' 的數量，這些符號通常用於分隔 URL 中的參數。例如：
    # https://example.com/search?q=keyword&page=2
    # 在這個 URL 中，'?' 後面是第一個參數 'q=keyword'，'&' 後面是第二個參數 'page=2'。
    # 因此，url_param_count 可以幫助我們了解 URL 中包含多少參數。
    # 若 url 為 nan 則填充為 0
    # 最後轉換為整數類型。

    # 特殊字元數量
    df['url_special_chars'] = df['url'].str.count(r'[<>\'";%\(\)\[\]{}]').fillna(0).astype(int)
    # <> ' ";%( ) [ ]{}

    # ===== SQL Injection 特徵 =====
    df['has_sql_injection'] = df['url'].str.contains(
        '|'.join(SQL_PATTERNS), case=False, na=False, regex=True
    ).astype(int)

    # ===== XSS (Cross-Site Scripting) 特徵 =====
    df['has_xss'] = df['url'].str.contains(
        '|'.join(XSS_PATTERNS), case=False, na=False, regex=True
    ).astype(int)

    # ===== Path Traversal 特徵 =====
    df['has_path_traversal'] = df['url'].str.contains(
        PATH_TRAVERSAL_PAT, na=False, case=False, regex=True
    ).astype(int)

    # ===== 命令注入特徵 =====
    df['has_command_injection'] = df['url'].str.contains(
        '|'.join(CMD_PATTERNS), case=False, na=False, regex=True
    ).astype(int)

    # ===== File Inclusion 特徵 =====
    df['has_file_inclusion'] = df['url'].str.contains(
        FILE_INCLUSION_PAT, case=False, na=False, regex=True
    ).astype(int)

    # URL 編碼數量（%XX 格式）
    df['url_encoding_count'] = df['url'].str.count(r'%[0-9A-Fa-f]{2}').fillna(0).astype(int)

    # 雙重編碼（嘗試繞過 WAF 過濾）
    df['has_double_encoding'] = df['url'].str.contains(
        r'%25[0-9A-Fa-f]{2}',  # %25 = 編碼的 %
        na=False, regex=True
    ).astype(int)

    # ===== 敏感路徑檢測 =====
    sensitive_paths = [
        'admin', 'backup', 'config', 'database', 'db',
        'test', 'temp', 'tmp', 'log', 'old', 'bak',
        'phpmyadmin', 'wp-admin', 'wp-login', '.git', '.env', '.env.example'
    ]
    df['accesses_sensitive_path'] = df['url'].apply(
        lambda x: int(any(path in str(x).lower() for path in sensitive_paths)) if pd.notna(x) else 0
    )

    # ===== 副檔名類型分類 =====
    def extract_file_type(url):
        """
        分類請求的檔案類型
        0: none (無副檔名)
        1: script (php, asp, aspx, jsp, cgi)
        2: image (jpg, png, gif, svg, webp, ico)
        3: asset (css, js)
        4: document (pdf, doc, docx, xls, xlsx)
        5: other
        """
        if pd.isna(url):
            return 0
        url_path = str(url).split('?')[0]  # 移除查詢參數
        if '.' in url_path:
            ext = url_path.split('.')[-1].lower()  # 選最後一段: .後面
            if ext in ['php', 'asp', 'aspx', 'jsp', 'cgi']:
                return 1  # script
            elif ext in ['jpg', 'png', 'gif', 'svg', 'webp', 'ico']:
                return 2  # image
            elif ext in ['css', 'js']:
                return 3  # asset
            elif ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx']:
                return 4  # document
            else:
                return 5  # other
        return 0  # none

    df['url_file_type'] = df['url'].apply(extract_file_type)

    return df


# ============================================================
# Referrer 特徵
# ============================================================

def extract_referrer_features(df):
    """
    從 Referrer 提取特徵

    產生欄位：
    - has_referrer: 是否有 Referrer (0/1)
    - referrer_type: Referrer 類型 (0=none, 1=local, 2=ip_address, 3=search_engine, 4=social, 5=external)
    - referrer_length: Referrer 長度
    """

    # 是否有 Referrer
    df['has_referrer'] = (df['referer'].notna() & (df['referer'] != '-')).astype(int)

    # Referrer 類型分類
    def classify_referrer(ref):
        """
        分類 Referrer 來源
        0: none (無 referrer)
        1: local (本地/內網)
        2: ip_address (IP 位址，可疑)
        3: search_engine (搜尋引擎)
        4: social (社交媒體)
        5: external (外部網站)
        """
        if pd.isna(ref) or ref == '-':
            return 0  # none

        ref = str(ref).lower()

        # 本地/內網
        if any(local in ref for local in ['localhost', '127.0.0.1', '192.168.', '10.0.']):
            return 1  # local

        # IP 位址（通常是掃描器，可疑）
        if re.match(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ref):  # d{1,3} => 1-3位數字
            return 2  # ip_address (可疑)

        # 搜尋引擎（可以擴充更多）
        if any(engine in ref for engine in ['google', 'bing', 'yahoo', 'baidu','duckduckgo','yandex','naver','sogou']):  # 搜尋引擎會不會太少
            return 3  # search_engine

        # 社交媒體
        if any(social in ref for social in ['facebook', 'twitter', 'linkedin','instagram', 'tiktok', 'youtube', 'line','telegram']):
            return 4  # social

        return 5  # external

    df['referrer_type'] = df['referer'].apply(classify_referrer)

    # Referrer 長度
    df['referrer_length'] = df['referer'].apply(
        lambda x: len(str(x)) if pd.notna(x) and x != '-' else 0
    )

    return df


# ============================================================
# Status 特徵
# ============================================================

def extract_status_features(df):
    """
    從 Status 提取特徵

    產生欄位：
    - status: HTTP 狀態碼（數值）
    - status_category: 狀態碼分類 (1xx, 2xx, 3xx, 4xx, 5xx)
    - is_error_status: 是否為錯誤狀態 4xx/5xx (0/1)
    - is_success_status: 是否為成功狀態 2xx (0/1)
    """

    df['status'] = pd.to_numeric(df['status'], errors='coerce').fillna(0).astype(int)

    # 狀態碼分類（取百位數）
    df['status_category'] = df['status'].apply(
        lambda x: x // 100 if x > 0 else 0
    )

    # 是否為錯誤狀態（4xx 客戶端錯誤，5xx 伺服器錯誤）
    df['is_error_status'] = ((df['status'] >= 400) & (df['status'] < 600)).astype(int)

    # 是否為成功狀態（2xx）
    df['is_success_status'] = ((df['status'] >= 200) & (df['status'] < 300)).astype(int)

    return df


# ============================================================
# Size 特徵
# ============================================================

def extract_size_features(df):
    """
    從 Size 提取特徵

    產生欄位：
    - size: 回應大小（bytes）
    - size_category: 大小分類 (0=zero, 1=<1KB, 2=1-10KB, 3=10-100KB, 4=100KB-1MB, 5=>1MB)
    - log_size: 對數大小（處理長尾分布）
    """

    df['size'] = pd.to_numeric(df['size'], errors='coerce').fillna(0).astype(int)

    # 大小分類
    def size_category(size):
        if size == 0:
            return 0  # zero
        elif size < 1024:
            return 1  # < 1KB
        elif size < 10240:
            return 2  # 1-10KB
        elif size < 102400:
            return 3  # 10-100KB
        elif size < 1024000:
            return 4  # 100KB-1MB
        else:
            return 5  # > 1MB

    df['size_category'] = df['size'].apply(size_category)

    # Log size
    df['log_size'] = np.log1p(df['size'])  # log(1 + x) 的自然對數，用於處理 size 的長尾分布，減少極端值的影響。
    # 不用 log(x) 是因為當 size 為 0 時會出現 log(0) 無限大的問題，而 log1p(x) 則能正確處理 size 為 0 的情況，返回 0。

    return df


# ============================================================
# Browser 特徵
# ============================================================

def extract_browser_features(df):
    """
    從 Browser/User Agent 提取 OS 特徵

    產生欄位：
    - os_type: 作業系統類型 (0=unknown, 1=windows, 2=android, 3=ios, 4=linux, 5=mac, 6=bot, 7=other)
    - is_bot: 是否為爬蟲/Bot (0/1)
    - ua_length: User Agent 長度
    """

    def parse_os(ua):
        """
        從 User Agent 解析作業系統
        0: unknown
        1: Windows
        2: Android
        3: iOS (iPhone/iPad)
        4: Linux
        5: macOS
        6: Bot/Crawler
        7: Other
        """
        if pd.isna(ua):
            return 0  # unknown
        ua = str(ua).lower()

        if 'windows' in ua:
            return 1
        elif 'android' in ua:
            return 2
        elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
            return 3
        elif 'linux' in ua and 'android' not in ua:
            return 4
        elif 'mac' in ua:
            return 5
        elif 'bot' in ua or 'crawler' in ua or 'spider' in ua:
            return 6  # bot
        else:
            return 7  # other

    df['os_type'] = df['browser'].apply(parse_os)

    # 是否為 Bot
    df['is_bot'] = (df['os_type'] == 6).astype(int)

    # User Agent 長度
    df['ua_length'] = df['browser'].apply(
        lambda x: len(str(x)) if pd.notna(x) else 0
    )

    return df


# ============================================================
# 主函數：執行完整特徵工程
# ============================================================

def create_all_features(df, verbose=True):
    """
    執行完整特徵工程

    Parameters:
    -----------
    df : pandas.DataFrame
        原始資料集
    verbose : bool
        是否印出進度訊息

    Returns:
    --------
    df : pandas.DataFrame
        包含所有特徵的資料集
    """

    if verbose:
        print("開始特徵工程...")

    if verbose:
        print("  [1/8] 提取 IP 特徵...")
    df = extract_ip_features(df)

    if verbose:
        print("  [2/8] 提取時間特徵...")
    df = extract_datetime_features(df)

    if verbose:
        print("  [3/8] 提取 Request 特徵...")
    df = extract_request_features(df)

    if verbose:
        print("  [4/8] 提取 URL 特徵...")
    df = extract_url_features(df)

    if verbose:
        print("  [5/8] 提取 Referrer 特徵...")
    df = extract_referrer_features(df)

    if verbose:
        print("  [6/8] 提取 Status 特徵...")
    df = extract_status_features(df)

    if verbose:
        print("  [7/8] 提取 Size 特徵...")
    df = extract_size_features(df)

    if verbose:
        print("  [8/8] 提取 Browser 特徵...")
    df = extract_browser_features(df)

    if verbose:
        print("特徵工程完成！")

    return df


# ============================================================
# 特徵欄位定義
# ============================================================

# 可泛化特徵列表（不包含具體 IP、URL 等，可用於不同環境）
# [P2 改善] 移除高度共線性特徵，避免特徵重要性被稀釋：
# - 移除 'is_weekend'（完全由 'day_of_week' 衍生，Pearson r ≈ 1.0）
# - 移除 'status'（與 'status_category' 高度共線，r > 0.95）
# - 移除 'is_success_status'（與 'is_error_status' 互補冗餘）
# - 移除 'size_category'（與 'log_size' 高度共線，r > 0.80）
FEATURE_COLUMNS = [
    # IP 特徵
    'ip_first_octet',

    # 時間特徵（移除 is_weekend，保留 day_of_week 作為源特徵）
    'hour', 'day_of_week', 'is_odd_hour', 'time_period',

    # URL 特徵
    'url_length', 'url_depth', 'url_param_count', 'url_special_chars',
    'has_sql_injection', 'has_xss', 'has_path_traversal',
    'has_command_injection', 'has_file_inclusion',
    'url_encoding_count', 'has_double_encoding',
    'accesses_sensitive_path', 'url_file_type',

    # Referrer 特徵
    'has_referrer', 'referrer_type', 'referrer_length',

    # Status 特徵（移除 is_success_status，因其與 is_error_status 完全互補冗餘；
    # 保留 status 原始值——它比 status_category 含有更細粒度資訊，如 401 vs 403 vs 404）
    'status', 'status_category', 'is_error_status',

    # Size 特徵（移除 size_category，保留資訊量更大的連續型 log_size）
    'log_size',

    # Browser 特徵
    'os_type', 'is_bot', 'ua_length',
]

# 需要 Label Encoding 的類別型特徵
CATEGORICAL_FEATURES = ['ip_type', 'request_method', 'request_version']

# SVM 專用特徵欄位（以 sin/cos 取代原始 hour/day_of_week，避免 SVM 距離計算錯誤）
SVM_FEATURE_COLUMNS = [
    # IP 特徵
    'ip_first_octet',

    # 時間特徵（週期性編碼取代線性整數）
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
    'is_weekend', 'is_odd_hour', 'time_period',

    # URL 特徵
    'url_length', 'url_depth', 'url_param_count', 'url_special_chars',
    'has_sql_injection', 'has_xss', 'has_path_traversal',
    'has_command_injection', 'has_file_inclusion',
    'url_encoding_count', 'has_double_encoding',
    'accesses_sensitive_path', 'url_file_type',

    # Referrer 特徵
    'has_referrer', 'referrer_type', 'referrer_length',

    # Status 特徵
    'status', 'status_category', 'is_error_status', 'is_success_status',

    # Size 特徵
    'size_category', 'log_size',

    # Browser 特徵
    'os_type', 'is_bot', 'ua_length',
]


# ============================================================
# 測試用
# ============================================================

if __name__ == "__main__":
    # 測試特徵工程
    print("測試特徵工程模組...")

    # 載入測試資料
    df = pd.read_csv('dataset/develop_set.csv')
    print(f"原始資料: {len(df)} 筆, {len(df.columns)} 欄位")

    # 執行特徵工程
    df = create_all_features(df)
    print(f"特徵工程後: {len(df)} 筆, {len(df.columns)} 欄位")

    # 顯示新增的特徵
    print(f"\n特徵欄位數量: {len(FEATURE_COLUMNS)}")
    print(f"類別型特徵: {CATEGORICAL_FEATURES}")
