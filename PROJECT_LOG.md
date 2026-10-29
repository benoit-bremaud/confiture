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
  - Mic switched off by the owner (orange LED). To do: check the Google Cast
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
- ProBook (`hp-probook`, user `<user>`, SSH key already accepted): sleep, suspend, hibernate and
  hybrid-sleep targets masked; `/etc/systemd/logind.conf.d/no-lid-sleep.conf` ignores the lid
  (logind restarted at 02:40 to apply it: `HandleLidSwitch` and `HandleLidSwitchExternalPower`
  read `ignore`). Verified: lid closed at 02:40:59, SSH still answers, no reboot, on mains power.
  Masked by mistake on the work PC first, then unmasked there.
- Ollama installed on the ProBook overnight (ADR-0004 prep, Docker without sudo, skill
  `docker-hardening` applied proportionally to this third-party image):
  `ollama/ollama:0.12.6@sha256:a61a8fd395db…`, `--restart unless-stopped`, `--user 1000:1000`
  (named volume `ollama-models` chowned to 1000, `HOME=/data`, `OLLAMA_MODELS=/data/models`),
  `--cap-drop ALL`, `no-new-privileges`, HEALTHCHECK `ollama list` → `healthy`; verified Uid
  1000, `CapEff 0`, `NoNewPrivs 1`. Port 11434 published on all interfaces (home LAN behind the
  box). `qwen2.5:3b` pulled (1.9 GB). First unhardened container removed. Gotcha again:
  `pkill -f` over SSH killed my own shell (pattern in its command line) → kill by PID.
- Test from the work PC: 11.7 s incl. cold load, 8.6 tok/s, but the answer **switched to Chinese**
  mid-sentence → the system prompt must force French ("Réponds uniquement en français").
- Follow-ups: fixed DHCP lease for .167; compose file for this container in the repo; Trivy scan
  of the image; system prompt; connect Home Assistant; `~/ollama-install.log` left on the ProBook.
- Yuki persona: `config/ollama/yuki.Modelfile` (French-only SYSTEM rule, temperature 0.4,
  num_predict 160) built as model `yuki` on the ProBook. 5 test questions: **all answers in
  French** (English question included); "I don't know" works on an obscure question; but
  answers still run long (5 sentences) and contain factual errors (sky, salty sea) — expected
  from a 3B model, revisit with the GPU host. Times 2–15 s warm, 19 s on first load.
- Box DHCP reservation added (Réseau > LAN > LAN DHCP): ProBook `<mac>` →
  `<probook-ip>`, hostname `hp-probook`, rule active; listed next to bb-homelab (<pi5-ip>).
- Box DHCP reservation added for the Nest Mini: `<mac>` → `<nest-mini-ip>`,
  hostname `nest-mini-sejour`, rule active.
- Box DHCP reservation added for the Pi 3: `<mac>` → `<pi3-ip>`, hostname
  `pitest`, rule active. The Pi 5 (`<pi5-ip>`) was already reserved as bb-homelab.
- Box DHCP reservation added for the projector: `<mac>` → `<projector-ip>`,
  hostname `projector`, rule active (entered by hand, projector offline). The MAC is
  Android-randomised: if the projector shows up at another IP, set its Wi-Fi privacy to
  "device MAC" and update the reservation.
- Box DHCP reservation added for the ESPHome device: `<mac>` → `<esphome-ip>`,
  hostname `espectre-01`, rule active.
- Box DHCP reservation added for the Zigbee coordinator: `<mac>` → `<zigbee-coordinator-ip>`,
  hostname `zigbee-coordinator`, rule active. MAC read with `ip neigh` (absent from the box's
  client list); it is locally administered, so re-check if the coordinator changes IP.
  7 of 10 reservations used.
- Box DHCP reservation added for the owner's phone: `<mac>` → `<phone-ip>`,
  hostname `owner-phone`, rule active (MAC read with `ip neigh`). 8 of 10 reservations used.
