# LFI/RFI Sink — `GET /api/events/:id/attachment`

> 對應 `Verify_doc/attack_log_instruments.md` 第 6 項 `has_file_inclusion`。
> 實際攻擊 payload 清單與收集流程在
> `nginx/collected/collection_method.md` 第 6 節，這份文件只講這個 sink
> 本身：為什麼要建、怎麼建、風險在哪。

## 為什麼要建這個 sink

一開始想直接拿 TixMaster 既有端點打 LFI/RFI payload，但搜過整個
`backend/routes/` 後發現**這個 app 原本沒有任何檔案讀取端點**——所有
`:id`/`:key`/`:orderNumber` 參數都只餵進 Sequelize/pg 參數化查詢，
從沒碰過 `fs`。打 `php://`、`file://` 這類 payload 只會落在
`server.js` 的 SPA fallback（一律回 200 + 固定大小的 `index.html`），
訓練資料的 status/size 完全沒有變異，跟 `known_gaps_attack_patterns.md`
記錄的問題是同一類：payload 沒進到真實的應用邏輯。

所以刻意在 `backend/routes/events.js` 加一個「附件下載」端點，語意上
合理（活動有附件很正常），實作上刻意不做路徑淨化，讓它是一個**真的
會被 LFI/path-traversal 打中的 sink**，而不是模擬出來的假回應。

## 端點規格

```
GET /api/events/:id/attachment?file=<name>
```

##啟動方式
```powershell
cd backend
$env:ENABLE_LFI_SINK = "true"
npm start
```
重開之後,直接用瀏覽器訪問下面這些網址(都會透過 nginx → 8080 → backend,同步寫進你剛打開的 access.log):

正常附件(200,AMAN 對照)

```word

http://192.168.194.86:8080/api/events/1/attachment?file=poster.txt
路徑遍歷打中 decoy(200,BAHAYA)


http://192.168.194.86:8080/api/events/1/attachment?file=../../etc/passwd
http://192.168.194.86:8080/api/events/1/attachment?file=..%2F..%2Fetc%2Fpasswd
http://192.168.194.86:8080/api/events/1/attachment?file=..%5C..%5Cwindows%5Cwin.ini
LFI wrapper 打不中(404,Node 不吃這套語法)


http://192.168.194.86:8080/api/events/1/attachment?file=php://filter/convert.base64-encode/resource=index.php
http://192.168.194.86:8080/api/events/1/attachment?file=expect://id
http://192.168.194.86:8080/api/events/1/attachment?file=data://text/plain;base64,PD9waHAgcGhwaW5mbygpOz8+
```

瀏覽器直接貼網址列就能打,access.log 會即時看到新的一行。
--- 


| 情況 | 回應 |
|---|---|
| `ENABLE_LFI_SINK` 未設為 `true` | `403 { error: "Attachment sink disabled", hint: "..." }` |
| 缺少 `file` 參數 | `400 { error: "file query parameter is required" }` |
| `file` 解析後指到讀得到的檔案 | `200` + 檔案內容（真的讀到，不是模擬） |
| `file` 解析後讀不到（檔案不存在 / wrapper 語法對 Node 無意義） | `404 { error: "attachment not found" }` |

核心程式碼（`backend/routes/events.js`）：

```js
const target = path.join(ATTACH_DIR, file);   // 故意不 sanitize
fs.readFile(target, (err, data) => {
    if (err) return res.status(404).json({ error: 'attachment not found' });
    res.status(200).send(data);
});
```

`:id` 本身完全沒被使用，只是讓 URL 看起來像正常功能（`/api/events/1/attachment`）。

## 為什麼是「打中/打不中」而不是「全部模擬成功」

決策時比較過兩種做法：

1. **純檔案讀取 sink（採用這個）**：`php://`、`expect://`、`input://`
   這類 PHP stream wrapper 語法在 Node 上完全沒有意義，`fs.readFile`
   會因為路徑本身無效或找不到而回 `404`。純路徑遍歷
   （`../`、`..%2F`、`..%5C`）因為沒有 sanitize，是真的能讀到
   sandbox 裡的 decoy 檔案，回 `200`。
