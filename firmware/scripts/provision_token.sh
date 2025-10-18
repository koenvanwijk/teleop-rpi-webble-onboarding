#!/usr/bin/env bash
set -euo pipefail
# Ensure onboarding.env exists and SETUP_TOKEN present
if ! grep -q "^SETUP_TOKEN=" /etc/teleop/onboarding.env; then
  echo "SETUP_TOKEN=$(cat /proc/sys/kernel/random/uuid)" | sudo tee -a /etc/teleop/onboarding.env >/dev/null
fi
