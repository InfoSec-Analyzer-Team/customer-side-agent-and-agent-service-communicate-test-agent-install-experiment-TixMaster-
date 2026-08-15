# DIVERSITY_SPEC — Per-stage 多元度驗收模組施作規格
> 這是per state LOG驗證的施作文件，目的是確保在靶機上打的log能夠得到均衡的特徵，使模型不易學到shortcut 與工具設定。
> 本文件定義 `dataset_health/diversity.py` 與 `dataset_health/config.py` 的理論依據、
公式、config schema、模組介面契約,以及 CI 整合方式。目標:讓實作者不必回頭問「這個
分數為什麼這樣算」就能直接寫出正確、可重現的程式,並讓 reviewer / 口試委員能追溯每個
公式的文獻出處。
> 
> 
> 適用範圍:**只涵蓋 per-stage 多元度(diversity)這一塊**。confounder 作弊模型、MI、
> Overlap、JS-based realism 屬於 whole-dataset 驗收,另立 `confounder.py` / `realism.py`
> 規格,本文件只在介面邊界處引用。
> 

---

## 0. 一句話摘要

每收完一個攻擊 stage,對「這個 stage 應該要有變異的支撐特徵」計算分佈散度(類別型用標準化
熵、數值型用四分位離散係數)與類別涵蓋率,合成一個 `Diversity_stage ∈ [0,1]` 分數,並輸出
「缺哪些取值」的可行動診斷。此分數是 G(泛化模型導向)總分的主要成分,用來在進入下一個
stage 前,判斷這批攻擊樣本是否夠雜、有沒有淪為單一工具指紋。

---

## 1. 為什麼要做 per-stage 多元度(理論動機)

### 1.1 核心風險:shortcut learning / 工具指紋

深度與傳統模型都會傾向學「捷徑」——在訓練分佈裡有預測力、但換個分佈就失效的表面相關特徵
(Geirhos et al., 2020, *Shortcut Learning in Deep Neural Networks*, Nature Machine
Intelligence)。經典例子是「草地 → 牛」:模型用背景而非物體本身做判斷,一旦牛出現在非典型
背景就失敗。對應到我們的處境,風險是模型學到「**這個工具的 User-Agent → 攻擊**」而非「**這個
URL pattern → 攻擊**」。

這不是假想。CICIDS2017 被重新檢視時,Engelen et al.(2021)明確指出:資料集**每個攻擊類別
的內部多樣性未被討論**,不確定攻擊工具是用固定設定還是變動參數,而用單一設定模擬的攻擊軌跡
訓練出的 NIDS,可能無法類化到其他設定。我們自建靶機用固定幾支工具(curl / sqlmap / nikto)
打,面臨的正是同一個問題。差別在於:**我們主動量測它**。per-stage 多元度分數就是這個量測。

### 1.2 為什麼「排除該 stage 的定義 flag」

stage 2 的樣本 `has_sql_injection` 幾乎全為 1(那是這個 stage 的定義)。把它列進多元度評分
只會拉低分數且沒有意義——我們不希望 SQLi 樣本的「是不是 SQLi」有變異。我們希望的是:在
「都是 SQLi」的前提下,**承載這些 payload 的 UA、HTTP 方法、URL 長度/結構夠雜**,這樣模型
才不能靠「UA=sqlmap」或「長度=某固定值」作弊。因此多元度只評**支撐特徵(support features)**,
不評定義 flag。

### 1.3 為什麼熵不夠、還要涵蓋率

標準化熵回答「散不散」,但兩批資料可以熵相近卻缺不同的取值。涵蓋率(coverage)回答「缺哪個」,
而且直接可行動——報告能寫出「`os_type` 缺 android / ios / mac,請補手機與 mac UA」。這正對應
到你們最擔心的「手機流量缺口」「少數瀏覽器(DuckDuckGo 等)沒收集到」。兩個指標互補,都算。

### 1.4 設計原則:一律量測 pre-encoding 的原始特徵,不吃既有的編碼邏輯

多元度監管的對象是「log 本身多不多樣」,不是「某個已訓練模型看到的碼多不多樣」——這兩件事
不能混。已存在的編碼邏輯(不管是哪種形式)是**為了訓練模型而存在**,會受該次訓練用的資料切分、
fit 順序、甚至該模型當下版本影響;拿它來量測多樣性,量到的是模型的偏誤,不是資料的偏誤。因此
`diversity.py` 的所有輸入一律是 `create_all_features()` 輸出的原始特徵(數值型是最終值,類別型
是 encode **之前**的原始字串/整數),完全不經過、也不 import 任何模型的編碼器或前處理管線。
細節與具體案例見 §3.5、§3.6、§4。

---

## 2. 公式定義

以下所有符號:`f` 表示一個特徵,`stage` 表示當前 stage 的樣本集合。

