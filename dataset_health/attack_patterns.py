"""
Attack-pattern regex strings (and one small stdlib-only detector function)
shared between feature_engineering.py (pandas batch) and pipeline_utils.py
(online streaming inference).

No pandas here — only `re`/`ast`/`itertools`/`os` from the standard library —
so this module is safe to import in any container without pulling in heavy
dependencies.
"""

import ast
import itertools
import operator
import os
import re

SQL_PATTERNS = [
    r"union.*select",
    r"select.*from",
    r"insert.*into",
    r"delete.*from",
    r"drop.*table",
    r"'.*or.*'",
    #
    # sqlmap 的 boolean-blind 測試預設用「隨機數字」而非固定的 1=1（就是為了
    # 閃避只認字面 "1=1" 的簡單 WAF 規則），例如 "7973=2007"、"(8113=8113"。
    # (?<![A-Za-z0-9_]) 排除左邊緊接字母/數字/底線的情況，避免誤中像
    # "v1=2"、"item1=5"、"q1=100" 這種「參數名稱剛好以數字結尾」的正常
    # query string。注意：只排除緊接字母（(?<![A-Za-z])）不夠——regex 引擎
    # 會從 \d+ 內部的每個位置嘗試起始，所以像 "item12=5" 這種參數名以「兩位
    # 以上數字」結尾時，內層數字左邊是另一個數字（不是字母），舊版
    # (?<![A-Za-z]) 會放行、對 "2=5" 誤判；必須連數字/底線一起排除才能擋住
    # 這整類參數名。涵蓋 "=" 跟編碼後的 "%3D" 兩種形式。這個 pattern 涵蓋了
    # 原本 "1=1" 的絕大多數情境，但不是嚴格超集——"1=1" 左邊緊接字母時（如
    # "abc1=1"）不再命中，這類形式在真實 payload 中罕見（sqlmap 產生的
    # boolean-blind payload 前面一定是空白/括號/引號等分隔符，不是字母）。
    # 詳見 docs/fix_module_log/attack_pattern_detection_gaps.md 缺口 2：用
    # sqlmap 實測，378 筆已知 SQLi 樣本裡 68.5% 因為只認字面 1=1 而漏判。
    r"(?<![A-Za-z0-9_])\d+\s*(?:=|%3[dD])\s*\d+",
    r"admin'--",
    r"benchmark\(",
    r"sleep\(",
    r"--\s*$",
    r"#\s*$",
    r";\s*--",
]

# ── 括號/運算子包裝的算術 tautology（例如 "(22+22)=44"、"(2*3)=6"）─────────
#
# 上面的 r"(?<![A-Za-z0-9_])\d+\s*(?:=|%3[dD])\s*\d+" 只認「= 兩側緊鄰裸數字」，
# 一旦攻擊者在 = 前面加個括號（"(22+22)=44"），數字就不再緊鄰 =，regex 直接
# 抓不到——這是 regex-only 比對的天花板：它沒辦法配對括號、算出算式的值，
# 只能認字面樣式。
#
# 這裡改用「找出候選算式 → 用白名單 AST 安全求值 → 兩側都能算出數值就算命中」
# 取代單純字串比對：
#   - 只要 = 兩側各自是合法的算術式（只含數字、+ - * / ( ) 空白），不要求兩側
#     數值相等——sqlmap 的 boolean-blind 技巧一定會成對送出 true/false 兩種
#     算式做對照測試（例如先送 (22+22)=44 驗證「相等時」的回應，再送
#     (22+22)=45 驗證「不相等時」的回應），只認「數值真的相等」的 tautology
#     會直接漏掉一半的探測封包；反過來，一般網站的 query string 幾乎不會出現
#     「括號/運算子組成的算式緊鄰著另一個算式」這種結構本身，所以光是「兩側
#     都能被安全解析成合法算術式」就已經是很強的訊號，不需要額外比較數值。
#   - 求值用 Python ast 模組手刻白名單 walker，只允許 Constant（數字字面值）、
#     BinOp（+ - * /）、UnaryOp（+ -）這幾種節點，其餘一律拒絕——這不是在
#     一般字串上呼叫 eval()/exec()：任何 Name/Call/Attribute/Subscript/...
#     節點都會落到白名單外直接回傳 None，不會被求值也不會被執行，因此無法
#     被拿來當 RCE 跳板（例如 "__import__('os').system('id')=1" 這種輸入，
#     Name/Call 節點不在白名單內，直接視為「不是合法算術式」，不會執行）。
#   - 每個候選算式長度上限 32 字元、每個 URL 最多掃前 20 個 "="/"%3D"
#     出現位置，避免惡意超長 URL 或塞大量 "=" 拖慢單一 request 的處理時間
#     （這支函式會在即時 serving pipeline 裡對每一筆進來的 request 執行）。
#
# 已知取捨：計算機/報價工具類網站如果把算式直接放進 query string（例如
# "?q=2+2=4"），會被這個規則誤判——這類網站在本系統的實際流量情境（電商/
# 一般 Web 服務）裡極少見，先接受這個取捨，不特別排除。

