from __future__ import annotations

import argparse
import sys

from edap.config import ConfigError, default_runtime_platform
from edap.tts import NullSpeechBackend, build_speech_backend


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Speak a short message through EDAP TTS")
    parser.add_argument("text", nargs="+", help="Text to speak")
    args = parser.parse_args(argv)

    try:
        platform_name = default_runtime_platform()
    except ConfigError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    backend = build_speech_backend(platform_name)
    if isinstance(backend, NullSpeechBackend):
        sys.stderr.write(f"No TTS backend available for detected platform: {platform_name}\n")
        return 2

    backend.speak(" ".join(args.text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
