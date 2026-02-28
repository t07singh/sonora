import os
import torch
import logging
from typing import Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logger = logging.getLogger("sonora.translator.qwen_local")

class LocalQwenTranslator:
    """
    Local implementation of Qwen2.5-7B-Instruct using 4-bit quantization.
    Handles high-quality, syllable-aware translation.
    """
    def __init__(self, model_path: str = "models/qwen7b"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.is_ready = False
        
        if os.path.exists(model_path):
            try:
                logger.info(f"🚀 Loading Qwen2.5-7B (INT4) on {self.device}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                
                # Configure 4-bit quantization for VRAM efficiency
                bnb_config = None
                if self.device == "cuda":
                    bnb_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.float16
                    )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    quantization_config=bnb_config,
                    device_map="auto" if self.device == "cuda" else None,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                
                if self.device == "cpu":
                    self.model = self.model.to("cpu")
                    
                self.is_ready = True
                logger.info("✅ Qwen2.5-7B INT4 Loaded Successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to load Qwen 7B: {e}")
        else:
            logger.warning(f"⚠️ Qwen 7B weights not found at {model_path}.")

    def translate(self, prompt: str, system_prompt: str = "You are a professional translator and dubbing script editor.") -> str:
        if not self.is_ready:
            raise RuntimeError("Local Qwen Translator not loaded.")
        
        logger.info(f"🧠 [REASONING] Local Qwen-7B Translation: Prompt length={len(prompt)}")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        from src.core.reliability import HardwareLock
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
        
        # Guard GPU - Translation is Priority 5
        with HardwareLock.locked_sync("Local-Qwen-7B", priority=5):
            with torch.no_grad():
                generated_ids = self.model.generate(
                    model_inputs.input_ids,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
            
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_code=True)[0]
        logger.info("✅ Translation Complete.")
        return response.strip()
