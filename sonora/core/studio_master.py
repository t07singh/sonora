
import os
import json
from sonora.core.orchestrator import SonoraOrchestrator

class SonoraBatchExecutor:
    """
    Handles batch processing of all segments for a project.
    """
    def __init__(self, project_name):
        self.project_name = project_name
        self.data_dir = os.path.join("sonora/data", project_name)
        
    def run_full_pipeline(self, video_path, translations):
        """
        Runs the end-to-end studio pipeline for all segments.
        """
        print(f"🎬 Starting Studio Master for project: {self.project_name}")
        orchestrator = SonoraOrchestrator(video_path)
        
        # 1. Transcription (if not already done)
        raw_data = orchestrator.run_transcription()
        
        # 2. Grouping
        from sonora.core.orchestrator import group_words_by_pause
        segments = group_words_by_pause(raw_data)
        
        # 3. Process each segment through Studio Pipeline (Emotion + Synth + Refine + Match)
        mastered_clips = []
        for i, segment in enumerate(segments):
            if i >= len(translations): break
            
            print(f"Processing Segment {i+1}/{len(segments)}...")
            clip_path, emotion_stats = orchestrator.process_studio_pipeline(
                segment, 
                translations[i]
            )
            mastered_clips.append({
                'path': clip_path,
                'start': segment[0]['start'],
                'end': segment[-1]['end'],
                'emotion': emotion_stats['token']
            })
            
        # 4. Final Assembly (Find stems in project dir if they exist)
        stems = {
            'music': os.path.join(self.data_dir, "music.wav"),
            'vocals': os.path.join(self.data_dir, "vocals.wav"),
            'sfx': os.path.join(self.data_dir, "sfx.wav")
        }
        # Only pass stems that actually exist
        available_stems = {k: v for k, v in stems.items() if os.path.exists(v)}
        
        output_path = os.path.join(self.data_dir, "master_output.mp4")
        final_video = orchestrator.assemble_final_dub(
            segments, 
            translations, 
            output_path=output_path,
            mix_mode="Smart", # Default to Smart for Studio Master
            stems=available_stems
        )
        
        # Statistics for the UI
        final_stats = {
            "token": mastered_clips[0]['emotion'] if mastered_clips else "neutral",
            "segments_processed": len(mastered_clips)
        }
        
        return final_video, final_stats
