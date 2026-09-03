# Stage 10（Scanner UA）多元度補強計劃

## 根因（已用 report/stage_10.json 確認）

`dataset_health/feature_engineering.py` 的分類邏輯：

```python
def parse_os(ua):
    ua = str(ua).lower()
    if 'windows' in ua: return 1
    elif 'android' in ua: return 2
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua: return 3
    elif 'linux' in ua and 'android' not in ua: return 4
    elif 'mac' in ua: return 5
    elif 'bot' in ua or 'crawler' in ua or 'spider' in ua: return 6  # bot
    else: return 7  # other

df['is_bot'] = (df['os_type'] == 6).astype(int)  # 完全衍生自 os_type，不是獨立判斷
```

過去 stage 10 所有批次（`nginx01_batch_scanner_ua_gobuster_*`）的 User-Agent 都是
`gobuster/x.y` 這種格式，不含 `windows`/`android`/`iphone`/`linux`/`mac`/
`bot`/`crawler`/`spider` 任何關鍵字 → 全部落在 `7 other`。`is_bot` 只看
`os_type==6`，同理永遠是 0。gobuster 也不帶 Referer（永遠 `referrer_type=0`），
dir 模式預設固定 GET（永遠 `request_method=GET`）。這就是為什麼過去換 IP/
換時段的幾輪（round 002/005/006）完全沒有改善這四個支撐特徵的原因——
換的是不影響分類的東西。

`dataset_health/config.py` 裡 stage 10 **沒有 `DEFINING_FLAG`/`DEFINING_PREDICATE`**
（跟 SQLi/XSS 這種有 regex 判準的 stage 不同），代表這個 stage 沒有「必須維持
什麼樣子」的限制，合法的修法就是用真實工具打真實流量、但刻意控制 UA/Referer/
Method 落進目前缺的分類桶，不需要換成另一個工具本身。

## 目標分類桶（來自 `config.EXPECTED_VALUES`）

| 特徵 | 目前只有的值 | 還缺的值 |
|---|---|---|
| `os_type`（0-7） | 7（other） | 0,1,2,3,4,5,6 |
| `is_bot`（0/1） | 0 | 1（讓某些 UA 含 bot/crawler/spider） |
| `referrer_type`（0-5） | 0（none） | 1,2,3,4,5 |
| `request_method` | GET | 至少 1-2 種其他 method |

## 建議 UA / Referer 對照表

不需要冒充任何真實公司或產品，字串只是拿來讓 parser 命中對應的關鍵字：

```text
os_type=1 windows : Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36
os_type=2 android : Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36
os_type=3 ios     : Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1
os_type=4 linux   : Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
os_type=5 mac     : Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15
os_type=6 bot     : Mozilla/5.0 (compatible; ExampleCrawler/1.0; +http://example.invalid/bot)
os_type=7 other   : 維持現狀（既有批次已覆蓋，不用再收）
```

```text
referrer_type=1 local        : http://localhost:8080/              （含 "localhost"）
referrer_type=2 ip_address   : http://203.0.113.10/                （RFC 5737 保留測試網段，不指向任何真實主機）
referrer_type=3 search_engine: https://www.google.com/search?q=tixmaster
referrer_type=4 social       : https://www.facebook.com/
referrer_type=5 external     : https://example.com/
referrer_type=0 none         : 不帶 Referer header（維持現狀）
```

Method：至少加 `HEAD`，有餘力再加 `OPTIONS`——跟 stage 11（abnormal methods）
的 PUT/DELETE 不同，這裡只是要打破「永遠 GET」的塌縮，不用刻意做異常 method。

## 三個工具怎麼下指令

沙盒裡目前沒有裝 dirb / feroxbuster / wfuzz，本機也沒有這幾個 docker image
（`docker images` 查過），實際執行前要先 `docker pull` 或本機安裝。flag 名稱
以工具版本為準，執行前建議先 `<tool> -h`/`--help` 確認。

### wfuzz（專案已用過，見 stage 6 LFI 批次）

wfuzz 原生支援 `-X` 指定 method、`-H` 可重複疊加 header：

```bash
wfuzz -c -z file,nginx/collected/scanner_ua_gobuster_wordlist_001.txt \
  -H "User-Agent: <上面表的 UA>" \
  -H "Referer: <上面表的 Referer，不需要就整行拿掉>" \
  -X GET \
  --hc 404 \
  http://localhost:8080/FUZZ
```

換 `-X HEAD` 就能收 method 多元度那一批。

### dirb

```bash
dirb http://localhost:8080/ nginx/collected/scanner_ua_gobuster_wordlist_001.txt \
  -a "<UA>" \
  -H "Referer: <Referer>" \
  -o /tmp/dirb_run.txt
```

