#!/usr/bin/env bash
set -euo pipefail
sudo systemctl daemon-reload
# If firstboot flag exists in /boot, enable firstboot, else just enable ble service
if [[ -f /boot/firstboot.flag ]]; then
  sudo systemctl enable firstboot.service
else
  sudo systemctl enable ble_onboard.service
fi
echo "Services enabled."
