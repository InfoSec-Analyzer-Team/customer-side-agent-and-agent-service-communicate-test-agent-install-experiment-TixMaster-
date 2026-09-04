#!/bin/bash
# ── 敏感路徑存取 / 多元化版 (純 curl,不需要 Kali/gobuster) ──
#
# 這支腳本是從最初「單一 UA、固定 sleep 節奏、全掃全部路徑、只有 GET」
# 的版本擴充來的。原本版本只變化了 UA 一個維度，等於只模擬了一種攻擊者
# 畫像；下面每個參數對應的是討論中補上的訊號軸：
#
#   1) 節奏 (-m)        單一固定 sleep 只長得像一種行為。實際 recon 節奏
#                        差很多：工具化高速掃描 (fast)、人工手動慢慢試
#                        且間隔不規則 (slow)、多執行緒工具間歇性突發
#                        (burst，靠背景平行 + wait，不是加大 sleep)。
#                        這三種在 log 的時間間隔分布上完全不同，分開產生
#                        才有代表性。
#   2) 子集抽樣 (-n)     原本版本每次都跑完整個路徑清單 = 只模擬「窮舉式
#                        全掃」。真實攻擊者常常只挑幾個關鍵路徑試探，抽
#                        樣子集才能覆蓋「局部試探」這種更難被固定字典
#                        比對抓到的行為。
#   3) HTTP method (-x)  原本只有 GET。很多輕量掃描器預設用 HEAD 省流量，
#                        對登入頁 (wp-login.php、/admin/login) 用 POST
#                        試登入也是常見行為，method 分布本身就有鑑別力。
#   4) UA/Header 真實度 (-u)  curl 預設幾乎不帶 Accept / Accept-Language /
#                        Accept-Encoding，即使把 UA 字串換成 Chrome，其餘
#                        指紋還是一眼看出是 curl。browser 模式額外帶上這
#                        組常見瀏覽器 header，「偽裝瀏覽器」樣本才不會只
#                        靠 header 組合被拆穿。
#   5) 不混 benign 流量 (已拿掉 -b)  原本想在同一輪裡穿插正常路由請求，
#                        讓攻擊/正常混在同一時間軸上；但這樣會讓打標籤
#                        變麻煩 (同一批 log 裡哪幾行是 benign 沒有另外記
#                        錄，等於還要重新用規則反推)。改成這支腳本只產生
#                        「純攻擊」樣本、整批可以直接標同一個 label；正
#                        常流量另外用別的方式產生 (例如 playwright_test.py
#                        跑真實使用者流程)，之後再把兩批 log 合併、依需求
#                        重新分布時間。
#
#   附註 (下游打標時務必記得):
#   TixMaster 後端 (backend/server.js 的 SPA fallback middleware) 對所有
#   非 /api、非 /auth 且無明顯副檔名的路徑，一律回 200 + index.html，即使
#   路徑實際不存在，因此打出來的 log 裡 status code 幾乎全是 200。不能拿
#   status/size 當作「該路徑是否存在」的 ground truth；要標記惡意掃描 vs
#   正常瀏覽，得靠路徑本身、節奏、method、UA/header 組合這些特徵，而不是
#   HTTP 回應本身。(nginx 這層本身沒有 try_files，只是單純 proxy_pass，
#   問題出在後端的 catch-all fallback，不是 nginx 設定。)
#
#   時間戳記本身先照實際下針時間記錄就好，之後要打散/隨機化交給
#   anonymize_log.py 的 TIME_SPREAD_DAYS 處理 (它是照 session 整體平移，
#   不是逐行亂數，才不會打亂同一次掃描內部的相對節奏)，這支腳本不用自己
#   再做時間隨機化。
#
#   只對你自己的測試靶機使用 (TARGET 指向自己的 lab/容器)。
#
# 用法:
#   ./sensitive_path_scan.sh -t <IP:PORT> [-m fast|slow|burst] \
#       [-n 抽樣數量] [-u scanner|browser|both] [-x GET,HEAD,POST]
#
# 範例:
#   ./sensitive_path_scan.sh -t 192.168.1.50:8080 -m burst -u both -x GET,HEAD -n 8

set -euo pipefail

TARGET=""
MODE="slow"        # fast | slow | burst
SUBSET=0            # 0 = 全部路徑；>0 = 隨機抽樣這麼多筆 (局部試探)
UA_MODE="scanner"  # scanner | browser | both
METHODS="GET"       # 逗號分隔，如 GET,HEAD,POST

while getopts "t:m:n:u:x:" opt; do
  case "$opt" in
    t) TARGET="$OPTARG" ;;
    m) MODE="$OPTARG" ;;
    n) SUBSET="$OPTARG" ;;
    u) UA_MODE="$OPTARG" ;;
    x) METHODS="$OPTARG" ;;
    *) echo "未知參數"; exit 1 ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "用法: $0 -t <IP:PORT> [-m fast|slow|burst] [-n 抽樣數量] [-u scanner|browser|both] [-x GET,HEAD,POST]"
  exit 1
fi

SENSITIVE_PATHS=(
  "/admin" "/admin/login" "/administrator"
  "/backup" "/backup.zip" "/backup.tar.gz"
  "/config" "/config.php" "/configuration.php"
  "/database" "/database.sql" "/db" "/db.sql"
  "/test" "/test.php" "/temp" "/tmp"
  "/logs" "/access.log" "/error.log"
  "/old" "/index.old" "/index.bak" "/backup.bak"
  "/phpmyadmin" "/wp-admin" "/wp-login.php"
  "/.git/config" "/.git/HEAD" "/.env"
)

