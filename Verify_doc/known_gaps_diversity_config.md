# `dataset_health/config.py` 已知問題 — `ua_length` 系統性獎勵工具指紋混合

> 這份文件記錄的是 **diversity 模組自己的 `SUPPORT_FEATURES` 選擇**有問題，
> 跟 `Verify_doc/known_gaps_attack_patterns.md` 記錄的 `attack_patterns.py`
> regex 缺口是不同性質的問題（那個是「pattern 覆蓋率不夠」，這個是「選錯
> 特徵去量測」）。這裡的修復是本地就能做、也已經做掉的（不像 attack_patterns.py
> 需要等 `log-analysis-core` 權威版本），所以狀態直接是「已處理」。

## 發現

拿 `nginx/logs/access2_Dicurigai_sensitive_path.log`（264 筆，56% 是
curl/gobuster/Nikto/python-requests/nmap/dirb 這類工具 UA，44% 是真實瀏覽器
UA）跑 stage 1，`ua_length` 的 QCD = 0.8347——是那個 stage 六個支撐特徵裡
**最高**的一個，反而把總分撐起來。

對照一組純瀏覽器、零工具指紋的理想資料，同一個特徵 QCD 只有 0.1878。

| 資料組成 | `ua_length` QCD |
|---|---:|
| 56% 攻擊工具 + 44% 瀏覽器（`access2_Dicurigai_sensitive_path.log`） | 0.8347 |
| 純瀏覽器、零指紋（對照組） | 0.1878 |

**結論：工具流量混得越多，這個特徵的分數反而越高。**

## 為什麼會這樣

`ua_length` 量的是「UA 字串長度的離散程度」，不是「UA 種類的多樣性」。
攻擊工具的 UA 通常很短（`curl/8.5.0` = 10 字元、`gobuster/3.6` = 12 字元），
真實瀏覽器 UA 通常很長（100+ 字元，塞滿 `Mozilla/5.0 (...) AppleWebKit/...
Chrome/... Safari/...` 這類冗長版本字串）。只要資料裡同時有這兩種來源，長度
分布會呈現明顯雙峰，QCD（`(Q3-Q1)/(Q3+Q1)`）這種基於四分位距的離散度量，
剛好就是雙峰分布最容易衝高的情境——即使實際上只有「兩種固定長度」而不是
真正多樣的長度分布，QCD 數字看起來也會很高。

`ua_length` 出現在全部 12 個 stage 的 `SUPPORT_FEATURES` 裡，所以這是系統性
問題，不是單一 stage 的巧合，直接違反規格 §1.1 想防範的 shortcut learning
（模型可能學到「UA 短 = 攻擊工具」這種捷徑，而不是學攻擊的實質特徵）。

## 討論過的兩個修法

1. **`ua_length` 退出所有 stage 的 F**：最簡單、最低風險，但 stage 10「UA
   多樣性」本身的收集目標就是評 UA 夠不夠雜，整批拿掉會讓這個 stage 的
   定義特徵開天窗。
2. **改成 UA 家族的類別型熵**（browser/curl/python/scanner/...）：真正修到
   問題根源（量「種類」而不是「長度」），但需要在 `feature_engineering.py`
   新增分類邏輯——而那份檔案的權威版本在 `log-analysis-core`（見
   `known_gaps_attack_patterns.md` 開頭的說明，同一個道理），本地加了下次
   `sync/from-private` 進來時會被覆蓋或衝突；而且可能跟 `fingerprint.py`
   的 UA 字串分析職責重疊（附錄 B 把 UA 指紋分析劃給 `fingerprint.py`），
   需要先確認沒有重複才能做。

## 決定採用的做法：折衷

- **stage 10 以外的 11 個 stage**：`ua_length` 從 `SUPPORT_FEATURES` 拿掉
  （用註解掉的方式保留在 `config.py` 裡，不是直接刪除，方便之後追溯／
  還原）。立即解決「12 個 stage 全部系統性受影響」的問題。
- **stage 10**：`ua_length` 保留，因為拿掉會讓這個 stage 自己的定義目標
  失去意義。等方案 2（UA 家族類別型熵）真的做出來、且確認跟
  `fingerprint.py` 沒有職責重疊，再換掉 stage 10 這裡的 `ua_length`。

實作：`dataset_health/config.py` 的 `SUPPORT_FEATURES`（含區塊開頭的完整
說明註解）。規格文件 `log_per_stage_verify_diversity_module_design_instruments.md`
§3.1 的表格本身沒有改動（保留原始設計意圖的歷史紀錄），在該表格下方加了
一段「實作偏離紀錄」註記這個決定，指回這份文件。

## 尚未做的事

- UA 家族分類特徵本身還沒設計／實作（分類體系要拍板：browser 要不要細分
  Chrome/Firefox/Safari？各版本算不算不同類？）。
- 沒有確認 `fingerprint.py` 目前的 UA 分析邏輯長什麼樣子，方案 2 動工前
  必須先看過，避免重複造輪子。
- 拿掉 `ua_length` 後，各 stage 的 `Diversity_stage` 分數會下降（少了一個
  權重貢獻），§7 門檻校準那輪要拿新的權重組成重新跑一次印尼 baseline，
  不能沿用舊的門檻數字。
