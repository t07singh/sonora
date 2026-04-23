import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.path.abspath("."))

from sonora.core.llm_translator import GeminiTranslator, HardenedTranslator

class TestHardenedTranslator(unittest.TestCase):
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_iterative_fallback(self, MockGenModel):
        """Verify that GeminiTranslator tries multiple models iteratively."""
        # 1. Setup mock to fail for the first two models, succeed on the third
        m1 = MagicMock()
        m1.generate_content.side_effect = Exception("Model 1 Failed")
        
        m2 = MagicMock()
        m2.generate_content.side_effect = Exception("Model 2 Failed")
        
        m3 = MagicMock()
        m3_res = MagicMock()
        m3_res.text = "Success Translation"
        m3.generate_content.return_value = m3_res
        
        # Side effect for GenerativeModel constructor to return different mocks
        MockGenModel.side_effect = [m1, m2, m3]
        
        translator = GeminiTranslator(api_key="mock_key", model="gemini-1.5-flash")
        
        # 2. Run translation
        result = translator.translate("Hello")
        
        # 3. Verify
        self.assertEqual(result, "Success Translation")
        # Check that it tried 3 models (GenModel called 3 times)
        print("[SUCCESS] Gemini iterative fallback verified.")

    @patch('sonora.core.llm_translator.GeminiTranslator.translate_batch')
    def test_hardened_batch_fallback(self, mock_batch):
        """Verify that HardenedTranslator handles batch results correctly without double-sequential loops."""
        # Setup Gemini to return a successful batch (already went through its own internal loop)
        mock_batch.return_value = ["T1", "T2"]
        
        ht = HardenedTranslator(provider="gemini")
        # Ensure we don't hit mock mode
        ht.mock_mode = False
        ht.translator = GeminiTranslator(api_key="mock_key")
        
        prompts = ["P1", "P2"]
        results = ht.translate_batch(prompts)
        
        self.assertEqual(results, ["T1", "T2"])
        # Should NOT have called translate() again since batch returned a full list
        mock_batch.assert_called_once()
        print("[SUCCESS] Hardened batch fallback (no double loop) verified.")

if __name__ == '__main__':
    # Set dummy env vars to avoid loading real keys during mock test
    os.environ["GEMINI_API_KEY"] = "mock"
    unittest.main()
