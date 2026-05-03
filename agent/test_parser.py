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
