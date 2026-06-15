from typing import List

from .audio_player import AudioPlayer
from .tts_engine import TTSEngine
from .calendar_sync import summarize_events

player = AudioPlayer()


async def trigger_alarm(message: str = None):
    await player.start_radio()
    if message:
        await player.play_message(message)


async def stop_alarm():
    await player.stop_radio()


async def play_schedule_summary(events: List[dict]):
    summary = summarize_events(events)
    tts = TTSEngine()
    if tts.is_configured():
        output_path = tts.synthesize(summary, tts.TMP_DIR / "schedule_summary.wav")
        await player.stop_radio()
        await player.play_wav(output_path)
        return output_path

    await player.stop_radio()
    await player.play_message(summary)
    return None
