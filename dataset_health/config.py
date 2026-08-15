"""dataset_health.config — per-stage 多元度驗收的唯一事實來源。

對照 Verify_doc/log_per_stage_verify_diversity_module_design_instruments.md §3。
`diversity.py` 不得硬編任何 stage 專屬常數，一律從這裡讀。
"""

# ============================================================
# §3.7 — 基本門檻
# ============================================================

MIN_SAMPLES = 200  # 低於此，熵/QCD 標 provisional=true，CI 不得當硬門檻


# ============================================================
# §3.1 — 每個 stage 的定義 flag 與支撐特徵集
# ============================================================

STAGE_NAMES = {
    1: "敏感路徑",
    2: "SQLi",
    3: "XSS",
    4: "路徑遍歷",
    5: "命令注入",
    6: "檔案包含",
    7: "雙重編碼",
    8: "URL 編碼變形",
    9: "特殊字元密集",
    10: "UA 多樣性",
    11: "異常 HTTP 方法",
    12: "異常 URL 結構",
}

# stage_id -> 定義 flag 欄位名（0/1 欄，flag==1 即屬於該 stage）
# None 代表這個 stage 不是靠單一 0/1 flag 定義（改用 DEFINING_PREDICATE，
# 或像 stage 10/12 是「目標即多樣性」型，完全沒有定義判準，見 §3.1 表格附註）。
DEFINING_FLAG = {
    1: "accesses_sensitive_path",
    2: "has_sql_injection",
    3: "has_xss",
    4: "has_path_traversal",
    5: "has_command_injection",
    6: "has_file_inclusion",
    7: "has_double_encoding",
    8: None,
    9: None,
    10: None,
    11: None,
    12: None,
}

# stage 9「特殊字元密集」是複合定義（has_xss + url_special_chars 數值門檻，
# 見 §3.1 表格 row 9 與 attack_log_instruments.md 的「視情況」）。這個數值門檻
# 規格文件沒有給定案數字，是團隊要拍板的收集範圍問題（同 §3.7 STAGE_LOG_PATHS
# 待補的性質一樣）——在團隊訂出來之前先留 None，diversity.py 只驗 has_xss==1
# 那一半，並在 warnings 註明複合定義尚未補齊數值門檻。
SPECIAL_CHARS_DENSE_THRESHOLD = None  # TODO(team): 訂出 url_special_chars 密集門檻後填數字

# stage_id -> [condition, ...]（AND 起來一起驗證）。用在 DEFINING_FLAG 不夠表達
# 的情況：stage 8（數值門檻）、stage 9（flag + 數值門檻的複合定義）、
# stage 11（不是 0/1 flag，而是「request_method 不屬於 GET/POST」）。
#
# condition = {"feature": str, "op": "eq"|"ne"|"gt"|"ge"|"lt"|"le"|"in"|"not_in",
#              "value": Any, "exclude_from_support": bool（預設 True）}
#
# exclude_from_support=False 是刻意的例外：stage 11 的 request_method 雖然是
# 定義判準的一部分，但它本身的多樣性（PUT/DELETE/OPTIONS/TRACE/PATCH 夠不夠雜）
# 正是要評的東西，所以規格 §3.1 表格刻意把它留在支撐特徵集 F 裡（見 §3.5 說明），
# 跟其他 stage「排除定義 flag」的一般規則不同。
DEFINING_PREDICATE = {
    8: [
        {"feature": "url_encoding_count", "op": "gt", "value": 0},
    ],
    9: (
        [
            {"feature": "has_xss", "op": "eq", "value": 1},
            {"feature": "url_special_chars", "op": "gt", "value": SPECIAL_CHARS_DENSE_THRESHOLD},
        ]
        if SPECIAL_CHARS_DENSE_THRESHOLD is not None
        else [
            {"feature": "has_xss", "op": "eq", "value": 1},
        ]
    ),
    11: [
        {
            "feature": "request_method",
            "op": "not_in",
            "value": ["GET", "POST"],
            "exclude_from_support": False,
        },
    ],
}

# stage_id -> 支撐特徵集 F（評多元度用，已排除定義 flag，例外見上方 stage 11 註）
SUPPORT_FEATURES = {
    1: ["os_type", "ua_length", "request_method", "url_depth", "url_length", "referrer_type"],
    2: [
        "os_type", "ua_length", "url_length", "url_special_chars",
        "url_param_count", "request_method", "url_encoding_count",
    ],
    3: ["url_special_chars", "url_length", "ua_length", "url_encoding_count", "os_type", "request_method"],
    4: ["url_depth", "url_length", "url_encoding_count", "os_type", "ua_length", "has_double_encoding"],
    5: ["url_length", "url_special_chars", "os_type", "ua_length", "request_method", "url_param_count"],
    6: ["url_length", "url_special_chars", "os_type", "ua_length", "url_encoding_count"],
    7: ["url_encoding_count", "url_length", "os_type", "ua_length"],
    8: ["url_length", "url_special_chars", "os_type", "ua_length"],
    9: ["url_length", "os_type", "ua_length", "url_encoding_count"],
    10: ["os_type", "ua_length", "is_bot", "referrer_type", "request_method"],
    11: ["request_method", "url_length", "os_type", "ua_length"],
    12: ["url_length", "url_depth", "url_param_count", "url_special_chars", "os_type", "ua_length"],
}


