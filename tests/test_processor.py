import unittest
from src.pipeline.processor import process_data

class TestProcessor(unittest.TestCase):

    def test_process_data_valid(self):
        input_data = "valid,csv,data"
        expected_output = {"key": "value"}  # Replace with actual expected output
        self.assertEqual(process_data(input_data), expected_output)

    def test_process_data_invalid(self):
        input_data = "invalid,data"
        with self.assertRaises(ValueError):
            process_data(input_data)

if __name__ == '__main__':
    unittest.main()