### 2.1 標準化 Shannon 熵(類別型特徵)

```
             -  Σ_i  p_i · ln(p_i)
H_norm(f) = ───────────────────────
                   ln(N_f)
```

- `p_i`:特徵 `f` 第 i 個取值在 stage 樣本中的觀察比例,只對 `p_i > 0` 的取值加總。
- `N_f`:**理論取值數**(見 §3.2),**不是觀察到的 unique 數**。
- 值域 `[0, 1]`:0 = 所有質量集中在單一取值(死特徵);1 = 在全部 `N_f` 個理論取值上均勻分佈。
- `N_f = 1` 時定義為 0(無變異空間)。

> ⚠️ **最容易寫錯的地方**:分母若用「觀察到的 unique 數」,任何資料都會顯得均勻(因為只跟
自己比),指標失去意義。**分母一律用理論基數**,寫死在 config。
> 

理論依據:Shannon 熵是資訊理論中衡量分佈均勻程度的標準量(Cover & Thomas, *Elements of
Information Theory*)。除以 `ln(N_f)` 做標準化,使不同基數的特徵彼此可比。

### 2.2 類別涵蓋率(類別型特徵)

```
Cov(f) = | observed(f) ∩ expected(f) |  /  | expected(f) |
missing(f) = expected(f) \ observed(f)
```

- `expected(f)`:該特徵理論上該出現的取值集合(見 §3.2)。
- 回傳 `Cov(f) ∈ [0,1]` 與 `missing(f)`(缺漏集合)。`missing` 是報告可行動診斷的來源。

### 2.3 四分位離散係數 QCD(數值型特徵)

```
        Q3(f) − Q1(f)
QCD(f) = ─────────────       (若 Q3+Q1 > 0,否則 0)
        Q3(f) + Q1(f)
```

- 對非負特徵值域為 `[0,1]`。
- 選 QCD 而非「(P95−P5)/P50」的理由:後者在 **中位數為 0** 時發散,而 `url_param_count`、
`url_encoding_count` 這類特徵超過半數樣本為 0,中位數常為 0。QCD 用 `Q3+Q1` 當分母,只有在
超過 75% 樣本為 0(Q1=Q3=0)時才回 0,而那個 0 正確反映「無離散」。
- QCD 對離群值穩健,但**抓不到尾巴**,因此另設尾部旗標(§2.4)。

### 2.4 尾部涵蓋旗標(數值型,歸屬 realism 側,不進 diversity)

```
tail_reach(f) = ( stage 中 f 超過 baseline 之 P95(f) 的樣本數 ) / ( stage 樣本數 )
```

- 衡量「這批有沒有觸及分佈尾巴」(超長 UA、超長 URL)。
- **此旗標不併入 `Diversity_stage`**,因為它需要外部 baseline(印尼真實 log / CSIC),屬於
realism 評估。放這裡只是提醒:數值型特徵除了「散度」還要看「尾巴」,兩者分開報。

### 2.5 stage 多元度總分

```
                Σ_{f∈F}  w_f · d(f)
Diversity_stage = ──────────────────
                    Σ_{f∈F}  w_f
```

- `F`:該 stage 的**支撐特徵集**(§3.1),**排除定義 flag**。
- `d(f)`:類別型取 `H_norm(f)`;數值型取 `QCD(f)`。
- `w_f`:per-stage 權重(config,預設全 1)。
- 涵蓋率 `Cov(f)` 不直接進總分,而是作為獨立的「及格門檻」與診斷輸出(§7)。混進總分會讓
「散度低但涵蓋齊」與「散度高但缺類別」互相抵銷,失去可行動性。

---

## 3. `config.py` schema

config 是唯一事實來源。`diversity.py` 不得硬編任何 stage 專屬常數。

### 3.1 每個 stage 的支撐特徵清單

