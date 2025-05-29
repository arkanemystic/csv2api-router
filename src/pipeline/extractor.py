import pandas as pd
import re
from typing import Dict, List, Union
import json
import logging
from pathlib import Path

class DataExtractor:
    """Handles extraction of API-relevant data from CSV files and unstructured text."""
    
    def __init__(self):
        self.tx_hash_pattern = re.compile(r'0x[a-fA-F0-9]{64}')
        self.chain_patterns = {
            'ethereum': re.compile(r'etherscan\.io', re.IGNORECASE),
            'polygon': re.compile(r'polygonscan\.com', re.IGNORECASE),
            'bsc': re.compile(r'bscscan\.com', re.IGNORECASE)
        }
    
    def extract_from_csv(self, file_path: Union[str, Path]) -> List[Dict]:
        """
        Extract API-relevant data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of dictionaries containing extracted API data
        """
        try:
            df = pd.read_csv(file_path)
            extracted_data = []
            
            for _, row in df.iterrows():
                data = {}
                
                # Extract transaction hash if present
                if 'transaction_link' in row:
                    tx_hash_match = self.tx_hash_pattern.search(str(row['transaction_link']))
                    if tx_hash_match:
                        data['tx_hash'] = tx_hash_match.group()
                
                # Infer blockchain chain from domain
                if 'transaction_link' in row:
                    for chain, pattern in self.chain_patterns.items():
                        if pattern.search(str(row['transaction_link'])):
                            data['chain'] = chain.upper()
                            break
                
                # Extract other fields
                for col in row.index:
                    if pd.notna(row[col]):
                        data[col] = row[col]
                
                # Fill missing fields with defaults
                data.setdefault('chain', 'ETHEREUM')
                data.setdefault('purpose', 'general')
                data.setdefault('amount', 0.0)
                
                extracted_data.append(data)
            
            return extracted_data
            
        except Exception as e:
            logging.error(f"Error processing CSV file: {e}")
            raise
    
    def process_text_input(self, input_str: str) -> Dict:
        """
        Process unstructured text input (like emails) and convert to structured API data.
        
        Args:
            input_str: Raw text input
            
        Returns:
            Dictionary containing extracted API data
        """
        # Extract transaction hash if present
        tx_hash_match = self.tx_hash_pattern.search(input_str)
        data = {
            'raw_text': input_str,
            'tx_hash': tx_hash_match.group() if tx_hash_match else None
        }
        
        # Infer chain from text
        for chain, pattern in self.chain_patterns.items():
            if pattern.search(input_str):
                data['chain'] = chain.upper()
                break
        
        # Set defaults
        data.setdefault('chain', 'ETHEREUM')
        
        return data

def extract_api_calls(data: Union[str, Path, Dict]) -> List[Dict]:
    """
    Extract API-relevant data from the given CSV or unstructured text.

    Args:
        data: Input data - can be a path to CSV file, raw text, or pre-processed dict

    Returns:
        List of extracted API calls
    """
    extractor = DataExtractor()
    
    if isinstance(data, (str, Path)) and str(data).endswith('.csv'):
        return extractor.extract_from_csv(data)
    elif isinstance(data, str):
        return [extractor.process_text_input(data)]
    elif isinstance(data, dict):
        return [data]
    else:
        raise ValueError(f"Unsupported input type: {type(data)}")

def main():
    # Example usage
    extractor = DataExtractor()
    
    # Test CSV extraction
    csv_data = '''transaction_link,purpose,amount
https://etherscan.io/tx/0x123abc...,equipment,100.0
https://polygonscan.com/tx/0x456def...,services,50.0'''
    
    with open('test.csv', 'w') as f:
        f.write(csv_data)
    
    print("CSV Extraction:")
    print(extract_api_calls('test.csv'))
    
    # Test text extraction
    text_input = "Please process transaction 0xabcdef... from etherscan.io for equipment purchase"
    print("\nText Extraction:")
    print(extract_api_calls(text_input))

if __name__ == "__main__":
    main()