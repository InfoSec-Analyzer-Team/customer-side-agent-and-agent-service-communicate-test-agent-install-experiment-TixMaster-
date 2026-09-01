# attack_patterns.py 偵測缺口 — 拿真實工具流量實測發現

> 這份文件記錄的是 **`has_path_traversal` / `has_sql_injection` 這兩個 regex
> 本身的偵測缺口**，不是 `dataset_health`（diversity 驗收模組）的 bug。
> `dataset_health/diversity.py` 忠實回報了「這批樣本不符合定義判準」——
> 問題出在 `attack_patterns.py` 的 pattern 對這兩種工具產生的常見變形有漏洞，
> 才會讓大量真實攻擊流量被判成 `has_*=0`。
>
> `attack_patterns.py` 的權威版本在 `log-analysis-core` repo 的
> `machine_learning_models/attack_patterns.py`；這裡（TixMaster / 靶機端）
> 的 `dataset_health/attack_patterns.py`、`Verify_doc/attack_patterns.py`
> 都只是手動複製過來的拷貝（見規格 §4），改這裡不會真的修到東西——這份文件
> 只是把發現記下來，交給那份權威版本的維護者評估要不要改。

## 怎麼發現的

拿 `nginx/collected/`（真實攻擊工具打本機 nginx 產生的 log，見
`collection_method.md`）跑 `dataset_health.run_stage`，用
`StageDiversityReport.defining_violations` 回頭核對「不符合定義判準」的
樣本，逐筆看實際 payload 才發現的——這兩個缺口在只用少量手寫測試案例時
不會浮現，因為手寫案例通常照著 pattern 的邏輯去寫，剛好會命中。

## 缺口 1：`has_path_traversal` 漏掉 `..%2F`（dot-dot + URL 編碼斜線）

```python
PATH_TRAVERSAL_PAT = r"\.\./|\.\.\\|%2e%2e"
```

只認字面的 `../`、`..\`，或是 `%2e%2e`（dot 本身被編碼）。**沒有涵蓋
「dot 是字面值、只有斜線被編碼」這個最常見的變形**：`..%2F`、`..%5C`。

真實案例(`nginx/collected/nginx01_batch_path_traversal_001.log`，PowerShell
手動送出的 path traversal payload)：

| Payload | `has_path_traversal` |
|---|---|
| `/..%2F..%2F..%2Fetc%2Fpasswd` | ❌ False |
| `/download?file=..%2F..%2F..%2Fetc%2Fpasswd` | ❌ False |
| `/download?file=..%5C..%5Cwindows%5Cwin.ini` | ❌ False |
| `/view?file=..%2F..%2F..%2Fetc%2Fshadow` | ❌ False |
| `/images/%2e%2e/%2e%2e/%2e%2e/etc/passwd`(dot 也編碼) | ✅ True |

**影響**：這個批次(120 筆，`.meta.txt` 標 `label: BAHAYA`)裡
**105/120（87.5%）** `has_path_traversal=0`——絕大多數明確的路徑遍歷攻擊
在這個特徵上完全偵測不到。

**建議方向**（未套用，留給權威版本維護者決定）：把 `%2[fF]`、`%5[cC]`
（分別是編碼後的 `/`、`\`）也算進斜線變形：

```python
PATH_TRAVERSAL_PAT = r"\.\.(?:/|\\|%2[fF]|%5[cC])|%2e%2e"
```

需要注意：改寬鬆的同時也要留意有沒有引入誤判（例如合法檔名剛好含
`..%2f` 字面文字的極端情境，機率很低但理論上存在）。

## 缺口 2：`has_sql_injection` 漏掉 sqlmap 常見的數字型 boolean-blind payload

```python
SQL_PATTERNS = [
    r"union.*select", r"select.*from", r"insert.*into", r"delete.*from",
    r"drop.*table", r"'.*or.*'", r"1\s*=\s*1", r"admin'--",
    r"benchmark\(", r"sleep\(", r"--\s*$", r"#\s*$", r";\s*--",
]
```

`1\s*=\s*1` 只認字面的 `1=1`，**沒有涵蓋 sqlmap 實際測試時常用的「任意數字
=任意數字」**（sqlmap 故意用隨機數字而不是固定的 `1=1`，避免被最簡單的
WAF 規則擋下——這正是它被規避掉的原因）。

真實案例(`nginx/collected/nginx01_batch_sqlmap_sqli_001.log`，
`sqlmap -u ".../api/events?id=1" --batch --level=2 --risk=1`)：

| Payload（URL 解碼後） | `has_sql_injection` |
|---|---|
| `id=1) AND 7973=2007 AND (8113=8113` | ❌ False |
| `id=1 AND 7110=9042` | ❌ False |
| `id=1 AND 6218=3524-- hJSL` | ❌ False |
| `id=1' AND 5206=9476 AND 'KyHp'='KyHp` | ❌ False |

**影響**：這個批次(378 筆，`.meta.txt` 標 `label: BAHAYA`)裡
**259/378（68.5%）** `has_sql_injection=0`。

**建議方向**（未套用，留給權威版本維護者決定，這個比缺口 1 更需要斟酌）：
加一個通用的「數字 (=|%3D) 數字」pattern，例如
`r"\d+\s*(?:=|%3[dD])\s*\d+"`。**這個改動的取捨比缺口 1 大**：字面
`\d+=\d+` 在一般 query string 裡不算罕見（例如 `page=2`、`v=1` 這類參數
剛好前後都是數字時不會誤觸，因為那是 `key=value` 不是 `value=value`，
但如果之後要收 stage 12「異常 URL 結構」那種大量參數的樣本，或正常
API 剛好有 `from=1&to=2` 這種語意，還是要留意會不會拉高 benign 流量的
`has_sql_injection` 誤判率——這是為什麼沒有直接套用，需要團隊在權威版本
那邊評估過再改。

## 已知不受影響的部分

`dataset_health` 這邊自己的邏輯是對的：`_defining_violations()`
正確回報了「這批樣本不符合定義判準」，`defining_violations` 明細
（`log_source`/`log_line_no`/`url`/...）也正確地讓人能回頭核對是哪一行——
問題全部出在 `attack_patterns.py` 的 pattern 覆蓋率，不是 diversity
驗收邏輯本身。
