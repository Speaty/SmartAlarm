import os
from pathlib import Path
import requests
from .config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR.parent / "tmp"
TMP_DIR.mkdir(exist_ok=True)


class TTSEngine:
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.voice_id = ELEVENLABS_VOICE_ID

    def is_configured(self) -> bool:
        return self.api_key is not None

    def synthesize(self, text: str, file_path: Path) -> Path:
        if not self.is_configured():
            raise RuntimeError("ElevenLabs API key not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }
        payload = {
            "text": text,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        file_path.write_bytes(response.content)
        return file_path
