
import unittest
from unittest.mock import MagicMock
from sonora.utils.reliability import retry_api_call
import time

class TestReliabilityEngine(unittest.TestCase):
    def test_retry_eventually_succeeds(self):
        self.call_count = 0
        
        @retry_api_call(max_retries=3, base_delay=0.1, jitter=False)
        def failing_function():
            self.call_count += 1
            if self.call_count < 3:
                raise Exception("Transient Error")
            return "Success"
        
        result = failing_function()
        self.assertEqual(result, "Success")
        self.assertEqual(self.call_count, 3)

    def test_retry_max_retries_exceeded(self):
        self.call_count = 0
        
        @retry_api_call(max_retries=2, base_delay=0.1, jitter=False)
        def perpetual_failure():
            self.call_count += 1
            raise Exception("Perpetual Error")
            
        with self.assertRaises(Exception):
            perpetual_failure()
        self.assertEqual(self.call_count, 3) # Original call + 2 retries

    def test_non_transient_error(self):
        self.call_count = 0
        
        @retry_api_call(max_retries=3, base_delay=0.1, jitter=False)
        def auth_failure():
            self.call_count += 1
            raise Exception("Authentication Failed: 401 Unauthorized")
            
        with self.assertRaises(Exception):
            auth_failure()
        self.assertEqual(self.call_count, 1) # Should FAIL IMMEDIATELY without retry

if __name__ == "__main__":
    unittest.main()