2. 模擬全部 wrapper 都「成功」（例如假裝解析 `php://filter` 回
   base64、假裝 `expect://id` 回 `uid=1000...`）：能讓
   `has_file_inclusion` 覆蓋率更高，但回應是編出來的，不是這個
   Node 後端真實會有的行為，等於在訓練資料裡混入假的攻防訊號。

選了做法 1：**最貼近「這個 app 到底有沒有洞」的真相**——它對路徑遍歷
真的有洞，對 PHP 系列 wrapper 天生免疫（因為它根本不是 PHP）。這個
不對稱本身就是有意義的訓練訊號，不需要用假回應去補。

## 目錄配置

```
backend/data/attachments/poster.txt   ← 合法附件（AMAN 對照組用）
backend/etc/passwd                    ← decoy，假內容，非真系統檔案
backend/windows/win.ini               ← decoy，假內容，非真系統檔案
```

`ATTACH_DIR = backend/data/attachments`，decoy 放在 `backend/`
下兩層（`etc/passwd`、`windows/win.ini`），對應的打中 payload：

```
?file=poster.txt                        → 200，合法附件
?file=../../etc/passwd                  → 200，打中 decoy
?file=..%2F..%2Fetc%2Fpasswd            → 200，打中 decoy（URL 編碼版）
?file=..%5C..%5Cwindows%5Cwin.ini       → 200，打中 decoy（Windows 分隔符）
?file=php://filter/convert.base64-encode/resource=index.php  → 404
?file=expect://id                       → 404
?file=data://text/plain;base64,...      → 404
?file=nonexistent.txt                   → 404
```

## 風險與限制（重要）

- **這是真的漏洞，不是演戲**：`path.join(ATTACH_DIR, file)` 沒有做
  `path.resolve` + 前綴檢查，所以只要 `../` 疊得夠深，理論上可以跳出
  `backend/` 逃到整台機器上 Node process 讀得到的任何檔案，不只是
  兩層 decoy。目前收集用的 payload 只疊 2 層剛好打中 decoy，但這不代表
  這個 sink 的攻擊面被限制在那兩層。
- **預設關閉**：`ENABLE_LFI_SINK` 沒設為 `true` 時一律回
  `403`，不會意外暴露。**只在本機 lab 收集訓練資料時手動開啟**，
  不要在任何非本機環境（Railway/Render/正式站）設這個環境變數。
- decoy 檔案內容都寫明「lab decoy - not a real system file」，即使
  被打中外洩也不是真的敏感資料。

## 怎麼手動測試

```powershell
cd backend
$env:ENABLE_LFI_SINK = "true"
npm start
```

另開一個 terminal：

```powershell
Invoke-WebRequest "http://localhost:3000/api/events/1/attachment?file=poster.txt" -UseBasicParsing
Invoke-WebRequest "http://localhost:3000/api/events/1/attachment?file=../../etc/passwd" -UseBasicParsing
Invoke-WebRequest "http://localhost:3000/api/events/1/attachment?file=php://filter/convert.base64-encode/resource=index.php" -UseBasicParsing
```

正式收集訓練資料時要走 `http://localhost:8080`（nginx），這樣
request 才會進到 `nginx/logs/access.log`，流程見
`nginx/collected/collection_method.md` 第 6 節。

## 這次收集的方法論

實際收集分三個階段，對應 `nginx/LFI_method_record/` 底下三份 log，已登記進
`nginx/logs/stage_log_CHECK/stage_log_map.txt`（stage id `6`）：

### 階段 1：手動精準案例 — `access3_Local_file_inclusion_1.log`

用瀏覽器（後來確認手動 PowerShell/curl 更乾淨，見下方「踩過的坑」）逐一打
本文件前面列的那組 payload，目的是**先核對 sink 的 hit/miss 邏輯對不對**，
不是衝量：

- `?file=poster.txt` → 200（合法附件基準）
- `?file=../../etc/passwd`、`..%2F..%2Fetc%2Fpasswd`、
  `..%5C..%5Cwindows%5Cwin.ini` → 200（打中 decoy，含未編碼/URL 編碼/
  Windows 分隔符三種變形）
- `?file=php://...`、`expect://id`、`data://...` → 404（wrapper 對 Node
  無意義，如實反映這個後端沒有這類洞）

### 階段 2：wfuzz + SecLists 既有 wordlist — `access4_Local_file_inclusion_2_wfuzz.log`

