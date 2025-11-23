"""
Main pipeline orchestrator - coordinates all modules
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime

from config import ensure_directories, OUTPUT_DIR, TEMP_DIR, USE_STORYBOARD
from script_generator import ScriptGenerator
from scene_planner_ENHANCED import ScenePlanner
from storyboard_generator import StoryboardGenerator
from video_generator import VideoGenerator
from audio_generator import AudioGenerator
from video_assembler import VideoAssembler
from face_rig_integrator import FaceRigIntegrator


def safe_print(*args, **kwargs):
    """Safely print messages, handling closed file errors in Streamlit"""
    try:
        print(*args, **kwargs)
    except (IOError, OSError, ValueError):
        # Silently fail if stdout is closed (Streamlit context)
        pass


class VideoPipeline:
    def __init__(self, 
                 openai_api_key=None,
                 video_api_key=None,
                 tts_api_key=None,
                 video_provider="replicate",
                 tts_provider="elevenlabs",
                 use_storyboard=None,
                 svd_model=None,
                 sdxl_model=None,
                 voice_id=None,
                 use_face_rig=True,
                 face_rig_url="http://localhost:8000",
                 face_rig_voice_id="21m00Tcm4TlvDq8ikWAM"):
        """
        Initialize the video generation pipeline
        
        Args:
            openai_api_key (str): API key for OpenAI (GPT-4)
            video_api_key (str): API key for video generation (Replicate API key)
            tts_api_key (str): API key for text-to-speech
            video_provider (str): Video generation provider (replicate, runwayml, pika, etc.)
            tts_provider (str): TTS provider (elevenlabs, openai, etc.)
            use_storyboard (bool): Whether to generate storyboard images first (default: from config)
            use_face_rig (bool): Whether to generate face_rig character animations
            face_rig_url (str): URL of the face_rig server
            face_rig_voice_id (str): ElevenLabs voice ID for face_rig (default: Sam voice)
        """
        ensure_directories()
        
        self.script_gen = ScriptGenerator(openai_api_key)
        self.scene_planner = ScenePlanner(openai_api_key)
        self.storyboard_gen = StoryboardGenerator(video_api_key)
        self.video_gen = VideoGenerator(video_api_key, svd_model=svd_model, sdxl_model=sdxl_model)
        self.audio_gen = AudioGenerator(tts_api_key, tts_provider, voice_id=locals().get('voice_id'))
        self.assembler = VideoAssembler()
        
        self.use_storyboard = use_storyboard if use_storyboard is not None else USE_STORYBOARD
        self.use_face_rig = use_face_rig
        
        # Initialize face_rig integrator if enabled
        if self.use_face_rig:
            self.face_rig = FaceRigIntegrator(face_rig_url=face_rig_url, voice_id=face_rig_voice_id)
            # Check if face_rig server is available
            if not self.face_rig.check_server_health():
                safe_print("⚠️  Face_rig server not available, disabling face_rig integration")
                self.use_face_rig = False
        
        self.current_project = None
    
    def run(self, user_prompt, output_filename=None, num_scenes=None, scene_duration=None, progress_callback=None):
        """
        Run the complete pipeline
        
        Args:
            user_prompt (str): User's description of desired video
            output_filename (str): Optional custom output filename
            num_scenes (int): Number of scenes to generate
            scene_duration (int): Duration per scene in seconds
            progress_callback (callable): Optional callback for progress updates
            
        Returns:
            dict: Results including paths and metadata
        """
        safe_print("\n" + "=" * 70)
        safe_print("🎬 VIDEO GENERATION PIPELINE")
        safe_print("=" * 70)
        safe_print(f"Prompt: {user_prompt}")
        safe_print("=" * 70 + "\n")
        
        # Create project data structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_project = {
            "prompt": user_prompt,
            "timestamp": timestamp,
            "steps": {}
        }
        
        try:
            # Step 1: Generate script
            if progress_callback:
                progress_callback(1, 6, "📝 Generating script...", "Creating narrative structure")
            safe_print("\n[1/6] Script Generation")
            safe_print("-" * 70)
            script_data = self.script_gen.generate(user_prompt)
            self.current_project["steps"]["script"] = script_data
            if progress_callback:
                progress_callback(1, 6, "✅ Script generated", f"Title: {script_data.get('title', 'Untitled')}")
            
            # Step 2: Plan scenes
            if progress_callback:
                progress_callback(2, 6, "🎬 Planning scenes...", f"Creating {num_scenes or 5} scenes")
            safe_print("\n[2/6] Scene Planning")
            safe_print("-" * 70)
            scene_plan = self.scene_planner.create_plan(script_data, target_scenes=num_scenes, scene_duration=scene_duration)
            self.current_project["steps"]["scenes"] = scene_plan
            if progress_callback:
                progress_callback(2, 6, "✅ Scenes planned", f"{len(scene_plan.get('scenes', []))} scenes created")
            
            # Step 3: Generate storyboard (optional)
            storyboard_images = None
            if self.use_storyboard:
                if progress_callback:
                    progress_callback(3, 6, "🎨 Generating storyboards...", "Creating visual storyboards for each scene")
                safe_print("\n[3/6] Storyboard Generation")
                safe_print("-" * 70)
                storyboard_images = self.storyboard_gen.generate(scene_plan)
                self.current_project["steps"]["storyboard"] = storyboard_images
                if progress_callback:
                    progress_callback(3, 6, "✅ Storyboards generated", f"{len(storyboard_images or [])} storyboard images created")
            else:
                if progress_callback:
                    progress_callback(3, 6, "⏭️ Storyboard generation skipped", "Using text-to-video generation")
                safe_print("\n[3/6] Storyboard Generation (skipped)")
                safe_print("-" * 70)
            
            # Step 3.5: Generate face_rig videos (if enabled)
            face_rig_videos = []
            face_rig_audio_files = []
            scene_audio_durations = []
            if self.use_face_rig:
                if progress_callback:
                    progress_callback(3.5, 7, "🎭 Generating face_rig character animations...", "Creating lip-sync videos for each scene")
                safe_print("\n[3.5/7] Face_rig Character Animation")
                safe_print("-" * 70)
                
                for scene in scene_plan['scenes']:
                    try:
                        face_rig_result = self.face_rig.generate_scene_video(
                            scene['narration'],
                            scene['scene_number']
                        )
                        face_rig_videos.append(face_rig_result['video_path'])
                        face_rig_audio_files.append(face_rig_result['audio_path'])
                        scene_audio_durations.append(face_rig_result['audio_duration'])
                        
                        # Update scene duration to match actual audio duration
                        scene['duration'] = int(face_rig_result['audio_duration'])
                        
                    except Exception as e:
                        safe_print(f"  ⚠️  Failed to generate face_rig for scene {scene['scene_number']}: {e}")
                        # Continue without face_rig for this scene
                
                self.current_project["steps"]["face_rig_videos"] = face_rig_videos
                self.current_project["steps"]["face_rig_audio_files"] = face_rig_audio_files
                self.current_project["steps"]["scene_audio_durations"] = scene_audio_durations
                
                if progress_callback:
                    progress_callback(3.5, 7, "✅ Face_rig videos generated", f"{len(face_rig_videos)} character animations created")
            
            # Step 4: Generate video clips
            if progress_callback:
                progress_callback(4, 7, "🎥 Generating video clips...", "Creating animated video clips for each scene")
            safe_print("\n[4/7] Video Clip Generation")
            safe_print("-" * 70)
            clip_paths = self.video_gen.generate_clips(scene_plan, storyboard_images=storyboard_images)
            self.current_project["steps"]["clips"] = clip_paths
            if progress_callback:
                progress_callback(4, 7, "✅ Video clips generated", f"{len(clip_paths)} video clips created")
            
            # Step 5: Generate voiceover (skip if face_rig already generated audio)
            if self.use_face_rig and face_rig_videos and face_rig_audio_files:
                # Use face_rig audio instead - combine the audio files
                safe_print("\n[5/7] Voiceover Generation (using face_rig audio)")
                safe_print("-" * 70)
                safe_print("  ⏭️  Skipping generation - using audio from face_rig character animations")
                safe_print(f"  🎵 Combining {len(face_rig_audio_files)} audio files...")
                audio_path = self._combine_audio_files(face_rig_audio_files)
                self.current_project["steps"]["audio"] = audio_path
                safe_print(f"  ✅ Combined audio: {Path(audio_path).name}")
                if progress_callback:
                    progress_callback(5, 7, "✅ Using face_rig audio", f"Combined {len(face_rig_audio_files)} audio files")
            else:
                if progress_callback:
                    progress_callback(5, 7, "🎙️ Generating voiceover...", "Creating audio narration from script")
                safe_print("\n[5/7] Voiceover Generation")
                safe_print("-" * 70)
                audio_path = self.audio_gen.generate(script_data)
                self.current_project["steps"]["audio"] = audio_path
                if progress_callback:
                    progress_callback(5, 7, "✅ Voiceover generated", f"Audio file created: {Path(audio_path).name}")
            
            # Step 6: Assemble final video
            if progress_callback:
                progress_callback(6, 7, "🎬 Assembling final video...", "Combining video clips with audio and face_rig overlay")
            safe_print("\n[6/7] Final Assembly")
            safe_print("-" * 70)
            
            if not output_filename:
                safe_title = "".join(c for c in script_data['title'] if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.replace(' ', '_')[:50]
                output_filename = f"{safe_title}_{timestamp}.mp4"
            
            output_path = OUTPUT_DIR / output_filename
            
            # Pass face_rig videos to assembler for PiP overlay
            final_video = self.assembler.assemble(
                clip_paths, 
                audio_path, 
                output_path,
                face_rig_videos=face_rig_videos if self.use_face_rig else None
            )
            self.current_project["steps"]["final_video"] = final_video
            if progress_callback:
                progress_callback(6, 7, "✅ Video complete!", f"Final video saved: {output_filename}")
            
            # Save project metadata
            self._save_metadata()
            
            # print summary
            self._print_summary(final_video)
            
            return {
                "success": True,
                "video_path": final_video,
                "script": script_data,
                "scenes": scene_plan,
                "project_data": self.current_project
            }
            
        except Exception as e:
            safe_print(f"\n❌ Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_data": self.current_project
            }
    
    def _save_metadata(self):
        """Save project metadata to JSON file"""
        metadata_path = OUTPUT_DIR / f"project_{self.current_project['timestamp']}.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_project, indent=2, fp=f, ensure_ascii=False)
        
        safe_print(f"\n💾 Metadata saved: {metadata_path.name}")
    
    def _combine_audio_files(self, audio_files):
        """
        Combine multiple audio files into a single file using FFmpeg
        
        Args:
            audio_files: List of audio file paths to combine
            
        Returns:
            str: Path to combined audio file
        """
        if not audio_files:
            raise ValueError("No audio files to combine")
        
        if len(audio_files) == 1:
            # Only one file, just return it
            return audio_files[0]
        
        # Create a list file for FFmpeg concat
        list_file = TEMP_DIR / "audio_concat_list.txt"
        combined_audio_path = TEMP_DIR / "combined_narration.wav"
        
        try:
            # Write list of audio files
            with open(list_file, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    # Escape single quotes in path
                    escaped_path = str(Path(audio_file)).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Use FFmpeg to concatenate audio files
            cmd = [
                self.assembler.ffmpeg_cmd,
                "-y",  # Overwrite output
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",  # Copy codec (no re-encoding)
                str(combined_audio_path)
            ]
            
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Clean up list file
            if list_file.exists():
                list_file.unlink()
            
            return str(combined_audio_path)
            
        except subprocess.CalledProcessError as e:
            safe_print(f"  ⚠️  FFmpeg concat failed, trying alternative method...")
            # Fallback: use filter_complex for concatenation
            return self._combine_audio_files_filter(audio_files, combined_audio_path)
        except Exception as e:
            safe_print(f"  ❌ Error combining audio files: {e}")
            raise
    
    def _combine_audio_files_filter(self, audio_files, output_path):
        """
        Combine audio files using FFmpeg filter_complex (alternative method)
        
        Args:
            audio_files: List of audio file paths
            output_path: Output path for combined audio
            
        Returns:
            str: Path to combined audio file
        """
        # Build FFmpeg command with filter_complex
        cmd = [self.assembler.ffmpeg_cmd, "-y"]
        
        # Add input files
        for audio_file in audio_files:
            cmd.extend(["-i", str(audio_file)])
        
        # Build filter_complex for concatenation
        filter_inputs = "".join([f"[{i}:a]" for i in range(len(audio_files))])
        filter_complex = f"{filter_inputs}concat=n={len(audio_files)}:v=0:a=1[outa]"
        
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outa]",
            str(output_path)
        ])
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        return str(output_path)
    
    def _print_summary(self, video_path):
        """print pipeline completion summary"""
        safe_print("\n" + "=" * 70)
        safe_print("✨ PIPELINE COMPLETE!")
        safe_print("=" * 70)
        safe_print(f"Title: {self.current_project['steps']['script']['title']}")
        safe_print(f"Scenes: {len(self.current_project['steps']['scenes']['scenes'])}")
        safe_print(f"Output: {video_path}")
        safe_print("=" * 70 + "\n")


if __name__ == "__main__":
    # Example usage
    pipeline = VideoPipeline(
        openai_api_key="your-key-here",  # Will use env var if not provided
        video_provider="replicate",
        tts_provider="elevenlabs"
    )
    
    result = pipeline.run("Explain how photosynthesis works in simple terms")
    
    if result["success"]:
        safe_print(f"✅ Video created: {result['video_path']}")
    else:
        safe_print(f"❌ Failed: {result['error']}")
