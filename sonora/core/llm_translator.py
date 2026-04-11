import os
import logging
import time
import functools
from typing import Optional, Literal, List, Dict, Any, Union
import json
from openai import OpenAI
from sonora.utils.reliability import retry_api_call
from dotenv import load_dotenv

# Force load environment
load_dotenv()

logger = logging.getLogger(__name__)

class OpenAITranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    @retry_api_call(max_retries=2, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using OpenAI GPT-4o with robust retries."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0 # Strict internal timeout
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

    @retry_api_call(max_retries=2, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using Anthropic Claude with robust retries."""
        if not self.client:
            raise ImportError("Anthropic client not initialized.")
            
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0 # Strict internal timeout
        )
        return message.content[0].text.strip()

class GeminiTranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-flash-latest"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.client = None
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config={"temperature": 0.1},
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                }
            )
            logger.info(f"Initialized Gemini translator with verified model: {self.model}")
        except ImportError:
            logger.warning("google-generativeai package not installed. GeminiTranslator will fail.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    @retry_api_call(max_retries=3, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using Google Gemini with verified model fallback."""
        if not self.client:
            raise ImportError("Gemini client not initialized.")
            
        try:
            # Gemini Python SDK doesn't have a direct timeout param in generate_content, 
            # so we use request_options if supported or rely on the retry wrapper.
            response = self.client.generate_content(prompt)
            # Response might be blocked by safety filters
            if hasattr(response, 'text'):
                return response.text.strip()
            return "[SAFETY BLOCKED]"
        except Exception as e:
            # Fallback chain based on verified Cloud Probe results
            import google.generativeai as genai
            if self.model == "gemini-1.5-flash":
                logger.warning(f"Gemini 1.5-Flash failed: {e}. Falling back to gemini-flash-latest...")
                self.model = "gemini-flash-latest"
            elif self.model == "gemini-flash-latest":
                logger.warning(f"Gemini-Flash-Latest failed: {e}. Falling back to gemini-pro-latest...")
                self.model = "gemini-pro-latest"
            else:
                raise e # End of verified chain
                
            self.client = genai.GenerativeModel(self.model)
            return self.translate(prompt)

    @retry_api_call(max_retries=1, base_delay=1) # Fast Fail for 429s
    def translate_batch(self, prompts: List[str]) -> List[str]:
        """Translates a batch of texts in a single call for RPM efficiency."""
        if not self.client:
            raise ImportError("Gemini client not initialized.")
            
        # Structure the batch prompt as a JSON-request for reliability
        batch_prompt = (
            "Translate the following array of segments into NATURAL ENGLISH for professional dubbing.\n"
            "FORMAT: Return ONLY a JSON array of strings. No markdown, no prefixes.\n"
            "SYNC: Maintain rhythm and constraints exactly.\n\n"
            f"Segments: {prompts}"
        )
        
        try:
            response = self.client.generate_content(batch_prompt)
            text = response.text.strip()
            # Clean up potential markdown formatting
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
                
            results = json.loads(text)
            if isinstance(results, list) and len(results) == len(prompts):
                return results
            return [f"[BATCH ERROR] {p[:20]}..." for p in prompts]
        except Exception as e:
            logger.error(f"Gemini Batch Translation failed: {e}")
            # Individual fallback if batch fails
            results = []
            for p in prompts:
                results.append(self.translate(p))
                # Only sleep for Gemini Free Tier (protecting RPM)
                if "flash" in self.model:
                    time.sleep(1.0) 
            return results

class GroqTranslator:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )

    @retry_api_call(max_retries=2, base_delay=1)
    def translate(self, prompt: str) -> str:
        """Translates text using Groq Llama with robust retries."""
        if not self.client:
            raise ImportError("Groq client not initialized (check API key).")
            
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0 # Strict internal timeout
        )
        return completion.choices[0].message.content.strip()

class LocalQwenProvider:
    def __init__(self, model_path: str = "models/qwen7b"):
        self.model_path = model_path
        self.translator = None
        try:
            from src.services.translator.qwen_local import LocalQwenTranslator
            self.translator = LocalQwenTranslator(model_path=model_path)
        except Exception as e:
            logger.warning(f"Failed to load LocalQwenTranslator: {e}")

    @retry_api_call(max_retries=3, base_delay=1)
    def translate(self, prompt: str) -> str:
        if not self.translator:
            # Try to initialize on demand if not ready
            from src.services.translator.qwen_local import LocalQwenTranslator
            try:
                self.translator = LocalQwenTranslator(model_path=self.model_path)
            except Exception as e:
                logger.error(f"Failed to load LocalQwenTranslator on demand: {e}")
                
        if not self.translator or not self.translator.is_ready:
            raise RuntimeError("Local Qwen Translator not ready.")
        return self.translator.translate(prompt)

