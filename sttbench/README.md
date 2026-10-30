# Speech-to-text bench

Chooses the speech-to-text model for the Yuki pipeline (benoit-bremaud/confiture#18,
ADR-0008): 20 French sentences, 10 by the young child and 10 by an adult, recorded with the
USB webcam microphone on the Pi 5 at real living-room distance. The smallest model with at
least 8/10 correct child transcriptions and an STT latency of 3 s or less wins.

Recordings are family voices: they stay in `~/stt-bench/` on the Pi 5, never here.

1. Record, on the Pi 5: copy `sentences.tsv` and `record.sh` into `~/stt-bench/`, then
   `sh ~/stt-bench/record.sh ~/stt-bench [adult|child]` (8 s per sentence; speak after 2 s,
   the microphone takes that long to open).
2. Run, for each model (`STT_LIBRARY` / `STT_STREAMING` in `~/confiture-pi5/.env`, see
   ADR-0008): `docker compose -p confiture up -d whisper`, wait for `Ready`, then
   run `bench.py ~/stt-bench` from a venv with `requirements-dev.txt` (port 10300 is
   loopback only: run it on the Pi 5 or through `ssh -L 10300:127.0.0.1:10300`).
3. Record the three summaries and the choice in ADR-0008.

Tests: `pytest --cov=score tests` (scoring only; the Wyoming client is exercised by the run).
