# Pi 5 deployment

Containers that confiture owns on the Pi 5, next to the bb-homelab stack (ADR-0006).

## Piper text-to-speech

Copy the files into `~/confiture-pi5` on the Pi 5 from a checkout (placeholders, real values
in `.env`). Copy files, not the folder: `scp -r` into an existing folder would nest it and
leave the old `compose.yaml` in place. Create `data/` first: if Docker creates it, it belongs
to root and Piper, which runs as uid 1000, cannot write the voice.

```sh
ssh <user>@<pi5-host> mkdir -p confiture-pi5/data
scp deploy/pi5/compose.yaml deploy/pi5/README.md deploy/pi5/.env.example <user>@<pi5-host>:confiture-pi5/
```

First run, on the Pi 5, in `~/confiture-pi5`:

```sh
docker compose -p confiture up -d
docker compose -p confiture logs -f piper
```

Check, once the log says `Ready`:

```sh
docker inspect -f '{{.State.Health.Status}}' confiture-piper      # healthy
docker exec confiture-piper grep -E '^(Uid|CapEff)' /proc/1/status  # 1000, 0
ss -ltn | grep 10200                                               # 127.0.0.1 only
docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' confiture-piper     # true
```

- Settings: copy `.env.example` to `.env` next to `compose.yaml` only to change a default.
- `PIPER_VOICE` sets the default voice (`fr_FR-siwis-medium` if unset); Piper downloads it into
  `data/` on first start. Extra voices: copy their `.onnx` and `.onnx.json` into `data/`.
- `PI5_UID` / `PI5_GID` (formerly `PIPER_UID` / `PIPER_GID`) default to 1000: every service runs
  as this user, which owns `data/`, `whisper/`, `satellite/` and the PipeWire session.
- Home Assistant runs with host networking, so it adds Piper with the Wyoming integration at
  `127.0.0.1:10200`; ask for language `fr_FR`, not `fr` (ADR-0006).
- `mem_limit: 1g` (a ~1000-character sentence peaked at ~730 MiB) needs the kernel memory
  cgroup. The Raspberry Pi firmware adds `cgroup_disable=memory`, so append
  `cgroup_enable=memory` to the single line of `/boot/firmware/cmdline.txt` (back it up first),
  reboot, then recreate the container (`up -d --force-recreate piper`): a container created
  without the cgroup keeps `HostConfig.Memory` at 0. Check with
  `docker inspect -f '{{.HostConfig.Memory}}' confiture-piper` (1073741824).
- Update: Dependabot proposes the new tag and digest in `compose.yaml`; review it, copy the
  files again with the `scp` line above, then `docker compose -p confiture pull`, `up -d` and
  `docker image prune -a -f` (the old image is otherwise left on the card, see below).

## Disk housekeeping

On 2026-10-30 the 29 GB card reached 99 %: every image update leaves the previous image behind
(~1 GB each, 6 GB in total). Two pieces keep this from happening again, no container added:

- `docker-housekeeping.sh` removes the images no container uses and the build cache, every
  Sunday at 04:00 through a systemd timer (`Persistent=true` catches a week the Pi was off).
  It never prunes volumes, containers or networks. The one risk is an image pulled but not yet
  started by `up -d`: it would be pruned and re-pulled, hence the Sunday-night slot. No
  rollback image is kept either: to roll back, pull the old tag again.
- `disk-space-alert.yaml` is a Home Assistant automation that notifies at 85 % (10 minutes
  sustained) and at 95 % disk use, for what the prune does not cover (logs, recorder, models).

Install the timer from the Pi 5 (`sudo` steps):

```sh
scp deploy/pi5/docker-housekeeping.* <user>@<pi5-host>:confiture-pi5/
ssh -t <user>@<pi5-host> 'cd confiture-pi5 &&
  sudo install -m 0755 docker-housekeeping.sh /usr/local/bin/ &&
  sudo install -m 0644 docker-housekeeping.service docker-housekeeping.timer /etc/systemd/system/ &&
  sudo systemctl daemon-reload && sudo systemctl enable --now docker-housekeeping.timer'
```

Check:

