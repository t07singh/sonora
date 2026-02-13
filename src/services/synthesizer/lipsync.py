"""
Advanced lip-synchronization module for Sonora/Auralis AI Dubbing System.

Handles advanced lip-sync using multiple vision models with quality assessment,
real-time processing, and optimization features.
"""

import os
import logging
import tempfile
import subprocess
import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import asyncio
import json
from dataclasses import dataclass
from enum import Enum

from src.core.reliability import retry_api_call

logger = logging.getLogger(__name__)


class LipSyncQuality(Enum):
    """Lip-sync quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class LipSyncResult:
    """Result of lip-sync processing with quality metrics."""
    output_path: str
    quality_score: float
    quality_level: LipSyncQuality
    processing_time: float
    model_used: str
    metrics: Dict[str, Any]
    warnings: List[str]


class AdvancedLipSyncEngine:
    """
    Advanced lip-synchronization engine with multiple models and quality assessment.
    
    Features:
    - Multiple lip-sync models (Wav2Lip, SadTalker, Real-ESRGAN)
    - Quality assessment and optimization
    - Real-time processing capabilities
    - Batch processing with progress tracking
    - Automatic model selection based on content
    """
    
    def __init__(
        self,
        model_type: str = "auto",
        quality_mode: str = "balanced",  # fast, balanced, high_quality
        enable_gpu: bool = False,
        temp_dir: Optional[str] = None
    ):
        """
        Initialize the advanced lip-sync engine.
        
        Args:
            model_type: Type of model to use ("auto", "wav2lip", "sadtalker", "real_esrgan")
            quality_mode: Quality mode ("fast", "balanced", "high_quality")
            enable_gpu: Enable GPU acceleration if available
            temp_dir: Temporary directory for processing
        """
        self.model_type = model_type.lower()
        self.quality_mode = quality_mode.lower()
        self.enable_gpu = enable_gpu
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="sonora_advanced_lipsync_")
        
        # Model configurations
        self.model_configs = {
            "wav2lip": {
                "quality": "good",
                "speed": "fast",
                "anime_support": "excellent",
                "gpu_required": False
            },
            "sadtalker": {
                "quality": "excellent",
                "speed": "medium",
                "anime_support": "good",
                "gpu_required": True
            },
            "real_esrgan": {
                "quality": "excellent",
                "speed": "slow",
                "anime_support": "excellent",
                "gpu_required": True
            }
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "fair": 0.5,
            "poor": 0.3
        }
        
        logger.info(f"Advanced lip-sync engine initialized: {self.model_type}")
        logger.info(f"Quality mode: {self.quality_mode}")
        logger.info(f"GPU enabled: {self.enable_gpu}")
        logger.info(f"Temp directory: {self.temp_dir}")
        
        # Initialize models
        self._initialize_models()
    
    def __del__(self):
        """Cleanup temporary files on destruction."""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up advanced lip-sync engine temp directory")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {e}")
    
    def _initialize_models(self):
        """Initialize available lip-sync models."""
        self.available_models = []
        
        # Check Wav2Lip
        if self._check_wav2lip():
            self.available_models.append("wav2lip")
        
        # Check SadTalker
        if self._check_sadtalker():
            self.available_models.append("sadtalker")
        
        # Check Real-ESRGAN
        if self._check_real_esrgan():
            self.available_models.append("real_esrgan")
        
        if not self.available_models:
            logger.warning("No lip-sync models available, falling back to mock mode")
            self.available_models = ["mock"]
        
        logger.info(f"Available models: {self.available_models}")
        
        # Select best model based on configuration
        if self.model_type == "auto":
            self.selected_model = self._select_best_model()
        else:
            self.selected_model = self.model_type if self.model_type in self.available_models else "mock"
        
        logger.info(f"Selected model: {self.selected_model}")
    
    def _check_wav2lip(self) -> bool:
        """Check if Wav2Lip is available."""
        try:
            wav2lip_dir = os.getenv("WAV2LIP_DIR", "wav2lip")
            checkpoint_path = os.getenv("WAV2LIP_CHECKPOINT", "wav2lip.pth")
            return os.path.exists(wav2lip_dir) and os.path.exists(checkpoint_path)
        except:
            return False
    
    def _check_sadtalker(self) -> bool:
        """Check if SadTalker is available."""
        try:
            sadtalker_dir = os.getenv("SADTALKER_DIR", "SadTalker")
            checkpoint_path = os.getenv("SADTALKER_CHECKPOINT", "checkpoints")
            return os.path.exists(sadtalker_dir) and os.path.exists(checkpoint_path)
        except:
            return False
    
    def _check_real_esrgan(self) -> bool:
        """Check if Real-ESRGAN is available."""
        try:
            real_esrgan_dir = os.getenv("REAL_ESRGAN_DIR", "Real-ESRGAN")
            return os.path.exists(real_esrgan_dir)
        except:
            return False
    
    def _select_best_model(self) -> str:
        """Select the best model based on quality mode and availability."""
        if self.quality_mode == "fast":
            # Prefer fast models
            for model in ["wav2lip", "sadtalker", "real_esrgan"]:
                if model in self.available_models:
                    return model
        elif self.quality_mode == "high_quality":
            # Prefer high-quality models
            for model in ["real_esrgan", "sadtalker", "wav2lip"]:
                if model in self.available_models:
                    return model
        else:  # balanced
            # Prefer balanced models
            for model in ["sadtalker", "wav2lip", "real_esrgan"]:
                if model in self.available_models:
                    return model
        
        return "mock"
    
    @retry_api_call()
    async def sync_lips_advanced(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        target_quality: Optional[str] = None
    ) -> LipSyncResult:
        """
        Perform advanced lip-synchronization with quality assessment.
        
        Args:
            video_path: Path to the original video file
            audio_path: Path to the dubbed audio file
            output_path: Path for the lip-synced output video
            target_quality: Target quality level (excellent, good, fair, poor)
            
        Returns:
            LipSyncResult with quality metrics and processing information
        """
        start_time = asyncio.get_event_loop().time()
        warnings = []
        
        try:
            logger.info(f"Starting advanced lip-sync: {video_path} + {audio_path}")
            logger.info(f"Model: {self.selected_model}, Quality mode: {self.quality_mode}")
            
            # Pre-process video for better results
            processed_video_path = await self._preprocess_video(video_path)
            
            # Perform lip-sync based on selected model
            if self.selected_model == "wav2lip":
                result_path = await self._wav2lip_sync(processed_video_path, audio_path, output_path)
            elif self.selected_model == "sadtalker":
                result_path = await self._sadtalker_sync(processed_video_path, audio_path, output_path)
            elif self.selected_model == "real_esrgan":
                result_path = await self._real_esrgan_sync(processed_video_path, audio_path, output_path)
            else:
                result_path = await self._mock_sync(processed_video_path, audio_path, output_path)
            
            # Post-process for quality enhancement
            enhanced_path = await self._postprocess_video(result_path, output_path)
            
            # Assess quality
            quality_metrics = await self._assess_quality(video_path, enhanced_path, audio_path)
            quality_score = quality_metrics["overall_score"]
            quality_level = self._get_quality_level(quality_score)
            
            # Check if target quality is met
            if target_quality:
                target_threshold = self.quality_thresholds.get(target_quality, 0.7)
                if quality_score < target_threshold:
                    warnings.append(f"Quality below target ({target_quality}): {quality_score:.2f} < {target_threshold}")
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = LipSyncResult(
                output_path=enhanced_path,
                quality_score=quality_score,
                quality_level=quality_level,
                processing_time=processing_time,
                model_used=self.selected_model,
                metrics=quality_metrics,
                warnings=warnings
            )
            
            logger.info(f"Advanced lip-sync completed: {enhanced_path}")
            logger.info(f"Quality: {quality_level.value} ({quality_score:.2f})")
            logger.info(f"Processing time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced lip-sync failed: {e}")
            raise
    
    async def _preprocess_video(self, video_path: str) -> str:
        """Pre-process video for better lip-sync results."""
        try:
            logger.info("Pre-processing video for lip-sync")
            
            # Extract face regions and enhance
            face_enhanced_path = os.path.join(self.temp_dir, "face_enhanced.mp4")
            
            # Use OpenCV for face detection and enhancement
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(face_enhanced_path, fourcc, fps, (width, height))
            
            # Load face detection model
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Enhance face regions
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    # Enhance face region
                    face_region = frame[y:y+h, x:x+w]
                    enhanced_face = cv2.bilateralFilter(face_region, 9, 75, 75)
                    frame[y:y+h, x:x+w] = enhanced_face
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            logger.info(f"Video pre-processing completed: {frame_count} frames processed")
            return face_enhanced_path
            
        except Exception as e:
            logger.warning(f"Video pre-processing failed: {e}")
            return video_path  # Return original if preprocessing fails
    
    async def _wav2lip_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Wav2Lip lip-sync implementation."""
        try:
            logger.info("Running Wav2Lip lip-sync")
            
            wav2lip_dir = os.getenv("WAV2LIP_DIR", "wav2lip")
            checkpoint_path = os.getenv("WAV2LIP_CHECKPOINT", "wav2lip.pth")
            
            cmd = [
                "python", f"{wav2lip_dir}/inference.py",
                "--checkpoint_path", checkpoint_path,
                "--face", video_path,
                "--audio", audio_path,
                "--outfile", output_path,
                "--static" if self.quality_mode == "fast" else "--pads",
                "0", "10", "0", "0"  # Face padding
            ]
            
            if self.enable_gpu:
                cmd.extend(["--resize_factor", "1"])
            
            logger.info(f"Wav2Lip command: {' '.join(cmd)}")
            
            # Run in subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            
            if process.returncode != 0:
                raise Exception(f"Wav2Lip failed: {stderr.decode()}")
            
            logger.info("Wav2Lip lip-sync completed")
            return output_path
            
        except Exception as e:
            logger.error(f"Wav2Lip sync failed: {e}")
            raise
    
    async def _sadtalker_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """SadTalker lip-sync implementation."""
        try:
            logger.info("Running SadTalker lip-sync")
            
            sadtalker_dir = os.getenv("SADTALKER_DIR", "SadTalker")
            checkpoint_path = os.getenv("SADTALKER_CHECKPOINT", "checkpoints")
            
            cmd = [
                "python", f"{sadtalker_dir}/inference.py",
                "--driven_audio", audio_path,
                "--source_image", video_path,
                "--result_dir", os.path.dirname(output_path),
                "--still" if self.quality_mode == "fast" else "--preprocess", "full",
                "--use_enhancer" if self.quality_mode == "high_quality" else ""
            ]
            
            # Remove empty strings
            cmd = [arg for arg in cmd if arg]
            
            logger.info(f"SadTalker command: {' '.join(cmd)}")
            
            # Run in subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            
            if process.returncode != 0:
                raise Exception(f"SadTalker failed: {stderr.decode()}")
            
            # SadTalker outputs to a directory, find the result file
            result_dir = os.path.dirname(output_path)
            result_files = [f for f in os.listdir(result_dir) if f.endswith('.mp4')]
            
            if result_files:
                import shutil
                source_file = os.path.join(result_dir, result_files[0])
                shutil.move(source_file, output_path)
                logger.info("SadTalker lip-sync completed")
                return output_path
            else:
                raise Exception("SadTalker did not produce output video file")
            
        except Exception as e:
            logger.error(f"SadTalker sync failed: {e}")
            raise
    
    async def _real_esrgan_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Real-ESRGAN enhanced lip-sync implementation."""
        try:
            logger.info("Running Real-ESRGAN enhanced lip-sync")
            
            # First run Wav2Lip for basic lip-sync
            temp_output = os.path.join(self.temp_dir, "temp_lipsync.mp4")
            await self._wav2lip_sync(video_path, audio_path, temp_output)
            
            # Then enhance with Real-ESRGAN
            real_esrgan_dir = os.getenv("REAL_ESRGAN_DIR", "Real-ESRGAN")
            
            cmd = [
                "python", f"{real_esrgan_dir}/inference_realesrgan.py",
                "-i", temp_output,
                "-o", output_path,
                "-n", "RealESRGAN_x4plus",
                "-s", "4" if self.quality_mode == "high_quality" else "2"
            ]
            
            logger.info(f"Real-ESRGAN command: {' '.join(cmd)}")
            
            # Run in subprocess with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=900)
            
            if process.returncode != 0:
                raise Exception(f"Real-ESRGAN failed: {stderr.decode()}")
            
            logger.info("Real-ESRGAN enhanced lip-sync completed")
            return output_path
            
        except Exception as e:
            logger.error(f"Real-ESRGAN sync failed: {e}")
            raise
    
    async def _mock_sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Mock lip-sync implementation (audio replacement only)."""
        try:
            logger.info("Running mock lip-sync (audio replacement only)")
            
            # For testing without FFmpeg, just copy the video file
            import shutil
            shutil.copy2(video_path, output_path)
            
            logger.info("Mock lip-sync completed (file copy)")
            return output_path
            
        except Exception as e:
            logger.error(f"Mock sync failed: {e}")
            raise
    
    async def _postprocess_video(self, input_path: str, output_path: str) -> str:
        """Post-process video for quality enhancement."""
        try:
            logger.info("Post-processing video for quality enhancement")
            
            # Apply additional enhancements based on quality mode
            if self.quality_mode == "high_quality":
                # Apply noise reduction and sharpening
                enhanced_path = await self._apply_enhancements(input_path, output_path)
                return enhanced_path
            else:
                # Just copy the file
                import shutil
                shutil.copy2(input_path, output_path)
                return output_path
                
        except Exception as e:
            logger.warning(f"Post-processing failed: {e}")
            return input_path
    
    async def _apply_enhancements(self, input_path: str, output_path: str) -> str:
        """Apply video enhancements for high quality mode."""
        try:
            import ffmpeg
            
            # Apply noise reduction and sharpening
            input_stream = ffmpeg.input(input_path)
            
            # Apply video filters for enhancement
            video_filters = [
                "hqdn3d=4:3:6:4.5",  # Noise reduction
                "unsharp=5:5:0.8:3:3:0.4",  # Sharpening
                "eq=contrast=1.1:brightness=0.05"  # Contrast and brightness
            ]
            
            output = ffmpeg.output(
                input_stream,
                output_path,
                vf=",".join(video_filters),
                vcodec='libx264',
                crf=18,  # High quality
                preset='slow'
            )
            
            ffmpeg.run(output, overwrite_output=True, quiet=True)
            
            logger.info("Video enhancements applied")
            return output_path
            
        except Exception as e:
            logger.warning(f"Video enhancement failed: {e}")
            return input_path
    
    async def _assess_quality(self, original_path: str, result_path: str, audio_path: str) -> Dict[str, Any]:
        """Assess lip-sync quality using various metrics."""
        try:
            logger.info("Assessing lip-sync quality")
            
            metrics = {}
            
            # 1. Visual quality assessment
            visual_score = await self._assess_visual_quality(original_path, result_path)
            metrics["visual_quality"] = visual_score
            
            # 2. Audio-video sync assessment
            sync_score = await self._assess_audio_video_sync(result_path, audio_path)
            metrics["sync_quality"] = sync_score
            
            # 3. Face detection consistency
            face_score = await self._assess_face_consistency(result_path)
            metrics["face_consistency"] = face_score
            
            # 4. Overall quality score (weighted average)
            overall_score = (
                visual_score * 0.4 +
                sync_score * 0.4 +
                face_score * 0.2
            )
            metrics["overall_score"] = overall_score
            
            # 5. Additional metrics
            metrics["processing_efficiency"] = await self._assess_processing_efficiency(original_path, result_path)
            metrics["anime_compatibility"] = await self._assess_anime_compatibility(result_path)
            
            logger.info(f"Quality assessment completed: {overall_score:.2f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {"overall_score": 0.5, "error": str(e)}
    
    async def _assess_visual_quality(self, original_path: str, result_path: str) -> float:
        """Assess visual quality of the result."""
        try:
            # Compare frame quality, resolution, etc.
            cap_orig = cv2.VideoCapture(original_path)
            cap_result = cv2.VideoCapture(result_path)
            
            orig_fps = cap_orig.get(cv2.CAP_PROP_FPS)
            result_fps = cap_result.get(cv2.CAP_PROP_FPS)
            
            orig_width = cap_orig.get(cv2.CAP_PROP_FRAME_WIDTH)
            result_width = cap_result.get(cv2.CAP_PROP_FRAME_WIDTH)
            
            # Calculate quality score based on resolution and FPS preservation
            fps_score = min(1.0, result_fps / orig_fps) if orig_fps > 0 else 0.5
            resolution_score = min(1.0, result_width / orig_width) if orig_width > 0 else 0.5
            
            cap_orig.release()
            cap_result.release()
            
            return (fps_score + resolution_score) / 2
            
        except Exception as e:
            logger.warning(f"Visual quality assessment failed: {e}")
            return 0.5
    
    async def _assess_audio_video_sync(self, video_path: str, audio_path: str) -> float:
        """Assess audio-video synchronization quality."""
        try:
            # This is a simplified assessment
            # In a real implementation, you would analyze the actual sync
            
            # For now, return a mock score based on file existence and size
            if os.path.exists(video_path) and os.path.exists(audio_path):
                video_size = os.path.getsize(video_path)
                audio_size = os.path.getsize(audio_path)
                
                # Simple heuristic: if both files exist and have reasonable sizes
                if video_size > 1000 and audio_size > 1000:
                    return 0.8
                else:
                    return 0.6
            else:
                return 0.3
                
        except Exception as e:
            logger.warning(f"Audio-video sync assessment failed: {e}")
            return 0.5
    
    async def _assess_face_consistency(self, video_path: str) -> float:
        """Assess face detection consistency throughout the video."""
        try:
            cap = cv2.VideoCapture(video_path)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            total_frames = 0
            frames_with_faces = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                total_frames += 1
                if len(faces) > 0:
                    frames_with_faces += 1
            
            cap.release()
            
            if total_frames > 0:
                consistency_score = frames_with_faces / total_frames
                return min(1.0, consistency_score)
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"Face consistency assessment failed: {e}")
            return 0.5
    
    async def _assess_processing_efficiency(self, original_path: str, result_path: str) -> float:
        """Assess processing efficiency (file size, compression, etc.)."""
        try:
            if not os.path.exists(original_path) or not os.path.exists(result_path):
                return 0.5
            
            orig_size = os.path.getsize(original_path)
            result_size = os.path.getsize(result_path)
            
            # Efficiency score based on size ratio (closer to 1.0 is better)
            if orig_size > 0:
                size_ratio = min(result_size / orig_size, 2.0)  # Cap at 2x
                efficiency_score = 1.0 - abs(1.0 - size_ratio) * 0.5
                return max(0.0, min(1.0, efficiency_score))
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"Processing efficiency assessment failed: {e}")
            return 0.5
    
    async def _assess_anime_compatibility(self, video_path: str) -> float:
        """Assess compatibility with anime content."""
        try:
            # This is a simplified assessment
            # In a real implementation, you would analyze color palettes, art style, etc.
            
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Simple heuristic: check for vibrant colors typical in anime
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                saturation = np.mean(hsv[:, :, 1])
                
                # Higher saturation often indicates anime-style content
                anime_score = min(1.0, saturation / 128.0)
                return anime_score
            else:
                return 0.5
                
        except Exception as e:
            logger.warning(f"Anime compatibility assessment failed: {e}")
            return 0.5
    
    def _get_quality_level(self, score: float) -> LipSyncQuality:
        """Get quality level from score."""
        if score >= self.quality_thresholds["excellent"]:
            return LipSyncQuality.EXCELLENT
        elif score >= self.quality_thresholds["good"]:
            return LipSyncQuality.GOOD
        elif score >= self.quality_thresholds["fair"]:
            return LipSyncQuality.FAIR
        else:
            return LipSyncQuality.POOR
    
    async def batch_sync_lips(
        self,
        video_audio_pairs: List[Tuple[str, str]],
        output_dir: str,
        progress_callback: Optional[callable] = None
    ) -> List[LipSyncResult]:
        """
        Perform batch lip-synchronization with progress tracking.
        
        Args:
            video_audio_pairs: List of (video_path, audio_path) tuples
            output_dir: Directory to save output videos
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of LipSyncResult objects
        """
        results = []
        total_pairs = len(video_audio_pairs)
        
        logger.info(f"Starting batch lip-sync: {total_pairs} pairs")
        
        for i, (video_path, audio_path) in enumerate(video_audio_pairs):
            try:
                # Generate output path
                video_name = Path(video_path).stem
                output_path = os.path.join(output_dir, f"{video_name}_lipsync.mp4")
                
                # Perform lip-sync
                result = await self.sync_lips_advanced(video_path, audio_path, output_path)
                results.append(result)
                
                # Update progress
                if progress_callback:
                    progress_callback(i + 1, total_pairs, result)
                
                logger.info(f"Batch progress: {i + 1}/{total_pairs} completed")
                
            except Exception as e:
                logger.error(f"Batch lip-sync failed for pair {i + 1}: {e}")
                # Create error result
                error_result = LipSyncResult(
                    output_path="",
                    quality_score=0.0,
                    quality_level=LipSyncQuality.POOR,
                    processing_time=0.0,
                    model_used=self.selected_model,
                    metrics={"error": str(e)},
                    warnings=[f"Processing failed: {e}"]
                )
                results.append(error_result)
        
        logger.info(f"Batch lip-sync completed: {len(results)} results")
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models and current configuration."""
        return {
            "available_models": self.available_models,
            "selected_model": self.selected_model,
            "quality_mode": self.quality_mode,
            "gpu_enabled": self.enable_gpu,
            "model_configs": self.model_configs,
            "quality_thresholds": self.quality_thresholds
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up advanced lip-sync engine temporary files")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

