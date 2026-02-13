import os
import logging
from typing import Optional, Literal
from openai import OpenAI
from sonora.utils.reliability import retry_api_call

logger = logging.getLogger(__name__)

class OpenAITranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    @retry_api_call(max_retries=3, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using OpenAI GPT-4o with robust retries."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip()

class AnthropicTranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.warning("Anthropic package not installed. AnthropicTranslator will fail.")

    @retry_api_call(max_retries=3, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using Anthropic Claude with robust retries."""
        if not self.client:
            raise ImportError("Anthropic client not initialized.")
            
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()

class GeminiTranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.client = None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
            logger.info(f"Initialized Gemini translator with model: {self.model}")
        except ImportError:
            logger.warning("google-generativeai package not installed. GeminiTranslator will fail.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    @retry_api_call(max_retries=3, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using Google Gemini with robust retries."""
        if not self.client:
            raise ImportError("Gemini client not initialized.")
            
        response = self.client.generate_content(prompt)
        return response.text.strip()

class HardenedTranslator:
    """
    Consolidated Translator that delegates to cloud providers.
    Supports: OpenAI (GPT-4o), Anthropic (Claude), Gemini (Free tier)
    Fallback to mock mode if no API keys are available.
    """
    def __init__(self, provider: Literal["openai", "anthropic", "gemini"] = "gemini"):
        self.provider = provider
        self.mock_mode = False
        
        # Check if API keys are available
        if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            logger.warning("No OPENAI_API_KEY found. Falling back to MOCK mode.")
            self.mock_mode = True
        elif provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            logger.warning("No ANTHROPIC_API_KEY found. Falling back to MOCK mode.")
            self.mock_mode = True
        elif provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
            logger.warning("No GEMINI_API_KEY found. Falling back to MOCK mode.")
            self.mock_mode = True
        
        if not self.mock_mode:
            if provider == "openai":
                self.translator = OpenAITranslator()
            elif provider == "anthropic":
                self.translator = AnthropicTranslator()
            elif provider == "gemini":
                self.translator = GeminiTranslator()

    def translate(self, prompt: str) -> str:
        if self.mock_mode:
            # Mock translation for demo purposes
            logger.info("Using MOCK translation mode")
            # Extract the text from the prompt (very basic)
            if "Text:" in prompt:
                original = prompt.split("Text:")[-1].strip()
                # Simple mock: reverse and add "[MOCK]" prefix
                return f"[MOCK TRANSLATION] {original[:50]}"
            return "[MOCK] This is a simulated translation."
        
        try:
            # Internal retries (1s, 2s, 4s) happen inside this call
            return self.translator.translate(prompt)
        except Exception as e:
            logger.error(f"Cloud translation completely failed after 3 attempts: {e}")
            # Final fallback to mock
            logger.warning("Falling back to MOCK mode due to API failure")
            return f"[FALLBACK MOCK] Translation unavailable")