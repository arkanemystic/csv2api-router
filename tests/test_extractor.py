import unittest
from src.pipeline.extractor import Extractor

class TestExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = Extractor()

    def test_extract_csv(self):
        # Test extraction from a sample CSV
        sample_csv = "name,age\nAlice,30\nBob,25"
        expected_output = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        result = self.extractor.extract(sample_csv)
        self.assertEqual(result, expected_output)

    def test_extract_unstructured_text(self):
        # Test extraction from unstructured text
        sample_text = "Alice is 30 years old. Bob is 25."
        expected_output = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
        result = self.extractor.extract(sample_text)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()