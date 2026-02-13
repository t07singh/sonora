"""
Audio Bus System for Sonora Voice & Sound Editing Core

This module provides a layered audio bus system for professional audio mixing
and routing. It enables studios to manage multiple audio stems with individual
controls for volume, effects, and routing.

Key Features:
- Layered audio bus system (voice_bus, music_bus, sfx_bus, env_bus)
- Individual volume and effect controls per bus
- Real-time audio routing and mixing
- Professional mixing console interface
- Integration with editing workflow
"""

import os
import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from pathlib import Path
import threading
import queue
import time
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class BusType(Enum):
    """Types of audio buses."""
    VOICE = "voice_bus"
    MUSIC = "music_bus"
    SFX = "sfx_bus"
    ENVIRONMENT = "env_bus"
    MASTER = "master_bus"


class EffectType(Enum):
    """Types of audio effects."""
    EQ = "equalizer"
    COMPRESSOR = "compressor"
    REVERB = "reverb"
    DELAY = "delay"
    FILTER = "filter"
    GAIN = "gain"


@dataclass
class EffectParameter:
    """Audio effect parameter."""
    name: str
    value: float
    min_value: float
    max_value: float
    unit: str = ""
    description: str = ""


@dataclass
class AudioEffect:
    """Audio effect configuration."""
    effect_type: EffectType
    enabled: bool
    parameters: Dict[str, EffectParameter]
    order: int = 0


@dataclass
class BusConfiguration:
    """Audio bus configuration."""
    bus_type: BusType
    volume: float = 1.0
    pan: float = 0.0  # -1.0 to 1.0
    mute: bool = False
    solo: bool = False
    effects: List[AudioEffect] = field(default_factory=list)
    routing: List[BusType] = field(default_factory=list)


@dataclass
class AudioBus:
    """Audio bus instance."""
    config: BusConfiguration
    audio_data: Optional[np.ndarray] = None
    sample_rate: int = 44100
    is_active: bool = False
    last_update: float = 0.0


