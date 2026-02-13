import os
import logging
import gc
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.core.reliability import HardwareLock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sonora-isometric-translator")

app = FastAPI(title="Sonora Isometric Translation Node (Qwen 2.5 INT4)")

# Configuration
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# For GPTQ on CPU, we might need specific library versions, 
# but we configure for auto-detection.

class TranslationRequest(BaseModel):
    text: str
    target_syllables: int
    speaker_id: str = "PROTAGONIST"

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Bootstrapping Qwen 2.5 Isometric Node on {DEVICE}...")

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "Qwen2.5-7B-Instruct-INT4",
        "role": "Isometric_Agent",
        "device": DEVICE
    }

@app.post("/translate")
async def translate(request: TranslationRequest):
    # Lock hardware to prevent OOM during weight loading
    await HardwareLock.acquire("Qwen2.5-Isometric")
    
    try:
        logger.info(f"🧩 Fitting dialogue for: {request.speaker_id} | Target: {request.target_syllables}")
        
        # Load weights into RAM (Transient pattern)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
            trust_remote_code=True
        )

        prompt = f"Japanese Source: {request.text}\nTarget Syllables: {request.target_syllables}\nTranslate to English dub script while strictly maintaining {request.target_syllables} syllables for lip-sync:"
        
        messages = [
            {"role": "system", "content": "You are the Sonora Isometric Translator. Translate Japanese anime dialogue into English matching source syllable counts (Morae) exactly. Output only the translated text string."},
            {"role": "user", "content": prompt}
        ]
        
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=128,
            temperature=0.4,
            top_p=0.9
        )
        
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        # Cleanup: Remove prompt parts if they are returned by decoder
        clean_response = response.split("assistant\n")[-1].strip().replace('"', '')

        # CRITICAL: Resource Release
        del model
        del tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"✅ Isometric Fit Success: '{clean_response}'")
        
        return {
            "translation": clean_response,
            "target_syllables": request.target_syllables,
            "engine": "Qwen2.5-7B-INT4"
        }
        
    except Exception as e:
        logger.error(f"❌ Translation failed: {str(e)}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        HardwareLock.release()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
