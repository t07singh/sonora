"""
Local offline translation implementation for Sonora/Auralis.

This module provides translation services using local Hugging Face
Transformers models for offline anime content translation, preserving
context and cultural nuances without requiring external API calls.
"""

import asyncio
from typing import Dict, List, Optional, Literal
import logging
from abc import ABC, abstractmethod

from ..config import settings

logger = logging.getLogger(__name__)


class TranslationResult:
    """Container for translation results with metadata."""
    
    def __init__(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
        confidence: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        self.original_text = original_text
        self.translated_text = translated_text
        self.source_language = source_language
        self.target_language = target_language
        self.confidence = confidence
        self.metadata = metadata or {}


class BaseTranslator(ABC):
    """Abstract base class for translation providers."""
    
    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str = "ja",
        target_language: str = "en"
    ) -> TranslationResult:
        """Translate text from source to target language."""
        pass


class LocalHuggingFaceTranslator(BaseTranslator):
    """Local Hugging Face Transformers-based translator for anime content."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize local translator.
        
        Args:
            model_name: Hugging Face model identifier (defaults to config setting)
        """
        from .local_translator import LocalTranslator
        
        self.model_name = model_name or getattr(
            settings.translation, 'model_name', 
            "Helsinki-NLP/opus-mt-ja-en"
        )
        
        self._local_translator = LocalTranslator(model_name=self.model_name)
        self.temperature = getattr(settings.translation, 'temperature', 0.3)
    
    async def translate(
        self,
        text: str,
        source_language: str = "ja",
        target_language: str = "en"
    ) -> TranslationResult:
        """
        Translate text using local Hugging Face model.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            TranslationResult with translated text and metadata
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0
            )
        
        try:
            logger.info(f"Translating {len(text)} characters from {source_language} to {target_language}")
            
            # Use local translator (synchronous, but we'll run it in executor)
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Convert language codes for local translator
            lang_hint = "JP" if source_language == "ja" else None
            
            translated_text = await loop.run_in_executor(
                None,
                lambda: self._local_translator.translate(text, lang_hint)
            )
            
            # Estimate confidence based on translation success
            confidence = 0.9 if translated_text and not translated_text.startswith("[MOCK") else 0.5
            
            result = TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                confidence=confidence,
                metadata={
                    "model": self.model_name,
                    "provider": "local_huggingface",
                    "offline": True
                }
            )
            
            logger.info(f"Translation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise


class AnthropicTranslator(BaseTranslator):
    """Anthropic Claude-based translator for anime content."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Anthropic translator.
        
        Args:
            api_key: Anthropic API key (defaults to environment variable)
            model_name: Model to use (defaults to config setting)
        """
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        self.model_name = model_name or "claude-3-sonnet-20240229"
        self.temperature = settings.translation.temperature
        self.max_tokens = settings.translation.max_tokens
    
    async def translate(
        self,
        text: str,
        source_language: str = "ja",
        target_language: str = "en"
    ) -> TranslationResult:
        """
        Translate text using Anthropic Claude.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            TranslationResult with translated text and metadata
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                confidence=1.0
            )
        
        try:
            prompt = f"""You are an expert anime translator. Translate the following {source_language} text to {target_language} while preserving character personality, cultural context, and emotional tone.

Text: "{text}"

Translation:"""
            
            logger.info(f"Translating {len(text)} characters from {source_language} to {target_language}")
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            translated_text = response.content[0].text.strip()
            
            result = TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                metadata={
                    "model": self.model_name,
                    "provider": "anthropic",
                    "usage": response.usage.dict() if hasattr(response, 'usage') else None
                }
            )
            
            logger.info(f"Translation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise


class LLMTranslator:
    """
    Main translation interface with provider abstraction.
    
    Now uses local offline Hugging Face Transformers models by default.
    Legacy provider names (openai, anthropic) fallback to local models.
    """
    
    def __init__(self, provider: Optional[Literal["local", "huggingface", "openai", "anthropic"]] = None):
        """
        Initialize LLM translator.
        
        Args:
            provider: Translation provider to use (defaults to "local" for offline operation)
        """
        self.provider = provider or getattr(settings.translation, 'provider', 'local')
        self._translator = self._create_translator()
    
    def _create_translator(self) -> BaseTranslator:
        """Create the appropriate translator based on provider setting."""
        if self.provider == "local" or self.provider == "huggingface":
            return LocalHuggingFaceTranslator()
        elif self.provider == "openai":
            # Legacy: fallback to local if OpenAI is requested but not available
            logger.warning("OpenAI provider requested but not available. Using local HuggingFace model.")
            return LocalHuggingFaceTranslator()
        elif self.provider == "anthropic":
            # Legacy: fallback to local if Anthropic is requested but not available
            logger.warning("Anthropic provider requested but not available. Using local HuggingFace model.")
            return LocalHuggingFaceTranslator()
        else:
            # Default to local
            logger.info(f"Using default local translation provider")
            return LocalHuggingFaceTranslator()
    
    async def translate(
        self,
        text: str,
        source_language: str = "ja",
        target_language: str = "en"
    ) -> TranslationResult:
        """
        Translate text using the configured provider.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            TranslationResult with translated text and metadata
        """
        return await self._translator.translate(text, source_language, target_language)
    
    async def translate_batch(
        self,
        texts: List[str],
        source_language: str = "ja",
        target_language: str = "en"
    ) -> List[TranslationResult]:
        """
        Translate multiple texts concurrently.
        
        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            List of TranslationResult objects
        """
        tasks = [
            self.translate(text, source_language, target_language)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
    
    def switch_provider(self, provider: Literal["local", "huggingface", "openai", "anthropic"]) -> None:
        """
        Switch to a different translation provider.
        
        Args:
            provider: New provider to use
        """
        if provider != self.provider:
            self.provider = provider
            self._translator = self._create_translator()
            logger.info(f"Switched translation provider to: {provider}")

