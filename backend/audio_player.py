import asyncio
import os
import subprocess
from pathlib import Path
from .config import (
    ALARM_RADIO_URL,
    DEFAULT_ALARM_VOLUME,
    DEFAULT_MUSIC_LEVEL,
    DEFAULT_VOICE_LEVEL,
    PIPEWIRE_SINK,
)

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)

# mpg123's output scale for unity gain
MPG123_FULL_SCALE = 32768


def _clamp(level: int) -> int:
    return max(0, min(100, level))


class AudioPlayer:
    """Plays radio and speech. `volume` is the speaker (sink) volume; `music_level` and
    `voice_level` scale the radio and speech streams within it, so the two can be balanced."""

    def __init__(self):
        self.radio_process = None
        self.radio_url = None
        self.volume = DEFAULT_ALARM_VOLUME
        self.music_level = DEFAULT_MUSIC_LEVEL
        self.voice_level = DEFAULT_VOICE_LEVEL

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
        self.volume = _clamp(volume)
        await self._set_volume(self.volume)

    async def set_music_level(self, level: int):
        """Set the radio level. mpg123 can't change it mid-stream, so a playing stream restarts."""
        self.music_level = _clamp(level)
        if self.is_radio_playing():
            url = self.radio_url
            await self.stop_radio()
            await self.start_radio(url)

    def set_voice_level(self, level: int):
        self.voice_level = _clamp(level)

    def is_radio_playing(self) -> bool:
        return self.radio_process is not None and self.radio_process.returncode is None

    async def start_radio(self, url: str = None):
        if self.is_radio_playing():
            return
        await self._run_volume(self.volume)
        stream = url or ALARM_RADIO_URL
        env = {**os.environ}
        if PIPEWIRE_SINK != "@DEFAULT_AUDIO_SINK@":
            env["PULSE_SINK"] = PIPEWIRE_SINK
        scale = str(round(MPG123_FULL_SCALE * self.music_level / 100))
        self.radio_process = await self._exec(
            "mpg123", "-q", "-o", "pulse", "-f", scale, stream, env=env
        )
        self.radio_url = stream
        await asyncio.sleep(0.5)
        if self.radio_process.returncode is not None:
            stderr_bytes = await self.radio_process.stderr.read()
            raise RuntimeError(f"mpg123 failed: {stderr_bytes.decode().strip()}")

    async def stop_radio(self):
        if self.is_radio_playing():
            self.radio_process.kill()
            await self.radio_process.wait()
            self.radio_process = None

    async def play_wav(self, wav_path: Path):
        args = ["pw-play", "--volume", f"{self.voice_level / 100:.2f}"]
        if PIPEWIRE_SINK != "@DEFAULT_AUDIO_SINK@":
            args += ["--target", PIPEWIRE_SINK]
        proc = await self._exec(*args, str(wav_path))
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