| Stage | 攻擊項目 | 定義 flag(排除) | 支撐特徵集 F(評多元度) | 型態備註 |
| --- | --- | --- | --- | --- |
| 1 | 敏感路徑 | `accesses_sensitive_path` | `os_type`, `ua_length`, `request_method`, `url_depth`, `url_length`, `referrer_type` | 標準 |
| 2 | SQLi | `has_sql_injection` | `os_type`, `ua_length`, `url_length`, `url_special_chars`, `url_param_count`, `request_method`, `url_encoding_count` | 標準 |
| 3 | XSS | `has_xss` | `url_special_chars`, `url_length`, `ua_length`, `url_encoding_count`, `os_type`, `request_method` | 標準 |
| 4 | 路徑遍歷 | `has_path_traversal` | `url_depth`, `url_length`, `url_encoding_count`, `os_type`, `ua_length`, `has_double_encoding` | 標準 |
| 5 | 命令注入 | `has_command_injection` | `url_length`, `url_special_chars`, `os_type`, `ua_length`, `request_method`, `url_param_count` | 標準 |
| 6 | 檔案包含 | `has_file_inclusion` | `url_length`, `url_special_chars`, `os_type`, `ua_length`, `url_encoding_count` | 標準 |
| 7 | 雙重編碼 | `has_double_encoding` | `url_encoding_count`, `url_length`, `os_type`, `ua_length` | 常與 base 攻擊並存 |
| 8 | URL 編碼變形 | *(數值門檻:`url_encoding_count > 0`)* | `url_length`, `url_special_chars`, `os_type`, `ua_length` | 定義為數值,見 §3.4 |
| 9 | 特殊字元密集 | `has_xss` +`url_special_chars`(數值) | `url_length`, `os_type`, `ua_length`, `url_encoding_count` | 複合定義 |
| 10 | UA 多樣性 | *(無單一 flag)* | `os_type`, `ua_length`, `is_bot`, `referrer_type`, `request_method` | 目標即多樣性,見 §3.3 |
| 11 | 異常 HTTP 方法 | `request_method` | `request_method`, `url_length`, `os_type`, `ua_length` | ⚠️ 見 §3.5 |
| 12 | 異常 URL 結構 | *(無單一 flag)* | `url_length`, `url_depth`, `url_param_count`, `url_special_chars`, `os_type`, `ua_length` | 目標即結構變異,見 §3.3 |

> **stage 10 / 12 是「目標即多樣性」型**:它們沒有一個該恆為 1 的定義 flag,反而是「讓
`os_type`/`ua_length`(stage 10)或 `url_*` 結構(stage 12)盡量散」本身就是收集目標。這類
stage 的 `Diversity_stage` 直接衡量它自己的成敗,是最單純的用法。
> 

### 3.2 類別型特徵的理論基數與期望取值

| 特徵 | `N_f`(理論基數) | `expected(f)` | 依據 |
| --- | --- | --- | --- |
| `os_type` | 8 | {0,1,2,3,4,5,6,7} | `_browser_features` unknown/win/android/ios/linux/mac/bot/other |
| `referrer_type` | 6 | {0,1,2,3,4,5} | none/local/ip/search/social/external |
| `url_file_type` | 6 | {0,1,2,3,4,5} | none/script/image/asset/document/other |
| `request_method` | 8(團隊決策,見 §3.5) | {"GET","POST","PUT","DELETE","OPTIONS","TRACE","PATCH","HEAD"} | ⚠️ 讀原始字串,不要吃任何模型的 LabelEncoder 輸出,見 §3.5 |
| `request_version` | 3 | {"HTTP/1.0","HTTP/1.1","HTTP/2.0"} | ⚠️ 讀原始字串,理由同 §3.5 |
| `ip_type` | 7 | {"public","private_class_a","private_class_b","private_class_c","loopback","invalid","unknown"} | ⚠️ 讀原始字串,不是壓平後的整數,見 §3.6 |
| `status_category` | 6 | {0,1,2,3,4,5} | 0 與百位 1–5 |
| `time_period` | 4 | {0,1,2,3} | night/morning/afternoon/evening |
| `day_of_week` | 7 | {0..6} | 週一–週日 |
| `local_day_of_week` | 7 | {0..6} | 同上,local 版 |
| `hour` / `local_hour` | 24 | {0..23} | — |
| `is_bot` | 2 | {0,1} | — |
| `is_odd_hour` / `local_is_odd_hour` | 2 | {0,1} | — |
| `is_error_status` | 2 | {0,1} | — |

### 3.3 數值型特徵清單

`url_length`, `url_depth`, `url_param_count`, `url_special_chars`, `url_encoding_count`,
`ua_length`, `referrer_length`, `log_size`。以 QCD 計散度;尾部旗標需 baseline。

### 3.4 數值定義門檻(stage 8 等)

部分 stage 的「定義」不是 0/1 flag 而是數值條件(stage 8 = `url_encoding_count > 0`)。config
用一個可選欄位 `defining_predicate` 描述,`diversity.py` 用它來(a)驗證這批樣本確實符合定義、
(b)把被當定義用的數值特徵排除在支撐集之外。

### 3.5 ⚠️ `request_method` / `request_version` 沒有共用、穩定的 encode(影響 stage 11)

**先更正一個對現況的誤判**:`pipeline_utils.py` 裡沒有 `_METHOD_ENCODE` 這種寫死的 dict——
`to_ml_payload()`(`processing/pipeline_utils.py`)只是照 `ML_API_ALLOWED_FIELDS` 白名單過濾欄位、
原樣傳遞,完全不做任何 encode。真正把 `request_method`(以及 `request_version`、`ip_type`)轉成
整數的地方,是**各模型自己的** `prepare_features()`(`rf_model/model.py`、`dt_model/model.py`
等,介面一致):對 `feature_engineering.CATEGORICAL_FEATURES` 裡的每一欄,**各模型各自 fit 一份
`sklearn.LabelEncoder`**(存在該模型的 `self.feature_encoders[col]`,序列化進 joblib),fit 時看
到什麼值就給什麼碼,訓練時未出現的值在推論時 fallback 成 **`-1`**(`le.transform(...) if x in
le.classes_ else -1`)。

