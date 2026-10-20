"""Generate the placeholder AI voiceover with Kokoro (Apache-2.0, runs locally, no key).

Usage: python scripts/tts_kokoro.py <kokoro.onnx> <voices.bin> [voice] [ids...]
Writes public/vo/kokoro/<id>.mp3. Owner recordings in public/vo/owner/ take precedence at render time.
"""
import pathlib
import subprocess
import sys

import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "vo" / "kokoro"


def lines() -> list[tuple[str, str]]:
    out = []
    for raw in (ROOT / "narration.txt").read_text().splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        ident, _window, text = [p.strip() for p in raw.split("|", 2)]
        out.append((ident, text))
    return out


def main() -> None:
    model, voices = sys.argv[1], sys.argv[2]
    voice = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
    only = set(sys.argv[4:])
    OUT.mkdir(parents=True, exist_ok=True)
    k = Kokoro(model, voices)
    for ident, text in lines():
        if only and ident not in only:
            continue
        samples, rate = k.create(text, voice=voice, speed=1.0, lang="en-us")
        wav = OUT / f"{ident}.wav"
        sf.write(wav, samples, rate)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "160k", str(wav.with_suffix(".mp3"))], check=True)
        wav.unlink()
        print(ident, f"{len(samples) / rate:.2f}s")


if __name__ == "__main__":
    main()
