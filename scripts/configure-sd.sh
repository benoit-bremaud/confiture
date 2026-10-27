#!/usr/bin/env bash
# Writes cloud-init user + Wi-Fi config onto a freshly flashed Raspberry Pi OS boot partition.
# Secrets are typed interactively and never echoed or stored in plain text (password is hashed).
set -euo pipefail

BOOT="${1:-/run/media/vev/bootfs}"
[ -f "$BOOT/user-data" ] || { echo "No user-data in $BOOT" >&2; exit 1; }

read -rp "Username: " USERNAME
HASH=$(openssl passwd -6)   # prompts for the password twice, prints only the hash
read -rp "Wi-Fi SSID (empty = Ethernet only): " SSID

cat > "$BOOT/user-data" <<EOF
#cloud-config
hostname: pitest
users:
  - name: $USERNAME
    groups: [sudo, adm, video, plugdev, netdev]
    shell: /bin/bash
    lock_passwd: false
    passwd: "$HASH"
ssh_pwauth: true
EOF

if [ -n "$SSID" ]; then
  read -rsp "Wi-Fi password: " WIFIPASS; echo
  cat > "$BOOT/network-config" <<EOF
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      optional: true
  wifis:
    wlan0:
      dhcp4: true
      optional: true
      regulatory-domain: FR
      access-points:
        "$SSID":
          password: "$WIFIPASS"
EOF
fi

sync
echo "Done: user '$USERNAME' configured${SSID:+, Wi-Fi '$SSID'}."
