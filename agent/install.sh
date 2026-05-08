#!/usr/bin/env bash
# install.sh — 將 XDR Agent 安裝為 systemd service
#
# 使用方式：
#   sudo bash install.sh
#
# 安裝完成後請編輯 /etc/xdr-agent/config.yaml，填入 tenant_id 與 gateway_url，
# 然後執行 sudo systemctl start xdr-agent

set -euo pipefail

# ── 必須以 root 執行 ──────────────────────────────────────────────────────────
if [[ "$EUID" -ne 0 ]]; then
  echo "請用 root 執行：sudo bash install.sh" >&2
  exit 1
fi

INSTALL_DIR="/opt/xdr-agent"
CONFIG_DIR="/etc/xdr-agent"
BUFFER_DIR="/var/lib/xdr-agent"
LOG_DIR="/var/log/xdr-agent"
SERVICE_FILE="/etc/systemd/system/xdr-agent.service"
AGENT_USER="xdr-agent"

echo "=== XDR Agent 安裝程序 ==="

# ── 1. 建立專用系統帳號 ───────────────────────────────────────────────────────
if ! id "$AGENT_USER" &>/dev/null; then
  echo "[1/6] 建立系統帳號 $AGENT_USER"
  groupadd --system "$AGENT_USER"
  useradd  --system --gid "$AGENT_USER" --no-create-home \
           --shell /usr/sbin/nologin "$AGENT_USER"
else
  echo "[1/6] 帳號 $AGENT_USER 已存在，跳過"
fi

# ── 2. 建立目錄 ───────────────────────────────────────────────────────────────
echo "[2/6] 建立目錄"
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$BUFFER_DIR" "$LOG_DIR"
chown "$AGENT_USER:$AGENT_USER" "$BUFFER_DIR" "$LOG_DIR"
# config 目錄由 root 持有，agent 只需 read 權限
chmod 750 "$CONFIG_DIR"

# ── 3. 建立 Python virtualenv 並安裝依賴 ─────────────────────────────────────
echo "[3/6] 建立 virtualenv 並安裝 Python 依賴"
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --no-cache-dir -r "$(dirname "$0")/requirements.txt"

# ── 4. 複製 agent 程式碼 ──────────────────────────────────────────────────────
echo "[4/6] 複製 agent 程式碼至 $INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR"/{agent,collector,parser,buffer,sender,config}.py "$INSTALL_DIR/"
chown -R root:root "$INSTALL_DIR"
chmod -R 644 "$INSTALL_DIR"/*.py
chmod 755 "$INSTALL_DIR"

# ── 5. 安裝 config 範本（若尚未存在） ────────────────────────────────────────
echo "[5/6] 安裝設定檔"
if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
  cp "$SCRIPT_DIR/config.yaml.example" "$CONFIG_DIR/config.yaml"
  echo "    ✔ 已建立 $CONFIG_DIR/config.yaml（請編輯後再啟動服務）"
else
  echo "    已有 config.yaml，保留現有設定"
fi
chmod 640 "$CONFIG_DIR/config.yaml"

# ── 6. 安裝並啟用 systemd service ────────────────────────────────────────────
echo "[6/6] 安裝 systemd service"
cp "$SCRIPT_DIR/xdr-agent.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable xdr-agent

echo ""
echo "=== 安裝完成 ==="
echo ""
echo "下一步："
echo "  1. 編輯設定檔：sudo nano $CONFIG_DIR/config.yaml"
echo "     填入 tenant_id、gateway_url、log 來源路徑"
echo ""
echo "  2. 啟動服務：  sudo systemctl start xdr-agent"
echo "  3. 查看狀態：  sudo systemctl status xdr-agent"
echo "  4. 即時 log：  sudo journalctl -u xdr-agent -f"
echo ""
echo "  移除服務：     sudo systemctl disable --now xdr-agent && sudo rm $SERVICE_FILE"
