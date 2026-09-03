"""dataset_health.config — per-stage 多元度驗收的唯一事實來源。

對照 Verify_doc/log_per_stage_verify_diversity_module_design_instruments.md §3。
`diversity.py` 不得硬編任何 stage 專屬常數，一律從這裡讀。
"""

import warnings
from pathlib import Path

# ============================================================
# §3.7 — 基本門檻
# ============================================================

MIN_SAMPLES = 200  # 低於此，熵/QCD 標 provisional=true，CI 不得當硬門檻

# defining_violations 明細（StageDiversityReport）超過這個數字就截斷，只留
# 前 N 筆 + 真實總數。拿大型工具掃描（例如 15843 筆的 nikto scan，其中
# 11223 筆不符合 stage 1 的定義判準）實測過：不截斷的話 JSON 報告會膨脹到
# 5+ MB，且每次重跑內容都會變、被 git 追蹤只會讓 repo 越滾越大。500 這個數字
# 純粹是「肉眼核對綽綽有餘、又不會讓報告失控變大」的經驗值，不是規格定義的
# 門檻，需要的話可以調。
MAX_DEFINING_VIOLATIONS = 500


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
#
# ⚠️ ua_length 從下面 11 個 stage（除了 stage 10）的 F 裡拿掉了，是刻意的，
# 不是漏打：真實資料驗證發現 QCD 量的是「UA 長度的離散」不是「UA 的多樣性」，
# 工具 UA 短（curl/8.5.0 = 10 字元）、瀏覽器 UA 長（100+ 字元），只要混一點
# 攻擊工具流量進來，雙峰分布就把 IQR 比值撐到很高，QCD 反而給高分——工具
# 混得越多分數越高，跟 shortcut-learning 防範的目的完全相反（§1.1），而且
# ua_length 原本出現在全部 12 個 stage 的 F 裡，是系統性問題。詳細數字對照
# 見 Verify_doc/known_gaps_diversity_config.md（QCD=0.8347
# vs 純瀏覽器零指紋資料的 0.1878）。
#
# 沒有整批刪掉、stage 10 刻意保留：stage 10「UA 多樣性」本身的收集目標就是
# UA 夠不夠雜，拿掉 ua_length 會讓這個 stage 自己的定義特徵開天窗（F 只剩
# os_type/is_bot 這種粗粒度分類，力道不夠）。長期修法是把 ua_length 換成
# UA 家族的類別型熵（browser/curl/python/scanner...），但那需要在
# feature_engineering.py 新增分類邏輯（而且那份檔案的權威版本在
# log-analysis-core，不是這裡，見 §4），還要先確認跟 fingerprint.py 有沒有
# 職責重疊，不是能在這裡單方面做的小改動——stage 10 先維持原狀，等那個
# UA 家族特徵真的做出來再換掉。
SUPPORT_FEATURES = {
    1: [
        "os_type", "request_method", "url_depth", "url_length", "referrer_type",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    2: [
        "os_type", "url_length", "url_special_chars",
        "url_param_count", "request_method", "url_encoding_count",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    3: [
        "url_special_chars", "url_length", "url_encoding_count", "os_type", "request_method",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    4: [
        "url_depth", "url_length", "url_encoding_count", "os_type", "has_double_encoding",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    5: [
        "url_length", "url_special_chars", "os_type", "request_method", "url_param_count",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    6: [
        "url_length", "url_special_chars", "os_type", "url_encoding_count",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    7: [
        "url_encoding_count", "url_length", "os_type",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    8: [
        "url_length", "url_special_chars", "os_type",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    9: [
        "url_length", "os_type", "url_encoding_count",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    10: ["os_type", "ua_length", "is_bot", "referrer_type", "request_method"],  # ua_length 保留，見上方說明
    11: [
        "request_method", "url_length", "os_type",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
    12: [
        "url_length", "url_depth", "url_param_count", "url_special_chars", "os_type",
        # "ua_length",  # 移除，見上方本區塊開頭的說明
    ],
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
    # stage 4（路徑遍歷）的支撐特徵集 F 明確保留 has_double_encoding 本身的
    # 多元度（§3.1 表格 row 4）——這裡跟其他 stage 排除定義 flag 的規則不同，
    # 不是漏掉，是 stage 4 就是要看「這批路徑遍歷樣本裡，有沒有混雙重編碼
    # 變形」。之前漏掉沒登記進 CARDINALITY/EXPECTED_VALUES，拿真實 log
    # （nginx/collected/nginx01_batch_path_traversal_001.log）測 stage 4
    # 時直接 ValueError，這裡補上。
    "has_double_encoding": 2,
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
    "has_double_encoding": [0, 1],
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

# stage_id -> log 檔案路徑清單（一個 stage 可以有多份 log，例如 stage 1 現在
# 同時有手打的敏感路徑探測 + nikto 大量掃描）。§3.7 原本一直留空的命名慣例，
# 現在由 nginx/logs/stage_log_CHECK/stage_log_map.txt 拍板（格式與規則見同
# 目錄 README.md）；這裡在 import 時自動解析那份純文字表，不用改這份
# config.py。手動指定路徑（run_stage.py 的 --log）仍然優先於這裡的查表，
# 兩者互不依賴。
_REPO_ROOT = Path(__file__).resolve().parent.parent
_NGINX_DIR = _REPO_ROOT / "nginx"
_STAGE_LOG_MAP_PATH = _NGINX_DIR / "logs" / "stage_log_CHECK" / "stage_log_map.txt"


def _load_stage_log_map(map_path: Path) -> dict:
    """解析 stage_log_map.txt。

    格式：`<path1>[,<path2>,...]==<stage id>`，# 開頭是註解。每個 path 相對
    `nginx/`（不是 `nginx/logs/`——collected/ 底下的批次也要能指到）。同一個
    stage id 可以出現在多行，或用逗號在同一行列多個檔案，兩種寫法都會累積
    進同一個 list，不會互相覆蓋。

    檔案不存在，或某一行格式不對，就跳過該行並發 warning，不讓
    `import dataset_health.config` 整個炸掉——這張表本來就是持續在填的
    施工中狀態，缺一筆不該讓其他完全無關的東西一起壞掉。
    """
    result: dict[int, list[str]] = {}
    if not map_path.exists():
        return result

    for line_no, raw_line in enumerate(map_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            warnings.warn(f"{map_path}:{line_no}: 格式不對（缺 '=='），跳過：{raw_line!r}")
            continue

        paths_text, _, stage_text = line.partition("==")
        stage_text = stage_text.strip()
        try:
            stage_id = int(stage_text)
        except ValueError:
            warnings.warn(f"{map_path}:{line_no}: stage id 不是整數，跳過：{raw_line!r}")
            continue

        filenames = [f.strip() for f in paths_text.split(",") if f.strip()]
        if not filenames:
            warnings.warn(f"{map_path}:{line_no}: '==' 前面沒有檔名，跳過：{raw_line!r}")
            continue

        resolved = [(_NGINX_DIR / f).relative_to(_REPO_ROOT).as_posix() for f in filenames]
        result.setdefault(stage_id, []).extend(resolved)

    return result


_LOG_PATH_MAP = _load_stage_log_map(_STAGE_LOG_MAP_PATH)

# 只有 1-12（SUPPORT_FEATURES 涵蓋的攻擊 stage）會被 diversity 模組吃。
STAGE_LOG_PATHS = {
    stage_id: paths for stage_id, paths in _LOG_PATH_MAP.items() if stage_id in SUPPORT_FEATURES
}

# stage 0（benign/非攻擊，見 stage_log_CHECK/README.md）以及其他不在
# SUPPORT_FEATURES 裡的代號，先留著當參考/未來擴充用（例如
# confounder.py/realism.py 需要 benign baseline，見規格附錄 B）。
# stage_diversity() 目前不吃這些，傳進去會直接 KeyError——這是刻意的，
# diversity 這份規格只涵蓋攻擊 stage 的多元度，benign 流量的健檢屬於
# 別的模組，不在這裡硬塞。
NON_DIVERSITY_LOG_PATHS = {
    stage_id: paths for stage_id, paths in _LOG_PATH_MAP.items() if stage_id not in SUPPORT_FEATURES
}

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