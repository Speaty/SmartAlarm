import asyncio

from .audio_player import player
from .tts_engine import TMP_DIR, TTSEngine
from .calendar_summary import calendar_summary_service

_ringing = False


def is_ringing() -> bool:
    return _ringing


async def trigger_alarm(message: str = None):
    global _ringing
    _ringing = True
    await player.start_radio()
    if message:
        await player.play_message(message)


async def stop_alarm() -> bool:
    """Stop the radio. Returns True if an alarm was ringing (not just a speaker test)."""
    global _ringing
    was_ringing = _ringing
    _ringing = False
    await player.stop_radio()
    return was_ringing


async def test_speakers(url: str):
    await player.start_radio(url)


async def stop_test():
    await player.stop_radio()


async def test_voice():
    """Speak a short phrase over whatever is playing, to balance voice against music."""
    await player.play_message("This is how loud the alarm voice will be.")


def get_levels() -> dict:
    return {"volume": player.volume, "music": player.music_level, "voice": player.voice_level}


async def set_levels(volume: int = None, music: int = None, voice: int = None) -> dict:
    if volume is not None:
        await player.set_volume(volume)
    if music is not None:
        await player.set_music_level(music)
    if voice is not None:
        player.set_voice_level(voice)
    return get_levels()


async def play_schedule_summary():
    summary = await calendar_summary_service.get_summary()
    tts = TTSEngine()
    if tts.is_configured():
        output_path = await asyncio.to_thread(
            tts.synthesize, summary, TMP_DIR / "schedule_summary.wav"
        )
        await player.stop_radio()
        await player.play_wav(output_path)
        return output_path

    await player.stop_radio()
    await player.play_message(summary)
    return None
