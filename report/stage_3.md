# Stage 3 多元度驗收報告 — XSS

- 樣本數：250
- **Diversity_stage = 0.1178**

## Warnings

- ⚠️ stage 3: 支撐特徵 'os_type' 完全塌縮（d=0）
- ⚠️ stage 3: 支撐特徵 'request_method' 完全塌縮（d=0）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_special_chars` | 0.0769 | — | — |
| `url_length` | 0.1111 | — | — |
| `ua_length` | 0.4074 | — | — |
| `url_encoding_count` | 0.1111 | — | — |
| `os_type` | 0.0000 | 0.12 | 0, 1, 2, 3, 4, 5, 6 |
| `request_method` | 0.0000 | 0.12 | DELETE, HEAD, OPTIONS, PATCH, POST, PUT, TRACE |
