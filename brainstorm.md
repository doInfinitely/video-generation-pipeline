me:
I want to create a video generating ai application. The primary video generating model is minimax/video-01 which generate 6s videos and can be prompted with text and either a starting frame or subject reference. I’m thinking what happens first is the user prompt (“Generate a video illustrating quicksort”) gets fed into the “play by play” agent which generates a structured json of of prompts at each keyframe in the video mapping time in ms to keyframe prompts ({0:”A random series of numbers from 0 to 11 each wrapped in a box are scrambled in a line”, 1000: “The first box from left to right is chosen as the pivot, it rises upwards and it’s box outline changes color to indicate that it was selected”, 1500: “The second box is compared numerically with the pivot and they are moved to their proper place in relation to each other.”, 2000: “The third box…} in practice the keyframe play by play might start with the precise sequence of numbers in this example). Once the keyframe play by play has been generated the keyframe prompts are split into six second chunks, the time numbers are changed to be in relation to the start of their chunks, and the first frame from the first keyframe prompt from the first chunk is optionally generated. The optional first frame image along with the times and text from the first chunk are integrated into a prompt for video-01. The last frame from each video gen is used as the first frame for the next video gen until the keyframe play by play has been fully exhausted. This is how the visuals of the video are to be generated, subsequently we will develop the script and audio.

chatgpt:
Cool, this is a really nice pipeline idea—and it’s actually quite implementable. Let me turn what you described into a concrete architecture plus some data structures and pseudo-code so you can start building.

I’ll focus on **visuals only** (play-by-play → chunks → minimax/video-01 chaining). We can layer script/audio on later.

---

## 1. High-level architecture

**Core components:**

1. **Frontend (Web / Desktop)**

   * Text box: “Generate a video illustrating quicksort.”
   * Optional: upload reference image / subject image.
   * Progress display + previews of each 6s segment.

2. **Backend Orchestrator (Python / Node)**

   * Endpoint: `/generate_video`
   * Calls:

     * **Play-by-Play Agent (LLM)** → structured keyframe JSON
     * **Chunker** → convert global keyframes into 6s chunks
     * **Video Worker** → calls `minimax/video-01` for each chunk, chaining the last frame as the next start frame.
   * Handles storage (S3 / GCS / local) and final concatenation.

3. **Play-by-Play Agent (LLM chain)**

   * Input: user prompt + optional constraints (duration, fps, teaching level, style).
   * Output: JSON like:

     ```json
     {
       "duration_ms": 18000,
       "keyframes": {
         "0": "…",
         "1000": "…",
         "1500": "…",
         "2000": "…"
       }
     }
     ```
   * Could also include **global style** and **subject descriptors** to keep everything consistent.

4. **Video Generation Worker**

   * Takes a chunk (≤ 6000 ms) and:

     * Optional initial frame (image URL / bytes)
     * Timeline of prompts
   * Calls `minimax/video-01` to generate a 6s clip.
   * Extracts the **last frame** to feed as the starting image to the next chunk.

5. **Post-processing**

   * Concatenate the generated 6s clips into one video.
   * Optional: add captions / voiceover later.

---

## 2. JSON schema for the play-by-play

### Input to Play-by-Play Agent

You can give the LLM a structured system prompt like:

> You are a “video storyboard AI” for an educational video generator that uses a 6-second video model. Given a user’s request, you must output a timeline of keyframe prompts that visually explain the concept over time.
>
> Output JSON with:
>
> * duration_ms: total duration in milliseconds
> * fps: assumed frame rate (default 24)
> * global_style: description of visual style and subject appearance
> * keyframes: an object mapping time in ms to a short, vivid visual description of what is on screen at that moment (no dialogue, visual actions only).
>
> Only output JSON. Do not include any explanations.

**Example user prompt:**

> “Generate a video illustrating quicksort on an array of twelve numbers from 0 to 11, showing partition around a pivot and recursive subarrays.”

### Expected LLM JSON output (example)

