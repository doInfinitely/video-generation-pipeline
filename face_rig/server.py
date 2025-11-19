#!/usr/bin/env python3
import os
import json
import subprocess
from io import BytesIO
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from PIL import Image
import replicate

# --- CONFIG ---

REPLICATE_MODEL = os.environ.get("REPLICATE_MODEL")  # e.g. "minimax/hailuo-2.3:VERSION_HASH"
if not REPLICATE_MODEL:
    raise RuntimeError("Set REPLICATE_MODEL env var, e.g. minimax/hailuo-2.3:VERSION_HASH")

if "REPLICATE_API_TOKEN" not in os.environ:
    raise RuntimeError("Set REPLICATE_API_TOKEN env var")

# Prompts per part/action — tweak as needed
PROMPTS: Dict[str, Dict[str, str]] = {
    "eyes": {
        "blink": (
            "[Static shot] A close-up of the boy's face, same framing as the first frame. "
            "The head does NOT move or tilt at all. Only the eyelids gently blink a few times. "
            "No changes to the mouth, nose, or eyebrows. Flat bright green background."
        ),
        "look_left": (
            "[Static shot] A close-up of the boy's face. The head stays perfectly still. "
            "Only the eyeballs move smoothly to look left and then return to center. "
            "Eyelids, eyebrows, mouth, and jaw remain almost completely still. Flat bright green background."
        ),
        "look_right": (
            "[Static shot] A close-up of the boy's face. The head stays perfectly still. "
            "Only the eyeballs move smoothly to look right and then return to center. "
            "Eyelids, eyebrows, mouth, and jaw remain almost completely still. Flat bright green background."
        ),
    },
    "brows": {
        "raise": (
            "[Static shot] A close-up of the boy's face. Camera and head do not move. "
            "Only the eyebrows lift slightly in surprise and then relax. "
            "Eyes mostly stay centered and the mouth stays neutral. Flat bright green background."
        ),
        "furrow": (
            "[Static shot] A close-up of the boy's face. Camera and head stay still. "
            "Only the eyebrows furrow into a thinking expression, then relax toward neutral. "
            "Eyes and mouth barely move. Flat bright green background."
        ),
    },
    "mouth": {
        "talk_loop": (
            "[Static shot] A close-up of the boy's face. No camera motion. "
            "The head does not move at all. Only the mouth moves in a natural, subtle talking loop "
            "as if speaking silently. Eyes and eyebrows stay mostly still. Flat bright green background."
        ),
        "smile": (
            "[Static shot] A close-up of the boy's face. Camera and head are completely still. "
            "Only the mouth slowly transitions from neutral to a gentle smile and then back to neutral. "
            "Eyes and eyebrows remain almost unchanged. Flat bright green background."
        ),
    },
}

# Timeline config
FRAMES_DIR = Path(__file__).parent / "frames"
SEQUENCES_DIR = FRAMES_DIR / "sequences"
CONFIG_PATH = Path(__file__).parent / "expressions.json"

# --- MODELS ---

class FrameInfo(BaseModel):
    t: float
    file: str

class Timeline(BaseModel):
    path_id: str
    expr_start: str
    expr_end: str
    pose: str
    frames: List[FrameInfo]

class RegenerateRequest(BaseModel):
    t: float

app = FastAPI()

# CORS so your browser app can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- TIMELINE HELPERS ---

def parse_path_id(path_id: str) -> tuple:
    """Parse path_id like 'neutral_to_speaking_ah__center' -> (expr_start, expr_end, pose)"""
    if "__" not in path_id:
        raise ValueError(f"Invalid path_id format: {path_id}")
    
    base, pose = path_id.rsplit("__", 1)
    
    # Try to extract start/end from base_path pattern
    if "_to_" in base:
        parts = base.split("_to_")
        if len(parts) == 2:
            return parts[0], parts[1], pose
    
    # Fallback: assume it's in config
    return base.split("_")[0], base.split("_")[-1], pose


