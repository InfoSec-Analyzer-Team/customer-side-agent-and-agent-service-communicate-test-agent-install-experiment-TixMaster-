# stage_log_map.txt 怎麼填

這張表是規格 §3.7 一直留空的 `STAGE_LOG_PATHS` 對照表：哪些 log 檔案對應
哪個 stage。`dataset_health/config.py` 會在 import 時自動解析
`stage_log_map.txt`，填進 `config.STAGE_LOG_PATHS`（給 `run_stage.py`
`--log` 省略時查表用）。改這張表不用動 Python 程式碼。

## 格式

一行一筆，`<path1>[,<path2>,...]==<stage id>`：

```
logs/access1_Aman.log==0


logs/access2_Dicurigai_sensitive_path.log,collected/nginx01_batch_nikto_scan_xff_clean_003.log==1
collected/nginx01_batch_sqli_sqlmap_randomua_002.log==2

```

- path 是**相對 `nginx/` 的路徑**（不是相對 `nginx/logs/`，也不是完整路徑）——
  這樣 `logs/` 跟 `collected/` 底下的檔案才能用同一張表管理。
- 一個 stage 有多份 log 時，可以用逗號在同一行列多個 path（如上面 stage 1
  那行），或分成好幾行、每行各寫一個 path、stage id 相同——兩種寫法效果一樣，
  都會累積進同一個 list，不會互相覆蓋。`run_stage.py` 會把同一個 stage 的
  所有 log 合併成一份 DataFrame 一起評多元度（不是各自算再取平均），這樣才
  反映這個 stage 目前收集到的資料全貌。
- `#` 開頭是註解，空行會被忽略。
- 等號兩側前後空白會被去掉，逗號分隔的每個 path 也會各自去頭尾空白。
- 一行格式不對(沒有 `==`、`==` 前面沒有 path、或 stage id 不是整數)會被跳過
  並印警告，不會讓 `import dataset_health.config` 整個炸掉——這張表本來就是
  持續在填的施工中狀態。

## stage id 是什麼

- **1–12**：對照 `dataset_health/config.py` 的 `STAGE_NAMES` / `SUPPORT_FEATURES`
  （敏感路徑、SQLi、XSS…見規格 §3.1 表格）。這個範圍的條目會被收進
  `config.STAGE_LOG_PATHS`，`run_stage.py`／`stage_diversity()` 吃得到。
- **0**：**benign（非攻擊）流量的保留代號，不是規格 §3.1 定義的攻擊 stage**。
  目前只當標記用，不會被送進 `stage_diversity()`（`SUPPORT_FEATURES` 沒有
  key `0`，硬傳會直接 `KeyError`）。這類條目會被收進另一個字典
  `config.NON_DIVERSITY_LOG_PATHS`，先留著給以後 whole-dataset 模組
  （`confounder.py`/`realism.py` 需要 benign baseline，見規格附錄 B）用，
  是否要接進某個模組是之後的規劃項目，不在這次 diversity 模組的範圍內。

## `nginx/collected/` 裡「混合、不對應單一 stage」的批次怎麼辦？

`nginx/collected/nginx01_batch_dicurigai_probe_001.log` 這類批次故意混合多種
探測行為（敏感路徑 + 異常 method + 雙重編碼…），沒有單一定義 flag，硬塞一個
stage id 進來只會讓 `defining_violations` 洗版。這種批次**不放進**
`stage_log_map.txt`——它的品質評估要靠人直接看內容，不是透過
`stage_diversity()`。

## 目前每個 stage 條目的來源



- stage 0（benign）：`nginx/logs/access1_Aman_clean.log`
- stage 1（敏感路徑 / scanner probe）：手打探測 `logs/access2_Dicurigai_sensitive_path.log` + Nikto controlled scan clean subset `collected/nginx01_batch_nikto_scan_xff_clean_003.log`
- stage 2（SQLi）：`collected/nginx01_batch_sqli_sqlmap_randomua_002.log` + night/IP/POST method diversity batches
- stage 3（XSS）：`collected/nginx01_batch_xss_zap_fullscan_clean_001.log` + ffuf night/IP/POST method diversity batches
- stage 4（Path Traversal）：`collected/nginx01_batch_path_traversal_ffuf_002.log` + IP/UA/POST method diversity batches
- stage 5（Command Injection）：`collected/nginx01_batch_command_injection_commix_001.log` + ffuf night/POST method diversity batches
- stage 6（LFI/RFI）：`LFI_method_record/access3_Local_file_inclusion_1.log` + `access4_Local_file_inclusion_2_wfuzz_clean.log` + `access5_Local_file_inclusion_3_wfuzz.log`
- stage 7（Double Encoding）：`collected/nginx01_batch_double_encoding_ffuf_002.log` + IP/UA/POST method diversity batches
- stage 8（URL Encoding Count）：`collected/nginx01_batch_url_encoding_count_ffuf_001.log` + IP/UA/POST method diversity batches
- stage 9（Special Chars Dense）：`collected/nginx01_batch_special_chars_dense_ffuf_001.log` + IP/UA/POST method diversity batches
- stage 10（Scanner UA）：`collected/nginx01_batch_scanner_ua_gobuster_005.log` + IP/UA diversity batch
- stage 11（Abnormal Methods）：`collected/nginx01_batch_abnormal_methods_ffuf_002.log` + clean-IP method diversity batch
- stage 12（Abnormal URL）：`collected/nginx01_batch_abnormal_url_ffuf_001.log` + IP/UA/POST method diversity batches

詳細收集方式見 `nginx/collected/collection_method.md`。LFI sink 本身的設計與風險說明見 `Verify_doc/lfi_sink.md`。