_TAUTOLOGY_MAX_OPERAND_LEN = 32
_TAUTOLOGY_MAX_EQUALS_SCANNED = 20

_TAUTOLOGY_CANDIDATE_RE = re.compile(
    # (?<![A-Za-z0-9_]) 在左側算式前面：避免把 "item1=5"、"v1=2"、"q1=100"
    # 這種「參數名稱剛好以數字結尾」的正常 query string 誤當成左運算元（此時
    # = 前緊鄰的數字其實是識別字尾巴，不是算式）——跟 SQL_PATTERNS 那條裸
    # 數字 tautology pattern 用同一個排除規則，同樣必須排除數字/底線（不只
    # 字母），否則 "item12=5" 這種兩位數結尾的參數名，regex 會從內層數字
    # "2" 開始起始比對，左邊是數字而不是字母，(?<![A-Za-z]) 放行、誤判成
    # "2=5"。若這個起點被擋下，regex 引擎會繼續往右找下一個可能的起點
    # （例如 "OR (22+22)=44" 裡，雖然緊接在 "OR " 後面的空白起點會被 'R'
    # 擋掉，但從 "(" 開始的起點前面是空白，不是字母/數字，一樣找得到、一樣
    # 命中）。
    r"(?<![A-Za-z0-9_])([\d+\-*/(). \t]{1," + str(_TAUTOLOGY_MAX_OPERAND_LEN) + r"})"
    r"(?:=|%3[dD])"
    r"([\d+\-*/(). \t]{1," + str(_TAUTOLOGY_MAX_OPERAND_LEN) + r"})"
)

_TAUTOLOGY_ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
}
_TAUTOLOGY_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_eval_arith(expr: str):
    """把 expr 當成純算術式安全求值；回傳數值，若 expr 不是合法/在白名單內的
    算術式（語法錯誤、除以零、含任何非數字運算節點...）一律回傳 None，絕不
    拋例外、絕不執行白名單以外的節點。"""
    expr = expr.strip()
    if not expr:
        return None
    try:
        tree = ast.parse(expr, mode="eval")
    except (SyntaxError, ValueError, RecursionError):
        return None

    def _walk(node):
        if isinstance(node, ast.Expression):
            return _walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _TAUTOLOGY_ALLOWED_BINOPS:
            left, right = _walk(node.left), _walk(node.right)
            if left is None or right is None:
                return None
            try:
                return _TAUTOLOGY_ALLOWED_BINOPS[type(node.op)](left, right)
            except (ZeroDivisionError, OverflowError):
                return None
        if isinstance(node, ast.UnaryOp) and type(node.op) in _TAUTOLOGY_ALLOWED_UNARYOPS:
            val = _walk(node.operand)
            return None if val is None else _TAUTOLOGY_ALLOWED_UNARYOPS[type(node.op)](val)
        return None  # Name/Call/Attribute/Subscript/... 都在這裡被擋下

    try:
        return _walk(tree)
    except RecursionError:
        return None


