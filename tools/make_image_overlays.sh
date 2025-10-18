#!/usr/bin/env bash
# Copy boot overlay and prepare root overlay for a flashed SD card.
# Usage:
#   BOOT_MNT=/media/$USER/boot ROOT_MNT=/media/$USER/rootfs ./tools/make_image_overlays.sh
set -euo pipefail
BOOT_MNT=${BOOT_MNT:-/mnt/boot}
ROOT_MNT=${ROOT_MNT:-/mnt/rootfs}

if [[ ! -d "$BOOT_MNT" || ! -d "$ROOT_MNT" ]]; then
  echo "Please set BOOT_MNT and ROOT_MNT to your mounted SD partitions."
  exit 1
fi

mkdir -p "$BOOT_MNT"
mkdir -p "$ROOT_MNT/usr/local/teleop" "$ROOT_MNT/etc/teleop" "$ROOT_MNT/etc/systemd/system"

# Boot files
cp -v firmware/boot/* "$BOOT_MNT/"
# Systemd + scripts
cp -v firmware/systemd/*.service "$ROOT_MNT/etc/systemd/system/"
cp -v firmware/scripts/* "$ROOT_MNT/usr/local/teleop/"
chmod +x "$ROOT_MNT/usr/local/teleop/"*.sh || true

# Default env if none in boot
if [[ ! -f "$BOOT_MNT/onboarding.env" ]]; then
  cp -v config/onboarding.env.example "$ROOT_MNT/etc/teleop/onboarding.env"
fi

echo "Overlay copy done."
