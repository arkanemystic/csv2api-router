import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def tag_as_expense(
    tx_hash: str,
    purpose: Optional[str] = None,
    amount_in_eth: Optional[float] = None,
    amount_in_usd: Optional[float] = None,
    chain: str = "ETHEREUM",
    **kwargs
) -> Dict[str, Any]:
    """
    Tag a transaction as an expense.
    
    Args:
        tx_hash: Transaction hash
        purpose: Purpose of the expense
        amount_in_eth: Amount in ETH
        amount_in_usd: Amount in USD
        chain: Blockchain network
        **kwargs: Additional fields from CSV
        
    Returns:
        Dict containing the processed data
    """
    # Validate required fields
    if not tx_hash:
        raise ValueError("Transaction hash is required")
    
    # Process the data
    result = {
        "method": "tag_as_expense",
        "params": {
            "tx_hash": tx_hash,
            "chain": chain,
            "purpose": purpose or "Unspecified",
            "amount_in_eth": amount_in_eth,
            "amount_in_usd": amount_in_usd
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Log the API call
    logger.info(f"Generated API call for {tx_hash}:")
    logger.info(json.dumps(result, indent=2))
    
    return result

def get_transaction(
    tx_hash: str,
    chain: str = "ETHEREUM",
    **kwargs
) -> Dict[str, Any]:
    """
    Get transaction details.
    
    Args:
        tx_hash: Transaction hash
        chain: Blockchain network
        **kwargs: Additional fields from CSV
        
    Returns:
        Dict containing transaction details
    """
    # Validate required fields
    if not tx_hash:
        raise ValueError("Transaction hash is required")
    
    # Process the data
    result = {
        "method": "get_transaction",
        "params": {
            "tx_hash": tx_hash,
            "chain": chain
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Log the API call
    logger.info(f"Generated API call for {tx_hash}:")
    logger.info(json.dumps(result, indent=2))
    
    return result

def get_receipt(
    tx_hash: str,
    chain: str = "ETHEREUM",
    **kwargs
) -> Dict[str, Any]:
    """
    Get transaction receipt.
    
    Args:
        tx_hash: Transaction hash
        chain: Blockchain network
        **kwargs: Additional fields from CSV
        
    Returns:
        Dict containing receipt request
    """
    # Validate required fields
    if not tx_hash:
        raise ValueError("Transaction hash is required")
    
    # Process the data
    result = {
        "method": "get_receipt",
        "params": {
            "tx_hash": tx_hash,
            "chain": chain
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Log the API call
    logger.info(f"Generated API call for {tx_hash}:")
    logger.info(json.dumps(result, indent=2))
    
    return result 