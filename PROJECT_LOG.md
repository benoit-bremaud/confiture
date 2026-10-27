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

## 2026-10-27 — Cameras, failing card, Pi 5 fan

- Pi 5 (`bb-homelab`): 8 GB RAM (6.1 GB free), load ~0.1, SD 71 % full, 458 GB SATA disk at
  `/mnt/appdata`. Logitech C270 detected (`/dev/video0` + USB mic); test capture OK.
- Pi 3: Camera Module 3 (IMX708) detected via `rpicam-hello`; test still OK (mounted upside
  down, fix with `--rotation 180`). GEMBIRD `1908:3261` is a mass-storage device, not a camera.
- Decision (MCDA): mount the Pan-Tilt HAT on the Pi 3 (465/500), not the Pi 5 (170/500:
  homelab risk, 22-pin camera connector, blocks the fan).
- New need REQ-12 (to brainstorm): remote "levée de doute" — ESPectre (`espectre-01.lan`, Wi-Fi
  motion sensing) raises an alert, the owner checks a camera snapshot. Remote access option
  Tailscale scored 460/500 vs Cloudflared 340 vs open ports 180 → open question Q8, ADR later.
- After enabling I²C + reboot the Pi 3 never rejoined Wi-Fi (also without the HAT). Root cause:
  the 32 GB card — hardware read I/O errors and ext4 errors again on a fresh flash. Card
  discarded. Lesson: `f3probe` only checks real capacity; use `f3write` + `f3read` for health.
- 64 GB card: the laptop's built-in SD slot failed to initialise it (`error -123`); works in the
  USB reader. Its 1,214 photos/videos (12 GB) were saved to `02_personal/a-trier/`, the rest
  deleted on owner request. Full `f3write`/`f3read` test running overnight (~5.5 MB/s, slow).
- Pi 5 rebooted (owner): official fan detected, 5,952 rpm. zigbee2mqtt looped because its network
  Zigbee coordinator (<zigbee-coordinator-ip>:8888) was unplugged; replugged, z2m started.
- LLM benchmark on Pi 5 started (temporary `confiture-bench` Ollama container, models on the
  SATA disk; qwen2.5 1.5b/3b, llama3.2 3b). First attempt failed: IPv6 network unreachable.
