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

## 2026-10-28 — 64 GB card, Pan-Tilt calibration, LLM benchmarks

- 16 GB card dead (not detected by two readers). 64 GB card: `f3write`/`f3read` stopped at the
  owner's request; flashed directly, Pi 3 boots, survives reboots, 0 ext4/mmc errors.
- Reintroduced one change at a time: I²C enabled → reboot OK; HAT mounted → boot OK. HAT is a
  Waveshare Pan-Tilt HAT: PCA9685 at 0x40 (+0x70 all-call), TSL25911 light sensor at 0x28/0x29.
  `<user>` added to `i2c,gpio` groups (todo: add them to `scripts/configure-sd.sh`).
- Servo calibration (pulse width; directions from the camera's point of view; slow ramp
  ~100 µs/s; signal cut after each move). Redo calibration later, Pi placed high:

  | Axis | PCA9685 channel | Limit A | Centre | Limit B |
  |---|---|---|---|---|
  | Pan | 1 | right 500 µs | 1625 µs | left 2750 µs |
  | Tilt | 0 | up 500 µs | 1650 µs | down 2300 µs (provisional) |

  Tilt down: servo forced at 2750 and 2800 µs, and image barely changed past ~2300 µs with no
  obstacle → provisional limit 2300 µs.
- Method: no servo feedback, so position is checked by photo diff between steps (image mean
  difference ~30 while moving, ~7 when stalled).
- Pi 3 Wi-Fi drops for 30–60 s several times (Pi never rebooted, `throttled=0x0`): likely
  brcmfmac power saving → disable Wi-Fi power save before the satellite goes live.
- LLM benchmark (Ollama 0.12.6 in a temporary container, 3 French prompts, 120 tokens max;
  everything removed afterwards):

  | Host / model | TTFT | tok/s | short answer | 120 tokens |
  |---|---|---|---|---|
  | Pi 5 `qwen2.5:3b` | 3.0 s | 5.3 | 16 s | 26 s |
  | Pi 5 `llama3.2:3b` | 3.2 s | 4.8 | 17 s | 28 s |
  | HP ProBook 450 G5 (i5-8250U, 8 GB) `qwen2.5:3b` | 1.4 s | 8.0 | 8.7 s | 16.7 s |
  | ProBook `llama3.2:3b` | 1.5 s | 7.8 | 9.8 s | 17.3 s |
  | ProBook `qwen2.5:7b` | 3.2 s | 3.6 | 13.5 s | 37 s |

  Only the ProBook + 3B model meets NFR-5 for short answers. All models make factual errors;
  llama3.2 refused a recipe ("mineurs") → guard with a system prompt, short answers, "I don't know".
- Incident: the Ollama image filled the Pi 5 SD card to 97 % (861 MB free) — models were on the
  SATA disk but Docker's root is on the SD. Cleaned up (back to 71 %). Lesson: never pull large
  images on the homelab SD; check `docker info` root dir first.
- Future brain host (owner): a more powerful machine later. MCDA: PC with a ≥ 8 GB NVIDIA GPU 380,
  mini-PC without GPU 345, NAS 290 (NAS = storage, not inference). To fold into the Q2 ADR.

## 2026-10-28 (night) — Pi 3 Wi-Fi power save, Nest Mini, projector, brain ADRs

- Pi 3: Wi-Fi power save was on (`802-11-wireless.powersave: 0 (default)`). Disabled with
  `/etc/NetworkManager/conf.d/wifi-powersave-off.conf` (`wifi.powersave = 2`), NetworkManager
  restarted, `wlan0` reconnected. `iw` not installed, so driver state unverified; watch whether
  the 30–60 s drops stop. To add to `scripts/configure-sd.sh` (with groups `i2c,gpio`).
- Google Nest Mini (2nd gen) → REQ-12 announcement speaker (MCDA: Cast output 420, Google
  Assistant alongside 165, unused 350). Firmware locked to Google, so output only, never a
  satellite. Set up from the owner's phone over adb (Google Home app):
  - Old offline "Séjour" device removed; new device "Nest Mini Sejour" (no accent: adb
    `input text` cannot type it), room Séjour, `<nest-mini-ip>`, MAC `<mac>`.
  - Off: usage stats, ultrasound sensing, cast control from other devices, personal results,
    music services, marketing e-mails. Voice Match never offered (screen would not open).
  - Child filters for everyone: videos blocked, non-explicit music, news on, non-explicit
    podcasts, calls blocked. Downtime skipped (could block night ESPectre alerts; quiet hours
    will live in Home Assistant). Equaliser left flat. Auto firmware updates kept.
  - Owner choices: Wi-Fi password from the saved Google entry; Google Assistant terms accepted;
    WAA auto-delete at 3 months approved but **not applied yet**.
  - To do: owner flips the physical mic switch (orange LED); check the Google Cast
    integration in Home Assistant.
- REQ-13 (remote visual check after ESPectre alerts, NoIR at night) and Q8 (remote access,
  Tailscale first at 460) added to the needs document.
- LAN map (ping sweep): 10 hosts found; addresses kept in `inventory.local.md` (gitignored).
- Projector ("smart-projecteur", Android 13, randomised MAC
  `<mac>`, `<projector-ip>`, confirmed by power-cycling). No Android TV Remote (6466/6467),
  no Cast. Developer options, USB debugging, wireless debugging, "Internet Adb" and "Android
  bug collector" enabled by the owner; pairing failed and a full TCP scan (1–65535) after a
  reboot found **no open port**: "Internet Adb" does nothing. Only USB-A ports (host), so no
  USB debugging; never use an A-to-A cable. Menu read with the Pi 3 camera (manual focus
  `--lens-position 0.3` works at ~3 m). Next: owner opens it to look for UART/USB service
  pads; otherwise ESPHome IR blaster (MCDA 450 vs smart plug 295 vs nothing 270). Disable the
  unused developer options meanwhile.
- ADR-0004 (proposed): voice pipeline on the Pi 5, LLM (`qwen2.5:3b`) on the laptop — 385 vs
  Pi 5 alone 315 vs laptop alone 295. ADR-0005 (proposed): local LLM only — 395 vs hybrid 380
  vs cloud 280; fragile: flips to hybrid if quality outweighs privacy. Q2 and Q6 closed in the
  needs document. Owner to validate the weights.
- Next: owner runs `ssh-copy-id` to the ProBook (key refused), then install Ollama as a LAN
  service with a fixed IP lease.
