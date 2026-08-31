#!/usr/bin/env bash
# install.sh — XDR Agent 一行安裝腳本
#
# 使用方式（本機）：
#   sudo bash install.sh --tenant-id <你的租戶ID> --gateway-url https://gw.example.com
#
# 使用方式（一行安裝）：
#   curl -fsSL https://<平台網域>/install.sh | sudo bash -s -- \
#       --tenant-id <你的租戶ID> --gateway-url https://gw.example.com \
#       --source-url https://<平台網域>/xdr-agent.tar.gz
#
# 腳本會：偵測 OS → 安裝相依 → 佈署程式 → 自動偵測 nginx/apache log 路徑 →
#         產生設定檔 → 安裝 systemd service（**不自動啟動**）。
#
# 安裝完成後租戶需自行：
#   1. 把 Portal 產生的 Ingest API Key 填進 /etc/xdr-agent/secrets.env
#   2. sudo systemctl start xdr-agent
#
# API Key 刻意不接受命令列參數：命令列參數在 /proc/<pid>/cmdline 全主機可見，
# 且會留在 shell history。自動換發憑證見 AGENT_MANAGEMENT.md §10 Phase 2。

set -euo pipefail

# ── 發版資訊（由 tool_script/build_agent_release.sh 在打包時置換） ────────────
# 未置換（直接從 repo 執行）時維持 @@ 佔位字串，腳本會走「本機原始碼」路徑。
AGENT_VERSION="@@AGENT_VERSION@@"
AGENT_SHA256="@@AGENT_SHA256@@"
DEFAULT_SOURCE_URL="@@DEFAULT_SOURCE_URL@@"
# 直接從 repo 執行時上面三個值仍是 @@ 佔位字串，一律視為空值。
# 這裡刻意用 @@* 萬用比對，避免打包時的 sed 連這段判斷一起換掉。
case "$AGENT_VERSION"     in @@*) AGENT_VERSION="" ;;     esac
case "$AGENT_SHA256"      in @@*) AGENT_SHA256="" ;;      esac
case "$DEFAULT_SOURCE_URL" in @@*) DEFAULT_SOURCE_URL="" ;; esac

INSTALL_DIR="/opt/xdr-agent"
CONFIG_DIR="/etc/xdr-agent"
BUFFER_DIR="/var/lib/xdr-agent"
LOG_DIR="/var/log/xdr-agent"
SERVICE_FILE="/etc/systemd/system/xdr-agent.service"
AGENT_USER="xdr-agent"

TENANT_ID=""
GATEWAY_URL=""
AGENT_ID=""
LOG_PATH=""
LOG_FORMAT=""
SOURCE_DIR=""
SOURCE_URL="${XDR_AGENT_SRC:-}"
ASSUME_YES="no"

usage() {
  cat <<'USAGE'
用法：sudo bash install.sh [選項]

必要（未給則互動詢問）：
  --tenant-id <id>        租戶 ID（Portal 儀表板可查）
  --gateway-url <url>     Gateway 位址，例如 https://gw.example.com

選用：
  --agent-id <id>         Portal「新增 Agent」產生的識別碼
  --log-path <path>       web server access log 路徑（預設自動偵測）
  --log-format <fmt>      nginx_combined | apache_combined（預設依路徑推斷）
  --source-dir <dir>      agent 原始碼目錄（預設：腳本所在目錄）
  --source-url <url>      agent tarball 下載網址（curl | bash 模式使用）
  -y, --yes               非互動模式，缺參數即失敗
  -h, --help              顯示本說明
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tenant-id)   TENANT_ID="${2:-}";   shift 2 ;;
    --gateway-url) GATEWAY_URL="${2:-}"; shift 2 ;;
    --agent-id)    AGENT_ID="${2:-}";    shift 2 ;;
    --log-path)    LOG_PATH="${2:-}";    shift 2 ;;
    --log-format)  LOG_FORMAT="${2:-}";  shift 2 ;;
    --source-dir)  SOURCE_DIR="${2:-}";  shift 2 ;;
    --source-url)  SOURCE_URL="${2:-}";  shift 2 ;;
    -y|--yes)      ASSUME_YES="yes";     shift ;;
    -h|--help)     usage; exit 0 ;;
    *) echo "未知參數：$1" >&2; usage >&2; exit 1 ;;
  esac
done

die() { echo "[X] $*" >&2; exit 1; }

