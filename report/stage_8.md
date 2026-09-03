# Stage 8 多元度驗收報告 — URL 編碼變形

- 樣本數：180（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.3146**

## Warnings

- ⚠️ stage 8: n_samples=180 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.2672 | — | — |
| `url_special_chars` | 0.4359 | — | — |
| `os_type` | 0.2406 | 0.25 | 0, 2, 3, 4, 5, 6 |
