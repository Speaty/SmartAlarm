import wave
from pathlib import Path
import requests
from .config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)

# ElevenLabs returns MP3 by default; ask for raw 16-bit mono PCM and wrap it in a WAV header
# so pw-play gets a real WAV file.
OUTPUT_FORMAT = "pcm_22050"
SAMPLE_RATE = 22050


class TTSEngine:
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.voice_id = ELEVENLABS_VOICE_ID

    def is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.voice_id)

    def synthesize(self, text: str, file_path: Path) -> Path:
        if not self.is_configured():
            raise RuntimeError("ElevenLabs API key or voice ID not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        payload = {
            "text": text,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        response = requests.post(
            url,
            params={"output_format": OUTPUT_FORMAT},
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        with wave.open(str(file_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(response.content)
        return file_path
