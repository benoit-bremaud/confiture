"""Wiring: satellite peripheral WebSocket in, Home Assistant REST out."""

import asyncio
import http.client
import json
import logging
import os
import time
import urllib.request

import websockets

from relay import Speaker, Turn

log = logging.getLogger("nestrelay")
# How often the loop wakes up to let `Turn` speak its cue or fallback on time.
TICK_S = 0.25


class HomeAssistantSpeaker:
    """Runs script.yuki_speak through the Home Assistant REST API."""

    def __init__(self, base_url: str, token: str) -> None:
        self._url = f"{base_url}/api/services/script/yuki_speak"
        self._token = token

    def speak(self, text: str) -> None:
        """POST the text to the script; raises OSError or HTTPException when HA fails."""
        request = urllib.request.Request(
            self._url,
            data=json.dumps({"text": text}).encode(),
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            log.info("spoken (%s): %d characters", response.status, len(text))


def speak_all(texts: list[str], speaker: Speaker) -> None:
    """Speak each text in order; a failed call drops that text and keeps the relay alive.

    Blocking on purpose: the cue finishes before the reply is sent, and messages that arrive
    meanwhile wait in the WebSocket buffer.
    """
    for text in texts:
        try:
            speaker.speak(text)
        except (OSError, http.client.HTTPException) as error:  # HA down
            log.warning("Home Assistant call failed: %s", error)
        except Exception:  # any other speaker bug must not stop the relay
            log.exception("speaking failed")


async def run(satellite_uri: str, speaker: Speaker) -> None:
    """Relay every reply of the satellite forever, reconnecting when it goes away."""
    async for ws in websockets.connect(satellite_uri):  # reconnects with backoff
        turn = Turn()  # a dropped connection ends any open turn
        try:
            log.info("connected to %s", satellite_uri)
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), TICK_S)
                    texts = turn.on_message(str(message), time.monotonic())
                except TimeoutError:
                    texts = turn.tick(time.monotonic())
                if texts:
                    await asyncio.to_thread(speak_all, texts, speaker)
        except websockets.ConnectionClosed:
            log.warning("satellite connection closed, reconnecting")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    speaker = HomeAssistantSpeaker(
        os.environ.get("HA_URL", "http://127.0.0.1:8123"),
        os.environ["HA_TOKEN"],
    )
    asyncio.run(run(os.environ.get("SATELLITE_URI", "ws://127.0.0.1:6055"), speaker))


if __name__ == "__main__":
    main()
