"""Parser unit test — run: python3 test_parser.py"""

import json
import sys

sys.path.insert(0, ".")
from parser import parse_line

TENANT = "tenant-demo-001"

cases = [
    ("nginx combined 正常行",
     '203.0.113.45 - - [03/May/2026:10:30:15 +0000] "GET /api/v1/users HTTP/1.1" 200 1024 "https://example.com/" "Mozilla/5.0"',
     True),
    ("apache combined（有 auth user）",
     '198.51.100.7 - frank [03/May/2026:10:30:16 +0000] "POST /login HTTP/1.1" 401 212 "-" "curl/7.68.0"',
     True),
    ("bytes = - (zero)",
     '10.0.0.1 - - [03/May/2026:11:00:00 +0000] "HEAD / HTTP/1.1" 200 - "-" "-"',
     True),
    ("無 referer / UA（短格式）",
     '1.2.3.4 - - [03/May/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 512',
     True),
    ("空行",          "",                       False),
    ("不合格的行",    "this is not a log line", False),
]

def run_tests() -> None:
    passed, failed = 0, 0
    for desc, line, expect_ok in cases:
        result = parse_line(line, "nginx_combined", TENANT)
        ok = result is not None
        status = "PASS" if ok == expect_ok else "FAIL"
        if status == "FAIL":
            failed += 1
        else:
            passed += 1
        print(f"[{status}] {desc}")
        if result:
            p = result["payload"]
            print(f"       ip={result['source_ip']}  ts={result['timestamp']}  "
                  f"method={p['method']}  status={p['status']}  size={p['size']}")

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    # 這份檔案是手刻的獨立測試腳本（見檔頭 docstring），不是給 pytest 收集用
    # 的，但檔名符合 test_*.py，pytest 掃到目錄時還是會嘗試 import 它。用這個
    # guard 讓 import 本身無副作用（不會真的跑測試、不會呼叫 sys.exit()），
    # 只有真的用 `python test_parser.py` 執行才會跑——少了這個 guard，pytest
    # import 這個模組時會執行到底部的 sys.exit()，在 collection 階段觸發
    # SystemExit，讓 pytest 整個 INTERNALERROR、後面所有測試都不會跑（同一個
    # 問題在 test_buffer.py 已經在 CI 實際發生過）。
    run_tests()
