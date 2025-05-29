import unittest
from pathlib import Path
from src.pipeline.extractor import DataExtractor

class TestDataExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = DataExtractor()
        self.test_data_dir = Path(__file__).parent.parent / 'dataset'
        
    def test_tx_hash_extraction(self):
        # Test transaction hash extraction
        sample_tx = "View on Etherscan: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        match = self.extractor.tx_hash_pattern.search(sample_tx)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
    
    def test_chain_detection(self):
        # Test chain detection from URLs
        test_cases = {
            'https://etherscan.io/tx/0x123': 'ETHEREUM',
            'https://polygonscan.com/tx/0x123': 'POLYGON',
            'https://bscscan.com/tx/0x123': 'BSC',
            'https://optimistic.etherscan.io/tx/0x123': 'OPTIMISM'
        }
        
        for url, expected_chain in test_cases.items():
            chain = None
            for c, pattern in self.extractor.chain_patterns.items():
                if pattern.search(url):
                    chain = c.upper()
                    break
            self.assertEqual(chain, expected_chain)
    
    def test_extract_from_csv(self):
        # Create a temporary test CSV
        test_csv = self.test_data_dir / "ten_case_test.csv"
        if test_csv.exists():
            result = self.extractor.extract_from_csv(test_csv)
            self.assertIsInstance(result, list)
            if len(result) > 0:
                # Verify extracted data structure
                self.assertIsInstance(result[0], dict)
                # Check for expected keys
                for item in result:
                    if 'tx_hash' in item:
                        self.assertRegex(item['tx_hash'], r'^0x[a-fA-F0-9]{64}$')
                    if 'chain' in item:
                        self.assertIn(item['chain'], ['ETHEREUM', 'POLYGON', 'BSC', 'OPTIMISM'])

if __name__ == '__main__':
    unittest.main()