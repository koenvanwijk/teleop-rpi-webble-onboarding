#!/usr/bin/env bash
set -euo pipefail
# Return a simple JSON list of found SSIDs
if command -v nmcli >/dev/null 2>&1; then
  nmcli -t -f SSID dev wifi | awk 'length>0' | awk '!seen[$0]++' | jq -R . | jq -s .
else
  sudo iwlist wlan0 scan | awk -F 'ESSID:' '/ESSID/{gsub(/"/,"",$2); print $2}' | awk 'length>0' | awk '!seen[$0]++' | jq -R . | jq -s .
fi
