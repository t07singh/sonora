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

    @retry_api_call(max_retries=2, base_delay=1) # Reduced retries per model to speed up fallback
    def translate(self, prompt: str) -> str:
        """Translates text using Google Gemini with iterative model fallback and strict timeouts."""
        if not self.client:
            raise ImportError("Gemini client not initialized.")
            
        models_to_try = [self.model, "gemini-1.5-flash", "gemini-flash-latest", "gemini-pro-latest"]
        # De-duplicate while preserving order
        unique_models = []
        for m in models_to_try:
            if m not in unique_models:
                unique_models.append(m)
        
        last_exception = None
        for model_name in unique_models:
            try:
                logger.info(f"🧬 [GEMINI] Attempting translation via {model_name}...")
                import google.generativeai as genai
                current_model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={"temperature": 0.1}
                )
                
                # Use request_options to set a strict 25s timeout for the API call itself
                response = current_model.generate_content(
                    prompt, 
                    request_options={"timeout": 25.0}
                )
                
                if hasattr(response, 'text'):
                    # Update active model on success to 'stick' to working models
                    self.model = model_name
                    self.client = current_model
                    return response.text.strip()
                
                return "[SAFETY BLOCKED]"
            except Exception as e:
                last_exception = e
                err_msg = str(e).lower()
                logger.warning(f"⚠️ [GEMINI] Model {model_name} failed: {e}")
                
                # If it's a 429 (Quota), don't bother trying other models on this segment, 
                # let the HardenedTranslator handle the provider-level fallback instantly.
                if "429" in err_msg or "quota" in err_msg:
                    raise e
                
                continue # Try next model in chain
        
        if last_exception:
            raise last_exception
        return "[ERROR: NO MODELS AVAILABLE]"

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
            # Add timeout to batch call as well
            response = self.client.generate_content(batch_prompt, request_options={"timeout": 60.0})
            
            if not hasattr(response, 'text'):
                logger.warning("Gemini Batch response blocked by safety filters.")
                raise ValueError("Safety blocked batch")
                
            text = response.text.strip()
            # Clean up potential markdown formatting
            if "```json" in text:
                text = text.split("```json")[-1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[-1].split("```")[0].strip()
                
            results = json.loads(text)
            if isinstance(results, list) and len(results) == len(prompts):
                return results
            
            logger.warning("Gemini Batch JSON parse failed or length mismatch. Falling back to serial.")
            raise ValueError("Corrupt batch response")
        except Exception as e:
            # If it's a 429, raising here triggers HardenedTranslator provider-level fallback
            if "429" in str(e) or "quota" in str(e).lower():
                raise e
                
            logger.error(f"Gemini Batch Translation failed: {e}. Executing sequential surgery...")
            results = []
            for p in prompts:
                try:
                    results.append(self.translate(p))
                except:
                    results.append("[ERROR]")
                
                # Only sleep for Gemini Free Tier (protecting RPM)
                if "flash" in self.model:
                    time.sleep(0.5) # Reduced from 1.0 to speed up recovery
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
                            
                return {"text": "[RATE LIMIT: ALL PROVIDERS EXHAUSTED]", "provider": "error"}
                
            logger.error(f"Cloud translation completely failed: {e}")
            return {"text": "[ERROR: API FAULT]", "provider": "error"}

    def translate_batch(self, prompts: List[str]) -> List[Union[str, Dict[str, str]]]:
        if self.mock_mode:
            return [{"text": f"[MOCK BATCH] {p[:20]}", "provider": "mock"} for p in prompts]
            
        # Global Quota Check: If we recently hit a rate limit, stay in conservative mode
        if self.concurrency_mode == "conservative" and (time.time() - self.last_quota_error > 60):
            self.concurrency_mode = "burst"
            logger.info("🟢 Quota Restored. Returning to Burst Mode.")

        try:
            # 1. Try native provider batching first (Speed Layer)
            if hasattr(self.translator, 'translate_batch'):
                results = self.translator.translate_batch(prompts)
                
                # If Gemini's native batch failed and it already did its own internal sequential fallback,
                # we return those results instead of triggering ANOTHER sequential block here.
                if results and len(results) == len(prompts):
                    return results

            raise AttributeError("Serial fallback required")
            
        except Exception as e:
            # 2. Parallel Burst Fallback (Concurrency Layer)
            # Use high concurrency for Groq/OpenAI, serial for Gemini
            is_fast_provider = self.provider in ["groq", "openai", "anthropic"]
            
            if is_fast_provider and self.concurrency_mode == "burst":
                logger.info(f"⚡ [FAST-PATH] Bursting {len(prompts)} translations via {self.provider}...")
                from concurrent.futures import ThreadPoolExecutor
                
                def safe_translate(p):
                    try:
                        return self.translate(p)
                    except Exception as e:
                        logger.error(f"Parallel segment failed: {e}")
                        return {"text": "[RATE LIMIT: RETRY LATER]", "provider": "error"}

                # Use a slightly larger pool for fast providers to saturate throughput
                with ThreadPoolExecutor(max_workers=8) as executor:
                    return list(executor.map(safe_translate, prompts))
            else:
                # 3. Conservative Fallback: Throttled sequential processing
                logger.info(f"🐢 [CONSERVATIVE] Processing {len(prompts)} translations via {self.provider}...")
                results = []
                for p in prompts:
                    try:
                        results.append(self.translate(p))
                    except:
                        results.append({"text": "[ERROR]", "provider": "error"})
                    
                    # Mandatory breather for Free Tier stability: 2.5s for Gemini, 0.5s for others
                    delay = 2.0 if self.provider == "gemini" else 0.5
                    time.sleep(delay)
                return results