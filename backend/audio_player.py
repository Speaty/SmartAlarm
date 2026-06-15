import asyncio
import os
import shlex
import subprocess
from pathlib import Path
from .config import ALARM_RADIO_URL, DEFAULT_ALARM_VOLUME, AUDIO_DEVICE, AUDIO_MIXER_DEVICE

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)


class AudioPlayer:
    def __init__(self):
        self.radio_process = None

    async def _run(self, command: str):
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc

    async def _set_volume(self, volume: int):
        command = f"amixer -D {AUDIO_MIXER_DEVICE} sset '{ALSA_MIXER}' {volume}%"
        proc = await self._run(command)
        await proc.communicate()

    async def _run_volume(self, volume: int):
        try:
            await self._set_volume(volume)
        except Exception:
            # Some HiFiBerry boards may not expose a Master mixer control on the same device.
            pass

    async def start_radio(self, url: str = None):
        if self.radio_process and self.radio_process.returncode is None:
            return
        await self._run_volume(DEFAULT_ALARM_VOLUME)
        stream = url or ALARM_RADIO_URL
        command = f"mpg123 -q -o alsa -a {shlex.quote(AUDIO_DEVICE)} {shlex.quote(stream)}"
        self.radio_process = await self._run(command)

    async def stop_radio(self):
        if self.radio_process and self.radio_process.returncode is None:
            self.radio_process.kill()
            await self.radio_process.wait()
            self.radio_process = None

    async def play_wav(self, wav_path: Path):
        command = f"aplay -q -D {AUDIO_DEVICE} '{wav_path}'"
        proc = await self._run(command)
        await proc.communicate()

    async def play_message(self, text: str):
        wav_path = TMP_DIR / "tts_message.wav"
        command = f"espeak-ng -w '{wav_path}' '{text}'"
        proc = await self._run(command)
        await proc.communicate()
        if wav_path.exists():
            await self.play_wav(wav_path)