class AudioBusSystem:
    """
    Professional audio bus system for Sonora Voice & Sound Editing Core.
    
    Provides a layered audio bus system with individual controls for volume,
    effects, and routing, enabling studio-grade audio mixing and processing.
    """
    
    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 1024
    ):
        """
        Initialize audio bus system.
        
        Args:
            sample_rate: Target sample rate
            buffer_size: Audio buffer size
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # Initialize buses
        self.buses: Dict[BusType, AudioBus] = {}
        self._initialize_buses()
        
        # Audio processing
        self.is_processing = False
        self.processing_thread = None
        self.audio_queue = queue.Queue()
        
        # Callbacks
        self.on_audio_processed: Optional[Callable] = None
        self.on_bus_updated: Optional[Callable] = None
        
        logger.info(f"Initialized AudioBusSystem with {len(self.buses)} buses")
    
    def _initialize_buses(self) -> None:
        """Initialize all audio buses."""
        bus_types = [BusType.VOICE, BusType.MUSIC, BusType.SFX, BusType.ENVIRONMENT, BusType.MASTER]
        
        for bus_type in bus_types:
            config = BusConfiguration(bus_type=bus_type)
            
            # Set default routing
            if bus_type != BusType.MASTER:
                config.routing = [BusType.MASTER]
            
            self.buses[bus_type] = AudioBus(
                config=config,
                sample_rate=self.sample_rate
            )
    
    def load_audio_to_bus(
        self,
        bus_type: BusType,
        audio_data: np.ndarray,
        sample_rate: int = None
    ) -> bool:
        """
        Load audio data to a specific bus.
        
        Args:
            bus_type: Target bus type
            audio_data: Audio data to load
            sample_rate: Sample rate (defaults to instance setting)
            
        Returns:
            True if successful
        """
        try:
            sr = sample_rate or self.sample_rate
            
            # Resample if necessary
            if sr != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            
            # Ensure mono/stereo consistency
            if len(audio_data.shape) == 1:
                audio_data = np.stack([audio_data, audio_data])  # Convert to stereo
            elif len(audio_data.shape) == 2 and audio_data.shape[0] > audio_data.shape[1]:
                audio_data = audio_data.T  # Transpose if needed
            
            # Load audio to bus
            self.buses[bus_type].audio_data = audio_data
            self.buses[bus_type].is_active = True
            self.buses[bus_type].last_update = time.time()
            
            logger.info(f"Loaded audio to {bus_type.value}: {len(audio_data)} samples")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "audio_loaded")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load audio to {bus_type.value}: {e}")
            return False
    
    def set_bus_volume(self, bus_type: BusType, volume: float) -> None:
        """Set bus volume."""
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp to 0-1
            self.buses[bus_type].config.volume = volume
            
            logger.info(f"Set {bus_type.value} volume to {volume:.2f}")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "volume_changed")
                
        except Exception as e:
            logger.error(f"Failed to set volume for {bus_type.value}: {e}")
    
    def set_bus_pan(self, bus_type: BusType, pan: float) -> None:
        """Set bus pan position."""
        try:
            pan = max(-1.0, min(1.0, pan))  # Clamp to -1 to 1
            self.buses[bus_type].config.pan = pan
            
            logger.info(f"Set {bus_type.value} pan to {pan:.2f}")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "pan_changed")
                
        except Exception as e:
            logger.error(f"Failed to set pan for {bus_type.value}: {e}")
    
    def mute_bus(self, bus_type: BusType, mute: bool) -> None:
        """Mute/unmute bus."""
        try:
            self.buses[bus_type].config.mute = mute
            
            logger.info(f"{'Muted' if mute else 'Unmuted'} {bus_type.value}")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "mute_changed")
                
        except Exception as e:
            logger.error(f"Failed to mute/unmute {bus_type.value}: {e}")
    
    def solo_bus(self, bus_type: BusType, solo: bool) -> None:
        """Solo/unsolo bus."""
        try:
            self.buses[bus_type].config.solo = solo
            
            # If soloing, mute all other buses
            if solo:
                for other_bus_type in self.buses:
                    if other_bus_type != bus_type and other_bus_type != BusType.MASTER:
                        self.buses[other_bus_type].config.mute = True
            
            logger.info(f"{'Soloed' if solo else 'Unsoloed'} {bus_type.value}")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "solo_changed")
                
        except Exception as e:
            logger.error(f"Failed to solo/unsolo {bus_type.value}: {e}")
    
    def add_effect(
        self,
        bus_type: BusType,
        effect: AudioEffect
    ) -> bool:
        """
        Add effect to bus.
        
        Args:
            bus_type: Target bus type
            effect: Effect to add
            
        Returns:
            True if successful
        """
        try:
            # Set effect order
            effect.order = len(self.buses[bus_type].config.effects)
            
            # Add effect
            self.buses[bus_type].config.effects.append(effect)
            
            logger.info(f"Added {effect.effect_type.value} effect to {bus_type.value}")
            
            # Notify callback
            if self.on_bus_updated:
                self.on_bus_updated(bus_type, "effect_added")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add effect to {bus_type.value}: {e}")
            return False
    
    def remove_effect(
        self,
        bus_type: BusType,
        effect_index: int
    ) -> bool:
        """
        Remove effect from bus.
        
        Args:
            bus_type: Target bus type
            effect_index: Index of effect to remove
            
        Returns:
            True if successful
        """
        try:
            if 0 <= effect_index < len(self.buses[bus_type].config.effects):
                removed_effect = self.buses[bus_type].config.effects.pop(effect_index)
                
                # Reorder remaining effects
                for i, effect in enumerate(self.buses[bus_type].config.effects):
                    effect.order = i
                
                logger.info(f"Removed {removed_effect.effect_type.value} effect from {bus_type.value}")
                
                # Notify callback
                if self.on_bus_updated:
                    self.on_bus_updated(bus_type, "effect_removed")
                
                return True
            else:
                logger.warning(f"Invalid effect index {effect_index} for {bus_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove effect from {bus_type.value}: {e}")
            return False
    
    def update_effect_parameter(
        self,
        bus_type: BusType,
        effect_index: int,
        parameter_name: str,
        value: float
    ) -> bool:
        """
        Update effect parameter.
        
        Args:
            bus_type: Target bus type
            effect_index: Index of effect
            parameter_name: Parameter name
            value: New parameter value
            
        Returns:
            True if successful
        """
        try:
            if 0 <= effect_index < len(self.buses[bus_type].config.effects):
                effect = self.buses[bus_type].config.effects[effect_index]
                
                if parameter_name in effect.parameters:
                    param = effect.parameters[parameter_name]
                    param.value = max(param.min_value, min(param.max_value, value))
                    
                    logger.info(f"Updated {parameter_name} to {param.value} for {bus_type.value}")
                    
                    # Notify callback
                    if self.on_bus_updated:
                        self.on_bus_updated(bus_type, "effect_parameter_changed")
                    
                    return True
                else:
                    logger.warning(f"Parameter {parameter_name} not found in effect")
                    return False
            else:
                logger.warning(f"Invalid effect index {effect_index} for {bus_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update effect parameter: {e}")
            return False
    
    def process_audio(self) -> np.ndarray:
        """
        Process all buses and return mixed audio.
        
        Returns:
            Mixed audio data
        """
        try:
            # Get active buses
            active_buses = [
                bus for bus in self.buses.values()
                if bus.is_active and not bus.config.mute
            ]
            
            if not active_buses:
                # Return silence
                return np.zeros((2, self.buffer_size))
            
            # Process each bus
            processed_buses = []
            for bus in active_buses:
                if bus.audio_data is not None:
                    processed_audio = self._process_bus_audio(bus)
                    processed_buses.append(processed_audio)
            
            if not processed_buses:
                return np.zeros((2, self.buffer_size))
            
            # Mix all processed buses
            mixed_audio = self._mix_buses(processed_buses)
            
            # Apply master bus processing
            master_bus = self.buses[BusType.MASTER]
            if master_bus.config.effects:
                mixed_audio = self._process_bus_audio(master_bus, mixed_audio)
            
            return mixed_audio
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return np.zeros((2, self.buffer_size))
    
    def _process_bus_audio(self, bus: AudioBus, audio_data: np.ndarray = None) -> np.ndarray:
        """Process audio for a specific bus."""
        try:
            if audio_data is None:
                audio_data = bus.audio_data
            
            if audio_data is None:
                return np.zeros((2, self.buffer_size))
            
            processed_audio = audio_data.copy()
            
            # Apply effects
            for effect in bus.config.effects:
                if effect.enabled:
                    processed_audio = self._apply_effect(processed_audio, effect)
            
            # Apply volume
            processed_audio = processed_audio * bus.config.volume
            
            # Apply pan
            if bus.config.pan != 0.0:
                processed_audio = self._apply_pan(processed_audio, bus.config.pan)
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Bus audio processing failed: {e}")
            return audio_data if audio_data is not None else np.zeros((2, self.buffer_size))
    
    def _apply_effect(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply audio effect."""
        try:
            if effect.effect_type == EffectType.EQ:
                return self._apply_eq(audio_data, effect)
            elif effect.effect_type == EffectType.COMPRESSOR:
                return self._apply_compressor(audio_data, effect)
            elif effect.effect_type == EffectType.REVERB:
                return self._apply_reverb(audio_data, effect)
            elif effect.effect_type == EffectType.DELAY:
                return self._apply_delay(audio_data, effect)
            elif effect.effect_type == EffectType.FILTER:
                return self._apply_filter(audio_data, effect)
            elif effect.effect_type == EffectType.GAIN:
                return self._apply_gain(audio_data, effect)
            else:
                return audio_data
                
        except Exception as e:
            logger.warning(f"Effect application failed: {e}")
            return audio_data
    
    def _apply_eq(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply equalizer effect."""
        try:
            # Simple EQ implementation
            low_gain = effect.parameters.get("low_gain", EffectParameter("low_gain", 0.0, -12.0, 12.0)).value
            mid_gain = effect.parameters.get("mid_gain", EffectParameter("mid_gain", 0.0, -12.0, 12.0)).value
            high_gain = effect.parameters.get("high_gain", EffectParameter("high_gain", 0.0, -12.0, 12.0)).value
            
            # Apply frequency filtering
            # This is a simplified implementation
            processed_audio = audio_data.copy()
            
            # Low frequency boost/cut
            if low_gain != 0.0:
                sos = librosa.filters.butter(2, 1000, btype='low', fs=self.sample_rate, output='sos')
                low_filtered = librosa.filters.sosfilt(sos, processed_audio)
                processed_audio = processed_audio + low_filtered * (low_gain / 12.0)
            
            # High frequency boost/cut
            if high_gain != 0.0:
                sos = librosa.filters.butter(2, 4000, btype='high', fs=self.sample_rate, output='sos')
                high_filtered = librosa.filters.sosfilt(sos, processed_audio)
                processed_audio = processed_audio + high_filtered * (high_gain / 12.0)
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"EQ application failed: {e}")
            return audio_data
    
    def _apply_compressor(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply compressor effect."""
        try:
            # Simple compressor implementation
            threshold = effect.parameters.get("threshold", EffectParameter("threshold", -12.0, -60.0, 0.0)).value
            ratio = effect.parameters.get("ratio", EffectParameter("ratio", 4.0, 1.0, 20.0)).value
            
            # Convert to dB
            threshold_linear = 10 ** (threshold / 20)
            
            # Apply compression
            processed_audio = audio_data.copy()
            for i in range(len(processed_audio)):
                if len(processed_audio.shape) > 1:
                    for ch in range(processed_audio.shape[0]):
                        if abs(processed_audio[ch, i]) > threshold_linear:
                            processed_audio[ch, i] = np.sign(processed_audio[ch, i]) * (
                                threshold_linear + (abs(processed_audio[ch, i]) - threshold_linear) / ratio
                            )
                else:
                    if abs(processed_audio[i]) > threshold_linear:
                        processed_audio[i] = np.sign(processed_audio[i]) * (
                            threshold_linear + (abs(processed_audio[i]) - threshold_linear) / ratio
                        )
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Compressor application failed: {e}")
            return audio_data
    
    def _apply_reverb(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply reverb effect."""
        try:
            # Simple reverb implementation
            room_size = effect.parameters.get("room_size", EffectParameter("room_size", 0.5, 0.0, 1.0)).value
            damping = effect.parameters.get("damping", EffectParameter("damping", 0.5, 0.0, 1.0)).value
            
            # Apply simple reverb using convolution
            # This is a simplified implementation
            processed_audio = audio_data.copy()
            
            # Create simple reverb impulse response
            reverb_length = int(self.sample_rate * room_size * 0.5)
            impulse_response = np.random.randn(reverb_length) * (1 - damping)
            impulse_response = impulse_response * np.exp(-np.arange(reverb_length) / (reverb_length * 0.5))
            
            # Apply convolution
            if len(processed_audio.shape) > 1:
                for ch in range(processed_audio.shape[0]):
                    processed_audio[ch] = np.convolve(processed_audio[ch], impulse_response, mode='same')
            else:
                processed_audio = np.convolve(processed_audio, impulse_response, mode='same')
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Reverb application failed: {e}")
            return audio_data
    
    def _apply_delay(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply delay effect."""
        try:
            # Simple delay implementation
            delay_time = effect.parameters.get("delay_time", EffectParameter("delay_time", 0.25, 0.0, 2.0)).value
            feedback = effect.parameters.get("feedback", EffectParameter("feedback", 0.3, 0.0, 0.9)).value
            mix = effect.parameters.get("mix", EffectParameter("mix", 0.5, 0.0, 1.0)).value
            
            # Calculate delay samples
            delay_samples = int(delay_time * self.sample_rate)
            
            # Apply delay
            processed_audio = audio_data.copy()
            
            if len(processed_audio.shape) > 1:
                for ch in range(processed_audio.shape[0]):
                    delayed = np.zeros_like(processed_audio[ch])
                    delayed[delay_samples:] = processed_audio[ch][:-delay_samples]
                    processed_audio[ch] = processed_audio[ch] + delayed * feedback * mix
            else:
                delayed = np.zeros_like(processed_audio)
                delayed[delay_samples:] = processed_audio[:-delay_samples]
                processed_audio = processed_audio + delayed * feedback * mix
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Delay application failed: {e}")
            return audio_data
    
    def _apply_filter(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply filter effect."""
        try:
            # Simple filter implementation
            cutoff = effect.parameters.get("cutoff", EffectParameter("cutoff", 1000.0, 20.0, 20000.0)).value
            filter_type = effect.parameters.get("filter_type", EffectParameter("filter_type", 0.0, 0.0, 2.0)).value
            
            # Apply filter
            if filter_type == 0:  # Low-pass
                sos = librosa.filters.butter(2, cutoff, btype='low', fs=self.sample_rate, output='sos')
            elif filter_type == 1:  # High-pass
                sos = librosa.filters.butter(2, cutoff, btype='high', fs=self.sample_rate, output='sos')
            else:  # Band-pass
                sos = librosa.filters.butter(2, [cutoff * 0.5, cutoff * 1.5], btype='band', fs=self.sample_rate, output='sos')
            
            processed_audio = librosa.filters.sosfilt(sos, audio_data)
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Filter application failed: {e}")
            return audio_data
    
    def _apply_gain(self, audio_data: np.ndarray, effect: AudioEffect) -> np.ndarray:
        """Apply gain effect."""
        try:
            gain = effect.parameters.get("gain", EffectParameter("gain", 0.0, -12.0, 12.0)).value
            gain_linear = 10 ** (gain / 20)
            
            return audio_data * gain_linear
            
        except Exception as e:
            logger.warning(f"Gain application failed: {e}")
            return audio_data
    
    def _apply_pan(self, audio_data: np.ndarray, pan: float) -> np.ndarray:
        """Apply pan effect."""
        try:
            if len(audio_data.shape) == 1:
                # Convert mono to stereo
                audio_data = np.stack([audio_data, audio_data])
            
            if len(audio_data.shape) == 2 and audio_data.shape[0] == 2:
                # Apply pan
                left_gain = np.sqrt(0.5 * (1 - pan))
                right_gain = np.sqrt(0.5 * (1 + pan))
                
                audio_data[0] *= left_gain
                audio_data[1] *= right_gain
            
            return audio_data
            
        except Exception as e:
            logger.warning(f"Pan application failed: {e}")
            return audio_data
    
    def _mix_buses(self, processed_buses: List[np.ndarray]) -> np.ndarray:
        """Mix multiple processed buses."""
        try:
            if not processed_buses:
                return np.zeros((2, self.buffer_size))
            
            # Ensure all buses have the same shape
            target_shape = processed_buses[0].shape
            for i, bus_audio in enumerate(processed_buses):
                if bus_audio.shape != target_shape:
                    # Resize to match target shape
                    if len(bus_audio.shape) == 1:
                        bus_audio = np.stack([bus_audio, bus_audio])
                    elif len(bus_audio.shape) == 2 and bus_audio.shape[0] > bus_audio.shape[1]:
                        bus_audio = bus_audio.T
                    
                    # Simple resizing
                    if bus_audio.shape != target_shape:
                        bus_audio = np.resize(bus_audio, target_shape)
                    
                    processed_buses[i] = bus_audio
            
            # Mix all buses
            mixed_audio = np.sum(processed_buses, axis=0)
            
            # Normalize to prevent clipping
            max_val = np.max(np.abs(mixed_audio))
            if max_val > 1.0:
                mixed_audio = mixed_audio / max_val * 0.95
            
            return mixed_audio
            
        except Exception as e:
            logger.error(f"Bus mixing failed: {e}")
            return np.zeros((2, self.buffer_size))
    
    def get_bus_status(self) -> Dict[str, Any]:
        """Get status of all buses."""
        try:
            status = {}
            
            for bus_type, bus in self.buses.items():
                status[bus_type.value] = {
                    "is_active": bus.is_active,
                    "volume": bus.config.volume,
                    "pan": bus.config.pan,
                    "mute": bus.config.mute,
                    "solo": bus.config.solo,
                    "effects_count": len(bus.config.effects),
                    "last_update": bus.last_update
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get bus status: {e}")
            return {}
    
    def save_configuration(self, file_path: Union[str, Path]) -> bool:
        """Save bus system configuration to file."""
        try:
            config_data = {}
            
            for bus_type, bus in self.buses.items():
                config_data[bus_type.value] = {
                    "volume": bus.config.volume,
                    "pan": bus.config.pan,
                    "mute": bus.config.mute,
                    "solo": bus.config.solo,
                    "effects": [
                        {
                            "effect_type": effect.effect_type.value,
                            "enabled": effect.enabled,
                            "order": effect.order,
                            "parameters": {
                                name: {
                                    "value": param.value,
                                    "min_value": param.min_value,
                                    "max_value": param.max_value,
                                    "unit": param.unit,
                                    "description": param.description
                                }
                                for name, param in effect.parameters.items()
                            }
                        }
                        for effect in bus.config.effects
                    ],
                    "routing": [routing.value for routing in bus.config.routing]
                }
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved bus configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_configuration(self, file_path: Union[str, Path]) -> bool:
        """Load bus system configuration from file."""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            for bus_type_str, bus_config in config_data.items():
                bus_type = BusType(bus_type_str)
                
                if bus_type in self.buses:
                    # Update bus configuration
                    self.buses[bus_type].config.volume = bus_config.get("volume", 1.0)
                    self.buses[bus_type].config.pan = bus_config.get("pan", 0.0)
                    self.buses[bus_type].config.mute = bus_config.get("mute", False)
                    self.buses[bus_type].config.solo = bus_config.get("solo", False)
                    
                    # Load effects
                    self.buses[bus_type].config.effects = []
                    for effect_config in bus_config.get("effects", []):
                        effect = AudioEffect(
                            effect_type=EffectType(effect_config["effect_type"]),
                            enabled=effect_config["enabled"],
                            order=effect_config["order"],
                            parameters={
                                name: EffectParameter(
                                    name=name,
                                    value=param["value"],
                                    min_value=param["min_value"],
                                    max_value=param["max_value"],
                                    unit=param["unit"],
                                    description=param["description"]
                                )
                                for name, param in effect_config["parameters"].items()
                            }
                        )
                        self.buses[bus_type].config.effects.append(effect)
                    
                    # Load routing
                    self.buses[bus_type].config.routing = [
                        BusType(routing) for routing in bus_config.get("routing", [])
                    ]
            
            logger.info(f"Loaded bus configuration from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False























