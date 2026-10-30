"""Wiring: satellite peripheral WebSocket in, Home Assistant REST out."""

import asyncio
import http.client
import json
import logging
import os
import urllib.request

import websockets

from relay import Speaker, relay

log = logging.getLogger("nestrelay")


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


async def run(satellite_uri: str, speaker: Speaker) -> None:
    """Relay every reply of the satellite forever, reconnecting when it goes away."""
    async for ws in websockets.connect(satellite_uri):  # reconnects with backoff
        try:
            log.info("connected to %s", satellite_uri)
            async for message in ws:
                try:
                    await asyncio.to_thread(relay, str(message), speaker)
                except (
                    OSError,
                    http.client.HTTPException,
                ) as error:  # HA down: drop this reply, keep listening
                    log.warning("Home Assistant call failed: %s", error)
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
