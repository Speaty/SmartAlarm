import os
import wave

import pytest
import requests

from backend import tts_engine
from backend.tts_engine import SAMPLE_RATE, TTSEngine
from tests.fakes import FakeResponse, RecordingHTTP

PCM = b"\x01\x00\x02\x00" * 100  # 200 16-bit samples


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(tts_engine, "ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(tts_engine, "ELEVENLABS_VOICE_ID", "voice-123")


@pytest.mark.parametrize(
    "key,voice",
    [(None, "voice-123"), ("", "voice-123"), ("test-key", None), ("test-key", "")],
)
def test_not_configured_without_key_and_voice(monkeypatch, key, voice):
    monkeypatch.setattr(tts_engine, "ELEVENLABS_API_KEY", key)
    monkeypatch.setattr(tts_engine, "ELEVENLABS_VOICE_ID", voice)

    assert TTSEngine().is_configured() is False


def test_configured_with_key_and_voice(configured):
    assert TTSEngine().is_configured() is True


def test_synthesize_without_config_raises(tmp_path):
    with pytest.raises(RuntimeError, match="not configured"):
        TTSEngine().synthesize("hello", tmp_path / "out.wav")


def test_synthesize_posts_text_to_voice_endpoint(configured, monkeypatch, tmp_path):
    post = RecordingHTTP(FakeResponse(content=PCM))
    monkeypatch.setattr(requests, "post", post)

    TTSEngine().synthesize("Good morning", tmp_path / "out.wav")

    url, kwargs = post.calls[0]
    assert url == "https://api.elevenlabs.io/v1/text-to-speech/voice-123"
    assert kwargs["headers"]["xi-api-key"] == "test-key"
    assert kwargs["json"]["text"] == "Good morning"
    assert kwargs["params"]["output_format"] == f"pcm_{SAMPLE_RATE}"
    assert kwargs["timeout"] > 0


def test_synthesize_wraps_pcm_in_wav_header(configured, monkeypatch, tmp_path):
    monkeypatch.setattr(requests, "post", RecordingHTTP(FakeResponse(content=PCM)))
    out = tmp_path / "out.wav"

    result = TTSEngine().synthesize("hi", out)

    assert result == out
    with wave.open(str(out), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.readframes(wav.getnframes()) == PCM


def test_synthesize_raises_on_http_error(configured, monkeypatch, tmp_path):
    monkeypatch.setattr(requests, "post", RecordingHTTP(FakeResponse(status_code=401)))
    out = tmp_path / "out.wav"

    with pytest.raises(requests.HTTPError):
        TTSEngine().synthesize("hi", out)
    assert not out.exists()


@pytest.mark.live
def test_live_elevenlabs_returns_playable_wav(monkeypatch, tmp_path):
    key = os.getenv("ELEVENLABS_API_KEY")
    voice = os.getenv("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        pytest.skip("set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID (in .env) to run")
    monkeypatch.setattr(tts_engine, "ELEVENLABS_API_KEY", key)
    monkeypatch.setattr(tts_engine, "ELEVENLABS_VOICE_ID", voice)

    out = TTSEngine().synthesize("SmartAlarm test.", tmp_path / "live.wav")

    with wave.open(str(out), "rb") as wav:
        # A short phrase should be at least a quarter-second of audio.
        assert wav.getnframes() > SAMPLE_RATE // 4
        frames = wav.readframes(wav.getnframes())
    # PCM, not an MP3 smuggled into the WAV body.
    assert frames[:3] != b"ID3"
    assert any(frames)