這跟原本以為的缺陷不一樣,但問題一樣真實,而且是**兩層**:

1. **同一個原始值在不同模型的 encoded CSV 裡碼不同**——因為每個模型各自 fit,沒有共用、跨模型
一致的映射表。這代表**不存在一份「已編碼好的權威 CSV」**可供 `diversity.py` 直接讀(§4 原本假設
`pipeline_utils.to_ml_payload` 的輸出就是這份 CSV,但那個函式根本不編碼——這個假設本身要修,見
§4)。
2. **未知值 fallback 是 `-1`,不是退回某個已知碼**,所以不會出現「與 GET 同值、無法區分」的情況;
但如果 stage 11 打的 DELETE/OPTIONS/TRACE/PATCH 從未出現在任何模型的訓練集裡,它們會**全部塌
成同一個 `-1`**——彼此之間仍然無法區分(雖然能跟 GET/POST/PUT 分開),`request_method` 的
`H_norm` 一樣會假性偏低。

   **`Diversity_stage` 分數本身低不是問題**——如果正常流量本來就幾乎只有 GET/POST,`request_method`
   熵低是資料的真實樣貌,不需要硬拉高。真正重要的是 warnings 要講清楚**低分的原因是哪一種**,
   因為兩種原因需要的動作完全不同:
   - **原因 A(真實稀疏)**:raw log 裡的 `request_method` 真的就只有 GET/POST 這幾種——這是
     忠實反映流量,診斷應該直接說「stage 11 目前僅涵蓋 {GET,POST},缺 DELETE/OPTIONS/TRACE/PATCH」,
     交給團隊決定要不要補打這些方法。
   - **原因 B(量測工具的假象)**:如果 diversity 模組不小心接到了某個已訓練模型的 `feature_encoders`
     而不是 §1.4 要求的原始字串,分數低可能只是「這個特定模型的訓練集剛好沒看過這些值,被強制
     壓成同一個 `-1`」——這種低分是量測本身的偽陽性,不代表 log 真的缺多樣性。
   `diversity.py` 只要老實照 §1.4/§4 的契約走(讀 `create_all_features()` 的原始輸出),就只會
   遇到原因 A,不會遇到原因 B——這正是為什麼輸入契約要卡死在原始字串,而不是隨便一個「看起來
   已經是特徵 CSV」的來源。

**結論,不是「要不要改 encode dict」,而是架構層面的決定:**

`diversity.py` 完全不應該吃任何模型的 `feature_encoders` 輸出。應該讀
`feature_engineering.create_all_features()` 產生的**原始字串**(`"DELETE"`、`"HTTP/1.1"` 這種,
LabelEncoding 之前),對照 §3.2 的 `expected(f)` 字串集合算熵與涵蓋率。這樣一來:

- 不受任何單一模型訓練集內容影響,涵蓋率診斷也能直接印可讀字串(而非「碼 3 缺漏」這種要查表
才懂的訊息)。
- `expected(f)` 需要團隊先拍板 `request_method` 的理論集合是否含 HEAD(見 §3.2 已列
8 個候選),因為這不是程式碼決定的,是攻擊腳本要不要打到那些方法的收集範圍問題。

`create_all_features()` 目前的輸出本身不受 stage 11 影響、沒有塌縮問題——塌縮只發生在「送進某個
已訓練模型的 `feature_encoders` 之後」,而 diversity 模組原本就不該碰那一步。

### 3.6 ⚠️ `ip_type` 沒有壓平,但一樣不能吃 model 的 encode(影響涵蓋率解讀)

同樣先更正:沒有 `_IP_TYPE_ENCODE` 這個 dict。`ip_type` 由
`feature_engineering.classify_ip_type()`(`machine_learning_models/feature_engineering.py`)產生,
回傳 **7 個獨立字串類別**:`public` / `private_class_a` / `private_class_b` / `private_class_c` /
`loopback` / `invalid` / `unknown`——不是「只有 3 個有效值」。之後跟 `request_method` 一樣被列進
`CATEGORICAL_FEATURES`,交給**各模型各自 fit** 的 `LabelEncoder`(§3.5 所述機制)才變成整數,
所以「多數落在同一碼」這件事,是「某個特定模型的訓練集裡 `private_class_b`(如 Docker
`172.20.x`)樣本少,LabelEncoder 分配到的碼恰好排序在前面」造成的**表象**,不是壓平,而且每個
模型的表象可能還不一樣。

