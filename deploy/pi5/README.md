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
- `PIPER_UID` / `PIPER_GID` default to 1000 and must own `data/`.
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
  It never prunes volumes, containers or networks. An image pulled but not yet started is the
  only thing it could remove, hence the Sunday-night slot.
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
`disk-space-alert.yaml`, set the sensor entity id and your notify service (the file keeps
placeholders only).
