#!/usr/bin/env python3
"""Create a fast, full-resolution GIF preview from the project demo video."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=ROOT / "demo/demo1.mp4")
    parser.add_argument("output", nargs="?", type=Path, default=ROOT / "demo/demo1.gif")
    parser.add_argument("--speed", type=float, default=8.0, help="playback speed multiplier (default: 8x)")
    parser.add_argument("--fps", type=int, default=10, help="GIF frame rate (default: 10 fps)")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        parser.error("ffmpeg is required; install it and run this script again")
    if args.speed <= 0 or args.fps <= 0:
        parser.error("--speed and --fps must be positive")
    if not args.input.is_file():
        parser.error(f"input video not found: {args.input}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # A single shared palette pass keeps UI colors cleaner than direct RGB->GIF
    # conversion. No scale filter is applied, so the source resolution is kept.
    filters = (
        f"[0:v]setpts=PTS/{args.speed:g},fps={args.fps},split[a][b];"
        "[a]palettegen=max_colors=256:stats_mode=full[p];"
        "[b][p]paletteuse=dither=sierra2_4a"
    )
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(args.input),
        "-filter_complex",
        filters,
        "-loop",
        "0",
        str(args.output),
    ]
    subprocess.run(command, check=True)
    print(f"Wrote {args.output} at {args.speed:g}x, {args.fps} fps; source resolution preserved.")


if __name__ == "__main__":
    main()
