import unittest
import logging
from src.pipeline.llm_client import call_ollama, generate_api_calls

class TestLLMClient(unittest.TestCase):
    def setUp(self):
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Test transaction hash
        self.tx_hash = "0x1234567890123456789012345678901234567890123456789012345678901234"
        self.chain = "ETHEREUM"
        self.logger.info(f"Testing with tx_hash: {self.tx_hash}, chain: {self.chain}")

    def test_call_ollama_output_structure(self):
        """Test that the LLM generates correctly structured JSON output."""
        self.logger.info("Running test_call_ollama_output_structure")
        result = call_ollama(self.tx_hash, self.chain, debug=True)
        
        # Check if we got a result
        self.assertIsNotNone(result, "LLM should return a result")
        self.logger.info(f"Got result: {result}")
        
        # Check basic structure
        self.assertIn('api_calls', result, "Result should have api_calls key")
        self.assertIsInstance(result['api_calls'], list, "api_calls should be a list")
        
        # Check each API call
        for call in result['api_calls']:
            self.assertIn('method', call, "Each API call should have a method")
            self.assertIn('params', call, "Each API call should have params")
            self.assertIsInstance(call['params'], dict, "params should be a dictionary")
            self.assertEqual(call['params']['tx_hash'], self.tx_hash, "tx_hash should match input")
            self.assertEqual(call['chain'], self.chain, "chain should match input")
            self.logger.info(f"Validated API call: {call}")

    def test_invalid_tx_hash(self):
        """Test handling of invalid transaction hash."""
        self.logger.info("Running test_invalid_tx_hash")
        # Test with invalid tx_hash
        result = call_ollama("invalid", self.chain)
        self.assertIsNone(result, "Should return None for invalid tx_hash")
        self.logger.info("Invalid tx_hash test passed")
        
    def test_different_chains(self):
        """Test generation for different blockchain networks."""
        chains = ["ETHEREUM", "POLYGON", "OPTIMISM"]
        for chain in chains:
            with self.subTest(chain=chain):
                self.logger.info(f"Testing chain: {chain}")
                result = call_ollama(self.tx_hash, chain, debug=True)
                
                # Validate result
                self.assertIsNotNone(result, f"Should get result for {chain}")
                self.assertIn('api_calls', result)
                
                # Check chain is set correctly in all calls
                for call in result['api_calls']:
                    self.assertEqual(call['chain'], chain, 
                                  f"Chain should be {chain} in all API calls")
                    
                self.logger.info(f"Chain {chain} test passed")
                
    def test_token_artifact_sanitization(self):
        """Test that token artifacts and placeholders are sanitized."""
        self.logger.info("Running test_token_artifact_sanitization")
        # Simulate corrupted output
        corrupted_tx_hash = "tx<｜begin▁of▁sentence｜>_hash"
        result = call_ollama(corrupted_tx_hash, self.chain, debug=True)
        
        # Check if sanitization occurred
        self.assertIsNotNone(result, "LLM should return a result after sanitization")
        for call in result['api_calls']:
            self.assertEqual(call['params']['tx_hash'], self.tx_hash, "tx_hash should be sanitized to match input")
            self.assertEqual(call['chain'], self.chain, "chain should match input")
        self.logger.info("Token artifact sanitization test passed")

    def test_retry_mechanism(self):
        """Test that the function retries on corrupted output."""
        self.logger.info("Running test_retry_mechanism")
        # Simulate corrupted output by passing invalid tx_hash
        result = call_ollama("invalid", self.chain, debug=True)
        
        # Check if retries occurred and eventually failed
        self.assertIsNone(result, "Should return None after exhausting retries")
        self.logger.info("Retry mechanism test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
