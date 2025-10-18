#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  python3 python3-pip python3-gi \
  bluetooth bluez bluez-tools rfkill \
  qrencode \
  network-manager || true

# Python deps for GATT server
sudo pip3 install dbus-next

# Create dirs & install files
sudo mkdir -p /usr/local/teleop /etc/teleop
sudo cp -f firmware/scripts/*.py /usr/local/teleop/ || true
sudo cp -f firmware/scripts/*.sh /usr/local/teleop/ || true
sudo chmod +x /usr/local/teleop/*.sh
sudo cp -f firmware/systemd/*.service /etc/systemd/system/
# If /boot has onboarding.env, leave firstboot.service to move it;
# else copy example
if [[ ! -f /boot/onboarding.env && ! -f /etc/teleop/onboarding.env ]]; then
  sudo cp -f config/onboarding.env.example /etc/teleop/onboarding.env
fi

echo "Dependencies installed."
