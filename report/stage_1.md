# Stage 1 多元度驗收報告 — 敏感路徑

- 樣本數：264
- **Diversity_stage = 0.2854**

## Warnings

- ⚠️ stage 1: 支撐特徵 'url_depth' 完全塌縮（d=0）
- ⚠️ stage 1: 支撐特徵 'referrer_type' 完全塌縮（d=0）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.3260 | 0.25 | 0, 2, 3, 4, 5, 6 |
| `ua_length` | 0.8347 | — | — |
| `request_method` | 0.2577 | 0.25 | DELETE, OPTIONS, PATCH, POST, PUT, TRACE |
| `url_depth` | 0.0000 | — | — |
| `url_length` | 0.2941 | — | — |
| `referrer_type` | 0.0000 | 0.17 | 1, 2, 3, 4, 5 |