# scanner 模式的 UA 池：UA 只是 curl -A 送出去的字串，跟實際發 request 的
# 工具無關 (真的 gobuster 掃出來的 log 會是 "gobuster/3.6"，但我們用 curl
# 一樣可以宣稱自己是任何工具)。原本這裡只寫死 "curl/8.5.0"，等於每次 scanner
# 樣本的工具簽名都長一樣；現在改成池子，每個 request 隨機抽一個，涵蓋常見
# recon 工具的預設 UA，樣本才不會全部長得像同一支工具在打。
#
# 沒放 sqlmap：它是打 SQL injection 的工具，行為模式是打參數/表單，不是像
# gobuster/ffuf 這樣逐條路徑枚舉。放進「路徑掃描」腳本的 UA 池會產生
# 「UA 宣稱是 sqlmap，但行為是路徑枚舉」這種真實世界不太出現的矛盾樣本。
# 如果之後要做 SQLi 相關的樣本，應該另外開一支腳本、打參數注入的路徑，UA
# 才跟行為對得起來。
UA_SCANNER_POOL=(
  "gobuster/3.6"
  "curl/8.5.0"
  "ffuf/2.1.0"
  "Nikto/2.5.0"
  "dirb 2.22"
  "Mozilla/5.0 (compatible; Nmap Scripting Engine; https://nmap.org/book/nse.html)"
  "python-requests/2.31.0"
  "Go-http-client/1.1"
)
UA_BROWSER="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

# 依模式決定每個 request 之間的等待秒數 (burst 模式不靠 sleep，靠背景平行處理)
sleep_for_mode() {
  case "$MODE" in
    fast)  awk "BEGIN{srand(); print 0.05 + rand()*0.15}" ;;   # 高速掃描器
    slow)  awk "BEGIN{srand(); print 2 + rand()*8}" ;;         # 人工手動，間隔拉長且不規則
    burst) echo 0 ;;
    *) echo "未知模式: $MODE" >&2; exit 1 ;;
  esac
}

# 送出單一 request。scanner 模式每次從 UA_SCANNER_POOL 隨機抽一個 UA；
# browser 模式固定用 UA_BROWSER，並額外帶上完整瀏覽器 header 組合，避免
# 只換 UA、其餘指紋仍是 curl 預設值就被一眼看穿。
fire_request() {
  local method="$1" path="$2" mode_name="$3"
  local ua extra_headers=()
  if [ "$mode_name" = "browser" ]; then
    ua="$UA_BROWSER"
    extra_headers=(
      -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
      -H "Accept-Language: zh-TW,zh;q=0.9,en;q=0.8"
      -H "Accept-Encoding: gzip, deflate"
    )
  else
    ua="${UA_SCANNER_POOL[$((RANDOM % ${#UA_SCANNER_POOL[@]}))]}"
  fi
  curl -s -o /dev/null -w "%{http_code} $method $path ua=[$ua] ($mode_name)\n" \
    -X "$method" "http://$TARGET$path" -A "$ua" "${extra_headers[@]}"
}

case "$UA_MODE" in
  scanner) UA_MODES=("scanner") ;;
  browser) UA_MODES=("browser") ;;
  both)    UA_MODES=("scanner" "browser") ;;
  *) echo "未知 UA 模式: $UA_MODE" >&2; exit 1 ;;
esac

run_all() {
  # 子集抽樣：0 = 全掃 (窮舉)，>0 = 只隨機挑幾條 (局部試探)
  local paths=("${SENSITIVE_PATHS[@]}")
  if [ "$SUBSET" -gt 0 ]; then
    mapfile -t paths < <(printf '%s\n' "${SENSITIVE_PATHS[@]}" | shuf -n "$SUBSET")
  fi

  IFS=',' read -ra method_list <<< "$METHODS"

  # both 模式下，原本是「scanner 全部路徑跑完，才換 browser 全部路徑」，
  # 兩個 pass 在時間上完全分離，會讓整批 log 前半段全是 scanner UA、後半
  # 段全是 browser UA——如果下游模型不小心學到「這個時間窗 = scanner」，
  # 那是這支腳本製造出來的假訊號，真實世界不同工具/偽裝的流量是時間交錯
  # 的。這裡改成先把「路徑 × method × UA 模式」的完整組合列成一份 job
  # 清單，整份洗牌後再依序 (或 burst 模式下背景平行) 發送，讓 scanner /
  # browser 樣本在時間軸上是打散混合的，而不是兩坨分開的區塊。
  local jobs=()
  for path in "${paths[@]}"; do
    for method in "${method_list[@]}"; do
      for mode_name in "${UA_MODES[@]}"; do
        jobs+=("$method|$path|$mode_name")
      done
    done
  done
  mapfile -t jobs < <(printf '%s\n' "${jobs[@]}" | shuf)

  echo "[*] UA模式=$UA_MODE  節奏=$MODE  路徑數=${#paths[@]}  methods=$METHODS  總request數=${#jobs[@]}"

  for job in "${jobs[@]}"; do
    IFS='|' read -r method path mode_name <<< "$job"
    if [ "$MODE" = "burst" ]; then
      fire_request "$method" "$path" "$mode_name" &
    else
      # curl 連不上 (target 重啟、暫時掉線等) 會回非 0，配合開頭的
      # set -e 若不擋下來,整支腳本會在第一個失敗的 request 就整批中止,
      # 剩下的路徑都不會打到——這比任何節奏/UA 分佈問題都更直接破壞
      # 資料完整性,所以這裡用 || true 讓單一失敗只算一行 000,不影響
      # 這一輪剩下的 job。
      fire_request "$method" "$path" "$mode_name" || true
      sleep "$(sleep_for_mode)"
    fi
  done

  if [ "$MODE" = "burst" ]; then
    wait   # 併發模式：全部背景 request 打完才算結束
  fi
}

run_all
