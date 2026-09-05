# attack_patterns.py 偵測缺口 — 拿真實工具流量實測發現

> **狀態(2026-09-02 更新)**：缺口 1、缺口 2 已由 `log-analysis-core` 權威版本
> 修好，並透過 `sync/from-private` 同步進這個 repo、merge 進
> `feat/yc-dev_nginx`（見文末「✅ 修復驗證」）。修法比這份文件原本建議的更完整
> （缺口 2 除了裸數字 tautology，還加了括號/運算子算式的安全求值）。
> 用同一批真實資料重新驗證後，發現**修完之後還有殘留的違規**，而且殘留不是
> 隨機雜訊，是幾個完全沒被任何 pattern 涵蓋到的獨立技巧（`ORDER BY` 欄位數
> 枚舉、MySQL `SLEEP()`/`BENCHMARK()`、MSSQL `WAITFOR DELAY`、Oracle
> `DBMS_PIPE.RECEIVE_MESSAGE`）——這些記錄在文末「缺口 3（新發現）」一節，
> 是這次驗證新發現的，還沒有人修。
>
> **2026-09-04 更新**：用同樣的方法對 stage 5（Command Injection）、stage 6
> （LFI）跑了一次同樣的診斷，發現另外兩個缺口，記錄在「缺口 4」「缺口 5」
> 兩節——`has_command_injection` 97.1% 的殘留違規是同一類「literal-only
> regex 對不上 URL-encoded payload」問題（跟缺口 1/2 同一種病），而
> `has_file_inclusion` 的問題不一樣：它只認 PHP wrapper scheme，完全沒
> 設計來涵蓋這個 stage 實際收集的 traversal/絕對路徑 LFI，是 ground-truth
> 判準選錯特徵，不只是 regex 漏寫變形。這兩個都還沒有人修，一樣先記錄下來
> 交給權威版本維護者評估。
>
> 這份文件記錄的是 **`has_path_traversal` / `has_sql_injection` /
> `has_command_injection` / `has_file_inclusion` 這幾個 regex 本身的偵測
> 缺口**，不是 `dataset_health`（diversity 驗收模組）的 bug。
> `dataset_health/diversity.py` 忠實回報了「這批樣本不符合定義判準」——
> 問題出在 `attack_patterns.py` 的 pattern 對這些工具產生的常見變形有漏洞，
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

## 缺口 1：`has_path_traversal` 漏掉 `..%2F`（dot-dot + URL 編碼斜線）✅ 已修復

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