**處理方式與 §3.5 一致**:`diversity.py` 讀 `create_all_features()` 輸出的原始字串
(`"private_class_b"` 這種),對照 §3.2 的 7 類 `expected(f)` 算涵蓋率與熵,完全不經過任何模型的
`feature_encoders`。這樣「Docker 內網樣本多、真實 public IP 樣本少」這種涵蓋率缺口才會如實反映
在報告裡,而不是被特定模型的碼分配方式帶偏。`ip_type` 應正常列入需要它的 stage 支撐集(哪些
stage 用得到,由 §3.1 決定),不必因為以為的「encode 技術債」而預先排除。

### 3.7 其他 config 欄位

```python
MIN_SAMPLES = 200          # 低於此,熵/QCD 標「僅供參考」
DEFINING_FLAG   = { stage_id: feature_name | None }
SUPPORT_FEATURES= { stage_id: [feature, ...] }
FEATURE_TYPE    = { feature: "categorical" | "numeric" }
CARDINALITY     = { categorical_feature: N_f }
EXPECTED_VALUES = { categorical_feature: [values...] }
STAGE_WEIGHTS   = { stage_id: { feature: w_f } }   # 預設全 1
APPLY_TOOL_PENALTY = { stage_id: bool }            # 供 fingerprint.py,benign stage 為 False
STAGE_LOG_PATHS = { stage_id: "path/glob" }        # ⚠️ 待團隊填,見下方說明
# 以下欄位供後續 whole-dataset 模組共用,先在此集中定義避免散落:
CONFOUNDER_FEATURES = [...]   # ip_*, hour, day_of_week, is_odd_hour, time_period, os_type, is_bot, ua_length, local_*
CONTENT_FEATURES    = [...]   # has_*, url_special_chars, url_encoding_count, url_length, url_depth, ...
BIN_EDGES  = { numeric_feature: [edges...] }        # JS/overlap 共用,從 baseline 推定
BASELINE_PATHS = { "indonesia": "...", "csic": "..." }
```

> **`STAGE_LOG_PATHS` 待補**:哪個 stage 對應靶機上哪個 log 檔案(或哪個路徑/glob),目前沒有
> 定案的命名慣例——`attack_log.md` 只列了每個 stage 要打什麼、用什麼工具,沒有定輸出 log 要存
> 在哪、怎麼命名(例如是 `access_stage11.log`,還是同一份 `access.log` 靠時間戳切段落)。這件
> 事跟怎麼打 log 是同一個人決定的,`diversity.py` 只能消費,不能替團隊猜——`config.py` 先留空,
> 由實際負責打 log 的人補上,`run_stage.py` 的 `--log`/`--stage` 參數(§6.2)則是每次呼叫手動
> 指定,不依賴 `STAGE_LOG_PATHS` 自動探索,兩者可以獨立存在(手動指定路徑優先於 config 查表)。

---

## 4. `diversity.py` 模組介面契約

不在此給完整實作;定義函式簽章與輸入/輸出契約,實作者照此填。

**執行環境**:`dataset_health/` 整包(含 `config.py`、`diversity.py`)跑在**靶機**上(打 log 產生
攻擊資料的那台機器),不在 `log-analysis-core` 這個 repo 裡執行,兩邊沒有網路耦合。這代表
`extract_stage_features()` **不能**用 Python import 直接吃這個 repo 的 `machine_learning_models`
package——靶機上沒有這份 code。作法:把以下兩個檔案**手動複製**一份帶到靶機的 `dataset_health/`
目錄下:

1. `machine_learning_models/feature_engineering.py`——已確認只依賴 `pandas`/`numpy`/`re`,不 import
   本 repo 其他模組,所以整份檔案可以直接複製過去獨立跑,不用移植額外相依。
2. `machine_learning_models/all_feature_instruction.md`——給操作靶機的人看的欄位定義對照表,不用
   回來查這個 repo 的程式碼才看得懂每個特徵是什麼。

這是**人工同步**,不是 import 或 git submodule,所以有 skew 風險:這個 repo 之後改了
`feature_engineering.py`,靶機那份拷貝不會自動跟著變。§6.3 的可重現性要求要加一條:報告除了記
config hash,也要記靶機那份 `feature_engineering.py` 的檔案 hash,這樣事後能查出「這份分數是用
哪一版特徵邏輯算的」,並在本 repo 端這個檔案有異動時,提醒團隊該重新同步靶機那份拷貝了。