```json
{
  "duration_ms": 18000,
  "fps": 24,
  "global_style": "Clean flat 2D animation, pale background, each number in a rounded rectangle card, consistent font and colors.",
  "keyframes": {
    "0": "A horizontal row of 12 cards labeled 0 to 11 in random order, centered on screen.",
    "1000": "The leftmost card is highlighted, rises slightly above the row, its border turns blue to show it was chosen as pivot.",
    "1500": "A subtle arrow appears under the second card as it slides left or right to show comparing with pivot, with a small checkmark for correct side.",
    "2000": "The third card moves past the pivot to show it is greater; cards rearrange smoothly with a ghost trace of their previous positions.",
    "4000": "The pivot card glides to the correct sorted position, splitting the row into two colored subarrays on the left and right.",
    "6000": "Zoom slightly into the left subarray, highlighting it as the next partition to be processed.",
    "8000": "Left subarray is now a separate row; its first card becomes a new pivot with a different border color.",
    "12000": "Process repeats quickly with smaller card movements, showing sorting of left subarray.",
    "16000": "Zoom out to show the entire array now sorted from 0 to 11, cards glowing subtly."
  }
}
```

You don’t need perfect timing from the LLM; you just need a **monotonically increasing** ms timeline.

---

## 3. Chunking into 6-second segments

“minimax/video-01” gives you **6s videos**. So you’ll chunk the keyframes into segments:

* Segment 1: `0–5999 ms`
* Segment 2: `6000–11999 ms`
* Segment 3: `12000–17999 ms`
* …

**Chunking algorithm (conceptually):**

```python
CHUNK_MS = 6000

def chunk_keyframes(keyframes: dict[str, str], duration_ms: int, chunk_ms: int = CHUNK_MS):
    # keyframes: { "0": "...", "1000": "...", ... }
    # returns: list of chunks, where each chunk has local times 0..chunk_ms-1
    times = sorted(int(t) for t in keyframes.keys())
    max_time = duration_ms

    num_chunks = (max_time + chunk_ms - 1) // chunk_ms
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_ms
        end = min((i + 1) * chunk_ms, max_time)

        chunk_keyframes = {}
        for t in times:
            if start <= t < end:
                local_t = t - start
                chunk_keyframes[str(local_t)] = keyframes[str(t)]

        # If no keyframe at exactly 0, we can synthesize one by copying nearest previous or “hold state”.
        if "0" not in chunk_keyframes:
            # fallback: use earliest keyframe in this chunk as the 0 state
            if chunk_keyframes:
                first_time = min(int(k) for k in chunk_keyframes.keys())
                chunk_keyframes["0"] = chunk_keyframes[str(first_time)]

        chunks.append({
            "chunk_index": i,
            "start_global_ms": start,
            "end_global_ms": end,
            "keyframes": chunk_keyframes
        })

    return chunks
```

---

## 4. Building the prompt for each 6s generation

For each chunk, you’ll build a **single prompt** that gives the model:

1. **Global style and consistency info**
2. **What happened so far (summarized)**
3. **Timeline for this 0–6000 ms interval**
4. **Optional starting frame image** (for continuity)

### Prompt template (pseudo)

You won’t pass raw JSON to the video model; instead, convert it to text like:

> An educational flat 2D animation explaining quicksort.
> Maintain the same visual style and the same set of numbered cards as previous segments.
>
> For this 6-second segment, follow this visual timeline (times in milliseconds from the start of this segment):
>
> * At 0 ms: A horizontal row of 12 cards labeled 0 to 11 in random order, centered on screen.
> * At 1000 ms: The leftmost card is highlighted, rises slightly above the row, its border turns blue to show it was chosen as pivot.
> * At 1500 ms: The second card is compared with the pivot…
> * …
>   Smoothly animate between these states with clear, readable motion.

For **later segments**, add a short context summary like:

> Continue from the previous segment: the pivot has already been placed in its correct position, and the left subarray is about to be partitioned.

You can generate that summary automatically from the global `keyframes` or have the LLM also output high-level “scene notes” per chunk.

---

## 5. Chaining the frames between chunks

For continuity, you want:

