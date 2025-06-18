import csv
import logging
from typing import List, Dict, Tuple, Optional, Any
from urllib.parse import urlparse, parse_qs
from enum import Enum
import re
from pathlib import Path

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
    """Extract transaction hash from various URL formats."""
    if not url:
        return None
        
    try:
        # Clean the URL first
        url = url.strip()
        
        # Handle direct tx_hash input
        if url.startswith('0x') and len(url) == 66:
            return url
            
        # Handle malformed URLs (missing protocol)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Handle URL formats
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Try to find tx_hash in path
        parts = path.split('/')
        for part in parts:
            # Clean the part and check if it's a valid hash
            part = part.strip()
            if part.startswith('0x') and len(part) == 66:
                return part
                
        # Try to find tx_hash in query parameters
        query = parse_qs(parsed.query)
        for param in query.values():
            for value in param:
                # Clean the value and check if it's a valid hash
                value = value.strip()
                if value.startswith('0x') and len(value) == 66:
                    return value
                    
        # Try to find tx_hash in the entire URL
        # This handles cases where the URL might be malformed but still contains a valid hash
        words = url.split()
        for word in words:
            word = word.strip()
            if word.startswith('0x') and len(word) == 66:
                return word
                    
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting tx_hash from URL: {e}")
        return None

def determine_function_type(row_data: Dict[str, Any]) -> FunctionType:
    """
    Determine the function type based on the presence of required fields.
    """
    # Check for tag_as_expense requirements
    has_tx_hash = bool(row_data.get('tx_hash'))
    has_purpose = bool(row_data.get('purpose') or row_data.get('expense_category'))
    has_amount = bool(row_data.get('amount in ETH') or row_data.get('amount in USD'))
    
    if has_tx_hash and (has_purpose or has_amount):
        logger.debug("Row matches tag_as_expense requirements")
        return FunctionType.TAG_AS_EXPENSE
    
    # Check for get_transaction requirements
    if has_tx_hash:
        logger.debug("Row matches get_transaction requirements")
        return FunctionType.GET_TRANSACTION
    
    # Default to get_transaction if no other type matches
    logger.debug("No specific function type matched, defaulting to get_transaction")
    return FunctionType.GET_TRANSACTION

def clean_and_classify_csv(file_path: str) -> Tuple[str, List[Dict]]:
    """
    Reads and cleans a CSV, and determines the API function to call for all rows.
    Returns (function_name, cleaned_rows)
    """
    cleaned_rows = []
    function_counts = {ft: 0 for ft in FunctionType}
    
    logger.info(f"Starting to process CSV file: {file_path}")
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        total_rows = 0
        skipped_rows = 0
        
        for row_num, row in enumerate(reader, 1):
            total_rows += 1
            try:
                logger.debug(f"Processing row {row_num}: {row}")
                cleaned = {}
                
                # Clean and convert values
                for k, v in row.items():
                    if v is None or v.strip() == "":
                        cleaned[k] = None
                    else:
                        val = v.strip()
                        # Convert amounts to float
                        if k.lower().startswith('amount'):
                            try:
                                # Handle various amount formats
                                val = val.replace('USD', '').replace('ETH', '').replace('$', '').strip()
                                # Remove any currency symbols and commas
                                val = ''.join(c for c in val if c.isdigit() or c == '.')
                                cleaned[k] = float(val) if val else None
                            except Exception as e:
                                logger.warning(f"Row {row_num}: Could not convert {k}='{v}' to float: {str(e)}")
                                cleaned[k] = None
                        else:
                            cleaned[k] = val
                
                logger.debug(f"Row {row_num} after cleaning: {cleaned}")
                
                # Extract tx_hash and chain from tx_link if present
                tx_hash = None
                chain = "ETHEREUM"
                
                if 'tx_link' in cleaned and cleaned['tx_link']:
                    logger.debug(f"Row {row_num}: Found tx_link: {cleaned['tx_link']}")
                    tx_hash = extract_tx_hash_from_url(cleaned['tx_link'])
                    if tx_hash:
                        logger.debug(f"Row {row_num}: Extracted tx_hash from tx_link: {tx_hash}")
                        cleaned['tx_hash'] = tx_hash
                        chain = detect_chain_from_url(cleaned['tx_link'])
                        cleaned['chain'] = chain
                    else:
                        logger.warning(f"Row {row_num}: Could not extract tx_hash from tx_link: {cleaned['tx_link']}")
                
                # If no tx_hash from tx_link, try to find it in other columns
                if not tx_hash:
                    logger.debug(f"Row {row_num}: Searching for tx_hash in other columns")
                    # Look for tx_hash in other columns
                    for col, val in cleaned.items():
                        if val and isinstance(val, str) and val.startswith('0x') and len(val) == 66:
                            tx_hash = val
                            cleaned['tx_hash'] = tx_hash
                            logger.debug(f"Row {row_num}: Found tx_hash in column {col}: {tx_hash}")
                            break
                
                # Skip rows without tx_hash
                if not tx_hash:
                    logger.warning(f"Row {row_num}: No valid tx_hash found in any column")
                    skipped_rows += 1
                    continue
                
                # Ensure chain is set
                cleaned['chain'] = chain
                
                # Set default purpose if missing
                if 'purpose' not in cleaned or not cleaned['purpose']:
                    cleaned['purpose'] = 'General'
                    logger.debug(f"Row {row_num}: Set default purpose to 'General'")
                
                # Map purpose to expense_category for tag_as_expense
                cleaned['expense_category'] = cleaned.get('purpose', 'General')
                
                # Determine function type for this row
                function_type = determine_function_type(cleaned)
                function_counts[function_type] += 1
                logger.debug(f"Row {row_num}: Determined function type: {function_type.value}")
                
                # Add the row to cleaned rows
                cleaned_rows.append(cleaned)
                logger.info(f"Row {row_num}: Successfully processed and added to cleaned rows")
                
            except Exception as e:
                logger.error(f"Error processing row {row_num}: {str(e)}")
                skipped_rows += 1
                continue
    
    # Log summary
    logger.info(f"CSV processing summary:")
    logger.info(f"Total rows processed: {total_rows}")
    logger.info(f"Rows skipped: {skipped_rows}")
    logger.info(f"Rows successfully processed: {len(cleaned_rows)}")
    logger.info(f"Function type counts: {function_counts}")
    
    # Choose the most common function type
    if cleaned_rows:
        most_common = max(function_counts.items(), key=lambda x: x[1])
        function_name = most_common[0].value
        logger.info(f"Selected function {function_name} based on {most_common[1]} matching rows")
    else:
        function_name = FunctionType.GET_TRANSACTION.value
        logger.warning("No valid rows found, defaulting to get_transaction")
    
    return function_name, cleaned_rows 