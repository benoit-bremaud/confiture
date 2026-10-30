"""Run the speech-to-text bench against a Wyoming server (benoit-bremaud/confiture#18).

Usage: python bench.py <recordings-dir> [--uri tcp://127.0.0.1:10300]
The folder holds <speaker>-<NN>.wav (16 kHz mono 16-bit, speaker = adult or child) and
sentences.tsv ("<file>\t<reference sentence>"). Recordings are family voices: keep them
outside the repository.
"""

import argparse
import asyncio
import time
import wave
from pathlib import Path

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient

from score import Result, summarize

CHUNK_FRAMES = 1024


async def transcribe(uri: str, path: Path) -> tuple[str, float]:
    """Stream one WAV file; return the transcript and the time from audio-stop to it."""
    with wave.open(str(path), "rb") as wav:
        rate, width, channels = (
            wav.getframerate(),
            wav.getsampwidth(),
            wav.getnchannels(),
        )
        frames = wav.readframes(wav.getnframes())
    step = CHUNK_FRAMES * width * channels
    async with AsyncClient.from_uri(uri) as client:
        await client.write_event(Transcribe(language="fr").event())
        await client.write_event(AudioStart(rate, width, channels).event())
        for start in range(0, len(frames), step):
            chunk = AudioChunk(rate, width, channels, frames[start : start + step])
            await client.write_event(chunk.event())
        await client.write_event(AudioStop().event())
        stopped = time.monotonic()
        while event := await client.read_event():
            if Transcript.is_type(event.type):
                return Transcript.from_event(event).text, time.monotonic() - stopped
    raise ConnectionError(f"no transcript for {path.name}")


async def run(folder: Path, uri: str) -> list[Result]:
    """Transcribe every recorded sentence of sentences.tsv; missing files are listed, not run."""
    results = []
    for line in (folder / "sentences.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        name, reference = line.split("\t", 1)
        if not (folder / name).exists():  # a speaker not recorded yet
            print(f"{name}\tmissing")
            continue
        text, latency = await transcribe(uri, folder / name)
        results.append(Result(name.split("-", 1)[0], reference, text, latency))
        print(
            f"{name}\t{latency:.2f}s\t{'OK ' if results[-1].correct else 'ERR'}\t{text}"
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--uri", default="tcp://127.0.0.1:10300")
    args = parser.parse_args()
    summary = summarize(asyncio.run(run(args.folder, args.uri)))
    print(
        f"WER {summary.wer:.1%}  child correct {summary.child_correct_ratio:.0%}  "
        f"max latency {summary.max_latency_s:.2f}s  {'PASS' if summary.passes else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
