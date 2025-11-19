#!/usr/bin/env python3
"""
face_parts_to_video.py

Use Replicate to generate short green-screen videos for
different parts of the face (eyes, brows, mouth) from a base portrait.

Usage (example):
    python face_parts_to_video.py \
        --image watercolor_boy_greenscreen.png \
        --outdir face_movement
"""

import os
import argparse
from pathlib import Path
import replicate
from typing import Any

# --------- CONFIG ---------

# Put your chosen Replicate video model here
# e.g. "minimax/video-01:VERSION" or "minimax/hailuo-2.3:VERSION"
VIDEO_MODEL = "minimax/hailuo-2.3"

# Duration in seconds for each clip
CLIP_DURATION = 6

# Define the motions we want per face region
FACE_PART_CONFIG = {
    "eyes": {
        "blink": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, eyebrows and mouth are 100% frozen like a still image. "
            "The ONLY animation is that the eyelids gently blink a few times. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
        "look_left": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, eyebrows and mouth are 100% frozen like a still image. "
            "The ONLY animation is that the pupils and irises smoothly look to the boy's left and then return to center. "
            "The eyelids move as little as possible. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
        "look_right": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, eyebrows and mouth are 100% frozen like a still image. "
            "The ONLY animation is that the pupils and irises smoothly look to the boy's right and then return to center. "
            "The eyelids move as little as possible. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
    },
    "brows": {
        "raise": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, pupils, irises and mouth are 100% frozen like a still image. "
            "The ONLY animation is that the eyebrows slowly raise in surprise and then return to neutral. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
        "furrow": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, pupils, irises and mouth are 100% frozen like a still image. "
            "The ONLY animation is that the eyebrows slowly furrow into a thinking expression and then return to neutral. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
    },
    "mouth": {
        "talk_loop": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, pupils, irises and eyebrows are 100% frozen like a still image. "
            "The ONLY animation is that the mouth moves in a natural muted talking loop. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
        "smile": (
            "A static, hand-painted watercolor portrait of the same young boy on a flat bright green background. "
            "The CAMERA IS COMPLETELY LOCKED OFF. There is ABSOLUTELY NO camera motion and NO head motion. "
            "The body, head, hair, cheeks, nose, pupils, irises and eyebrows are 100% frozen like a still image. "
            "The ONLY animation is that the mouth smoothly changes from neutral into a small smile and back to neutral. "
            "Do not tilt, rotate, or move the head. Do not move the camera. Do not change lighting or background."
        ),
    },
}


def _save_output_to_file(output: Any, out_path: Path):
    """
    Handle Replicate outputs:

    - replicate.helpers.FileOutput (or any file-like with .read())
    - list[FileOutput]
    - list[str] (URLs)
    - raw bytes
    """
    # Try to import the actual FileOutput class (optional)
    try:
        from replicate.helpers import FileOutput
    except Exception:
        FileOutput = None  # type: ignore

    def _is_file_like(obj: Any) -> bool:
        return hasattr(obj, "read") and callable(getattr(obj, "read"))

    # Case 1: single FileOutput or any file-like
    if (FileOutput is not None and isinstance(output, FileOutput)) or _is_file_like(output):
        with open(out_path, "wb") as f:
            f.write(output.read())
        return

    # Case 2: list[...] of something
    if isinstance(output, list) and output:
        first = output[0]

        # list[FileOutput] or list[file-like]
        if (FileOutput is not None and isinstance(first, FileOutput)) or _is_file_like(first):
            with open(out_path, "wb") as f:
                f.write(first.read())
            return

        # list[str] of URLs
        if isinstance(first, str):
            import requests
            resp = requests.get(first)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return

    # Case 3: raw bytes
    if isinstance(output, (bytes, bytearray)):
        with open(out_path, "wb") as f:
            f.write(output)
        return

    raise TypeError(f"Don't know how to save output of type {type(output)}: {output!r}")

def generate_clip(
    image_path: Path,
    outdir: Path,
    part: str,
    action: str,
    prompt: str,
    duration: int = CLIP_DURATION,
):
    """Call Replicate to generate one video clip."""
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{part}_{action}.mp4"

    print(f"[+] Generating {part}/{action} -> {out_path}")

    with open(image_path, "rb") as img_file:
        # NOTE: adjust the inputs to match your chosen video model’s schema.
        # For minimax/video-01 or hailuo-style models this pattern is typical:
        output = replicate.run(
            VIDEO_MODEL,
            input={
                "prompt": prompt,
                "duration": duration,
                # Change this key name to whatever your model expects:
                "first_frame_image": img_file,
                # Add extra knobs (seed, fps, motion_strength, etc.) if needed.
            },
        )

    print(f"    [debug] Replicate output type: {type(output)}")
    _save_output_to_file(output, out_path)
    print(f"[✓] Saved {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Base portrait image (green background).")
    parser.add_argument("--outdir", required=True, help="Directory to write video clips.")
    parser.add_argument(
        "--only-part",
        choices=["eyes", "brows", "mouth"],
        help="Optionally only generate clips for a single part.",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    outdir = Path(args.outdir)

    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")

    for part, actions in FACE_PART_CONFIG.items():
        if args.only_part and part != args.only_part:
            continue
        for action, prompt in actions.items():
            try:
                generate_clip(image_path, outdir, part, action, prompt)
            except Exception as e:
                print(f"[!] Error generating {part}/{action}: {e}")


if __name__ == "__main__":
    if "REPLICATE_API_TOKEN" not in os.environ:
        raise SystemExit("REPLICATE_API_TOKEN not set. `export REPLICATE_API_TOKEN=xxx` first.")
    main()

