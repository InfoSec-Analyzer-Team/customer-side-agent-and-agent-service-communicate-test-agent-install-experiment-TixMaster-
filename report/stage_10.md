# Stage 10 多元度驗收報告 — UA 多樣性

- 樣本數：132（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.0173**

## Warnings

- ⚠️ stage 10: n_samples=132 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻
- ⚠️ stage 10: 支撐特徵 'os_type' 完全塌縮（d=0，只有 1 種取值）
- ⚠️ stage 10: 支撐特徵 'is_bot' 完全塌縮（d=0，只有 1 種取值）
- ⚠️ stage 10: 支撐特徵 'referrer_type' 完全塌縮（d=0，只有 1 種取值）
- ⚠️ stage 10: 支撐特徵 'request_method' 完全塌縮（d=0，只有 1 種取值）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `os_type` | 0.0000 | 0.12 | 0, 1, 2, 3, 4, 5, 6 |
| `ua_length` | 0.0865 | — | — |
| `is_bot` | 0.0000 | 0.50 | 1 |
| `referrer_type` | 0.0000 | 0.17 | 1, 2, 3, 4, 5 |
| `request_method` | 0.0000 | 0.12 | DELETE, HEAD, OPTIONS, PATCH, POST, PUT, TRACE |
