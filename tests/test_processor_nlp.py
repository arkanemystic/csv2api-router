import unittest
from src.pipeline.processor import PipelineProcessor

class TestProcessorNLP(unittest.TestCase):
    def setUp(self):
        self.processor = PipelineProcessor()
        
        # Sample CSV data
        self.csv_data = [
            {
                'tx_link': 'https://etherscan.io/tx/0xabc123',
                'purpose': 'Sandwich',
                'amount in ETH': '0.1',
                'amount in USD': '200'
            },
            {
                'tx_link': 'https://polygonscan.com/tx/0xdef456',
                'purpose': 'Equipment',
                'amount in ETH': '0.5',
                'amount in USD': '1000'
            }
        ]

    def test_expense_tagging(self):
        prompt = "Hey, can you tag all of these transactions as expenses? Chain is ETH, purpose is listed."
        function_name, formatted_rows = self.processor.process_natural_language(prompt, self.csv_data)
        
        # Check function name
        self.assertEqual(function_name, 'tag_as_expense')
        
        # Check formatted rows
        self.assertEqual(len(formatted_rows), 2)
        
        # Check first row
        row = formatted_rows[0]
        self.assertEqual(row['tx_hash'], '0xabc123')
        self.assertEqual(row['chain'], 'ETHEREUM')
        self.assertEqual(row['expense_category'], 'Sandwich')
        self.assertEqual(row['amount_in_eth'], 0.1)
        self.assertEqual(row['amount_in_usd'], 200.0)
        
        # Check chain detection from URL
        self.assertEqual(formatted_rows[1]['chain'], 'POLYGON')

    def test_transaction_details(self):
        prompt = "Get transaction details for these"
        function_name, formatted_rows = self.processor.process_natural_language(prompt, self.csv_data)
        
        # Should use get_transaction function
        self.assertEqual(function_name, 'get_transaction')
        
        # Should only include tx_hash and chain
        row = formatted_rows[0]
        self.assertEqual(set(row.keys()), {'tx_hash', 'chain'})

    def test_invalid_rows(self):
        # Test with missing tx_link
        invalid_data = [{'purpose': 'Test', 'amount': '0.1'}]
        with self.assertRaises(ValueError):
            self.processor.process_natural_language("Tag as expenses", invalid_data)

    def test_unknown_function(self):
        # Test with prompt that doesn't match any function
        prompt = "Do something undefined with these"
        with self.assertRaises(ValueError):
            self.processor.process_natural_language(prompt, self.csv_data)

if __name__ == '__main__':
    unittest.main()
