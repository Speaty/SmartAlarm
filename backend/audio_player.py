import asyncio
import os
import subprocess
from pathlib import Path
from .config import ALARM_RADIO_URL, DEFAULT_ALARM_VOLUME, PIPEWIRE_SINK

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)


class AudioPlayer:
    def __init__(self):
        self.radio_process = None
        self.volume = DEFAULT_ALARM_VOLUME

    async def _exec(self, *args: str, env: dict = None):
        return await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

    async def _set_volume(self, volume: int):
        proc = await self._exec("wpctl", "set-volume", PIPEWIRE_SINK, f"{volume / 100:.2f}")
        await proc.communicate()

    async def _run_volume(self, volume: int):
        try:
            await self._set_volume(volume)
        except Exception:
            pass

    async def set_volume(self, volume: int):
        self.volume = max(0, min(100, volume))
        await self._set_volume(self.volume)

    async def start_radio(self, url: str = None):
        if self.radio_process and self.radio_process.returncode is None:
            return
        await self._run_volume(self.volume)
        stream = url or ALARM_RADIO_URL
        env = {**os.environ}
        if PIPEWIRE_SINK != "@DEFAULT_AUDIO_SINK@":
            env["PULSE_SINK"] = PIPEWIRE_SINK
        self.radio_process = await self._exec("mpg123", "-q", "-o", "pulse", stream, env=env)
        await asyncio.sleep(0.5)
        if self.radio_process.returncode is not None:
            stderr_bytes = await self.radio_process.stderr.read()
            raise RuntimeError(f"mpg123 failed: {stderr_bytes.decode().strip()}")

    async def stop_radio(self):
        if self.radio_process and self.radio_process.returncode is None:
            self.radio_process.kill()
            await self.radio_process.wait()
            self.radio_process = None

    async def play_wav(self, wav_path: Path):
        args = ["pw-play", str(wav_path)]
        if PIPEWIRE_SINK != "@DEFAULT_AUDIO_SINK@":
            args = ["pw-play", "--target", PIPEWIRE_SINK, str(wav_path)]
        proc = await self._exec(*args)
        await proc.communicate()

    async def play_message(self, text: str):
        wav_path = TMP_DIR / "tts_message.wav"
        try:
            proc = await self._exec("espeak-ng", "-w", str(wav_path), text)
            await proc.communicate()
        except FileNotFoundError:
            return
        if wav_path.exists():
            await self.play_wav(wav_path)


player = AudioPlayer()
