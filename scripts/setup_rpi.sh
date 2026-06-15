#!/usr/bin/env bash
set -euo pipefail

echo "Adding smartalarm user and hardware groups..."
sudo useradd -m -s /bin/bash smartalarm 2>/dev/null || true
sudo usermod -aG audio,gpio smartalarm

echo "Checking audio devices..."
aplay -l

echo "If using HiFiBerry AMP4, ensure it is configured in /boot/config.txt and rebooted."

echo "If using RTC, enable i2c in raspi-config and verify with i2cdetect -y 1."