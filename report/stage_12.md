# Stage 12 多元度驗收報告 — 異常 URL 結構

- 樣本數：150（⚠️ provisional，< MIN_SAMPLES，數字僅供參考）
- **Diversity_stage = 0.4332**

## Warnings

- ⚠️ stage 12: n_samples=150 < MIN_SAMPLES=200，熵/QCD 數字僅供參考（provisional），CI 不得當硬門檻
- ⚠️ stage 12: 支撐特徵 'url_param_count' 的 QCD=0，但實際有 6 種取值（不是真塌縮，是低基數或尾部集中分布讓 Q1=Q3——見 §2.3 QCD 已知限制，strict 門檻的「塌縮數」不該把這種情況算進去）

## 支撐特徵明細

| 特徵 | d(f) | coverage | missing |
| --- | --- | --- | --- |
| `url_length` | 0.2043 | — | — |
| `url_depth` | 0.4545 | — | — |
| `url_param_count` | 0.0000 | — | — |
| `url_special_chars` | 1.0000 | — | — |
| `os_type` | 0.5073 | 0.38 | 0, 1, 4, 5, 6 |
