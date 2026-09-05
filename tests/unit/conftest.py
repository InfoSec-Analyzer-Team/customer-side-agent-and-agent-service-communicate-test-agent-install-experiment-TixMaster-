import os
import sys

# tests/unit 沒有 __init__.py，pytest 預設的 "prepend" import-mode不會自動把
# repo root 加進 sys.path，這裡手動補上，讓 `from dataset_health import ...`
# 在任何 cwd 下執行 pytest 都能 import 到。
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)