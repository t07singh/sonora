
import os
from openai import OpenAI

class LocalLLMClient:
    """
    Client for 'Sonora Swarm' - Local vLLM / Ollama instance.
    Enables offline dubbing and privacy-focused processing.
    """
    def __init__(self, base_url="http://localhost:11434/v1", api_key="ollama", model="llama3"):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key 
        )
        self.model = model
        print(f"DONE: Connected to Local Swarm Node at {base_url} (Model: {model})")

    def chat_completion(self, messages, temperature=0.7):
        """
        Standard chat completion for translation/adaptation.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Local Swarm Error: {e}")
            return None

    def translate_surgical(self, text, style="Anime", constraints=None):
        """
        Specialized prompt for offline surgical translation.
        """
        system_prompt = (
            f"You are an offline Anime Dubbing Assistant. "
            f"Style: {style}. "
            f"Task: Rewrite the input line to match the lip-flap count if provided."
        )
        
        user_content = f"Line: {text}"
        if constraints:
            user_content += f"\nConstraints: {constraints}"

        return self.chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ])

if __name__ == "__main__":
    # Test connection
    llm = LocalLLMClient()
    res = llm.chat_completion([{"role": "user", "content": "Say hello in Japanese style!"}])
    print(f"Swarm Response: {res}")