```python
def load_stage_log(log_path: str, stage_id: int, cfg) -> pd.DataFrame:
    """讀一份 stage 的**裸 access.log**,parse 成 create_all_features() 需要的原始欄位
    DataFrame(ip, request, referer, status, bytes, http_user_agent, timestamp...)。
    純 I/O + parsing,不算任何特徵。"""

def extract_stage_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """呼叫 machine_learning_models.feature_engineering.create_all_features(df_raw),
    回傳 31 欄特徵(28 欄程式碼內固定映射的整數特徵 + 3 欄尚未 LabelEncoding 的原始字串
    ip_type/request_method/request_version)。**必須直接 import 並呼叫 feature_engineering
    的函式,不得自己重寫一份平行邏輯**——否則又是 training-serving skew(參照架構文件第 9 節
    時間特徵的教訓,見 §3.5)。"""

def normalized_entropy(series: pd.Series, n_theoretical: int) -> float:
    """§2.1。n_theoretical 來自 config.CARDINALITY,不得用 series.nunique()。"""

def coverage(series: pd.Series, expected_values: list) -> tuple[float, set]:
    """§2.2。回傳 (cov, missing_set)。"""

def numeric_dispersion(series: pd.Series) -> float:
    """§2.3 QCD。Q3+Q1==0 時回 0.0。"""

def tail_reach(series: pd.Series, baseline_p95: float) -> float:
    """§2.4。baseline_p95 來自 baseline 資料;無 baseline 時回 None(不計入)。"""

def feature_diversity(series: pd.Series, feature: str, cfg) -> float:
    """依 FEATURE_TYPE 分派到 normalized_entropy 或 numeric_dispersion,回 d(f)。"""

def stage_diversity(df: pd.DataFrame, stage_id: int, cfg) -> StageDiversityReport:
    """§2.5。df = extract_stage_features() 的輸出(31 欄 + label)。呼叫端通常是
    load_stage_log → extract_stage_features → stage_diversity 這條鏈,但 stage_diversity
    本身只認已展開的特徵 DataFrame,方便單元測試直接餵 fixture,不必每次都經過真的 log parsing。
    步驟:
      1. 用 cfg.DEFINING_FLAG / defining_predicate 驗證這批確實屬於此 stage(不符 → warn)。
      2. F = cfg.SUPPORT_FEATURESstage_id。
      3. 對每個 f 算 d(f);類別型另算 coverage。
      4. 加權平均得 Diversity_stage。
      5. 組裝 per-feature 明細 + 缺漏診斷 + 樣本數警告。
    回傳結構化報告物件(可序列化成 JSON)。"""
```

**輸入契約**:對外(CLI / CI)的預設輸入是**裸的 stage access.log**,不是預先抽好特徵的 CSV。
`load_stage_log` 負責 parsing,`extract_stage_features` 直接呼叫
`machine_learning_models.feature_engineering.create_all_features()` 展開成 31 欄特徵
(見 §3.5/§3.6:三欄類別字串 `ip_type`/`request_method`/`request_version` 在這一步**還沒**經過
任何模型的 LabelEncoder),`stage_diversity` 只吃展開後的 DataFrame。

**明確不吃**兩種東西:

1. **`pipeline_utils.to_ml_payload` 的輸出**——這個函式只是即時 ingestion pipeline 裡的欄位白
名單過濾(見 `processing/pipeline_utils.py`),不做任何特徵計算或 encode,跟本模組要驗收的東西
是兩回事。
2. **任何已訓練模型的 `feature_encoders`/LabelEncoder 輸出**——原因見 §3.5/§3.6:那是各模型各自
fit 的、不共用、fit-time 依賴的整數碼,不適合當診斷用的權威特徵值。

原始 UA 字串的工具指紋分析屬於 `fingerprint.py`(層級 B),不在本模組——這條邊界要守住,否則
兩個模組職責重疊。

**輸出契約**:`StageDiversityReport` 至少含
`{stage_id, n_samples, diversity_score, per_feature: {f: {d, coverage, missing}}, warnings: [...]}`,
且**可被 `report.py` 序列化成 JSON**(供 CI artifact)與 markdown(供人看)。

---

## 5. 邊界情況與數值穩定性(實作必須處理)

1. **小樣本**:`n < MIN_SAMPLES(200)` 時,熵與 QCD 不穩。報告照算但每個數字標
`provisional=true`,且 CI 不得用它當硬門檻。
2. **理論基數分母**:§2.1 強調——恆用 `config.CARDINALITY`,禁用 `nunique()`。
3. **中位數為 0**:§2.3 已用 QCD 規避;仍須對 `Q3+Q1==0` 顯式回 0,不可讓除法拋錯。
4. **全常數特徵**:某支撐特徵在這批完全無變異 → `d(f)=0`,且在 warnings 標明「f 完全塌縮」。
這通常是紅旗(例如 stage 11 的 `request_method` 因 encode 塌縮)。
5. **決定性**:本模組純統計、無隨機性,天然可重現;仍須 pin `numpy` 版本(見 §6.3)。
6. **label 欄格式**:相容 `AMAN/BAHAYA/DICURIGAI` 字串與已 encode 的 0/1/2;在 loader 統一
正規化,不在 diversity 內處理。

