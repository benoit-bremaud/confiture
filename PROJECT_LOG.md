# Project log

## 2026-10-27 — Project bootstrap

- Hardware triage (power + boot LEDs): Pi #1 (Pi 1) OK with the 2015 card; Pi #2 (Pi 1) OK with its
  original card (first failure was a card seating issue); Pi #3 (Pi 3) not yet observed.
- Decision (MCDA): test the Pi 1s with the existing 2015 card as-is (405/500) rather than reflash (380/500).
- Flashed a 32 GB microSD with Raspberry Pi OS Lite 32-bit trixie 2026-10-06 (SHA-256 verified),
  SSH enabled. First boot on Pi #3 had no network (no Ethernet, no Wi-Fi entered) — to redo at home.
- Decision (MCDA): project name `confiture` (410/500); fallback `pi-phoenix` (400/500).
- Scope decision: the project is a fully local personal voice assistant (satellite + brain architecture).

## 2026-10-27 — Pi 3 on Wi-Fi and health check

- First home boot: no network. Root cause: cloud-init had cached its first run (`instance-id`
  `nocloud`), so bumping `instance_id` did not re-apply user-data/network-config; wlan0 was also
  rfkill-blocked. Clearing `/var/lib/cloud` did not help: the root filesystem was badly corrupted
  (`e2fsck` fixed many directory/inode errors) and mounted read-only.
- `f3probe`: the 32 GB card is genuine (29.30 GB usable = announced). Corruption most likely from
  unplugging during writes. Rule: unplug a Pi only once the green LED has stopped blinking.
- Decision (MCDA): keep the tested 32 GB card (475/500) over untested 64 GB cards (225/500); test
  those with `f3probe` before use.
- Reflashed (SHA-256 verified image), reran `scripts/configure-sd.sh` — with `bash`, not `sh`
  (`read -s` is a bashism). Pi 3 joined Wi-Fi as `pitest.lan` (<pi3-ip>), SSH key installed.
- Health: Pi 3 Model B rev 1.2, trixie armv7l, 39.7 °C idle, `get_throttled=0x0`, 920 MiB RAM,
  1.8/29 GB used, no ext4/mmc errors, Wi-Fi ch 10 (2.4 GHz) signal 67 %, cloud-init done.
  Unknown USB device GEMBIRD `1908:3261` plugged in (to identify).