def has_sql_tautology_expression(url: str) -> bool:
    """偵測「算術式 = 算術式」這種結構（不只是裸數字緊鄰 =），涵蓋
    "(22+22)=44"、"(2*3)=6" 這類用括號/運算子包裝來閃避純 regex 比對的
    boolean-blind SQLi 探測封包。見上方大段註解說明設計取捨。"""
    for m in itertools.islice(
        _TAUTOLOGY_CANDIDATE_RE.finditer(url), _TAUTOLOGY_MAX_EQUALS_SCANNED
    ):
        left, right = m.group(1), m.group(2)
        if not (any(c.isdigit() for c in left) and any(c.isdigit() for c in right)):
            continue
        if _safe_eval_arith(left) is not None and _safe_eval_arith(right) is not None:
            return True
    return False

XSS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"alert\s*\(",
    r"document\.cookie",
    r"<iframe",
    r"<img.*onerror",
]

# \.\.(?:/|\\|%2f|%5c) 涵蓋最常見的變形：dot 是字面值、只有斜線被
# URL 編碼（"..%2F"、"..%5C"）——這是滲透工具（例如手動打 path traversal
# payload）最常用的形式，原本只認字面 "../"/"..\\" 或是連 dot 都編碼的
# "%2e%2e" 會漏掉這個變形。詳見 docs/fix_module_log/attack_pattern_detection_gaps.md
# 缺口 1：用真實攻擊流量實測，120 筆已知路徑遍歷樣本裡 87.5% 因為這個漏洞被
# 判成 has_path_traversal=0。
# 大小寫一律靠呼叫端的 re.IGNORECASE / case=False 處理（兩處呼叫端皆已確認
# 為 case-insensitive），pattern 本身統一寫小寫，避免同一個 pattern 裡一部分
# 明寫大小寫、一部分依賴呼叫端，混用風格讓人搞不清楚這段能不能在
# case-sensitive 情境下單獨使用。
PATH_TRAVERSAL_PAT = r"\.\.(?:/|\\|%2f|%5c)|%2e%2e"

# commix 等命令注入工具預設會把 shell metacharacter 做 URL 編碼
# （";"→"%3b"、"|"→"%7c"、"&"→"%26"、"`"→"%60"、"$("→"%24%28"、
# "${"→"%24%7b"），原本只認字面字元的 pattern 對編碼後的字串完全對不上——
# 跟缺口 1（path traversal）、缺口 2（SQLi）同一種病。這裡統一寫成
# 「字面或編碼」的小型 building block，跟呼叫端一致靠 re.IGNORECASE 處理
# 大小寫，不在 pattern 裡混用大小寫字元類別。詳見
# docs/fix_module_log/founded_issues_known_gaps_attack_patterns..md 缺口 4：
# 用真實 commix/ffuf 流量實測，1786 筆已知命令注入樣本裡 99.8% 因為這個漏洞
# 被判成 has_command_injection=0（其中 97.1% 是編碼問題，2.0% 是下面命令
# 白名單太窄的問題疊加在一起）。
_CMD_SEMI = r"(?:;|%3b)"
_CMD_PIPE = r"(?:\||%7c)"
_CMD_AMP = r"(?:&|%26)"
_CMD_BACKTICK = r"(?:`|%60)"