dirb 沒有 method 覆寫（固定 GET），拿來跑 UA/Referer 那幾輪就好，method 多元度
留給 wfuzz/feroxbuster。

### feroxbuster

```bash
feroxbuster -u http://localhost:8080/ \
  -w nginx/collected/scanner_ua_gobuster_wordlist_001.txt \
  -a "<UA>" \
  -H "Referer: <Referer>" \
  -m GET,HEAD \
  -n -q \
  -o /tmp/ferox_run.txt
```

`-m` 可以吃逗號分隔的多個 method，一次跑就能同時拿到 GET 跟 HEAD 兩種
`request_method`。

### Docker 執行（本機沒裝二進位檔時）

⚠️ nginx 現在改綁 `127.0.0.1:8080`（見下面收集流程），container 裡的
`127.0.0.1` 指的是 container 自己，不是宿主機，直接打 `localhost:8080`
會連不到。用 Docker Desktop（Windows/Mac）跑掃描工具 container 時要改打
`host.docker.internal:8080`：

```bash
docker run --rm <wfuzz-image> wfuzz -c -z file,/wordlist.txt ... http://host.docker.internal:8080/FUZZ
```

如果是原生 Linux Docker Engine，`host.docker.internal` 預設不會自動解析，
要嘛加 `--add-host=host.docker.internal:host-gateway`，要嘛直接
`docker run --network host ...` 之後打 `localhost:8080`。

實際 image 名稱請先 `docker search` 或用 Docker Hub 確認，不同 image 掛載
wordlist 的路徑可能不同。

## 收集流程（跟過去每一輪一致，見 `nginx/collected/collection_method.md`）

不用分成 UA/Referer/Method 三個檔案——`stage_log_map.txt` 是把同一個 stage
底下所有對應檔案先合併成一份 DataFrame 再算 diversity，`label` 也是掛在
stage id 上（stage 10 一律 `BAHAYA`），不是掛在檔案上，分檔案對分數和標籤
完全沒有差別，只差在 traceability。既然這輪就是要一次把三個軸都補起來，
乾脆收成**一個檔案**，同一個 session 裡逐次換 UA / Referer / Method 打，
省事又不影響結果。

1. 確認 backend 有開（`cd backend && npm start`，監聽 :3000），確認
   `curl http://localhost:8080/api/events` 不是 502（nginx 現在綁定
   `127.0.0.1:8080`，不是舊的 `192.168.194.86:8080`，下面指令都改用
   `localhost:8080`）。
2. 記錄跑之前 `nginx/logs/access.log` 的行數。
3. 依序對同一份 wordlist 跑幾輪，每輪只換一個變數（例如：預設 UA/Referer/GET
   →換 2-3 種 UA（含一個 windows 樣式、一個含 bot/crawler 字樣）→換 2-3 種
   Referer（local/search engine/external 挑幾個）→換 method 成 HEAD），
   全部打同一個 target，log 自然會疊在同一段連續行數裡。
4. 跑完後把這整段新增的行取出來，存成一個檔案，例如
   `nginx/collected/nginx01_batch_scanner_ua_diversity_007.log`。
5. 用 `python -m dataset_health.run_stage --stage 10 --log <新檔路徑>`
   先單獨驗證這批不是 bad_format、看得到預期的分類值改變。
6. 寫 `.meta.txt`（格式比照現有檔案：batch_id/label/traffic_type/tool/
   count_collected/nginx/target/log_file/notes/timezone_note；notes 裡把
   這輪換過的 UA/Referer/Method 組合列清楚，取代分檔案的 traceability）。
7. 把新檔加進 `nginx/logs/stage_log_CHECK/stage_log_map.txt` 的 stage 10 那組。
8. 在 `nginx/collected/collection_method.md` 加一段新 round 說明（沿用既有
   round 002/005/006 的寫法）。
9. 重跑 `pytest tests/unit/test_run_stage.py -v` 或
   `python -m dataset_health.run_stage --stage 10`，確認
   `os_type`/`is_bot`/`referrer_type`/`request_method` 不再全部
   `collapsed=True`，`Diversity_stage` 有明顯提升。

## 驗收標準

- `report/stage_10.json` 的 `per_feature` 四個分類特徵至少各出現 2 種以上
  取值（`collapsed=False`）。
- `n_samples` 累加到 ≥ `MIN_SAMPLES`（目前 200），脫離 `provisional`。
- `Diversity_stage` 從 0.017 明顯回升（不用刻意衝到某個數字，門檻校準
  之前不設硬指標，見 `.github/workflows/diversity-report.yml` 的註解）。