**建議方向**（原本未套用，現已由權威版本採用類似寫法）：把 `%2f`、`%5c`
（分別是編碼後的 `/`、`\`）也算進斜線變形。**權威版本實際採用的寫法**：

```python
PATH_TRAVERSAL_PAT = r"\.\.(?:/|\\|%2f|%5c)|%2e%2e"
```

跟這份文件原本建議的幾乎一樣，差別只是大小寫統一寫小寫、靠呼叫端
`re.IGNORECASE`/`case=False` 處理（兩處呼叫端都已確認是 case-insensitive），
不在 pattern 裡混用大小寫字元類別。驗證結果見文末「✅ 修復驗證」。

## 缺口 2：`has_sql_injection` 漏掉 sqlmap 常見的數字型 boolean-blind payload ✅ 已修復

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

**建議方向**（原本未套用，現已由權威版本採用，而且比這份文件原本建議的更
完整）：

```python
r"(?<![A-Za-z0-9_])\d+\s*(?:=|%3[dD])\s*\d+"
```

跟原本建議的差別：加了 `(?<![A-Za-z0-9_])` 排除左邊緊接字母/數字/底線的
情況，避免像 `item1=5`、`v1=2`、`q1=100` 這種「參數名稱剛好以數字結尾」
的正常 query string 被誤判成 `value=value` 型的 tautology——這正是原本這份
文件提到「取捨比缺口 1 大」的那個疑慮，權威版本用排除規則解決了，不是
放著不管。

**權威版本還多做了一件事，是這份文件完全沒設想到的**：純 regex 只能認
「裸數字緊鄰 `=`」，攻擊者只要在 `=` 前面加個括號（`(22+22)=44`）數字就不
再緊鄰 `=`，regex 直接抓不到。權威版本額外加了
`has_sql_tautology_expression()`：先用 regex 抓出 `=` 兩側的候選算式，再用
Python `ast` 模組手刻白名單 walker 安全求值（只允許數字常數、`+ - * /`
運算，其餘節點一律拒絕，不是對任意字串呼叫 `eval()`，不能被拿來當 RCE
跳板），兩側都能算出合法數值就判定為 tautology 探測。細節見
`dataset_health/attack_patterns.py` 該函式上方的大段註解。

驗證結果見下方「✅ 修復驗證」。

## ✅ 修復驗證（2026-09-02）

### 方法

修復透過 `sync/from-private`（同步私有 `log-analysis-core` repo 的偵測檔案）
進到這個 repo，再經 `git merge origin/compare/yc-compare_premerge_branch`
進到 `feat/yc-dev_nginx`。驗證方式：拿**完全同一批**真實 log
（`nginx/collected/nginx01_batch_sqlmap_sqli_001.log` 378 筆、
`nginx/collected/nginx01_batch_path_traversal_001.log` 120 筆——跟本文件
一開始發現缺口時用的是同一份檔案，不是重新收集），修復前後各跑一次
`python -m dataset_health.run_stage --stage 2` / `--stage 4`，用
`StageDiversityReport.defining_violations_total` 比對「不符合定義判準」的
筆數變化。

### 結果

| Stage | 特徵 | 修復前違規 | 修復後違規 | 下降 |
|---|---|---|---|---|
| 2（SQLi） | `has_sql_injection` | 259/378（68.5%） | **102/378（27.0%）** | −157 筆（−41.5 個百分點） |
| 4（路徑遍歷） | `has_path_traversal` | 105/120（87.5%） | **30/120（25.0%）** | −75 筆（−62.5 個百分點） |

兩個修復都確認有效，不是巧合或誤測——下面把修復後**剩下**的違規逐筆分類，
證明殘留不是隨機雜訊，而是可以清楚指出原因的東西。

### Stage 4 殘留的 30 筆：不是偵測缺口，是同一批次故意混了「非 traversal」的樣本

```
15 筆  /etc/passwd
15 筆  /backend/.env
```

這兩個 payload **完全沒有 `..` 或任何遍歷語法**，是直接嘗試存取敏感檔案，
跟 `has_path_traversal` 這個特徵的定義本來就無關（`collection_method.md`
描述這批次同時包含「直接存取」與「用 `../` 變形讀取」兩種 payload，見該檔
的 example payloads 清單）。這 30 筆 `PATH_TRAVERSAL_PAT` 判 0 是**正確
行為**，stage 4 的缺口 1 已經**完全修復**（剩餘違規率降到 0，這 25% 是
batch 組成問題，不是 regex 問題）。

附帶一提，兩個 payload 的 `accesses_sensitive_path` 結果不一樣（實測
`extract_stage_features()` 輸出確認過，不是用肉眼猜）：`/backend/.env`
會命中（`.env` 就在 sensitive path token 清單裡），但 **`/etc/passwd`
15 筆完全不會被任何一個 stage 1-12 的定義 flag 認領**——"etc"、"passwd"
都不在 sensitive path token 清單裡，本身也沒有遍歷語法。這 15 筆算是
「有攻擊意圖但目前沒有對應特徵可歸類」的資料，跟本文件的兩個 regex
缺口是不同性質的問題（那兩個是「pattern 沒涵蓋到某個變形」，這個是
「這個攻擊目標本身就不在任何現有特徵的偵測範圍內」），先記在這裡，不在
這次修復範圍內。

### 缺口 3（新發現）：stage 2 殘留的 102 筆，可以清楚拆成 6 類，其中 4 類是全新、目前完全沒被涵蓋的技巧

用 `defining_violations` 裡的 `url` 欄位逐筆分類（102 筆全部人工核對過，
不是抽樣）：

| 類別 | 筆數 | 佔殘留比例 | 說明 |
|---|---:|---:|---|
| `ORDER BY` 欄位數枚舉 | 48 | 47% | 例：`id=1) ORDER BY 1-- WJqL`、`id=1' ORDER BY 2163#` |
| MySQL `SLEEP()`/`BENCHMARK()` | 29 | 28% | 例：`id=1);SELECT SLEEP(5)#`（見下方原因說明） |
| Oracle `DBMS_PIPE.RECEIVE_MESSAGE` | 10 | 10% | 例：`id=1 AND 9288=DBMS_PIPE.RECEIVE_MESSAGE(CHR(86)\|\|CHR(83)\|\|CHR(79)\|\|CHR(122),5)` |
| MSSQL `WAITFOR DELAY` | 10 | 10% | 例：`id=1 WAITFOR DELAY '0:0:5'` |
| 純 baseline 探測（真的不是 SQLi） | 3 | 3% | 例：`id=1`、`id=6275`——sqlmap 正式打 payload 前的基準請求 |
| 特殊字元 fuzzing（無法歸類） | 2 | 2% | 例：`id=1))(.)'.,")"`、`id=1'PDjlVW<'">YGheEx`——測試應用程式對雜亂符號的反應，沒有可辨識的 SQL 語法結構 |

