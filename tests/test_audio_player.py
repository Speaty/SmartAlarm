from unittest.mock import AsyncMock, MagicMock

import pytest

from backend import audio_player
from backend.audio_player import AudioPlayer


def fake_process(returncode=None, stderr=b""):
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(b"", b""))
    proc.wait = AsyncMock()
    proc.stderr.read = AsyncMock(return_value=stderr)
    return proc


@pytest.fixture
def fresh(monkeypatch):
    """A real AudioPlayer whose subprocess calls are recorded instead of run."""
    monkeypatch.setattr(audio_player.asyncio, "sleep", AsyncMock())
    p = AudioPlayer()
    p.calls = []

    async def fake_exec(*args, env=None):
        p.calls.append((args, env))
        return fake_process()

    p._exec = fake_exec
    return p


def commands(p):
    return [args for args, _ in p.calls]


async def test_start_radio_sets_volume_then_plays_stream_via_pulse(fresh):
    await fresh.start_radio("http://stream")

    wpctl, mpg123 = commands(fresh)
    assert wpctl[:3] == ("wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@")
    assert mpg123 == ("mpg123", "-q", "-o", "pulse", "http://stream")


async def test_start_radio_defaults_to_alarm_stream(fresh):
    await fresh.start_radio()

    assert commands(fresh)[-1][-1] == audio_player.ALARM_RADIO_URL


async def test_start_radio_routes_to_custom_sink(fresh, monkeypatch):
    monkeypatch.setattr(audio_player, "PIPEWIRE_SINK", "hifiberry")

    await fresh.start_radio("http://stream")

    _, env = fresh.calls[-1]
    assert env["PULSE_SINK"] == "hifiberry"


async def test_start_radio_is_noop_while_already_playing(fresh):
    await fresh.start_radio("http://stream")
    fresh.calls.clear()

    await fresh.start_radio("http://other")

    assert fresh.calls == []


async def test_start_radio_raises_if_mpg123_exits_immediately(monkeypatch):
    monkeypatch.setattr(audio_player.asyncio, "sleep", AsyncMock())
    p = AudioPlayer()

    async def fake_exec(*args, env=None):
        if args[0] == "mpg123":
            return fake_process(returncode=1, stderr=b"cannot open stream")
        return fake_process()

    p._exec = fake_exec

    with pytest.raises(RuntimeError, match="cannot open stream"):
        await p.start_radio("http://bad")


async def test_stop_radio_kills_running_process(fresh):
    await fresh.start_radio("http://stream")
    proc = fresh.radio_process

    await fresh.stop_radio()

    proc.kill.assert_called_once()
    assert fresh.radio_process is None


@pytest.mark.parametrize("requested,expected", [(50, "0.50"), (150, "1.00"), (-5, "0.00")])
async def test_set_volume_clamps_and_converts_to_fraction(fresh, requested, expected):
    await fresh.set_volume(requested)

    assert commands(fresh)[-1][-1] == expected


async def test_play_wav_uses_default_sink(fresh, tmp_path):
    await fresh.play_wav(tmp_path / "a.wav")

    assert commands(fresh)[-1] == ("pw-play", str(tmp_path / "a.wav"))


async def test_play_wav_targets_custom_sink(fresh, monkeypatch, tmp_path):
    monkeypatch.setattr(audio_player, "PIPEWIRE_SINK", "hifiberry")

    await fresh.play_wav(tmp_path / "a.wav")

    assert commands(fresh)[-1] == ("pw-play", "--target", "hifiberry", str(tmp_path / "a.wav"))


async def test_play_message_renders_with_espeak_then_plays(fresh, monkeypatch, tmp_path):
    monkeypatch.setattr(audio_player, "TMP_DIR", tmp_path)
    (tmp_path / "tts_message.wav").write_bytes(b"RIFF")

    await fresh.play_message("hello")

    espeak, play = commands(fresh)
    assert espeak == ("espeak-ng", "-w", str(tmp_path / "tts_message.wav"), "hello")
    assert play[0] == "pw-play"


async def test_play_message_is_silent_without_espeak(monkeypatch, tmp_path):
    monkeypatch.setattr(audio_player, "TMP_DIR", tmp_path)
    p = AudioPlayer()
    p._exec = AsyncMock(side_effect=FileNotFoundError)

    await p.play_message("hello")  # must not raise
