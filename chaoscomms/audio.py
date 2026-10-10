"""Receive-only ALSA audio capture for the browser stream."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

AUDIO_RATE = 48_000
AUDIO_CHANNELS = 2
AUDIO_FORMAT = "S16_LE"
DEFAULT_DEVICE = "plughw:CARD=Device,DEV=0"


class AudioCapture:
    """Capture PCM from ALSA; this class has no playback or PTT operations."""

    def __init__(self, device: str | None = None) -> None:
        self.device = device or os.getenv("CHAOSCOMMS_AUDIO_DEVICE", DEFAULT_DEVICE)

    async def chunks(self, chunk_bytes: int = 16_384) -> AsyncIterator[bytes]:
        process = await asyncio.create_subprocess_exec(
            "arecord",
            "-q",
            "-D",
            self.device,
            "-f",
            AUDIO_FORMAT,
            "-r",
            str(AUDIO_RATE),
            "-c",
            str(AUDIO_CHANNELS),
            "-t",
            "raw",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            assert process.stdout is not None
            while True:
                chunk = await process.stdout.read(chunk_bytes)
                if not chunk:
                    break
                yield chunk
        finally:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    def status(self) -> dict[str, object]:
        return {
            "source": "alsa",
            "device": self.device,
            "format": AUDIO_FORMAT,
            "sample_rate_hz": AUDIO_RATE,
            "channels": AUDIO_CHANNELS,
            "receive_only": True,
            "ptt": False,
        }