**前四類合計 97/102（95%）都是有明確 SQL 語法結構、只是目前完全沒有對應
pattern 的技巧**，不是模糊地帶：

- **`ORDER BY` 枚舉是目前最大宗、也最單純的缺口**（佔全部殘留違規的
  47%）：這是判斷 SELECT 語句欄位數最基本、幾乎每套自動化 SQLi 工具都會用
  的技巧，`SQL_PATTERNS` 目前完全沒有涵蓋任何形式的 `ORDER BY`。
- **`SLEEP()`/`BENCHMARK()` 沒被抓到，不是關鍵字沒寫對，是「原始字串
  vs. 解碼字串」的問題**：`SQL_PATTERNS` 裡本來就有 `sleep\(` 跟
  `benchmark\(` 兩個 pattern，但 sqlmap 預設會把 payload 裡的 `(`/`)`
  URL-encode 成 `%28`/`%29`，而 `has_sql_injection` 是直接對**原始、未解碼
  的 URL 字串**跑 regex（跟 `has_sql_tautology_expression()`
  一樣是對原始字串操作，只是 tautology 那個 pattern 設計時就沒有要求
  緊鄰的括號字元）。`SLEEP%285%29` 裡的關鍵字 `SLEEP` 是明碼、但緊接著的
  不是字面 `(` 而是 `%28`，所以 `sleep\(` 對不上。這意味著 `SQL_PATTERNS`
  裡任何要求緊鄰特定標點符號的 pattern（`sleep\(`、`benchmark\(`、
  `admin'--`、`--\s*$`、`#\s*$`、`;\s*--`）都可能有同樣的系統性問題，不只
  這一個——這次驗證只實際觀察到 `sleep\(`/`benchmark\(` 被繞過，其他幾個
  沒有在這批真實資料裡剛好被測到，但原理相通，值得一併檢視。
- **Oracle `DBMS_PIPE.RECEIVE_MESSAGE` 跟 MSSQL `WAITFOR DELAY`**：分別是
  Oracle 跟 MSSQL 資料庫特有的 time-based blind 技巧關鍵字，`SQL_PATTERNS`
  目前只涵蓋了 MySQL 的 `SLEEP`/`BENCHMARK`，對這兩套資料庫方言完全沒有
  對應 pattern（不是遇到編碼問題，是關鍵字本身就不在清單裡）。