# curl | bash 時 stdin 是腳本本身，互動詢問必須改讀 /dev/tty
ask() {
  local prompt="$1" default="${2:-}" reply=""
  if [[ "$ASSUME_YES" == "yes" ]]; then return 1; fi
  if [[ ! -e /dev/tty ]]; then return 1; fi
  if [[ -n "$default" ]]; then
    read -r -p "$prompt [$default]: " reply </dev/tty || return 1
    echo "${reply:-$default}"
  else
    read -r -p "$prompt: " reply </dev/tty || return 1
    echo "$reply"
  fi
}

if [[ -z "$AGENT_VERSION" ]]; then
  echo "=== XDR Agent 安裝程序（開發版，未經發版打包）==="
else
  echo "=== XDR Agent 安裝程序 v$AGENT_VERSION ==="
fi

# ── 0. 前置檢查 ───────────────────────────────────────────────────────────────
[[ "$EUID" -eq 0 ]] || die "請用 root 執行：sudo bash install.sh"
command -v systemctl >/dev/null 2>&1 || die "找不到 systemd，本腳本僅支援 systemd 系統"

# ── 1. 偵測 OS 與套件管理器 ──────────────────────────────────────────────────
OS_ID="unknown"; OS_LIKE=""; PRETTY_NAME=""
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  OS_ID="${ID:-unknown}"; OS_LIKE="${ID_LIKE:-}"
fi

PKG=""
case "$OS_ID $OS_LIKE" in
  *debian*|*ubuntu*) PKG="apt" ;;
  *rhel*|*fedora*|*centos*|*rocky*|*almalinux*)
    if command -v dnf >/dev/null 2>&1; then PKG="dnf"; else PKG="yum"; fi ;;
  *suse*)   PKG="zypper" ;;
  *alpine*) PKG="apk" ;;
esac
echo "[1/8] OS：${PRETTY_NAME:-$OS_ID}（套件管理器：${PKG:-未知}）"

# ── 2. 安裝相依套件 ──────────────────────────────────────────────────────────
echo "[2/8] 檢查／安裝相依套件（python3、venv、pip、curl）"
install_pkgs() {
  case "$PKG" in
    apt)
      export DEBIAN_FRONTEND=noninteractive
      apt-get update -qq
      apt-get install -y -qq python3 python3-venv python3-pip curl ca-certificates ;;
    dnf)    dnf install -y -q python3 python3-pip curl ca-certificates ;;
    yum)    yum install -y -q python3 python3-pip curl ca-certificates ;;
    zypper) zypper --non-interactive install python3 python3-pip curl ca-certificates ;;
    apk)    apk add --no-cache python3 py3-pip curl ca-certificates ;;
    *) return 1 ;;
  esac
}
if ! install_pkgs; then
  echo "    [!] 無法自動安裝套件（未知的套件管理器），改為僅檢查是否已具備"
fi
command -v python3 >/dev/null 2>&1 || die "找不到 python3，請先自行安裝 python3 >= 3.8"
PY_OK="$(python3 -c 'import sys; print(1 if sys.version_info[:2] >= (3,8) else 0)')"
[[ "$PY_OK" == "1" ]] || die "python3 版本過舊（需 >= 3.8）：$(python3 -V 2>&1)"
python3 -c 'import venv' 2>/dev/null || die "python3 缺少 venv 模組，請安裝 python3-venv"

# ── 3. 取得 agent 原始碼 ─────────────────────────────────────────────────────
# 三種來源，依序：--source-dir → 腳本同目錄（從 repo 直接跑）→ tarball 下載。
# curl | bash 模式下沒有本機原始碼，會走 tarball；網址取自 --source-url，
# 未給則用發版時內嵌的 DEFAULT_SOURCE_URL。
echo "[3/8] 取得 agent 原始碼"
SRC=""; TMP_SRC=""
if [[ -z "$SOURCE_URL" && -n "$DEFAULT_SOURCE_URL" ]]; then
  SOURCE_URL="$DEFAULT_SOURCE_URL"
fi

if [[ -n "$SOURCE_DIR" ]]; then
  SRC="$SOURCE_DIR"
