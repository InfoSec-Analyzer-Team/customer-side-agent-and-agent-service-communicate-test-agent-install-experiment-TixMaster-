# stage_log_map.txt 怎麼填

這張表是規格 §3.7 一直留空的 `STAGE_LOG_PATHS` 對照表：哪個 log 檔案對應
哪個 stage。`dataset_health/config.py` 會在 import 時自動解析
`stage_log_map.txt`，填進 `config.STAGE_LOG_PATHS`（給 `run_stage.py`
`--log` 省略時查表用）。改這張表不用動 Python 程式碼。

## 格式

一行一筆，`<檔名>==<stage id>`：

```
access1_Aman.log==0
access2_Dicurigai_sensitive_path.log==1
```

- 檔名是**相對 `nginx/logs/` 的檔名**（不是完整路徑），程式會自動接上
  `nginx/logs/` 前綴。
- `#` 開頭是註解，空行會被忽略。
- 兩邊都用純數字/純檔名，等號兩側前後空白會被去掉。
- 一行格式不對（沒有 `==`、或 stage id 不是整數）會被跳過並印警告，不會讓
  `import dataset_health.config` 整個炸掉——這張表本來就是持續在填的
  施工中狀態。

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

## 一份 log 對應多個 stage，或一個 stage 有多份 log 怎麼辦？

目前設計是 1 stage : 1 檔案（跟 `dict[int, str]` 的形狀一致）。如果之後同一個
stage 需要合併多份 log，或同一份 log 要拆給多個 stage，這張純文字格式撐不住，
需要回頭改 `_load_stage_log_map()`（`dataset_health/config.py`）換更豐富的
格式（例如允許逗號分隔多檔，或改讀 YAML）——先不要為了這個目前用不到的情境
過度設計。