**建議方向**（未套用，一樣留給權威版本維護者評估，這幾個牽涉到要不要擴大
偵測範圍、每加一個 pattern 都要重新評估 benign 流量誤判風險，取捨比缺口
1/2 都大，這裡不建議在沒有充分討論前直接動手）：

1. 加 `order\s+by` 這類 pattern（風險：`ORDER BY` 是完全合法的 SQL
   子句名稱，正常應用程式的除錯訊息、API 文件字串、甚至某些設計不良但合法
   的 API 直接把排序欄位當參數名傳（如 `?sort=name`）有機會提到這個詞，
   但**作為 URL query string 的值**出現「order by」字樣本身已經是很強的
   訊號，誤判機率預期比 tautology pattern 更低）。
2. 把 `sleep\(`/`benchmark\(` 這類要求緊鄰標點的 pattern，比照
   `has_sql_tautology_expression()` 的做法，改成也接受 `%28`/`%29`
   編碼形式，或先對整個 URL 做一次 `unquote()` 再跑全部 pattern（後者影響
   範圍更大，等於是整個偵測邏輯的輸入前處理方式改變，需要更謹慎評估對
   XSS/path traversal 那幾個 pattern 有沒有副作用）。
3. 加 `waitfor\s+delay` 與 `dbms_pipe`（或更廣的 `dbms_\w+\(`）涵蓋 MSSQL
   跟 Oracle 的 time-based blind 技巧。

## 缺口 4（新發現）：`has_command_injection` 幾乎完全偵測不到 URL-encoded 版本的 shell metacharacter

用 `nginx/collected/`（commix/ffuf 真打本機 nginx 產生的 stage 5 全部批次，
`cfg.STAGE_LOG_PATHS[5]`，合併後 1786 筆）跑 `dataset_health.run_stage --stage 5`，
`defining_violations` 顯示 **1783/1786（99.8%）** `has_command_injection=0`——
幾乎整個 stage 都不符合自己的定義判準。逐筆分類（1783 筆全部程式化分類，
不是抽樣）：

| 類別 | 筆數 | 佔比 | 說明 |
|---|---:|---:|---|
| URL-encoded shell metacharacter | 1732 | 97.1% | `;`→`%3B`、`|`→`%7C`、`&`→`%26`、`$(`→`%24%28`、`${`→`%24%7B`、`` ` ``→`%60` |
| PHP 程式碼執行函式呼叫 | 36 | 2.0% | `phpinfo()`/`exec()`/`eval()`/`print()`/`system()`，例：`test.print%28phpinfo%28%29%29` |
| 純換行注入 | 8 | 0.4% | `%0A`/`%0D%0A`，無任何運算子字元，例：`test%0Aid` |
| baseline 探測（真的不是攻擊） | 7 | 0.4% | `keyword=test`，commix 正式打 payload 前的基準請求 |

```python
CMD_PATTERNS = [
    r";.*ls", r";.*cat", r";.*rm", r";.*wget", r";.*curl",
    r"\|.*ls", r"&&.*ls", r"`.*`", r"\$\(", r"\$\{",
    r"/etc/passwd", r"/bin/bash", r"/bin/sh",
]
```

跟缺口 1（path traversal）、缺口 2（SQLi）是同一類問題：`CMD_PATTERNS` 只認
**字面**的 `;`/`|`/`&&`/`` ` ``/`$(`/`${`，commix 預設就會把 payload 裡的這些
shell metacharacter URL-encode（`%3B`/`%7C`/`%26`/`%60`/`%24%28`/`%24%7B`），
literal-only 的 regex 對編碼後的字串完全對不上。真實案例（URL 解碼後）：

| Payload（解碼後） | `has_command_injection` |
|---|---|
| `test;echo TJWJZH$((16+21))$(echo TJWJZH)TJWJZH` | ❌ False |
| `test&&echo TJWJZH$((12+54))$(echo TJWJZH)TJWJZH` | ❌ False |
| `test\|echo $((5308 + 5139))` | ❌ False |
| `test${IFS}id` | ❌ False |
| `test.print(phpinfo())` | ❌ False |