elif [[ -n "${BASH_SOURCE[0]:-}" && -f "$(dirname "${BASH_SOURCE[0]}")/agent.py" ]]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [[ -n "$SOURCE_URL" ]]; then
  case "$SOURCE_URL" in
    https://*) ;;
    http://*)  echo "    [!] 下載網址不是 HTTPS，憑證與程式在傳輸中可被竄改：$SOURCE_URL" ;;
    *) die "--source-url 必須是 http(s) 網址：$SOURCE_URL" ;;
  esac
  TMP_SRC="$(mktemp -d)"
  echo "    下載 $SOURCE_URL"
  curl -fsSL "$SOURCE_URL" -o "$TMP_SRC/agent.tar.gz" || die "下載失敗：$SOURCE_URL"

  # 校驗碼：發版時把 tarball 的 sha256 內嵌進本腳本，兩者必須一起從同一個
  # HTTPS 來源取得才有意義（腳本被竄改的話校驗碼也會被一起改掉）。
  if [[ "$AGENT_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
    ACTUAL="$(sha256sum "$TMP_SRC/agent.tar.gz" | awk '{print $1}')"
    if [[ "$ACTUAL" != "$AGENT_SHA256" ]]; then
      rm -rf "$TMP_SRC"
      die "tarball 校驗失敗（可能被竄改或版本不符）
        預期：$AGENT_SHA256
        實得：$ACTUAL"
    fi
    echo "    [OK] SHA256 校驗通過"
  else
    echo "    [!] 本腳本未內嵌校驗碼（開發版），略過完整性驗證"
  fi

  tar -xzf "$TMP_SRC/agent.tar.gz" -C "$TMP_SRC"
  FOUND="$(find "$TMP_SRC" -name agent.py -print -quit)"
  [[ -n "$FOUND" ]] || die "壓縮檔中找不到 agent.py"
  SRC="$(dirname "$FOUND")"
else
  die "找不到 agent 原始碼。請用 --source-dir <目錄> 或 --source-url <tarball 網址>"
fi
for f in agent collector parser buffer sender config; do
  [[ -f "$SRC/$f.py" ]] || die "原始碼不完整，缺少 $f.py（$SRC）"
done
echo "    來源：$SRC"

# ── 4. 收集設定值 ────────────────────────────────────────────────────────────
echo "[4/8] 收集設定值"
[[ -n "$TENANT_ID" ]]   || TENANT_ID="$(ask '租戶 ID (tenant_id)' || true)"
[[ -n "$TENANT_ID" ]]   || die "缺少 --tenant-id"
[[ -n "$GATEWAY_URL" ]] || GATEWAY_URL="$(ask 'Gateway 位址 (gateway_url)' || true)"
[[ -n "$GATEWAY_URL" ]] || die "缺少 --gateway-url"
GATEWAY_URL="${GATEWAY_URL%/}"

# 自動偵測 access log：取第一個存在且可讀的候選
if [[ -z "$LOG_PATH" ]]; then
  for cand in /var/log/nginx/access.log \
              /var/log/apache2/access.log \
              /var/log/httpd/access_log \
              /var/log/apache2/other_vhosts_access.log; do
    if [[ -r "$cand" ]]; then LOG_PATH="$cand"; break; fi
  done
  if [[ -n "$LOG_PATH" ]]; then
    echo "    自動偵測到 access log：$LOG_PATH"
  else
    LOG_PATH="$(ask 'access log 路徑' '/var/log/nginx/access.log' || true)"
    [[ -n "$LOG_PATH" ]] || die "找不到 access log，請用 --log-path 指定"
  fi
fi
[[ -r "$LOG_PATH" ]] || echo "    [!] $LOG_PATH 目前不存在或不可讀，仍會寫入設定（Agent 會等檔案出現）"

# 依路徑推斷格式；nginx/apache combined 欄位相同，猜錯不影響解析
if [[ -z "$LOG_FORMAT" ]]; then
  case "$LOG_PATH" in
    *apache*|*httpd*) LOG_FORMAT="apache_combined" ;;
    *)                LOG_FORMAT="nginx_combined" ;;
  esac
  echo "    log 格式：$LOG_FORMAT（依路徑推斷）"
fi
case "$LOG_FORMAT" in
  nginx_combined|apache_combined) ;;
  *) die "不支援的 --log-format：$LOG_FORMAT（僅支援 nginx_combined / apache_combined）" ;;
esac

# Gateway 連線檢查：不可達不中止安裝（可能是防火牆稍後才開）
if curl -fsS --max-time 5 "$GATEWAY_URL/health" >/dev/null 2>&1; then
  echo "    [OK] Gateway $GATEWAY_URL 可達"
else
  echo "    [!] 無法連上 $GATEWAY_URL/health —— 請確認網路／防火牆，安裝仍繼續"
fi

# ── 5. 建立帳號與目錄 ────────────────────────────────────────────────────────
echo "[5/8] 建立系統帳號與目錄"
if ! id "$AGENT_USER" &>/dev/null; then
  groupadd --system "$AGENT_USER"
  useradd  --system --gid "$AGENT_USER" --no-create-home \
           --shell /usr/sbin/nologin "$AGENT_USER"
fi
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$BUFFER_DIR" "$LOG_DIR"
chown "$AGENT_USER:$AGENT_USER" "$BUFFER_DIR" "$LOG_DIR"
chown root:"$AGENT_USER" "$CONFIG_DIR"
chmod 750 "$CONFIG_DIR"