# 邊界排除要同時擋掉兩種情況：(1) 正常字裡巧合包含關鍵字（"also" 裡的
# "ls"）；(2) 緊接在編碼運算子後面、無分隔符號直接黏在一起的情況（例如
# commix 常見的 "test%3Bwhoami"，沒有空白）。第 2 種情況麻煩在於 "%3B"
# （分號）、"%7C"（管線）這類編碼字串本身最後一碼剛好是英文字母
# （B、C），若單純用 (?<![A-Za-z]) 會被那個字母擋下，誤判成「前面接著
# 別的英文字」而漏掉——所以額外允許「前面剛好是一組完整的 %XX 編碼」通過
# 邊界檢查（這不是放寬到不安全，%[0-9A-Fa-f]{2} 只認得住合法的 2 碼 hex
# 編碼，不會被拿來繞過）。
_LETTER_OR_ENCODED_BOUNDARY = r"(?:(?<![A-Za-z])|(?<=%[0-9A-Fa-f]{2}))"

# 白名單從原本只認 "ls" 擴大到真實流量裡最常見的偵察/測試指令。仍然要求
# 前面有 ;/|/&& 其中一個運算子字元才會觸發，不是裸字比對。
# 已知殘留風險：像 "?fields=name|id|email" 這種合法的欄位選擇器 API，若欄位
# 名稱剛好叫 "id" 且用 "|" 分隔，會被誤判——這類 API 設計在一般網站少見，
# 團隊評估後接受這個取捨（跟 db2、badminton 那幾個已知取捨同一類判斷）。
_CMD_WORDS = (
    _LETTER_OR_ENCODED_BOUNDARY +
    r"(?:ls|cat|rm|wget|curl|whoami|id|uname|ping|nslookup|sleep|echo)"
    r"(?![A-Za-z])"
)

CMD_PATTERNS = [
    _CMD_SEMI + r".*" + _CMD_WORDS,
    _CMD_PIPE + r".*" + _CMD_WORDS,
    _CMD_AMP + _CMD_AMP + r".*" + _CMD_WORDS,
    _CMD_BACKTICK + r".*" + _CMD_BACKTICK,
    r"(?:\$\(|%24%28)",
    r"(?:\$\{|%24%7b)",
    r"/etc/passwd",
    r"/bin/bash",
    r"/bin/sh",
    # PHP 程式碼執行函式呼叫（phpinfo()/exec()/eval()/print()/system()），
    # 一樣要求緊接著左括號（字面或 "%28"）才算命中，不是裸字比對；
    # 邊界排除同上，避免 "sprint(" 這種正常函式名稱裡剛好包含 "print(" 被
    # 誤中，同時也不會被緊接在前面的編碼運算子誤擋。
    _LETTER_OR_ENCODED_BOUNDARY + r"(?:phpinfo|exec|eval|print|system)\s*(?:\(|%28)",
    # 裸換行注入（%0A / %0D%0A）緊跟常見偵察指令，無運算子字元也算命中——
    # 一般 query string 幾乎不會出現 URL-encoded 換行字元本身，誤判風險最低。
    r"(?:%0d%0a|%0a)(?:ls|cat|id|whoami|uname|pwd)(?![A-Za-z])",
]

# file://、php://、data:// 這幾個 PHP stream wrapper 只涵蓋「用特殊 URI
# scheme 讀檔」這一種 LFI 手法，完全沒有涵蓋「直接用絕對路徑讀取敏感系統
# 檔案」（例如 file=/etc/passwd，連 ../ 都不用，因為應用程式本身沒做路徑
# 白名單）——詳見上述缺口文件的缺口 5：974 筆真實 LFI 樣本裡 92.6%
# 是這種絕對路徑手法，原本的 pattern 完全沒有對應。這幾個系統目錄前綴在
# 正常網站的 query string 裡幾乎不會出現，用來當訊號補上這個空白。
# 已知殘留風險："/root/"、"/etc/" 這種前綴理論上可能撞上剛好取這種名字的
# 合法路徑段（例如網站真的有 "/etc/terms" 這種頁面），團隊評估後接受這個
# 取捨，跟命令白名單擴大是同一類判斷。
FILE_INCLUSION_PAT = (
    r"file://|php://|data://|expect://|input://"
    r"|/etc/|/proc/|/root/|/var/log/|/windows/|c:[\\/]"
)
