"""
Attack-pattern regex strings shared between feature_engineering.py (pandas batch)
and pipeline_utils.py (online streaming inference).

Only raw strings here — no pandas, no re.compile — so this module is safe to
import in any container without pulling in heavy dependencies.
"""

SQL_PATTERNS = [
    r"union.*select",
    r"select.*from",
    r"insert.*into",
    r"delete.*from",
    r"drop.*table",
    r"'.*or.*'",
    r"1\s*=\s*1",
    r"admin'--",
    r"benchmark\(",
    r"sleep\(",
    r"--\s*$",
    r"#\s*$",
    r";\s*--",
]

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

PATH_TRAVERSAL_PAT = r"\.\./|\.\.\\|%2e%2e"

CMD_PATTERNS = [
    r";.*ls",
    r";.*cat",
    r";.*rm",
    r";.*wget",
    r";.*curl",
    r"\|.*ls",
    r"&&.*ls",
    r"`.*`",
    r"\$\(",
    r"\$\{",
    r"/etc/passwd",
    r"/bin/bash",
    r"/bin/sh",
]

FILE_INCLUSION_PAT = r"file://|php://|data://|expect://|input://"
