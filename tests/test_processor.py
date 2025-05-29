import unittest
import asyncio
from src.pipeline.processor import LLMProcessor, process_with_llm

class TestProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = LLMProcessor(ollama_base_url="http://localhost:11434")
        
    def test_create_prompt(self):
        data = {
            "tx_hash": "0x123abc",
            "chain": "ETHEREUM"
        }
        prompt = self.processor._create_prompt(data)
        self.assertIsInstance(prompt, str)
        self.assertIn("0x123abc", prompt)
        self.assertIn("ETHEREUM", prompt)
        
    def test_create_prompt_no_hash(self):
        data = {"chain": "ETHEREUM"}
        prompt = self.processor._create_prompt(data)
        self.assertEqual(prompt, '{"api_calls": []}')
        
    def test_validate_api_call(self):
        valid_call = {
            "method": "get_transaction",
            "params": {"tx_hash": "0x123"}
        }
        self.assertTrue(self.processor.validate_api_call(valid_call))
        
        invalid_call = {
            "method": "get_transaction",
            "params": {}  # Missing tx_hash
        }
        self.assertFalse(self.processor.validate_api_call(invalid_call))
        
    async def async_test_process_data(self):
        test_data = {
            "tx_hash": "0x123abc",
            "chain": "ETHEREUM"
        }
        result = await self.processor.process_data(test_data)
        self.assertIsInstance(result, list)
        
    def test_process_data(self):
        # Run async test in event loop
        asyncio.run(self.async_test_process_data())
        
    async def async_test_process_with_llm(self):
        test_data = {
            "tx_hash": "0x123abc",
            "chain": "ETHEREUM"
        }
        result = await process_with_llm(test_data)
        self.assertIsInstance(result, list)
        
    def test_process_with_llm(self):
        # Run async test in event loop
        asyncio.run(self.async_test_process_with_llm())

if __name__ == '__main__':
    unittest.main()