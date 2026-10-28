# Pi 5 deployment

Containers that confiture owns on the Pi 5, next to the bb-homelab stack (ADR-0006).

## Piper text-to-speech

Copy this folder to the Pi 5 from a checkout (placeholders, real values in `.env`):

```sh
scp -r deploy/pi5 <user>@<pi5-host>:confiture-pi5
```

First run, on the Pi 5, in `~/confiture-pi5`:

```sh
mkdir -p data
docker compose -p confiture up -d
docker compose -p confiture logs -f piper
```

- `PIPER_VOICE` sets the default voice (`fr_FR-siwis-medium` if unset); Piper downloads it into
  `data/` on first start. Extra voices: copy their `.onnx` and `.onnx.json` into `data/`.
- `PIPER_UID` / `PIPER_GID` default to 1000 and must own `data/`.
- Home Assistant adds it with the Wyoming integration at `127.0.0.1:10200`.
- Update: change the image tag in `compose.yaml`, then pull and `up -d` again.