class HardenedTranslator:
    """
    Consolidated Translator that delegates to cloud providers.
    Supports: OpenAI (GPT-4o), Anthropic (Claude), Gemini (Free tier)
    Fallback to mock mode if no API keys are available.
    """
    def __init__(self, provider: Literal["openai", "anthropic", "gemini", "groq", "local_qwen"] = "gemini"):
        self.provider = provider
        self.mock_mode = False
        
        # Initialize all potential translators if keys exist
        self.translators = {}
        
        if os.getenv("GEMINI_API_KEY"):
            self.translators["gemini"] = GeminiTranslator()
        if os.getenv("GROQ_API_KEY"):
            self.translators["groq"] = GroqTranslator()
        if os.getenv("OPENAI_API_KEY"):
            self.translators["openai"] = OpenAITranslator()
        if os.getenv("ANTHROPIC_API_KEY"):
            self.translators["anthropic"] = AnthropicTranslator()
            
        # Local Qwen check - don't initialize yet (heavy), just mark as available
        if os.path.exists("models/qwen7b"):
            self.translators["local_qwen"] = LocalQwenProvider()
            
        if not self.translators:
            logger.warning("❌ No AI Provider API keys or local models found. Falling back to MOCK mode.")
            self.mock_mode = True
        else:
            # Set the primary translator based on requested provider
            if self.provider in self.translators:
                self.translator = self.translators[self.provider]
            else:
                # Fallback to first available
                self.provider = list(self.translators.keys())[0]
        self.last_quota_error = 0
        self.concurrency_mode = "burst" # burst or conservative

    def translate(self, prompt: str) -> Union[str, Dict[str, str]]:
        if self.mock_mode:
            # Mock translation for demo purposes
            logger.info("Using MOCK translation mode")
            # Extract the text from the prompt (very basic)
            if "Text:" in prompt:
                original = prompt.split("Text:")[-1].strip()
                # Simple mock: reverse and add "[MOCK]" prefix
                res = f"[MOCK TRANSLATION] {original[:50]}"
            else:
                res = "[MOCK] This is a simulated translation."
            return {"text": res, "provider": "mock"}
        
        try:
            result = self.translator.translate(prompt)
            return {"text": result, "provider": self.provider}
        except Exception as e:
            err_str = str(e).lower()
            # Catch broader set of quota/timeout errors
            is_quota = "quota" in err_str or "429" in err_str or "limit" in err_str or "timeout" in err_str or "deadline" in err_str
            
            if is_quota:
                self.last_quota_error = time.time()
                self.concurrency_mode = "conservative" # Slow down on 429
                logger.warning(f"🚦 Provider {self.provider} hit limit/timeout. Entering Conservative Mode (1 thread)...")
                # Fallback chain priority
                chain = ["gemini", "groq", "openai", "anthropic", "local_qwen"]
                try:
                    current_idx = chain.index(self.provider)
                except ValueError:
                    current_idx = -1
                    
                for next_provider in chain[current_idx + 1:]:
                    if next_provider in self.translators:
                        logger.info(f"🔄 Falling back to {next_provider}...")
                        try:
                            # Use a shorter internal timeout for fallbacks to keep UI responsive
                            result = self.translators[next_provider].translate(prompt)
                            return {"text": result, "provider": next_provider}
                        except Exception as inner_e:
                            logger.error(f"Fallback to {next_provider} failed: {inner_e}")
                            continue
                            
                return {"text": "[RATE LIMIT: ALL PROVIDERS EXHAUSTED]", "provider": "error"}
                
            logger.error(f"Cloud translation completely failed: {e}")
            return {"text": f"[ERROR] {str(e)[:50]}...", "provider": "error"}

    def translate_batch(self, prompts: List[str]) -> List[Union[str, Dict[str, str]]]:
        if self.mock_mode:
            return [{"text": f"[MOCK BATCH] {p[:20]}", "provider": "mock"} for p in prompts]
            
        try:
            # 1. Try native provider batching first (Speed Layer)
            if hasattr(self.translator, 'translate_batch'):
                results = self.translator.translate_batch(prompts)
                if results and isinstance(results[0], str) and ("[BATCH ERROR]" in results[0] or "[RATE LIMIT]" in results[0]):
                    raise RuntimeError("Native batch failed")
                return results
                
            raise AttributeError("Serial fallback required")
            
        except Exception:
            # 2. Parallel Burst Fallback (Concurrency Layer)
            # Use high concurrency for Groq/OpenAI, serial for Gemini
            is_fast_provider = self.provider in ["groq", "openai", "anthropic"]
            
            # Auto-Recovery for Circuit Breaker
            if self.concurrency_mode == "conservative" and (time.time() - self.last_quota_error > 60):
                self.concurrency_mode = "burst"
                logger.info("🟢 Quota Restored. Returning to Burst Mode (5 threads).")

            if is_fast_provider and self.concurrency_mode == "burst":
                logger.info(f"⚡ [FAST-PATH] Bursting {len(prompts)} translations via {self.provider}...")
                from concurrent.futures import ThreadPoolExecutor
                # Burst Throttler: 5 workers is the Sweet Spot for Groq RPM stability
                with ThreadPoolExecutor(max_workers=5) as executor:
                    return list(executor.map(self.translate, prompts))
            else:
                # Conservative fallback: Process one by one to avoid further 429s
                logger.info(f"🐢 [CONSERVATIVE] Processing {len(prompts)} translations sequentially...")
                return [self.translate(p) for p in prompts]