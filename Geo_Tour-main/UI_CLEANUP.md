# UI Cleanup - Voice Selection Simplification

## Changes Made

Simplified the Streamlit UI to remove redundant voice selection now that we're using face_rig audio exclusively.

## Before

The UI had **two separate voice selection sections**:

### 1. Geo_Tour Narrator Voice (Removed)
```
🗣️ Voice
└─ Choose Narrator Voice
   ├─ Sarah
   ├─ Nathaniel
   ├─ Zane
   ├─ Sona
   ├─ Russ
   └─ Ryan
```

### 2. Face Rig Character Voice
```
🎭 Face Rig Character Animation
├─ Enable Face Rig Character
├─ Face Rig Server URL
└─ Character Voice
   ├─ Sam
   ├─ Rachel
   ├─ Domi
   └─ Bella
```

**Problem**: Confusing! Users didn't know which voice would be used.

## After

Now there's **one unified voice selection**:

```
🎭 Face Rig Character & Voice
├─ Enable Face Rig Character
├─ Face Rig Server URL
└─ Narrator Voice (used for character and video)
   ├─ Sam (Male, Conversational) ⭐ Default
   ├─ Bella (Female, Engaging)
   ├─ Domi (Female, Confident)
   ├─ Adam (Male, Deep)
   ├─ Rachel (Female, Calm)
   └─ Antoni (Male, Young)

💡 The face_rig character will use this voice with lip-sync animation
```

## Benefits

✅ **Clearer** - One voice selection, one voice used  
✅ **Simpler** - No confusion about which voice is active  
✅ **Accurate** - Voice selection matches what's actually used  
✅ **Better labels** - Voice descriptions include gender and style  
✅ **Helpful info** - Tooltip explains the voice is used for everything  

## Technical Details

### Code Changes (`app.py`)

#### Removed: Geo_Tour Voice Selection
```python
# REMOVED:
with st.expander("🗣️ Voice", expanded=True):
    voice_options = {...}
    selected_voice = st.selectbox("Choose Narrator Voice", ...)
    st.session_state.voice_id = voice_options[selected_voice]
```

#### Enhanced: Face Rig Voice Selection
```python
# NEW: Combined into one section
with st.expander("🎭 Face Rig Character & Voice", expanded=True):
    st.checkbox("Enable Face Rig Character", ...)
    
    st.markdown("**Narrator Voice** (used for character and video)")
    face_rig_voice_options = {
        "Sam (Male, Conversational)": "21m00Tcm4TlvDq8ikWAM",
        # ... more options with descriptions
    }
    selected_fr_voice = st.selectbox(
        "Choose Voice",
        list(face_rig_voice_options.keys()),
        help="This voice will be used for all narration and character animation"
    )
```

#### Updated: Pipeline Initialization
```python
# REMOVED voice_id parameter (not needed for face_rig)
pipeline = VideoPipeline(
    openai_api_key=openai_key,
    video_api_key=replicate_key,
    tts_api_key=tts_key,
    # voice_id removed - using face_rig audio exclusively
    use_face_rig=st.session_state.get("use_face_rig", True),
    face_rig_url=st.session_state.get("face_rig_url", "http://localhost:8000"),
    face_rig_voice_id=st.session_state.get("face_rig_voice_id", "21m00Tcm4TlvDq8ikWAM")
)
```

## Voice Options

### Available Voices (with descriptions)

| Voice Name | ElevenLabs ID | Description |
|-----------|---------------|-------------|
| Sam | `21m00Tcm4TlvDq8ikWAM` | Male, Conversational (Default) |
| Bella | `EXAVITQu4vr4xnSDxMaL` | Female, Engaging |
| Domi | `AZnzlk1XvdvUeBnXmlld` | Female, Confident |
| Adam | `pNInz6obpgDQGcFmaJgB` | Male, Deep |
| Rachel | `21m00Tcm4TlvDq8ikWAM` | Female, Calm |
| Antoni | `ErXwobaYiN019PkySvjV` | Male, Young |

**Note**: Voice selection now includes gender and style in the label for easier selection.

## User Experience

### Before (Confusing)
```
User: "Which voice setting should I use?"
User: "Will both voices be in my video?"
User: "Why do I need to pick two voices?"
```

### After (Clear)
```
User: "I'll pick Sam for my narrator"
User: "This voice will be used for everything - perfect!"
```

## Backwards Compatibility

### Face Rig Disabled

If a user disables face_rig:

```python
# Pipeline still works, uses fallback to Geo_Tour audio_gen
# voice_id will be None, audio_gen uses its default
```

The pipeline gracefully handles this case by falling back to the Geo_Tour audio generator with default settings.

### Old Configuration

If someone has old code using `voice_id`:

```python
# Still works - voice_id is accepted but not used when face_rig is enabled
pipeline = VideoPipeline(
    voice_id="Lny4bN2CTZWgKZAgIHKa",  # Ignored if use_face_rig=True
    use_face_rig=True,
    face_rig_voice_id="21m00Tcm4TlvDq8ikWAM"  # This one is used
)
```

## Testing

To verify the changes:

1. **Start the UI**:
   ```bash
   cd Geo_Tour-main
   streamlit run app.py
   ```

2. **Check the sidebar**:
   - ✅ Should see ONE voice section: "🎭 Face Rig Character & Voice"
   - ✅ Voice options should have descriptions
   - ✅ Should see helpful tooltip about voice usage

3. **Generate a video**:
   - Select a voice (e.g., "Bella (Female, Engaging)")
   - Generate video
   - Verify the character uses that voice
   - Verify the video audio matches

## Summary

✅ **Removed**: Redundant Geo_Tour voice selection  
✅ **Enhanced**: Face rig voice selection with better labels  
✅ **Simplified**: One voice picker for everything  
✅ **Clearer**: Users understand which voice will be used  
✅ **Backwards compatible**: Old code still works  

The UI is now cleaner, simpler, and matches the actual audio pipeline! 🎉

