import csv
import logging
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)

class FunctionType(Enum):
    """Enum for supported API functions."""
    TAG_AS_EXPENSE = 'tag_as_expense'
    GET_TRANSACTION = 'get_transaction'
    GET_RECEIPT = 'get_receipt'

# Map of explorer domains to chain names
CHAIN_MAP = {
    "etherscan.io": "ETHEREUM",
    "polygonscan.com": "POLYGON",
    "optimistic.etherscan.io": "OPTIMISM",
    "arbiscan.io": "ARBITRUM",
    "basescan.org": "BASE"
}

def detect_chain_from_url(url: str) -> str:
    """Detect blockchain chain from explorer URL."""
    if not url:
        return "ETHEREUM"  # Default to Ethereum
        
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Find matching chain
        for domain_key, chain in CHAIN_MAP.items():
            if domain_key in domain:
                return chain
                
        return "ETHEREUM"  # Default if no match
    except Exception as e:
        logger.warning(f"Error parsing URL {url}: {e}")
        return "ETHEREUM"

def extract_tx_hash_from_url(url: str) -> Optional[str]:
    """Extract transaction hash from explorer URL."""
    if not url:
        return None
        
    try:
        # Split URL and find the last part that starts with 0x
        parts = url.split('/')
        tx_hash = next((p for p in parts if p.startswith('0x')), None)
        
        # Validate hash format
        if tx_hash and len(tx_hash) == 66:  # 0x + 64 hex chars
            return tx_hash
        return None
    except Exception as e:
        logger.warning(f"Error extracting tx_hash from {url}: {e}")
        return None

def determine_function_type(row: Dict) -> FunctionType:
    """
    Determine which function to use based on row contents.
    Uses heuristics to decide without LLM.
    """
    # If row has purpose and amount fields, it's likely an expense
    if 'purpose' in row and row['purpose'] and any(k.startswith('amount') for k in row.keys()):
        return FunctionType.TAG_AS_EXPENSE
        
    # If row has tx_hash but no purpose/amount, get transaction details
    if 'tx_hash' in row and row['tx_hash']:
        return FunctionType.GET_TRANSACTION
        
    # Default to getting transaction details
    return FunctionType.GET_TRANSACTION

def clean_and_classify_csv(file_path: str) -> Tuple[str, List[Dict]]:
    """
    Reads and cleans a CSV, and determines the API function to call for all rows.
    Returns (function_name, cleaned_rows)
    """
    cleaned_rows = []
    function_counts = {ft: 0 for ft in FunctionType}
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, 1):
            cleaned = {}
            
            # Clean and convert values
            for k, v in row.items():
                if v is None:
                    cleaned[k] = None
                else:
                    val = v.strip()
                    # Convert amounts to float
                    if k.lower().startswith('amount'):
                        try:
                            val = val.replace('$', '').replace('USD', '').replace('ETH', '').strip()
                            cleaned[k] = float(val) if val else None
                        except Exception:
                            logger.warning(f"Row {row_num}: Could not convert {k}='{v}' to float")
                            cleaned[k] = None
                    else:
                        cleaned[k] = val if val else None
            
            # Extract tx_hash and chain from tx_link if present
            if 'tx_link' in cleaned and cleaned['tx_link']:
                tx_hash = extract_tx_hash_from_url(cleaned['tx_link'])
                if tx_hash:
                    cleaned['tx_hash'] = tx_hash
                    cleaned['chain'] = detect_chain_from_url(cleaned['tx_link'])
            
            # Skip rows without tx_hash
            if 'tx_hash' not in cleaned or not cleaned['tx_hash']:
                logger.warning(f"Row {row_num}: No valid tx_hash found")
                continue
                
            # Determine function type for this row
            function_type = determine_function_type(cleaned)
            function_counts[function_type] += 1
            
            cleaned_rows.append(cleaned)
    
    # Choose the most common function type
    if cleaned_rows:
        most_common = max(function_counts.items(), key=lambda x: x[1])
        function_name = most_common[0].value
        logger.info(f"Selected function {function_name} based on {most_common[1]} matching rows")
    else:
        function_name = FunctionType.GET_TRANSACTION.value
        logger.warning("No valid rows found, defaulting to get_transaction")
    
    return function_name, cleaned_rows 