# agent 以非 root 執行，必須讀得到 web server 的 log
if [[ -r "$LOG_PATH" ]] && ! runuser -u "$AGENT_USER" -- test -r "$LOG_PATH" 2>/dev/null; then
  LOG_GROUP="$(stat -c '%G' "$LOG_PATH" 2>/dev/null || echo '')"
  if [[ -n "$LOG_GROUP" && "$LOG_GROUP" != "UNKNOWN" ]]; then
    usermod -aG "$LOG_GROUP" "$AGENT_USER"
    echo "    已把 $AGENT_USER 加入群組 $LOG_GROUP 以讀取 $LOG_PATH"
  else
    echo "    [!] $AGENT_USER 可能無權讀取 $LOG_PATH，請自行調整權限"
  fi
fi

# ── 6. 佈署程式與 virtualenv ─────────────────────────────────────────────────
echo "[6/8] 建立 virtualenv 並佈署程式"
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --no-cache-dir --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet --no-cache-dir -r "$SRC/requirements.txt"
cp "$SRC"/{agent,collector,parser,buffer,sender,config}.py "$INSTALL_DIR/"
chown -R root:root "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.py
chmod 755 "$INSTALL_DIR"

# ── 7. 產生設定檔 ────────────────────────────────────────────────────────────
echo "[7/8] 產生設定檔"
if [[ -f "$CONFIG_DIR/config.yaml" ]]; then
  cp "$CONFIG_DIR/config.yaml" "$CONFIG_DIR/config.yaml.bak.$(date +%Y%m%d%H%M%S)"
  echo "    已備份既有 config.yaml"
fi

if [[ -n "$AGENT_ID" ]]; then
  AGENT_ID_LINE="agent_id: \"$AGENT_ID\""
else
  AGENT_ID_LINE="# agent_id: \"agent-xxxxxxxxxxxx\""
fi

cat > "$CONFIG_DIR/config.yaml" <<YAML
# 由 install.sh 於 $(date -Iseconds) 產生
# API Key 不放這裡：請填入 $CONFIG_DIR/secrets.env（環境變數優先於本檔）

tenant_id: "$TENANT_ID"
gateway_url: "$GATEWAY_URL"
$AGENT_ID_LINE

sources:
  - type: file
    path: $LOG_PATH
    format: $LOG_FORMAT

batch:
  flush_interval_sec: 180
  chunk_size: 5000

buffer:
  path: $BUFFER_DIR/buffer.db
  max_size_mb: 200

retry:
  max_attempts: 10
  base_delay_sec: 1
  max_delay_sec: 60

checkpoint:
  path: $BUFFER_DIR/checkpoint.json

logging:
  level: INFO
  path: $LOG_DIR/agent.log
YAML
chown root:"$AGENT_USER" "$CONFIG_DIR/config.yaml"
chmod 640 "$CONFIG_DIR/config.yaml"

# secrets.env：只建立範本，絕不覆蓋既有憑證
if [[ ! -f "$CONFIG_DIR/secrets.env" ]]; then
  cat > "$CONFIG_DIR/secrets.env" <<'SECRETS'
# 貼上 Portal「API Key」頁產生的 Ingest API Key（明碼只顯示一次）
# 格式：XDR_API_KEY=lac_xxxxxxxxxxxxxxxxxxxx
XDR_API_KEY=
SECRETS
  chown root:root "$CONFIG_DIR/secrets.env"
  chmod 600 "$CONFIG_DIR/secrets.env"
else
  echo "    已有 secrets.env，保留現有憑證"
fi

# ── 8. 安裝 systemd service（不自動啟動） ────────────────────────────────────
echo "[8/8] 安裝 systemd service"
[[ -f "$SRC/xdr-agent.service" ]] || die "找不到 $SRC/xdr-agent.service"
cp "$SRC/xdr-agent.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable xdr-agent >/dev/null 2>&1

if [[ -n "$TMP_SRC" ]]; then rm -rf "$TMP_SRC"; fi

cat <<DONE

=== 安裝完成 ===

  租戶 ID   : $TENANT_ID
  Gateway   : $GATEWAY_URL
  log 來源  : $LOG_PATH ($LOG_FORMAT)
  設定檔    : $CONFIG_DIR/config.yaml

還差兩步（需要你自己做）：

  1. 填入 API Key：
       sudo nano $CONFIG_DIR/secrets.env
       # 把 XDR_API_KEY= 後面補上 Portal 產生的 lac_... 憑證

  2. 啟動服務：
       sudo systemctl start xdr-agent
       sudo systemctl status xdr-agent
       sudo journalctl -u xdr-agent -f

  移除：sudo bash uninstall.sh
DONE