```powershell
wfuzz -c -z file,/usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt `
  -u 'http://192.168.194.86:8080/api/events/1/attachment?file=FUZZ'
```

結果 882 筆全部 404。事後檢查發現這份 wordlist**全部是絕對路徑
（`/etc/passwd` 這種），沒有任何 `../` 相對路徑**——`path.join(ATTACH_DIR,
file)` 不會把開頭 `/` 當成檔案系統根目錄，絕對路徑一律被 normalize
成 `ATTACH_DIR` 底下一個不存在的子路徑，保證 100% 404。

**這不是這批資料失敗**：所有回應都是 `404 32 bytes`，對應
`res.status(404).json({error:'attachment not found'})`，證明每一筆都真的
進到 sink 程式碼跑過，不是落在 SPA fallback（`200/6537`）。「這招對這個
Node app 沒用」本身是有效的 ground truth，只是這個 batch 的 payload
shape 很單一（100% 404、同一秒內打完，見下方「已知限制」）。

### 階段 3：wfuzz + 客製 wordlist — `access5_Local_file_inclusion_3_wfuzz.log`

改用針對這個 sink 實際目錄結構寫的 `lfi_sink_traversal_wordlist.txt`
（44 個 payload，涵蓋：對深度 2 decoy 的正確/錯誤層數、單層/雙層 URL 編碼、
`....//`/`..;/` 繞過變形、null byte、wrapper、合法對照）：

```powershell
wfuzz -c -z file,lfi_sink_traversal_wordlist.txt `
  -u 'http://192.168.194.86:8080/api/events/1/attachment?file=FUZZ'
```

44 個 payload 全數送出，結果 `200×18、404×23、500×3`，三種回應都拿到了：

- `200`：打中 decoy 或合法附件
- `404`：深度不對 / wrapper 語法不支援 / 檔案不存在
- `500`：payload 含 null byte（`%00`），`fs.readFile` 對嵌入的 NUL byte
  直接同步丟 `ERR_INVALID_ARG_VALUE`，是這個 sink 第三種真實會發生的
  行為，不是模擬出來的

### 環境設定的坑

跑 wfuzz 之前修了一個跟 LFI 本身無關、但擋住整個收集流程的問題：
`docker-compose.nginx.yml` 把 nginx 綁在 ZeroTier 虛擬網卡 IP
（`192.168.194.86:8080`）上，container 若在該網卡還沒就緒時啟動，
Docker 會**靜默綁定失敗**（compose 設定看起來對，但 `docker inspect`
顯示 `NetworkSettings.Ports` 是空的，host 完全沒監聽）。解法是
`docker-compose -f docker-compose.nginx.yml up -d --force-recreate`
讓它在網卡穩定後重新綁定一次。

### 已知限制 / 之後要注意的雜訊

1. **瀏覽器手動測試會混進雜訊**：直接在網址列貼 API URL 會觸發瀏覽器
   快取（重複打同一個 URL 第二次變 `304`）、自動附帶 `favicon.ico`
   request、以及夾雜正常瀏覽行為（`referer` 帶著上一頁）。正式 batch
   改用 PowerShell/wfuzz 送 payload 後就沒有這個問題了。
2. **`access4` 的 timestamp 全部落在同一秒**：882 筆都是
   `04:32:11`，`hour`/`minute`/`is_odd_hour` 這幾個 feature 在這個
   batch 裡完全沒有變異，跟自己訂的「時序自然分散」原則有落差
   （高速批次本身也是自動化工具的真實特徵，不算致命，但混進其他
   batch 訓練前要留意這批的時間分佈很極端）。
3. **`access5` 有 27 筆非預期的 `file=`（空值）400**：比 wordlist 裡
   9 個空白行還多，推測跟 wfuzz 對 wordlist 空白行 / 含空白字元的
   payload（如 `expect://cat ../../etc/passwd`）的處理方式有關，
   確切原因還沒查到根因。這些 400 本身是真實回應（`file query
   parameter is required`），不是壞資料，但不是刻意設計的攻擊
   payload，算是這個 batch 裡的雜訊，篩選訓練資料時可以考慮排除。
4. **wfuzz 會自動跳過 wordlist 裡 `#` 開頭的註解行**（已用
   `access5` 實測確認，log 裡沒有任何以 `#`/`%23` 開頭的 payload）。