- Box DHCP reservation added for the work PC: `<mac>` → `<work-pc-ip>`,
  hostname `<work-pc-hostname>`, rule active. 9 of 10 reservations used.

## 2026-10-28 — Nest Mini in Home Assistant

- The Google Cast integration was already set up on the Pi 5 (HA 2026.6.2, host network) and
  had found the new Nest Mini (UUID `16acebbd…`, matches `eureka_info`). Cast link works:
  volume read at 0.6.
- Audible test (owner choice C, local sound, MCDA 440 vs Piper 410 vs Google Translate TTS 260):
  `connection_test.mp3` served from the work PC and cast with pychromecast at volume 0.3, then
  restored to 0.6. Owner heard it. HA logged a "Failed to cast media" for that URL afterwards
  (temporary server stopped); harmless.
- Owner choices applied with HA stopped (registry backups `*.bak-2026-10-28` in `.storage`):
  stale `media_player.sejour` (old device `3cb6ec83…`) and its device removed;
  `media_player.nestmini1401` renamed `media_player.nest_mini_sejour`. HA back up, 45 entities.
- Seen in passing: HA lacks `NET_ADMIN`/`NET_RAW` for Bluetooth recovery (bb-homelab compose,
  read only here). Google Translate TTS (cloud) stays installed but unused (NFR-1).
- Next: Piper (local French TTS) with the voice pipeline; port 8123 does not answer from the LAN
  (HA reached through SSH only).
- Nest Mini default volume (owner rule): 50 % from 07:00, 30 % from 21:00, for every sound
  including night alerts (owner choices). HA automation `nest_mini_default_volume` appended to
  `/config/automations.yaml` (backup `automations.yaml.bak-2026-10-28`); triggers at 07:00,
  21:00, HA start and the Nest Mini coming back online. `check_config` clean, HA restarted,
  volume read 0.6 → 0.5 right after start (08:xx). Not yet tracked in a repo (HA config lives
  in `/mnt/appdata/homeassistant`).
- DHCP: reservation for a family laptop not done — not on the network (full sweep .2–.254, absent
  from `ip neigh`); owner dropped it for now. When it is done: read its Wi-Fi MAC and set
  "Private Wi-Fi address" to Fixed for the home network. Last free slot: 9 of 10 used.
- State of the follow-ups: done today — ProBook fixed lease, Google Cast check in HA, Nest
  Mini volume schedule. Open — Ollama ↔ HA (A, waits on the owner validating ADR-0004/0005
  weights); compose file + Trivy scan for Ollama (B); Piper local TTS; HA config under version
  control; WAA auto-delete 3 months; `configure-sd.sh` (power save off, `i2c,gpio`); Pi 3
  Wi-Fi drops; projector teardown and dev options off; remove `~/ollama-install.log` on the
  ProBook.
