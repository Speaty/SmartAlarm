from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from backend import alarm_controller, tts_engine
from backend.tts_engine import TTSEngine

EVENTS = [{"start": {"dateTime": "2099-01-05T09:00:00"}, "summary": "Standup"}]


def enable_elevenlabs(monkeypatch):
    monkeypatch.setattr(tts_engine, "ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(tts_engine, "ELEVENLABS_VOICE_ID", "voice-123")


async def ring():
    await alarm_controller.trigger_alarm("ringing")


async def test_stop_when_nothing_is_ringing_plays_no_summary(client, player):
    response = await client.post("/alarm/stop")

    assert response.json() == {"status": "stopped", "summary_playing": False}
    player.stop_radio.assert_awaited()
    player.play_message.assert_not_awaited()


async def test_stop_ringing_alarm_plays_calendar_summary_with_espeak(client, player, calendar):
    calendar.return_value = EVENTS
    await ring()
    player.play_message.reset_mock()

    response = await client.post("/alarm/stop")

    assert response.json() == {"status": "stopped", "summary_playing": True}
    spoken = player.play_message.await_args.args[0]
    assert "Standup" in spoken
    assert not alarm_controller.is_ringing()


async def test_stop_twice_only_plays_summary_once(client, player):
    await ring()
    await client.post("/alarm/stop")
    player.play_message.reset_mock()

    response = await client.post("/alarm/stop")

    assert response.json()["summary_playing"] is False
    player.play_message.assert_not_awaited()


async def test_summary_uses_elevenlabs_when_configured(client, player, monkeypatch, tmp_path):
    enable_elevenlabs(monkeypatch)
    monkeypatch.setattr(TTSEngine, "synthesize", lambda self, text, path: tmp_path / "out.wav")
    await ring()
    player.play_message.reset_mock()

    await client.post("/alarm/stop")

    player.play_wav.assert_awaited_once_with(tmp_path / "out.wav")
    player.play_message.assert_not_awaited()


async def test_summary_passes_calendar_text_to_elevenlabs(client, monkeypatch, tmp_path, calendar):
    enable_elevenlabs(monkeypatch)
    calendar.return_value = EVENTS
    seen = {}

    def fake_synthesize(self, text, path):
        seen["text"], seen["path"] = text, path
        return path

    monkeypatch.setattr(TTSEngine, "synthesize", fake_synthesize)

    await client.post("/alarm/summary")

    assert "Standup" in seen["text"]
    assert seen["path"].name == "schedule_summary.wav"


async def test_elevenlabs_failure_surfaces_as_error(client, monkeypatch):
    enable_elevenlabs(monkeypatch)

    def boom(self, text, path):
        raise RuntimeError("elevenlabs down")

    monkeypatch.setattr(TTSEngine, "synthesize", boom)

    with pytest.raises(RuntimeError, match="elevenlabs down"):
        await client.post("/alarm/summary")


async def test_stopping_speaker_test_never_plays_summary(client, player):
    await client.post("/alarm/test-speakers")

    response = await client.post("/alarm/test-speakers/stop")

    assert response.json() == {"status": "stopped"}
    player.stop_radio.assert_awaited()
    player.play_message.assert_not_awaited()


async def test_test_speakers_starts_radio_with_test_url(client, player):
    from backend.config import TEST_SPEAKER_URL

    response = await client.post("/alarm/test-speakers")

    assert response.json()["url"] == TEST_SPEAKER_URL
    player.start_radio.assert_awaited_once_with(TEST_SPEAKER_URL)


async def test_set_volume(client, player):
    response = await client.post("/volume", json={"volume": 40})

    assert response.json() == {"volume": 40}
    player.set_volume.assert_awaited_once_with(40)


@pytest.mark.parametrize("volume", [-1, 101])
async def test_set_volume_rejects_out_of_range(client, volume):
    response = await client.post("/volume", json={"volume": volume})

    assert response.status_code == 422