**這個缺口比缺口 1/2 更嚴重的地方**：就算把編碼問題修好，現有 pattern 對
`;`/`\|`/`&&` 三個都還**綁死只認 `ls` 這一個命令**（`;.*ls`、`\|.*ls`、
`&&.*ls`），但真實 commix 流量裡接在這些運算子後面的絕大多數是
`whoami`/`id`/`uname -a`/`ping`/`nslookup`/`sleep`/`echo`——這些完全不在白
名單內，就算補了編碼也一樣抓不到，屬於白名單本身太窄的獨立問題，跟編碼是
兩層缺口疊在一起。

**建議方向**（未套用，比照缺口 1/2 已修復的手法，一樣留給 `log-analysis-core`
權威版本維護者評估）：

1. 補上編碼變形，比照 `PATH_TRAVERSAL_PAT` 已經採用的 `%2f`/`%5c` 寫法：
   `;`→加 `%3b`、`\|`→加 `%7c`、`&`→加 `%26`（不是只有 `&&`，單一 `&` 背景
   執行也是常見技巧）、`` ` ``→加 `%60`、`\$\(`→加 `%24%28`、`\$\{`→加
   `%24%7b`。
2. 把 `;.*ls`/`\|.*ls`/`&&.*ls` 的命令白名單從只認 `ls` 擴大到至少涵蓋
   `whoami`/`id`/`uname`/`ping`/`nslookup`/`sleep`/`echo`（風險：命令名稱
   越通用，越可能在合法 query string 裡巧合出現，例如 `?q=echo` 這種正常
   搜尋詞，需要跟 SQL_PATTERNS 缺口 3 的 `order by` 一樣評估 benign 誤判
   風險，取捨可能比補編碼更大）。
3. 加 `phpinfo\(|exec\(|eval\(|print\(|system\(` 涵蓋 PHP 程式碼執行函式呼叫
   （同樣要考慮編碼變形 `%28`）。
4. 加一個不依賴特定運算子字元的「裸換行後緊跟常見命令」pattern，涵蓋
   `%0A`/`%0D%0A` 換行注入（風險最低——一般 query string 幾乎不會出現
   URL-encoded 換行字元本身）。

## 缺口 5：`has_file_inclusion` 只認 wrapper scheme，完全沒涵蓋 traversal 或絕對路徑 LFI（項目 1 已修復，項目 2 未修）

> **狀態(2026-09-04 更新)**：下面「跟缺口 1-4 不同的地方」列的三個項目裡，
> **項目 1（35 筆 traversal-style flag 不對）已經修好**——這個不是
> `attack_patterns.py` regex 的問題（那份檔案的權威版本在 `log-analysis-core`，
> 本地改了會被蓋掉，見文件開頭說明），是 `dataset_health/config.py` 的
> `DEFINING_PREDICATE` 選錯判準這個**本地、非同步檔案**的問題，本地改是真的
> 有效的。改法：把 stage 6 的 `DEFINING_FLAG` 從單一 `has_file_inclusion`
> 改成 `DEFINING_PREDICATE` 的複合 `"any"` 群組（`has_file_inclusion==1 OR
> has_path_traversal==1`），連帶在 `dataset_health/diversity.py` 的
> `_eval_condition`/`_flatten_leaf_conditions` 加了 OR 群組支援（原本
> `DEFINING_PREDICATE` 的條件 list 只有 AND 語意）。**項目 2（890 筆絕對路徑
> LFI）仍未修**——這個真的需要新特徵，不是判準能解的，維持原樣待評估。

## 缺口 5（新發現）：`has_file_inclusion` 只認 wrapper scheme，完全沒涵蓋 traversal 或絕對路徑 LFI

同樣用 `nginx/collected/` + `nginx/LFI_method_record/`（真實瀏覽器手動 payload +
wfuzz 真打本機 nginx 產生的 stage 6 全部批次，合併後 974 筆）跑
`dataset_health.run_stage --stage 6`，`defining_violations` 顯示
**961/974（98.7%）** `has_file_inclusion=0`。逐筆分類：

| 類別 | 筆數 | 佔比 | 說明 |
|---|---:|---:|---|
| 絕對路徑 LFI（無 `../`、無 wrapper scheme） | 890 | 92.6% | 例：`file=/etc/passwd`、`file=/etc/aliases`、`file=/etc/apache2/httpd.conf` |
| traversal-style LFI（`has_path_traversal=1`） | 35 | 3.6% | 例：`file=../../etc/passwd`、`file=..%5C..%5Cwindows%5Cwin.ini` |
| 空 `file=` 參數（wfuzz 過程雜訊） | 27 | 2.8% | `file=` 值本身是空字串，不是攻擊 payload |
| `/favicon.ico`（瀏覽器自動請求，雜訊） | 7 | 0.7% | 手動瀏覽器 payload 那批混進的瀏覽器自動行為 |
| 正常附件檔名（baseline 對照） | 2 | 0.2% | `file=poster.txt`——真實存在的附件，用來對照攻擊 payload 跟正常請求的回應差異 |

```python
FILE_INCLUSION_PAT = r"file://|php://|data://|expect://|input://"
```

這個 pattern 設計上就只認 PHP wrapper scheme（`php://filter`、`data://`、
`expect://` 這類 PHP 特有的 stream wrapper 技巧），完全沒有涵蓋**古典
directory traversal 讀檔**（`../../etc/passwd`）跟**直接絕對路徑讀檔**
（`/etc/passwd`，連 `../` 都不用，因為應用程式本身沒有做路徑白名單）——但
`LFI_method_record/lfi_sink_traversal_wordlist.txt` 這份收集用的 wordlist
自己取名就叫 "traversal"，`collection_method.md` 也把這些批次歸在
「stage 6 LFI」底下，可見這個 stage 收集時設定的範圍本來就包含 traversal
跟絕對路徑兩種手法，不是只有 wrapper scheme——`DEFINING_FLAG` 選
`has_file_inclusion` 這一個窄定義的 flag 來驗證整個 stage，範圍對不起來。

**跟缺口 1-4 不同的地方**：這不是單純的「pattern 漏了一個編碼變形」，是
**這個 stage 的 ground-truth 判準選錯特徵**，需要的修法也不只是加
regex 變形：

1. **35 筆 traversal-style ✅ 已修復**：已經有 `has_path_traversal` 認領，這
   35 筆 `has_file_inclusion=0` 是符合這個 flag 窄定義下的正確行為（跟缺口 1
   驗證時 stage 4 殘留的 `/etc/passwd`/`/backend/.env` 那 30 筆是同一種
   「flag 定義本來就沒有要涵蓋這種 payload」的情況）。修法：把 stage 6 的
   `DEFINING_PREDICATE` 從單一 flag 改成複合 `"any"` 判準
   （`has_file_inclusion==1 OR has_path_traversal==1`）——這牽涉的是
   `dataset_health/config.py`/`diversity.py`，不是 `attack_patterns.py`
   regex，而且 `config.py`/`diversity.py` 是本地、非同步檔案（不像
   `attack_patterns.py` 那樣改了會被 `sync/from-private` 蓋掉），本地改
   真的有效，已經改完。原本考慮過再加一個「AND 命中 `file=` 類參數」的
   條件避免誤收其他 endpoint 的 traversal payload，但 stage 6 目前所有
   批次本來就都是打同一個 `/api/events/1/attachment?file=` sink 收集的，
   這個額外條件目前用不到，先不加，需要時再補。驗證：修復前
   `defining_violations_total`＝961/974，修復後＝**926/974**
   （−35，跟分類數字完全對上）；`Diversity_stage` 本身沒變（stage 6 的
   `SUPPORT_FEATURES` 不含 `has_file_inclusion`/`has_path_traversal`，這個
   修法解決的是 ground-truth 判準的準確度，不是這裡的多元度分數，兩者是
   獨立的兩件事）。單元測試見
   `tests/unit/test_diversity.py::test_stage_diversity_stage6_any_predicate_*`
   三個新測試。
2. **890 筆絕對路徑 LFI 是真正的偵測空白**：純 regex 沒辦法只憑
   `/etc/passwd` 這種字串本身判斷「這是攻擊」還是「這是正常參數值」，需要
   類似缺口 3 討論 `order by` 時的取捨——用已知敏感路徑前綴當訊號
   （`/etc/`、`/proc/`、`/root/`、`/var/log/`、`/windows/`、`c:\\` 等），
   誤判風險比單純加編碼變形更高，需要團隊先拍板哪些前綴要收，這裡不建議
   在沒有討論前直接動手。
3. **36 筆雜訊（空參數/favicon/正常附件）不需要修 regex**：這是收集批次本身
   混進的非攻擊請求，屬於 `collection_method.md` 該處理的資料清理問題，
   不是 `attack_patterns.py` 的偵測缺口。

## 已知不受影響的部分

`dataset_health` 這邊自己的邏輯是對的：`_defining_violations()`
正確回報了「這批樣本不符合定義判準」，`defining_violations` 明細
（`log_source`/`log_line_no`/`url`/...）也正確地讓人能回頭核對是哪一行——
問題全部出在 `attack_patterns.py` 的 pattern 覆蓋率，不是 diversity
驗收邏輯本身。這次的修復驗證（拿同一批 102/30 筆殘留違規逐筆分類）也是
直接靠 `defining_violations` 的明細資料做的，沒有另外寫工具——這條診斷路徑
本身在這次驗證裡又被證明一次是可靠的。

## 時間軸

| 日期 | 事件 |
|---|---|
| （本文件初版） | 用 `nginx/collected/` 真實資料跑 `dataset_health`，發現缺口 1、2，寫成本文件 |
| 2026-09-02 | `log-analysis-core` 私有 repo 修好缺口 1、2（修法比本文件建議更完整），透過 `sync/from-private` → `git merge origin/compare/yc-compare_premerge_branch` 進到 `feat/yc-dev_nginx` |
| 2026-09-02 | 用同一批真實資料重新驗證：stage 2 違規率 68.5%→27.0%、stage 4 違規率 87.5%→25.0%（stage 4 剩餘 25% 確認是 batch 組成問題，非 regex 缺口）；逐筆分類 stage 2 殘留的 102 筆，發現缺口 3（`ORDER BY` 枚舉／`SLEEP`＋`BENCHMARK` 編碼繞過／`WAITFOR DELAY`／`DBMS_PIPE`，見上方「缺口 3」一節） |
| 2026-09-04 | 對 stage 5、stage 6 跑同樣診斷：`has_command_injection` 違規率 99.8%（1783/1786），逐筆分類發現 97.1% 是 URL-encoded shell metacharacter（缺口 4）；`has_file_inclusion` 違規率 98.7%（961/974），逐筆分類發現 92.6% 是絕對路徑 LFI、3.6% 是已被 `has_path_traversal` 認領的 traversal-style（缺口 5，ground-truth 判準選錯特徵，不是單純 regex 漏寫） |
| 2026-09-04 | 修好缺口 5 項目 1：`config.py`/`diversity.py` 是本地檔案，不用等 `log-analysis-core`，把 stage 6 的 `DEFINING_PREDICATE` 改成 `has_file_inclusion==1 OR has_path_traversal==1` 複合判準（`diversity.py` 新增 `"any"` OR 群組支援），違規數 961→926/974（−35，即 traversal-style 那批）。缺口 4 跟缺口 5 項目 2（絕對路徑 LFI）都還要等 `attack_patterns.py`/`feature_engineering.py` 的權威版本更新，本地不動 |