* **Clip 1**: no initial frame (or maybe a user-provided reference/subject image).
* **Clip 2+**: starting frame = **last frame of previous clip**.

Implementation idea:

1. Call `minimax/video-01` → get video bytes / URL.

2. Extract final frame with ffmpeg:

   ```bash
   ffmpeg -sseof -0.04 -i clip1.mp4 -vframes 1 last_frame_1.png
   ```

   (Or programmatically via ffmpeg bindings.)

3. Use `last_frame_1.png`:

   * Either upload to a URL if the API expects URLs.
   * Or provide as binary/bytes if the API supports that.

4. For the next request:

   ```python
   video_model.generate(
       prompt=chunk_prompt,
       first_frame=last_frame_1_png_bytes,  # if supported
       duration=6.0,
       # any other params: seed, style, aspect ratio
   )
   ```

5. Repeat until all chunks are done.

At the end, concatenate all the 6s clips:

```bash
# create a file list.txt
# file clip_0.mp4
# file clip_1.mp4
# ...
ffmpeg -f concat -safe 0 -i list.txt -c copy full_quicksort.mp4
```

---

## 6. Rough backend flow in Python (pseudo-code)

Here’s a “single file” style view of the core orchestration:

```python
def generate_video_for_prompt(user_prompt: str, reference_image: bytes | None = None):
    # 1. Call LLM for play-by-play
    storyboard = call_llm_play_by_play(user_prompt)
    keyframes = storyboard["keyframes"]
    duration_ms = storyboard["duration_ms"]
    global_style = storyboard.get("global_style", "")

    # 2. Chunk keyframes into 6s segments
    chunks = chunk_keyframes(keyframes, duration_ms, chunk_ms=6000)

    previous_last_frame = reference_image  # may be None for first segment
    generated_clips = []

    for chunk in chunks:
        chunk_prompt = build_chunk_prompt(
            user_prompt=user_prompt,
            global_style=global_style,
            chunk=chunk,
        )

        # 3. Call video model
        video_bytes = call_minimax_video_01(
            prompt=chunk_prompt,
            first_frame=previous_last_frame,  # can be None
            duration_seconds=6
        )

        clip_path = save_temp_video(video_bytes)
        generated_clips.append(clip_path)

        # 4. Extract last frame for next iteration
        previous_last_frame = extract_last_frame_as_png_bytes(clip_path)

    # 5. Concatenate clips
    final_video_path = concat_videos_ffmpeg(generated_clips)
    return final_video_path
```

Your `call_llm_play_by_play`, `build_chunk_prompt`, and `call_minimax_video_01` will depend on which APIs you use (OpenAI, Minimax SDK, etc.), but this is the orchestration pattern.

---

## 7. Extension hooks for script + audio later

You already hinted at this:

> “Subsequently we will develop the script and audio.”

The nice thing about the play-by-play JSON is you can **re-use it**:

* Generate a **narration script**:

  * Ask an LLM to write a voiceover script whose paragraphs are aligned with the time ranges between keyframes (or chunks).
* Generate **subtitle lines**:

  * Another pass that converts narration to SRT/WEBVTT with time codes.
* Generate **audio**:

  * Use TTS (OpenAI TTS, ElevenLabs, etc.) with the script and align with the video timeline (you already have ms breakdown).
* Optional: use the same `keyframes` to place on-screen text callouts or highlights synced to narration.

---

## 8. Next steps I can help with

If you’d like, I can:

* Draft the **exact system prompt** and **function schema** for the Play-by-Play Agent (for OpenAI tools / JSON mode).
* Sketch concrete `call_minimax_video_01` function calls assuming a specific Minimax API signature.
* Help you choose a backend stack (FastAPI + Celery + Redis, etc.) and lay out endpoints and queues for longer multi-chunk jobs.

But as a starting point, your idea maps very cleanly to:

1. LLM → storyboard JSON
2. Chunk → 6s segments
3. For each segment: LLM → text prompt → minimax/video-01 (with chained last frame)
4. FFMPEG → concatenated final video

Which is exactly what you described, just nailed down into something you can start coding.