---

## 6. CI 整合

CI 分兩層,**兩層的性質完全不同**,不可混為一談。這個 soft/strict 的切分,刻意對齊你們
架構文件第 4 節 `STRICT_AGENT_VALIDATION` 的設計哲學:先觀察、後收緊。

### 6.1 Tier 1 — 指標程式的單元測試(硬性 gate,每次 PR)

測的是**公式實作對不對**,不碰真實資料,完全決定性。放進你們既有的 `tests/unit/`,與
`test_time_features.py` 等並列。必測案例:

- `normalized_entropy`:均勻分佈 → 1;單一取值 → 0;分母用理論基數(給定 `N_f` 大於觀察值時
結果 < 1)。
- `coverage`:缺漏集合正確;全覆蓋 → 1。
- `numeric_dispersion`:全 0 → 0;已知 Q1/Q3 → 手算值;含離群值時穩定。
- `stage_diversity`:定義 flag 被正確排除;小樣本標 provisional;全塌縮特徵進 warnings。

這層是**必過**的——公式寫錯 CI 就該紅。與資料品質無關,純程式正確性。

```yaml
# .github/workflows/diversity-unit.yml(骨架)
name: diversity-unit
on: [pull_request, push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r dataset_health/requirements.txt   # pin 版本,見 §6.3
      - run: pytest tests/unit/test_diversity.py -v
```

### 6.2 Tier 2 — 資料集健檢報告(預設 soft artifact,可選 strict gate)

測的是**資料夠不夠好**,吃真實收集的 stage **裸 access.log**(見 §4:`load_stage_log` →
`extract_stage_features` → `stage_diversity`)。這層**預設不擋 build**,只產出報告 artifact,
理由與 Tier 1 相反:資料品質門檻本質上是團隊校準出來的、會演進的,一開始就硬擋會造成頻繁
且武斷的失敗。

- **觸發**:log 檔案是跟 commit 一起推上這個 repo 的(不是靠 artifact store 或外部路徑傳入),
所以可以直接綁 `on: push`,用 `paths:` 過濾成只在 log 目錄有變動時才跑,不會因為改一行
`config.py` 就整批重算。額外保留 `workflow_dispatch` 供手動重跑單一 stage。
- **每次觸發都掃全部 stage,不是只查有變動的那個檔**:log 目錄下有幾份 `STAGE_LOG_PATHS`
對應得到的檔案,就對每一份各自跑一次 `stage_diversity`、各自出一份報告——理由是這樣才能在
同一份 job summary 裡看到全 stage 的橫向對照(哪個 stage 涵蓋率掉了、哪個還好),而不用為了
看全貌手動觸發 12 次。
- **soft 模式(預設)**:每個 stage 各自算出 `Diversity_stage`、涵蓋率表、缺漏診斷,輸出
JSON + markdown 當 CI artifact,並在 job summary 貼**全 stage 彙總表**。**不設 exit code 失敗。**
- **strict 模式(可選,環境變數開啟)**:`DIVERSITY_STRICT=true` 時,**任一** stage 的
`Diversity_stage < threshold` 或關鍵類別涵蓋率未達標,就 `exit 1` 擋住整個 job(哪個 stage 沒過
在 summary 裡標出來)。門檻見 §7,且**務必先用印尼真實資料集跑出 baseline 再定 threshold**,
不要憑空設。

```yaml
# .github/workflows/diversity-report.yml(骨架)
name: diversity-report
on:
  push:
    paths:
      - "logs/**"                # 實際路徑待 STAGE_LOG_PATHS 定案後補(§3.7)
  workflow_dispatch:
    inputs:
      stage_id:      { required: false }   # 留空 = 掃全部;有填 = 只重跑這一個
      stage_log_path:{ required: false }
jobs:
  health:
    runs-on: ubuntu-latest
    env:
      DIVERSITY_STRICT: "false"   # 預設 soft;團隊校準後可改 true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r dataset_health/requirements.txt
      - run: |
          # 手動指定單一 stage 就只跑那個;否則依 config.STAGE_LOG_PATHS 掃全部
          if [ -n "${{ inputs.stage_id }}" ]; then
            python -m dataset_health.run_stage \
              --stage ${{ inputs.stage_id }} --log ${{ inputs.stage_log_path }} --out report/
          else
            python -m dataset_health.run_all_stages --out report/   # 內部依序呼叫每個 stage 的 run_stage
          fi
      - uses: actions/upload-artifact@v4
        with: { name: diversity-report, path: report/ }
      - if: always()
        run: cat report/summary.md >> $GITHUB_STEP_SUMMARY   # summary.md 彙總全部 stage 的一行結果
```