# ============================================================
# §3.2 — 類別型特徵的理論基數與期望取值
# ============================================================

CARDINALITY = {
    "os_type": 8,
    "referrer_type": 6,
    "url_file_type": 6,
    "request_method": 8,
    "request_version": 3,
    "ip_type": 7,
    "status_category": 6,
    "time_period": 4,
    "day_of_week": 7,
    "local_day_of_week": 7,
    "hour": 24,
    "local_hour": 24,
    "is_bot": 2,
    "is_odd_hour": 2,
    "local_is_odd_hour": 2,
    "is_error_status": 2,
}

EXPECTED_VALUES = {
    # unknown/win/android/ios/linux/mac/bot/other（_browser_features）
    "os_type": [0, 1, 2, 3, 4, 5, 6, 7],
    # none/local/ip/search/social/external
    "referrer_type": [0, 1, 2, 3, 4, 5],
    # none/script/image/asset/document/other
    "url_file_type": [0, 1, 2, 3, 4, 5],
    # ⚠️ 讀 create_all_features() 的原始字串，不要吃任何模型的 LabelEncoder 輸出，見 §3.5
    "request_method": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH", "HEAD"],
    # ⚠️ 讀原始字串，理由同 §3.5
    "request_version": ["HTTP/1.0", "HTTP/1.1", "HTTP/2.0"],
    # ⚠️ 讀原始字串，不是壓平後的整數，見 §3.6
    "ip_type": [
        "public", "private_class_a", "private_class_b", "private_class_c",
        "loopback", "invalid", "unknown",
    ],
    # 0 與百位 1-5
    "status_category": [0, 1, 2, 3, 4, 5],
    # night/morning/afternoon/evening
    "time_period": [0, 1, 2, 3],
    "day_of_week": [0, 1, 2, 3, 4, 5, 6],
    "local_day_of_week": [0, 1, 2, 3, 4, 5, 6],
    "hour": list(range(24)),
    "local_hour": list(range(24)),
    "is_bot": [0, 1],
    "is_odd_hour": [0, 1],
    "local_is_odd_hour": [0, 1],
    "is_error_status": [0, 1],
}


# ============================================================
# §3.3 — 數值型特徵清單
# ============================================================

NUMERIC_FEATURES = [
    "url_length", "url_depth", "url_param_count", "url_special_chars",
    "url_encoding_count", "ua_length", "referrer_length", "log_size",
]

CATEGORICAL_FEATURES = list(CARDINALITY.keys())

# feature -> "categorical" | "numeric"，feature_diversity() 依此分派
FEATURE_TYPE = {f: "categorical" for f in CATEGORICAL_FEATURES}
FEATURE_TYPE.update({f: "numeric" for f in NUMERIC_FEATURES})


# ============================================================
# §2.5 — per-stage 權重（預設全 1）
# ============================================================

STAGE_WEIGHTS = {
    stage_id: {feature: 1.0 for feature in features}
    for stage_id, features in SUPPORT_FEATURES.items()
}


# ============================================================
# §3.7 — 其他 config 欄位
# ============================================================

# supply to fingerprint.py；benign stage 為 False。這 12 個 stage 都是攻擊/工具
# 相關 stage（見 attack_log_instruments.md），預設 True；日後若加入 benign 專屬
# stage id，記得在這裡把它設 False。
APPLY_TOOL_PENALTY = {stage_id: True for stage_id in SUPPORT_FEATURES}

# stage_id -> log 檔案路徑/glob。⚠️ 待團隊填（見規格 §3.7）：哪個 stage 對應
# 靶機上哪個 log 檔案，目前沒有定案的命名慣例。attack_log.md 只列了每個 stage
# 要打什麼、用什麼工具，沒有定輸出 log 要存在哪、怎麼命名。
# 目前 nginx/logs/ 底下已有 access1_Aman.log（benign）、
# access2_Dicurigai_sensitive_path.log（疑似對應 stage 1），但命名慣例還沒
# 拍板，此表故意留空——run_stage.py 的 --log/--stage 參數可以不依賴這張表，
# 手動指定路徑優先於這裡的查表。
STAGE_LOG_PATHS = {}

# 以下欄位供後續 whole-dataset 模組（confounder.py / realism.py）共用，
# 先在此集中定義避免散落；本文件（diversity）不使用它們。
CONFOUNDER_FEATURES = [
    "ip_type", "ip_first_octet",
    "hour", "day_of_week", "is_odd_hour", "time_period",
    "local_hour", "local_day_of_week", "local_is_odd_hour", "local_time_period",
    "os_type", "is_bot", "ua_length",
]

CONTENT_FEATURES = [
    "has_sql_injection", "has_xss", "has_path_traversal",
    "has_command_injection", "has_file_inclusion", "has_double_encoding",
    "url_special_chars", "url_encoding_count", "url_length", "url_depth",
    "url_param_count", "accesses_sensitive_path", "url_file_type",
]

BIN_EDGES = {}  # numeric_feature -> [edges...]，JS/overlap 共用，從 baseline 推定，待補
BASELINE_PATHS = {"indonesia": None, "csic": None}  # 待補實際路徑