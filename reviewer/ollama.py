from __future__ import annotations
from dataclasses import dataclass
import base64
from pathlib import Path
from typing import Sequence
import requests

@dataclass
class OllamaText:
    model: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    num_ctx: int = 16384
    num_predict: int = 3500
    timeout_s: int = 1800

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict,
            },
        }
        r = requests.post(url, json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()

@dataclass
class OllamaVLM:
    model: str
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    num_ctx: int = 8192
    timeout_s: int = 1800

    def analyze_images(self, prompt: str, image_paths: Sequence[str]) -> str:
        url = f"{self.base_url}/api/chat"
        images_b64 = []
        for p in image_paths:
            data = Path(p).read_bytes()
            images_b64.append(base64.b64encode(data).decode("utf-8"))
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt, "images": images_b64}],
            "stream": False,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
        }
        r = requests.post(url, json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        msg = r.json().get("message") or {}
        return (msg.get("content") or "").strip()