- ADR-0004 (B, Pi 5 voice pipeline + ProBook LLM, 385) and ADR-0005 (A, local LLM only, 395)
  accepted by the owner after a detailed walk-through of weights and sensitivity. Open check:
  speech-to-text speed on the Pi 5 (assumed in B's responsiveness score, not measured yet).
  Unblocks Ollama ↔ Home Assistant.

## 2026-10-28 — Ollama connected to Home Assistant

- UML first: `docs/architecture/diagrams/voice-assistant/02-sequence-ask-a-question.md`
  (local intents first, LLM fallback, LLM host down).
- HA (UI through Tailscale `<pi5-tailscale-ip>:8123`): Ollama integration at
  `http://<probook-ip>:11434`; conversation agent "Yuki" — model `yuki:latest` (the default
  `qwen3:4b-instruct` was not picked: HA would have pulled it), French instructions copied from
  `config/ollama/yuki.Modelfile` (HA sends its own system prompt, so the Modelfile SYSTEM is
  not enough), "Assist" control **off** (`llm_hass_api: []`), think off, keep alive -1,
  context 8192, history 20. Assist pipeline "Yuki" — French, agent `conversation.yuki`,
  "Prefer handling commands locally" on, no STT/TTS yet; "Home Assistant" (English) stays
  the preferred pipeline.
- Text tests through `assist_pipeline/run`:
  - "quelle heure est-il ?" → local, 0.4 s.
  - "pourquoi le ciel est-il bleu ?" → LLM, 26.7 s cold, answer wrong (nitrogen/"ethylene").
  - spider legs 3.2 s (right), short joke 4.6 s — warm.
  - Ollama stopped: local intent still answers (0.01 s); LLM path fails fast (0.06 s) with
    HA's generic `intent-failed`. Ollama restarted, healthy.
  - "pourquoi la mer est salée ?" → 23 s right after restart, answer partly wrong.
- Gotchas: NordPass's autofill overlay on HA text fields blocks every Chrome-extension action
  until closed; the HA code editor auto-indents typed lines (harmless leading spaces).
- Follow-ups: friendly "I can't think right now" answer when the LLM host is down (ADR-0004);
  cold start ≈ 25 s breaks NFR-5 — keep the model loaded (`OLLAMA_KEEP_ALIVE` on the container
  is 30m; HA asks -1); factual quality stays the 3B limit (GPU host). Voice tests next: Nest
  Mini as speaker, the webcam as microphone, Pi 3 camera for visual checks (owner suggestion),
  after Piper and a speech-to-text engine are in place.

## 2026-10-28 — Ollama upgrade and model benchmark (in progress)

- Ollama 0.12.6 (released 2025-10-15, a year old: my pinning checked "at least two weeks old"
  but not "not too old") could not pull `gemma3:4b` (republished) nor `ministral-3:3b`
  (supported since 0.13.1). Owner chose 0.40.4 (MCDA 475 vs 0.40.12 380 vs stay 155).
  Upgraded: `ollama/ollama:0.40.4@sha256:926d40fd…b1a6`, same flags, same volume; Uid 1000,
  CapEff 0, NoNewPrivs 1, healthy; HA → yuki answered (14.5 s cold). Old container kept stopped
  as `ollama-0.12.6` for rollback.
- Pulled: `qwen3:4b-instruct-2507-q4_K_M`, `gemma3:4b`, `ministral-3:3b` (all three done).
  False alarm: the "ProBook down" was the work PC leaving the home LAN with the owner
  (now on an outside network); the ProBook stayed up (uptime 8 h 39). From outside, reach the LAN
  through the Pi 5 on Tailscale: `ssh -J <user>@<pi5-tailscale-ip> <user>@<probook-ip>`.
- Benchmark script ready (scratchpad `bench.py`): 7 French/English questions, Yuki system
  prompt, warm timings; run on qwen2.5:3b, qwen3:4b-instruct, gemma3:4b, ministral-3:3b.
- Option A (friendly answer when the LLM is down), first attempt reverted: a wildcard
  `custom_sentences` intent + `intent_script` catch-all. HA always prefers custom sentences
  over built-in intents, so it stole "quelle heure est-il ?" too, and the script (mode
  `single`) failed with "Already running". Config restored from `configuration.yaml.bak-2026-10-28`,
  files removed, HA restarted, pipeline "Yuki" checked (agent `conversation.yuki`, French,
  prefer local on).
- Benchmark, warm means (7 questions): qwen2.5:3b 6.3 s (8.3 tok/s, short, one wrong answer,
  says "je ne sais pas" on the trap question); qwen3:4b-instruct 13.0 s (emojis, invents
  family details); gemma3:4b 17.2 s (invents a 1987 curling winner); ministral-3:3b 11.4 s
  (invents a winner and a captain, Markdown, emojis, follow-up questions). MCDA (speed 35,
  reliability 35, spoken style 20, RAM 10): qwen2.5:3b 410, qwen3 245, gemma3 215,
  ministral-3 165. The three losers and `ollama-0.12.6` still on disk (about 8 GB): delete
  only with the owner's approval.

## 2026-10-28 — LLM-down measurement and family question test

- Measured the LLM-down path on the "Yuki" pipeline (Ollama container stopped about one
  minute): free question → `intent-failed` "Unexpected error during intent recognition" in
  0.1 s (English, technical; in voice, probably silence, unverified); local intent unaffected.
  Not covered: the ProBook powered off (TCP timeout, possibly much longer). Owner decision
  (MCDA): A1, keep the generic error now (420 vs A2 custom agent 375 vs A3 HACS 320).
  **Follow-up: build A2 (own fallback conversation agent with its own timeout) at the voice
  step** — no GitHub remote yet, so no issue: tracked here.
- Gotcha: the preferred pipeline is still "Home Assistant" (English); my first test hit it by
  mistake. Pass `pipeline` explicitly, and pick "Yuki" for the Nest and microphones later.
- T1, 20 family questions on `yuki` (qwen2.5:3b), owner-chosen test: cold start 10.7 s (load
  3.6 s); mean 5.6 s, median 4.7 s, max 20.3 s (crêpes recipe, cut by `num_predict 160`).
  About 5 of 20 wrong, one unsafe ("hard-boiled egg 12-15 min in the microwave"); the
  French-only rule turned "merci en espagnol" into "merci". A rerun shows high variance
  (Mona Lisa once credited to Magritte).
- M1 (owner choice, MCDA 405): Modelfile rules added (translations allowed, recipe in one
  sentence first, safe advice and ask an adult). Gotcha: Ollama 0.40.4 rejects `create -f -`
  from stdin; copy the file into the container first. Rerun: mean 4.9 s, median 3.9 s, max
  19.5 s; still about 5 of 20 wrong (egg "5-6 min in a pan", "merci" again, horse fastest,
  numbered list on "peur du noir"). Prompt rules do not fix the 3B model's knowledge.
  HA sends its own copy of the instructions: the new rules are not in HA yet.
- Cleanup (owner D1 440, E1 440): deleted `ministral-3:3b`, `gemma3:4b`,
  `qwen3:4b-instruct-2507-q4_K_M`, container `ollama-0.12.6` and image `ollama/ollama:0.12.6`
  (about 12 GB). Left: `yuki`, `qwen2.5:3b`, Ollama 0.40.4.
- N1 (owner): HA agent "Yuki" instructions replaced by the Modelfile SYSTEM text through the
  subentry reconfigure flow (other options unchanged: `yuki:latest`, no HA API, ctx 8192,
  history 20, keep alive -1, think off). Check: "merci en espagnol" still wrong (13.6 s).
  Gotcha: "combien de temps faut-il pour cuire un œuf dur ?" is caught by HA's built-in
  timer intent ("Il n'y a aucun minuteur", 0.2 s) and never reaches the LLM.
- N2 as a reference only (owner): temporary `yuki7b` (same Modelfile, `FROM qwen2.5:7b`), same
  20 questions. Cold start 40.9 s (load 14.4 s); mean 17.5 s, median 16.7 s, max 44.9 s.
  Better: egg (9-12 min, boiling water), "gracias", Napoléon. Still about 5 of 20 wrong or
  unusable: "trente-six cinquante-six jours", hesitates on the Mona Lisa, pigeon fastest,
  77 million French, a non-joke cut mid-sentence, invents "Maman". Conclusion: a 7B is 3.5
  times slower for a small quality gain; it does not justify buying a GPU host just to run
  a 7B. Deleted `yuki7b` and `qwen2.5:7b`; `yuki` reloaded and answering through HA.
- HA config in git: not now (owner G3, MCDA 410 vs Yuki-only files 385 vs full copy 275).
  `configuration.yaml` is a bb-homelab seed (its ADRs 0003/0005/0007), so bb-homelab stays
  its source of truth; HA makes a full backup nightly at 03:15 (3 kept, 20-36 MB) but on the
  Pi 5's own disk. **Follow-up for bb-homelab (not this repo): copy HA backups off the Pi 5.**
  Next: brainstorm the voice step.
- Voice-step brainstorming done with the owner, every answer by MCDA: REQ-14 to REQ-20 and
  the iteration 1 success criterion recorded in `docs/architecture/specs/voice-assistant-needs.md`
  (Pi 5 listens in the living room, Nest output, Zigbee/Wi-Fi lamp as listening light, voice
  pause with auto-resume, 7-day text log, young child 8/10 criterion). Next: technical choices
  (speech-to-text engine, Piper voices, wake word "Yuki" model), then UML.

## 2026-10-28 — Brick 0: publish the repository (issue benoit-bremaud/confiture#1)

- Public repo `benoit-bremaud/confiture` created (owner P1: public during development,
  private later), GitHub project 76, secret scanning and push protection on.
- Two history scrubs removed personal and network data; real values live in the gitignored
  `inventory.local.md`. `CLAUDE.md` forbids sensitive data; `.env.example` has placeholders.
- CI: gitleaks with personal-data rules (MAC, private IPv4, Tailscale), no report artifact.
- Pre-push review (`docs/architecture/review-local.md`): Must 1 and Should 9 resolved.
- **Waiver** (owner, MCDA 450/500): pre-merge gate steps 1–2 (tests, coverage) waived until
  the first PR with executable code; shellcheck and actionlint run locally meanwhile.
- SonarQube on every local CI run (owner rule, all projects; global rule tracked in
  benoit-bremaud/agents-skills#159): `sonar-project.properties` added, local scan PASSED, 0 issues.

## 2026-10-28 — Brick 1: Piper text-to-speech (issue benoit-bremaud/confiture#4)

- Piper (`wyoming-piper` 2.5.2, voice `fr_FR-siwis-medium`) deployed on the Pi 5 from
  `deploy/pi5/` (owner approved the download), loopback only, healthy; Wyoming integration
  added in Home Assistant (`tts.piper`). ADR-0006 records the three MCDA choices.
- Blockers found and fixed: Piper wants `fr_FR`, not `fr`; Home Assistant never loaded
  scripts (benoit-bremaud/home-assistant#32); the Nest could not fetch the audio because UFW
  drops 8123 from the LAN, so 8123 opens to the Nest only (benoit-bremaud/bb-homelab#162) and
  `internal_url` is the Pi LAN URL.
- The ProBook "sleep" was Ollama down: `docker.service` was socket-activated only; the owner
  enabled it at boot.
- Measured: answer text 2.0 s warm (16.6 s cold), the Nest starts playing at 2.2 s.
- Gotcha: in zsh, `scp -r deploy/pi5 $HOST:confiture-pi5` reads `:c` as a history modifier and
  copies locally; write `${HOST}:confiture-pi5`.

## 2026-10-29 — Brick 2: Pan-Tilt camera agent (benoit-bremaud/confiture#3, benoit-bremaud/confiture#7)

- The Pi 3 agent was split into a pure domain and adapters (ADR-0007, MCDA 445/500 vs single
  file 335 and full hexagonal 345); UC12, aim-and-look sequence and deployment diagrams added.
- Scope decisions (owner, MCDA): the "recentre" button is the "Position par défaut" saved
  position; the TSL25911 light sensor moved to benoit-bremaud/confiture#8.
- review-local found two inputs that killed the MQTT thread (`inf`, invalid UTF-8), a
  corrupt-JSON restart loop and unlocked shared state; all fixed. Codex then found four real
  hardware and privacy issues: the PCA9685 forgets its 50 Hz prescale on power loss, a failed
  move left the PWM on, a crashed move's pulse resumed at restart, and a capture finishing after
  "camera off" was still published; all fixed. One remaining window (a capture starting
  microseconds after OFF) is accepted: its image is dropped, see the README.
- Deployed on the Pi 3 (prototype backed up in `~/pi3cam-backup/`); hardware smoke 19/19 over
  MQTT after each fix. 72 unit tests, SonarQube gate passed, merged as 8d9fda4.
- Merged without a staging tier, under the owner's waiver until staging exists in every
  project.
- Gotchas: the Pi 3 user is not the laptop user (`ssh <user>@pitest.lan`); it does not answer
  ping, so test SSH, not ping; `pkill -f "<pattern>"` over SSH kills the SSH command itself,
  so use a `[p]attern`.

## 2026-10-29 — Brick 3: TSL25911 illuminance sensor (issue benoit-bremaud/confiture#8)

- The Pan-Tilt HAT light sensor (I²C 0x29, ID 0x50) is now an HA `sensor` (lux) on
  `confiture/pi3/illuminance`, published every 30 s; UC3 partly realised (traceability matrix).
- Decision (MCDA): auto-gain 1×/25×/428× in the domain (450/500) over fixed medium gain (430)
  and fixed low gain (375): the camera may face a window, where 25× saturates near 6000 lx.
- Design: a separate `LightMeter` domain class (the `Agent` stays unchanged); the lux equation
  and gain choice are pure functions; a reading saturated at 1×, failed, or flickering across
  gains is not published. The sensor gets its own `SMBus` handle: smbus2 keeps the slave
  address per handle, so the mover and light threads must not share one.
- Unit tests caught a sign bug: infrared above full spectrum gave a positive lux.
- Hardware check on the Pi 3 (evening, room light): 30.7 lx at 25×, 31.1 lx at 428× on the same
  scene, 34 lx at 1× (coarse at low light, as expected); HA Discovery config and states seen
  on the broker. Previous agent files backed up in `~/pi3cam-backup/pre-8/`.

## 2026-10-29 — Hardening of Piper and yuki_say (issue benoit-bremaud/confiture#5)

- Piper container now `read_only` with a `/tmp` tmpfs and `mem_limit: 512m` (MCDA 430/500 over
  1g 400 and 256m 345); `deploy/pi5/.env.example` lists the `PIPER_*` defaults.
- Checked on the Pi 5: a fresh read-only container downloads the voice into `data/` and turns
  healthy; the redeployed `confiture-piper` is healthy with a read-only root.
- Gotcha: the Pi 5 kernel has no memory cgroup (`Limitation discarded`), so `mem_limit` is
  inert until `cgroup_enable=memory` is set on the host; documented, host change not made.
- `yuki_say`: `max: 3` on the queue; the header states it is the UI paste format.
- Log references now use full `owner/repo#N`.

## 2026-10-30 — Pi 5 memory cgroup for Piper (issue benoit-bremaud/confiture#14)

- Kernel `6.18.50+rpt-rpi-2712`: the firmware adds `cgroup_disable=memory`. Decision (MCDA):
  `cgroup_enable=memory` alone (475/500) over adding the legacy `cgroup_memory=1` (430);
  appended to `/boot/firmware/cmdline.txt` (dated backup kept on the host), rebooted.
- After the reboot the `memory` controller is listed and `docker run -m 64m` gives no warning,
  but `confiture-piper` still had `HostConfig.Memory` 0: it must be recreated after the change.
- Measured with a 1047-character sentence over Wyoming (~24 s of audio in 10.6 s): Piper hit
  the 512 MiB limit 435 times and pushed 167 MiB to swap, no OOM kill; it
  keeps ~500 MiB resident when idle. The ~200 MB estimate of benoit-bremaud/confiture#5 was wrong.
- Decision (MCDA): `mem_limit: 1g` (440/500) over 768m (400) and keeping 512m (330). Re-measured
  at 1g: peak 731 MiB, no swap, no limit hit, synthesis in 9.4 s; ~730 MiB resident when idle.
- The bb-homelab repository does not document the kernel command line; no change there.
