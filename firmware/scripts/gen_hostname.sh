#!/usr/bin/env bash
set -euo pipefail
. /etc/teleop/onboarding.env || true
PREFIX=${BRAND_PREFIX:-teleop}
MAC=$(cat /sys/class/net/eth0/address 2>/dev/null || cat /sys/class/net/wlan0/address 2>/dev/null || echo "00:00:00:00:00:00")
SUFFIX=$(echo "$MAC" | tr -d ':' | tail -c 7)
HOST="${PREFIX}-${SUFFIX}"
echo "$HOST" | sudo tee /etc/hostname >/dev/null
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$HOST/g" /etc/hosts || true
sudo hostname "$HOST"
echo "Hostname set to $HOST"
