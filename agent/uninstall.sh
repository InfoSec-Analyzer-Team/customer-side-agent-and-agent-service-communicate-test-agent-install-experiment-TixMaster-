#!/usr/bin/env bash
# uninstall.sh — 移除 XDR Agent
#
#   sudo bash uninstall.sh            # 保留設定與 buffer（可重裝後續傳）
#   sudo bash uninstall.sh --purge    # 連設定、憑證、buffer、log 一併刪除
#
# 預設保留 /etc/xdr-agent 與 /var/lib/xdr-agent：buffer.db 內可能還有尚未送出的
# 事件，checkpoint.json 記錄了讀到哪一行；砍掉會造成重裝後重送或漏送。

set -euo pipefail

INSTALL_DIR="/opt/xdr-agent"
CONFIG_DIR="/etc/xdr-agent"
BUFFER_DIR="/var/lib/xdr-agent"
LOG_DIR="/var/log/xdr-agent"
SERVICE_FILE="/etc/systemd/system/xdr-agent.service"
AGENT_USER="xdr-agent"

PURGE="no"
if [[ "${1:-}" == "--purge" ]]; then PURGE="yes"; fi

[[ "$EUID" -eq 0 ]] || { echo "請用 root 執行：sudo bash uninstall.sh" >&2; exit 1; }

echo "=== 移除 XDR Agent ==="

if systemctl list-unit-files 2>/dev/null | grep -q '^xdr-agent\.service'; then
  echo "[1/3] 停止並停用服務"
  systemctl disable --now xdr-agent >/dev/null 2>&1 || true
  systemctl reset-failed xdr-agent >/dev/null 2>&1 || true
else
  echo "[1/3] 服務未安裝，跳過"
fi
rm -f "$SERVICE_FILE"
systemctl daemon-reload

echo "[2/3] 移除程式：$INSTALL_DIR"
rm -rf "$INSTALL_DIR"

if [[ "$PURGE" == "yes" ]]; then
  echo "[3/3] --purge：刪除設定、憑證、buffer 與 log"
  rm -rf "$CONFIG_DIR" "$BUFFER_DIR" "$LOG_DIR"
  if id "$AGENT_USER" &>/dev/null; then
    userdel "$AGENT_USER" 2>/dev/null || true
    groupdel "$AGENT_USER" 2>/dev/null || true
  fi
else
  echo "[3/3] 保留設定與資料（要一併刪除請加 --purge）："
  echo "        $CONFIG_DIR   （config.yaml、secrets.env）"
  echo "        $BUFFER_DIR   （buffer.db、checkpoint.json）"
  echo "        $LOG_DIR      （agent.log）"
fi

echo ""
echo "=== 移除完成 ==="