def scan_timeline_frames(path_id: str) -> Timeline:
    """Scan a frames directory and return Timeline manifest"""
    # Check sequences directory first, then fall back to frames root
    frames_path = SEQUENCES_DIR / path_id
    if not frames_path.exists() or not frames_path.is_dir():
        frames_path = FRAMES_DIR / path_id
    
    if not frames_path.exists() or not frames_path.is_dir():
        raise HTTPException(404, f"Timeline directory not found: {path_id}")
    
    # Check for manifest.json first
    manifest_path = frames_path / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                data = json.load(f)
            # Validate and return
            frames = [FrameInfo(**f) for f in data.get("frames", [])]
            return Timeline(
                path_id=data["path_id"],
                expr_start=data["expr_start"],
                expr_end=data["expr_end"],
                pose=data["pose"],
                frames=frames
            )
        except Exception as e:
            print(f"[!] Failed to load manifest.json: {e}, falling back to scan")
    
    
    # Parse path_id to get metadata
    try:
        expr_start, expr_end, pose = parse_path_id(path_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Scan for PNG files
    frames = []
    for png_file in sorted(frames_path.glob("*.png")):
        filename = png_file.name
        # Extract t from filename like "050.png" -> 0.50
        stem = png_file.stem
        try:
            t = int(stem) / 100.0
            frames.append(FrameInfo(t=t, file=filename))
        except ValueError:
            # Skip files that don't match NNN.png pattern
            continue
    
    return Timeline(
        path_id=path_id,
        expr_start=expr_start,
        expr_end=expr_end,
        pose=pose,
        frames=sorted(frames, key=lambda f: f.t)
    )


# --- TIMELINE ENDPOINTS ---

@app.get("/timelines")
def list_timelines() -> List[str]:
    """List all available timeline path_ids"""
    timelines = []
    
    # Check sequences directory first
    if SEQUENCES_DIR.exists():
        for item in SEQUENCES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                timelines.append(item.name)
    
    # Also check root frames directory (legacy)
    if FRAMES_DIR.exists():
        for item in FRAMES_DIR.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Skip 'endpoints' and 'sequences' directories
                if item.name not in ("endpoints", "sequences") and item.name not in timelines:
                    timelines.append(item.name)
    
    return sorted(timelines)


@app.get("/timeline/{path_id:path}")
def get_timeline(path_id: str) -> Timeline:
    """Get timeline manifest with all frames"""
    return scan_timeline_frames(path_id)


@app.post("/timeline/{path_id:path}/regenerate")
async def regenerate_frame(
    path_id: str,
    req: RegenerateRequest,
    anchor_start_t: float = Query(None, description="t of left anchor; defaults to first frame"),
    anchor_end_t: float = Query(None, description="t of right anchor; defaults to last frame"),
) -> FrameInfo:
    """
    Regenerate a specific frame at time t using generate_sequence.py
    
    If anchor_start_t and anchor_end_t are provided, regenerates from those two
    frames as trusted anchors. Otherwise uses the nearest neighbor frame.
    """
    t = req.t
    
    # Don't regenerate endpoints
    if t <= 0 or t >= 1:
        raise HTTPException(400, "Cannot regenerate endpoint frames (t=0 or t=1)")
    
    # Parse path_id
    try:
        expr_start, expr_end, pose = parse_path_id(path_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Load config
    if not CONFIG_PATH.exists():
        raise HTTPException(500, "expressions.json not found")
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    # Get current timeline to find frames
    timeline = scan_timeline_frames(path_id)
    frames_path = FRAMES_DIR / path_id
    
    if not frames_path.exists():
        raise HTTPException(404, f"Timeline directory not found: {path_id}")
    
    # Determine output path
    frame_index = int(round(t * 100))
    out_name = f"{frame_index:03d}.png"
    out_path = frames_path / out_name
    
    # Import generation functions
    try:
        from generate_sequence import (
            generate_midframe_openai,
            generate_midframe_from_endpoints,
            load_config,
        )
        
        cfg = load_config(str(CONFIG_PATH))
        
        # Check if we're using anchors
        if anchor_start_t is not None and anchor_end_t is not None:
            # ANCHOR MODE: regenerate from two trusted endpoints
            print(f"[regenerate] Using anchor mode: t={t:.2f}, anchors=[{anchor_start_t:.2f}, {anchor_end_t:.2f}]")
            
            # Find the anchor frames
            def find_closest_frame(target_t: float):
                best = timeline.frames[0]
                best_diff = abs(best.t - target_t)
                for frame in timeline.frames[1:]:
                    diff = abs(frame.t - target_t)
                    if diff < best_diff:
                        best = frame
                        best_diff = diff
                return best
            
            left_frame = find_closest_frame(anchor_start_t)
            right_frame = find_closest_frame(anchor_end_t)
            
            if left_frame.t >= right_frame.t:
                raise HTTPException(400, "Invalid anchors: left.t must be < right.t")
            
            # Compute normalized position between anchors
            u = (t - left_frame.t) / (right_frame.t - left_frame.t)
            
            left_path = frames_path / left_frame.file
            right_path = frames_path / right_frame.file
            
            if not left_path.exists() or not right_path.exists():
                raise HTTPException(404, "Anchor frames not found")
            
            print(f"[regenerate] Anchors: left={left_frame.file} (t={left_frame.t:.2f}), right={right_frame.file} (t={right_frame.t:.2f}), u={u:.3f}")
            
            generate_midframe_from_endpoints(
                left_image_path=str(left_path),
                right_image_path=str(right_path),
                out_path=str(out_path),
                expr_start=expr_start,
                expr_end=expr_end,
                pose_id=pose,
                u=u,
                cfg=cfg,
            )
        else:
            # SINGLE-BASE MODE: use nearest neighbor (legacy behavior)
            print(f"[regenerate] Using single-base mode: t={t:.2f}")
            
            # Look for endpoint frames (or use endpoints directory)
            start_img = frames_path / "000.png"
            end_img = frames_path / "100.png"
            
            if not start_img.exists():
                endpoints_dir = FRAMES_DIR / "endpoints"
                start_img = endpoints_dir / f"{expr_start}_{pose}.png"
            
            if not end_img.exists():
                endpoints_dir = FRAMES_DIR / "endpoints"
                end_img = endpoints_dir / f"{expr_end}_{pose}.png"
            
            if not start_img.exists() or not end_img.exists():
                raise HTTPException(404, "Endpoint frames not found")
            
            # Choose which endpoint is closer to use as base
            base_image = start_img if abs(t - 0.0) < abs(t - 1.0) else end_img
            
            generate_midframe_openai(
                base_image_path=str(base_image),
                out_path=str(out_path),
                expr_start=expr_start,
                expr_end=expr_end,
                pose_id=pose,
                t_mid=t,
                cfg=cfg,
            )
        
        print(f"[regenerate] Successfully generated {out_path}")
        
    except Exception as e:
        print(f"[regenerate] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Regeneration failed: {e}")
    
    return FrameInfo(t=t, file=out_name)


@app.get("/frames/{path_id:path}/{filename}")
async def get_frame_image(path_id: str, filename: str):
    """Serve a frame PNG"""
    # Check sequences directory first, then fall back to frames root
    file_path = SEQUENCES_DIR / path_id / filename
    if not file_path.exists() or not file_path.is_file():
        file_path = FRAMES_DIR / path_id / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, "Frame not found")
    
    return FileResponse(file_path, media_type="image/png")


# --- FACE ANIMATOR ENDPOINT ---

def call_replicate_animate(part: str, action: str, crop_png: BytesIO) -> bytes:
    prompt = PROMPTS.get(part, {}).get(action)
    if not prompt:
        raise HTTPException(400, f"Unknown part/action: {part}/{action}")

    crop_png.seek(0)

    try:
        output = replicate.run(
            REPLICATE_MODEL,
            input={
                "prompt": prompt,
                "duration": 6,
                "first_frame_image": crop_png,
                "prompt_optimizer": False,
                "resolution": "1080p",
            },
        )
    except Exception as e:
        # Bubble up any Replicate error in a readable way
        raise HTTPException(500, f"Replicate run failed: {e}")

    # Debug – see what shape we're getting
    print("Replicate output type:", type(output))
    print("Replicate output repr (truncated):", repr(output)[:500])

    # Try to handle the common shapes:
    from replicate.helpers import FileOutput

    # Case 1: single FileOutput (newer Python client)
    if isinstance(output, FileOutput):
        return output.read()

    # Case 2: list[...] (older style or multi-output models)
    if isinstance(output, list) and output:
        first = output[0]

        # list[FileOutput]
        if isinstance(first, FileOutput):
            return first.read()

        # list[str] – URLs to the video
        if isinstance(first, str):
            import requests

            resp = requests.get(first)
            resp.raise_for_status()
            return resp.content

    # Case 3: raw bytes (just in case)
    if isinstance(output, (bytes, bytearray)):
        return output

    raise HTTPException(
        500,
        f"Unexpected Replicate output type: {type(output)}; "
        f"value (truncated): {repr(output)[:200]}",
    )


@app.post("/animate")
async def animate(
    part: str = Form(...),             # "eyes" | "brows" | "mouth" | etc.
    action: str = Form(...),           # "blink", "look_left", "talk_loop", ...
    x: int = Form(...),                # crop x (original image coordinates)
    y: int = Form(...),                # crop y
    width: int = Form(...),
    height: int = Form(...),
    file: UploadFile = File(...),      # full original image
):
    print(f"[/animate] Received request: part={part}, action={action}, x={x}, y={y}, width={width}, height={height}")
    
    try:
        raw = await file.read()
        img = Image.open(BytesIO(raw)).convert("RGBA")
        print(f"[/animate] Image loaded: {img.width}x{img.height}")
    except Exception as e:
        print(f"[/animate] Failed to read image: {e}")
        raise HTTPException(400, "Could not read image")

    # Clamp box to image bounds
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(img.width, x + width)
    y1 = min(img.height, y + height)
    if x1 <= x0 or y1 <= y0:
        raise HTTPException(400, "Invalid crop box")

    # Crop to selected region
    crop = img.crop((x0, y0, x1, y1))
    print(f"[/animate] Cropped region: {crop.width}x{crop.height}")

    # ---- NEW: wrap crop into a square canvas to keep aspect ratio valid ----
    cw, ch = crop.size
    side = max(cw, ch)

    # bright green background (for later chroma-key if you want)
    square = Image.new("RGBA", (side, side), (0, 255, 0, 255))

    # center the crop on the square canvas
    offset_x = (side - cw) // 2
    offset_y = (side - ch) // 2
    square.paste(crop, (offset_x, offset_y))

    print(f"[/animate] Wrapped crop in square: {square.width}x{square.height}")

    buf = BytesIO()
    square.save(buf, format="PNG")
    print(f"[/animate] Square PNG size: {len(buf.getvalue())} bytes")

    try:
        print(f"[/animate] Calling Replicate with part={part}, action={action}...")
        video_bytes = call_replicate_animate(part, action, buf)
        print(f"[/animate] Got video bytes: {len(video_bytes)} bytes")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[/animate] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Replicate error: {e}")

    # Assume mp4 from the video model
    return Response(content=video_bytes, media_type="video/mp4")

