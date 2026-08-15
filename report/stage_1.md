# Stage 1 多元度驗收報告 — 敏感路徑

- 樣本數：204
- **Diversity_stage = 0.2616**

## Warnings

- ⚠️ stage 1: 12/204 筆樣本不符合定義判準 [{'feature': 'accesses_sensitive_path', 'op': 'eq', 'value': 1, 'exclude_from_support': True}]，可能混入其他 stage 的樣本，或定義判準本身設錯
- ⚠️ stage 1: 支撐特徵 'request_method' 完全塌縮（d=0）
- ⚠️ stage 1: 支撐特徵 'url_depth' 完全塌縮（d=0）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.3294 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `ua_length` | 0.8347 | — | — |
| `request_method` | 0.0000 | 0.12 | DELETE, HEAD, OPTIONS, PATCH, POST, PUT, TRACE |
| `url_depth` | 0.0000 | — | — |
| `url_length` | 0.3043 | — | — |
| `referrer_type` | 0.1009 | 0.33 | 2, 3, 4, 5 |
