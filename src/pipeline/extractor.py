import pandas as pd
import re
from typing import Dict, List, Union, Any, cast
import json
import logging
from pathlib import Path

class DataExtractor:
    """Handles extraction of API-relevant data from CSV files and unstructured text."""
    
    def __init__(self):
        self.tx_hash_pattern = re.compile(r'0x[a-fA-F0-9]{64}')
        # Order patterns from most specific to least specific to avoid false matches
        self.chain_patterns = {
            'optimism': re.compile(r'optimistic\.etherscan\.io', re.IGNORECASE),
            'ethereum': re.compile(r'^(?!.*optimistic).*etherscan\.io', re.IGNORECASE),
            'polygon': re.compile(r'polygonscan\.com', re.IGNORECASE),
            'bsc': re.compile(r'bscscan\.com', re.IGNORECASE)
        }
        self.logger = logging.getLogger(__name__)
    
    def extract_from_csv(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
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
            
            for idx, row in df.iterrows():
                try:
                    data: Dict[str, Any] = {}
                    # Convert index to int safely
                    row_idx = int(str(idx))
                    
                    # Extract transaction hash if present
                    tx_link = row.get('tx_link') or row.get('transaction_link')
                    if isinstance(tx_link, str) and pd.notna(tx_link):
                        tx_hash_match = self.tx_hash_pattern.search(tx_link)
                        if tx_hash_match:
                            data['tx_hash'] = tx_hash_match.group()
                            self.logger.info(f"Extracted tx_hash {data['tx_hash']} from row {row_idx + 1}")
                        
                    # Infer blockchain chain from domain
                    if isinstance(tx_link, str) and pd.notna(tx_link):
                        for chain, pattern in self.chain_patterns.items():
                            if pattern.search(tx_link):
                                data['chain'] = chain.upper()
                                self.logger.info(f"Inferred chain {data['chain']} from URL for row {row_idx + 1}")
                                break
                    
                    # Map purpose to expense_category
                    if 'purpose' in row.index:
                        purpose_value = row.at['purpose']
                        if not pd.isna(purpose_value):
                            data['expense_category'] = str(purpose_value).strip()
                            self.logger.info(f"Mapped expense category {data['expense_category']} for row {row_idx + 1}")
                    
                    # Clean up amount fields
                    if 'amount in ETH' in row.index:
                        eth_amount = row.at['amount in ETH']
                        if not pd.isna(eth_amount):
                            try:
                                data['amount_in_eth'] = float(str(eth_amount).replace(',', ''))
                            except ValueError:
                                self.logger.warning(f"Invalid ETH amount in row {row_idx + 1}: {eth_amount}")
                    
                    if 'amount in USD' in row.index:
                        usd_amount = row.at['amount in USD']
                        if not pd.isna(usd_amount):
                            try:
                                # Remove $ and commas, then convert to float
                                usd_str = str(usd_amount).replace('$', '').replace(',', '')
                                data['amount_in_usd'] = float(usd_str)
                            except ValueError:
                                self.logger.warning(f"Invalid USD amount in row {row_idx + 1}: {usd_amount}")
                    
                    # Add timestamp if present
                    if 'Time' in row.index:
                        time_value = row.at['Time']
                        if not pd.isna(time_value):
                            data['timestamp'] = str(time_value)
                    
                    # Fill missing fields with defaults
                    data.setdefault('chain', 'ETHEREUM')
                    
                    # Only add rows that have either a transaction hash or a valid amount
                    if 'tx_hash' in data:
                        extracted_data.append(data)
                        self.logger.info(f"Successfully processed row {row_idx + 1}")
                    else:
                        self.logger.warning(f"Skipping row {row_idx + 1}: No valid transaction hash found")
                        
                except Exception as row_error:
                    self.logger.error(f"Error processing row {row_idx + 1}: {str(row_error)}")
                    continue
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
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