```sh
systemctl list-timers docker-housekeeping.timer        # next run: Sunday 04:00
sudo systemctl start docker-housekeeping.service       # first run by hand
journalctl -u docker-housekeeping.service -n 5         # "freed N MiB on /"
docker system df
```

Alert: in Home Assistant, add the System Monitor integration (Settings → Integrations) with the
`/` disk sensor, then Settings → Automations → Create → Edit in YAML, paste
`disk-space-alert.yaml`, check the sensor entity id (default `sensor.system_monitor_disk_usage`)
and uncomment the notify block with your service (the file keeps a placeholder only).

## Speech-to-text and the microphone satellite

`whisper` (Wyoming, sherpa-onnx backend) turns speech into text for the Yuki pipeline (benoit-bremaud/confiture#18, ADR-0008);
`satellite` (Linux Voice Assistant) streams the USB microphone to Home Assistant over the
ESPHome API. Both run as uid 1000, read-only, all capabilities dropped, loopback ports only.

One-time host setup, on the Pi 5 (needs `sudo`, so `ssh -t`): the satellite talks to a
PipeWire session of the uid 1000 user, which must run without a login.

```sh
sudo apt-get install -y pipewire pipewire-pulse wireplumber
sudo loginctl enable-linger <user>
systemctl --user enable --now pipewire pipewire-pulse wireplumber
pactl info | grep 'Server Name'                          # PulseAudio (on PipeWire)
```

Create the folders before the first start (same reason as `data/`), copy the files again with
the `scp` line above, then start:

```sh
mkdir -p whisper satellite/configuration satellite/local
docker compose -p confiture up -d
docker compose -p confiture logs -f whisper satellite
```

- `STT_LIBRARY` / `STT_STREAMING` pick the model (ADR-0008): Parakeet TDT v3 by default,
  `STT_STREAMING=1` for Kroko. It is downloaded into `whisper/` on first start. The backend is
  always pinned: the image's default `auto` picks one on its own.
- A headless Pi has no login seat, so WirePlumber ignores the USB microphone until seat
  monitoring is off, in `~/.config/wireplumber/wireplumber.conf.d/50-headless.conf`:
  `wireplumber.profiles = { main = { monitor.alsa.seat-monitoring = disabled } }`, then
  `systemctl --user restart wireplumber`; `pactl list short sources` shows `alsa_input.usb-…`.
- Home Assistant adds `whisper` with the Wyoming integration at `127.0.0.1:10300`, and the
  satellite with the ESPHome integration at `127.0.0.1:6053` (it listens on loopback only,
  host networking, #26). `SATELLITE_MAC` keeps its identity across recreates.
- The Pi 5 has no speaker: answers are spoken on the Nest Mini (REQ-16).

## Answers on the Nest Mini (nest-relay)

An Assist pipeline returns its audio to the satellite, and the Pi 5 has no speaker.
`nest-relay` listens to the satellite's peripheral events on `127.0.0.1:6055` and, for each
`tts_text` reply, runs the Home Assistant script `yuki_speak`
(`config/homeassistant/yuki_speak.yaml`), which speaks it on the Nest with Piper.

- Token: a long-lived token carries every right of its user, so create it on a dedicated
  non-admin, local-only user (Settings > People, e.g. `nest-relay`), not on the owner. Signed in
  as that user, create a token named `confiture-nest-relay` (Profile > Security), then put it in
  `.env` without echoing it, and `chmod 600 .env`:
  `read -rs T && echo "NEST_RELAY_HA_TOKEN=$T" >> .env`. Home Assistant gives it 10 years
  and no expiry choice: rotate it yearly (create the new token, update `.env`, recreate the
  container, revoke the old one).
- Copy `nest-relay/` next to `compose.yaml` (`scp deploy/pi5/nest-relay/{Dockerfile,.dockerignore,requirements.txt,relay.py,main.py}`), then
  `docker compose -p confiture build nest-relay && docker compose -p confiture up -d nest-relay`.
- Check: `docker logs confiture-nest-relay` shows `connected to ws://127.0.0.1:6055`, and
  `spoken (200)` after each answer.
- Host networking: the relay listens on nothing and reaches the loopback ports of the
  satellite and Home Assistant.