### 6.3 可重現性要求(兩層共用)

- Pin 依賴版本:`numpy`, `pandas`, `scipy`(至少這三個影響 percentile / 熵計算)。放
`dataset_health/requirements.txt` 並在 CI 用它安裝。
- 所有輸出報告帶上:模組版本、config hash、輸入 log 的行數與 checksum,便於日後追溯「這份
分數是哪版 config + 哪批資料算的」。

---

## 7. 每個 stage 的驗收判準(provisional,需校準)

以下門檻是**起始建議值,不是定論**。正確做法:先拿印尼真實 log(benign)與已收的 stage 1
跑一輪,看實際落點,再由三人校準。過早訂死高門檻會讓收集停滯。

| 判準 | soft 目標 | strict gate(校準後啟用) |
| --- | --- | --- |
| `Diversity_stage` | ≥ 0.5 觀察用 | < 0.4 擋 |
| 關鍵類別特徵涵蓋率(如 stage 1/10 的 `os_type`) | ≥ 0.5 | 缺 android+ios(手機全缺)擋 |
| 支撐特徵完全塌縮數 | 0 | ≥1 擋(若 `request_method`/`ip_type` 塌縮,先確認 §4 有沒有不小心接到某個模型的 `feature_encoders`,而不是 `create_all_features()` 的原始輸出——見 §3.5/§3.6) |
| 樣本數 | ≥ 200 | < 100 標不可用 |

**校準優先序**:先跑印尼資料集當 benign baseline → 得到「真實流量各特徵的自然散度」→ 用它
反推「攻擊 stage 至少該達到的散度」,而不是憑感覺設 0.5。這一步做完,§7 的數字才有意義。

---

## 8. 建置順序(對應本文件)

1. `config.py`:先把 §3 的表填成資料結構(尤其 §3.1 支撐特徵、§3.2 理論基數與 `expected_values`)。
這是其他一切的地基;§3.5 / §3.6 已定案為「讀 `create_all_features()` 的原始字串,不碰任何模型
的 LabelEncoder」,不是待決問題。
2. `diversity.py`:照 §4 契約實作 §2 公式(`load_stage_log` → `extract_stage_features` →
`stage_diversity`),處理 §5 邊界。
3. `tests/unit/test_diversity.py`:§6.1 案例,接上 Tier 1 CI。
4. `run_stage.py` + `report.py`:`run_stage.py` 處理單一 stage(接收裸 log,輸出 JSON/markdown);
再加一個 `run_all_stages.py`,依 `config.STAGE_LOG_PATHS` 迴圈呼叫 `run_stage.py` 邏輯,把每個
stage 的結果彙總成一份 `summary.md`(§6.2 `on: push` 用的就是這個)。後者依賴 `STAGE_LOG_PATHS`
先填好,所以順序上排在「§3.7 待補」解決之後。
5. 拿 stage 1(已收)+ 印尼 baseline 跑第一次,校準 §7 門檻。

---

## 附錄 A — 參考文獻

- Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M., &
Wichmann, F. A. (2020). *Shortcut Learning in Deep Neural Networks*. Nature Machine
Intelligence, 2(11), 665–673. — per-stage 多元度的核心動機(避免捷徑/工具指紋)。
- Engelen, G., Rimmer, V., & Joosen, W. (2021). *Troubleshooting an Intrusion Detection
Dataset: the CICIDS2017 Case Study*. IEEE S&P Workshops (WTMC). — 攻擊類別內部多樣性不足
導致無法類化;直接對應自建靶機的工具指紋風險。
- Cover, T. M., & Thomas, J. A. *Elements of Information Theory*. — Shannon 熵作為分佈均勻度
度量的理論來源。
- (whole-dataset 模組會另引 Jensen-Shannon divergence 相關文獻與 NLI label-leakage 之
PECO,本文件的 diversity 部分不依賴它們。)

---

## 附錄 B — 與其他模組的邊界

| 本模組(diversity) | 相鄰模組 | 邊界 |
| --- | --- | --- |
| 吃裸 access.log,但透過 `create_all_features()` 展開成結構化特徵才分析 | `fingerprint.py` 直接分析原始 UA 字串本身(不展開特徵) | 兩者都讀同一份原始 log,差別在「展開成表格特徵再算散度」vs.「直接對字串做指紋比對」,不在輸入格式 |
| per-stage、單類別可算 | `confounder.py` / MI / Overlap 需 ≥2 類別 | 本模組不算 label 相關性 |
| 產 `Diversity_stage`(G 分數成分) | `scoring.py` 合成 G / R | 合成與權重在 scoring,不在此 |
| 尾部旗標需 baseline | `realism.py`(JS-based) | 有 baseline 的比較歸 realism |