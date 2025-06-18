print("LLM_CLIENT_R5_CONFIRMATION: This version of llm_client.py is being loaded.")

import subprocess
import json
import re
import time
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_APIS = {
    "fill_account_by": {
        "params": ["account_id", "amount"]
    },
    "get_transaction": {
        "params": ["chain", "tx_hash"]
    },
    "tag_as_expense": {
        "params": ["chain", "tx_hash", "expense_category"]
    },
    "get_receipt": {
        "params": ["chain", "tx_hash"]
    },
    "list_chains": {
        "params": []
    }
}

def clean_and_validate_api_call(row: Dict[str, Any], debug: bool = False) -> Optional[Dict[str, Any]]:
    """Clean and validate API call parameters from row data."""
    try:
        row_num_info = row.get('csv_row_number', 'N/A')
        logger.info(f"LLM_CLIENT_R6: Attempting to extract API call for row {row_num_info}")
        
        # Extract tx_hash
        tx_hash = row.get('tx_hash')
        if not tx_hash and 'tx_link' in row:
            tx_link = row.get('tx_link', '')
            if tx_link and '/' in tx_link:
                tx_hash = tx_link.split('/')[-1]
                if not tx_hash or len(tx_hash) < 42:  # Basic validation for ETH tx hash
                    logger.error("Invalid tx_hash length")
                    return None
            else:
                logger.error("Invalid tx_link format")
                return None
        
        if not tx_hash:
            logger.error("No tx_hash found")
            return None
            
        # Extract chain
        chain = row.get('chain', 'ETHEREUM')
        
        # Extract expense category from purpose or other fields
        expense_category = None
        for field in ['purpose', 'expense_category', 'category']:
            if field in row and row[field]:
                expense_category = str(row[field]).strip()
                logger.info(f"Found expense category '{expense_category}' from field '{field}'")
                break
        
        if not expense_category:
            expense_category = 'general'
            logger.info("No expense category found, using default 'general'")
        
        # Build API call in the exact format from the prompt template
        api_call = {
            "api_calls": [
                {
                    "method": "tag_as_expense",
                    "params": {
                        "tx_hash": tx_hash,
                        "chain": chain,
                        "expense_category": expense_category
                    }
                }
            ]
        }
        
        # Validate all required parameters are present and non-empty
        params = api_call["api_calls"][0]["params"]
        if not all(params.values()):
            missing = [k for k, v in params.items() if not v]
            logger.error(f"Missing required parameters: {missing}")
            return None
            
        logger.info(f"Generated API call: {json.dumps(api_call, indent=2)}")
        return api_call
        
    except Exception as e:
        logger.error(f"Error in clean_and_validate_api_call: {str(e)}")
        return None

def generate_api_calls(row_data: Dict[str, Any], debug: bool = False) -> List[Dict[str, Any]]:
    """Generate API calls from row data."""
    try:
        logger.info(f"DIAGNOSTIC: Input row data: {json.dumps(row_data, indent=2)}")
        
        # Clean and validate the API call
        api_call = clean_and_validate_api_call(row_data, debug)
        if not api_call:
            logger.error("DIAGNOSTIC: Failed to generate valid API call")
            return []
            
        # Return the first API call from the list
        return api_call["api_calls"]
        
    except Exception as e:
        logger.error(f"DIAGNOSTIC: Error generating API calls: {str(e)}")
        return []

def batch_process_rows(rows: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    results = []
    for row in rows:
        try:
            api_calls = generate_api_calls(row, debug)
            if api_calls:
                results.extend(api_calls)
        except Exception as e:
            logger.error(f"Error processing row: {e}")
            continue
    return results

if __name__ == "__main__":
    # Add test cases for each API
    test_rows = [
        {"contract_address": "0xaabbccddeeff0011223344556677889900aabbcc", "event_name_raw": "Transfer(address", "event_params_raw": "address,uint256)"},
        {"chain": "ETHEREUM", "address": "0x1234567890abcdef"},
        {"chain": "ETHEREUM", "tx_hash": "0x96b4aca5d38bbdf39e667b3e74bcebaf464a0209d1f1e692d8b3220bcb6b7162", "expense_category": "sandwich"},
        {"account_id": "acct_123", "amount": 100.5},
        {"request": "list all chains"}
    ]
    print("--- Testing LLM Client (R6) ---")
    for i, row in enumerate(test_rows, 1):
        print(f"Test Case {i}:")
        result = clean_and_validate_api_call(row, debug=True)
        print(json.dumps(result, indent=2), "\n")
        if result:
            api_calls = generate_api_calls(row, debug=True)
            print(json.dumps(api_calls, indent=2), "\n")
