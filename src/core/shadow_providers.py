import os
import shutil
import logging
import time
from typing import List, Optional
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from gradio_client import Client, handle_file

logger = logging.getLogger("sonora.shadow_providers")

def cloud_separate_audio(input_audio_path: str) -> str:
    """
    Cloud Separation Node: Offloads Demucs processing to remote GPU via Gradio.
    Optimized for AI Studio: Uses client.submit() + polling to handle 60s+ tasks
    without triggering sandbox deadline timeouts.
    """
    try:
        logger.info(f"🚀 Neural Link: Offloading {input_audio_path} to Cloud GPU (Demucs)...")
        client = Client("facebook/demucs")

        # Use .submit() instead of .predict() to handle long-running tasks asynchronously
        job = client.submit(
            audio=handle_file(input_audio_path),
            model="htdemucs",
            api_name="/predict"
        )

        # Polling loop with 5-minute safety timeout
        start_time = time.time()
        while not job.done():
            time.sleep(2)
            if time.time() - start_time > 300:
                raise TimeoutError("Cloud Separation Node: Remote GPU timed out.")
            
            # Update internal logs for HUD
            try:
                status = job.status()
                logger.debug(f"Demucs Cloud Progress: {status.code}")
            except:
                pass

        result = job.result()

        # 3. Secure output in standard writeable sandbox
        output_dir = "/tmp/sonora_out"
        os.makedirs(output_dir, exist_ok=True)

        # result[0] is typically the isolated Vocals stem path
        vocals_temp = result[0] if isinstance(result, list) else result
        final_path = os.path.join(output_dir, f"isolated_vocals_{int(time.time())}.wav")

        shutil.copy(vocals_temp, final_path)
        logger.info(f"✅ Cloud Separation Complete: {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Cloud Separation Critical Failure: {e}")
        # Fallback to original audio if isolation fails
        return input_audio_path

def cloud_run_transcription(audio_path: str) -> list:
    """Fallback: Whisper Cloud Transcription."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: raise ValueError("OPENAI_API_KEY missing for cloud fallback")
    
    client = OpenAI(api_key=api_key)
    with open(audio_path, "rb") as audio:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    return response.words

def cloud_translate_segment(japanese_text: str, target_syllables: int, style: str) -> str:
    """Fallback: GPT-4o Isometric Translation."""
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    prompt = f"Translate to English in {style} style. Target syllables: {target_syllables}. Text: {japanese_text}"
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

def cloud_generate_voice(text: str, voice_id: str) -> bytes:
    """Fallback: ElevenLabs synthesis."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    client = ElevenLabs(api_key=api_key)
    audio_gen = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_flash_v2_5"
    )
    return b"".join(list(audio_gen))