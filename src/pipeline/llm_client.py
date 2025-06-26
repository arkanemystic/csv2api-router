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
        
        if not tx_hash or not isinstance(tx_hash, str) or tx_hash.strip() == '' or tx_hash.strip().upper() in ['POLYGON', 'ETHEREUM', '[CHAIN]', '[CHAI}']:
            logger.error(f"No valid tx_hash found: {tx_hash}")
            return None
        
        # Extract chain
        chain = row.get('chain', 'ETHEREUM')
        if not chain or not isinstance(chain, str) or chain.strip() == '' or chain.strip().upper() in ['[CHAIN]', '[CHAI}']:
            logger.warning(f"Invalid or placeholder chain value: {chain}, defaulting to 'ETHEREUM'")
            chain = 'ETHEREUM'
        
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
        missing = [k for k, v in params.items() if not v or (isinstance(v, str) and v.strip() == '')]
        if missing:
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

def extract_csv_from_text_with_llm(raw_text: str, debug: bool = False) -> str:
    """
    Use the LLM to extract a CSV table from pasted or raw text.
    Returns the CSV as a string (including header row).
    """
    prompt = f"""
Given the following data, extract a valid CSV table with EXACTLY these three columns in this order:
1. chain (e.g., ETHEREUM, POLYGON)
2. tx_hash (the transaction hash)
3. expense_category (the purpose or category of the expense)

IMPORTANT CSV FORMATTING RULES:
1. Output ONLY these three columns, no extra columns
2. Each row MUST have exactly three values
3. Use comma (,) as the delimiter
4. Do not include any blank lines
5. First line must be the header: chain,tx_hash,expense_category
6. Every line after must have exactly two commas (three fields)
7. Do not include any quotes unless the value contains a comma

Example of correct format:
chain,tx_hash,expense_category
ETHEREUM,0x123...,office supplies
POLYGON,0x456...,software license

Input Data:
{raw_text}

Output the CSV data only, no explanations or markdown."""

    if debug:
        logger.info(f"LLM CSV Extraction Prompt:\\n{prompt}")
    # Use the same LLM call logic as _call_llm or similar
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmpfile:
        tmpfile.write(prompt)
        tmpfile.flush()
        command = [
            "ollama", "run", "custom-mistral:instruct"
        ]
        process = subprocess.Popen(
            command,
            stdin=open(tmpfile.name, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=120)
    if debug:
        logger.info(f"LLM STDOUT (CSV Extraction): {stdout}")
    if stderr:
        logger.error(f"LLM STDERR (CSV Extraction): {stderr}")
    if process.returncode != 0:
        logger.error(f"LLM process error (CSV Extraction). Return code: {process.returncode}. Stderr: {stderr.strip()}")
    # Remove markdown code block markers if present
    csv_str = re.sub(r'```csv|```', '', stdout)
    return csv_str.strip()

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
