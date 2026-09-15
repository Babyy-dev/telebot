#!/bin/bash
# Run from the telebot folder on the VPS:
#   sudo bash setup-vps.sh

set -euo pipefail

APP_DIR="/opt/referral-bot"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_USER="${SUDO_USER:-$USER}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run with sudo: sudo bash setup-vps.sh"
  exit 1
fi

echo "==> Installing packages..."
apt-get update -qq
apt-get install -y python3 python3-venv python3-pip rsync

echo "==> Copying files to $APP_DIR ..."
mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude 'bot.log' \
  --exclude 'referrals.db' \
  "$SRC_DIR/" "$APP_DIR/"

chown -R "$SERVICE_USER":"$SERVICE_USER" "$APP_DIR"

echo "==> Python venv + deps..."
cd "$APP_DIR"
sudo -u "$SERVICE_USER" python3 -m venv .venv
sudo -u "$SERVICE_USER" .venv/bin/pip install -q -r requirements.txt

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Missing $APP_DIR/.env"
  echo "Copy your laptop .env here first."
  exit 1
fi

if [[ ! -f "$APP_DIR/referral_bot.session" ]]; then
  echo "Missing $APP_DIR/referral_bot.session"
  echo "On laptop: python login.py"
  echo "Then copy referral_bot.session to the VPS."
  exit 1
fi

echo "==> systemd service..."
sed "s/YOUR_USER/$SERVICE_USER/" "$APP_DIR/referral-bot.service" \
  > /etc/systemd/system/referral-bot.service
systemctl daemon-reload
systemctl enable referral-bot
systemctl restart referral-bot

echo ""
echo "Bot started."
echo "  sudo systemctl status referral-bot"
echo "  tail -f $APP_DIR/bot.log"
echo "Check Telegram Saved Messages for: Referral bot is running."
