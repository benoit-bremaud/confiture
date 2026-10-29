# Pi 5 deployment

Containers that confiture owns on the Pi 5, next to the bb-homelab stack (ADR-0006).

## Piper text-to-speech

Copy the files into `~/confiture-pi5` on the Pi 5 from a checkout (placeholders, real values
in `.env`). Copy files, not the folder: `scp -r` into an existing folder would nest it and
leave the old `compose.yaml` in place. Create `data/` first: if Docker creates it, it belongs
to root and Piper, which runs as uid 1000, cannot write the voice.

```sh
ssh <user>@<pi5-host> mkdir -p confiture-pi5/data
scp deploy/pi5/compose.yaml deploy/pi5/README.md <user>@<pi5-host>:confiture-pi5/
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
```

- `PIPER_VOICE` sets the default voice (`fr_FR-siwis-medium` if unset); Piper downloads it into
  `data/` on first start. Extra voices: copy their `.onnx` and `.onnx.json` into `data/`.
- `PIPER_UID` / `PIPER_GID` default to 1000 and must own `data/`.
- Home Assistant runs with host networking, so it adds Piper with the Wyoming integration at
  `127.0.0.1:10200`; ask for language `fr_FR`, not `fr` (ADR-0006).
- Update: Dependabot proposes the new tag and digest in `compose.yaml`; review it, copy the
  files again with the `scp` line above, then `docker compose -p confiture pull` and `up -d`.
