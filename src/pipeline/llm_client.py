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
    row_num_info = row.get('csv_row_number', 'N/A')
    logger.info(f"LLM_CLIENT_R6: Attempting to extract API call for row {row_num_info} with input: {row}")

    # Extract input transaction hash for validation
    input_tx_hash = row.get('tx_hash')
    if not input_tx_hash and 'tx_link' in row:
        input_tx_hash = row['tx_link'].split('/')[-1]

    # Extract chain information
    chain = row.get('chain', 'ETHEREUM')  # Default to ETHEREUM if not specified
    
    # Check for explicit request in the row data
    request = row.get('request', '').lower()
    
    # Determine API based on request first, then fall back to data structure
    api_method = None
    params = {}
    
    if 'get receipt' in request or 'fetch receipt' in request:
        api_method = 'get_receipt'
        params = {'chain': chain, 'tx_hash': input_tx_hash}
    elif 'get transaction' in request or 'fetch transaction' in request:
        api_method = 'get_transaction'
        params = {'chain': chain, 'tx_hash': input_tx_hash}
    elif 'tag expense' in request or 'mark expense' in request:
        api_method = 'tag_as_expense'
        params = {
            'chain': chain,
            'tx_hash': input_tx_hash,
            'expense_category': row.get('purpose', 'general')
        }
    elif 'list chains' in request:
        api_method = 'list_chains'
        params = {}
    elif all(key in row for key in ['account_id', 'amount']):
        api_method = 'fill_account_by'
        params = {
            'account_id': row['account_id'],
            'amount': row['amount']
        }
    else:
        # Default behavior based on available data
        if input_tx_hash:
            api_method = 'get_receipt'  # Default to get_receipt when no specific request
            params = {'chain': chain, 'tx_hash': input_tx_hash}

    if not api_method or not params:
        logger.error(f"LLM_CLIENT_R6: Could not determine API method for row {row_num_info}")
        return None

    return {
        "api": api_method,
        "params": params
    }

def generate_api_calls(row_data: Dict[str, Any], debug: bool = False) -> List[Dict[str, Any]]:
    try:
        cleaned_data = clean_and_validate_api_call(row_data, debug)
        if not cleaned_data:
            return []
        api_call = {
            "method": cleaned_data["api"],
            "params": cleaned_data["params"]
        }
        logger.info(f"Generated API call for {cleaned_data['api']}")
        return [api_call]
    except Exception as e:
        logger.error(f"Error generating API calls: {e}")
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
