import csv
import logging
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MethodType(Enum):
    """Enum for supported API methods."""
    GET_TRANSACTION = "get_transaction"
    GET_RECEIPT = "get_receipt"

@dataclass
class ParsedRow:
    """Data class for parsed and cleaned CSV row data."""
    method: MethodType
    params: Dict[str, Any]
    raw_data: Dict[str, Any]
    row_number: int

class CSVParser:
    """Parser for CSV files containing blockchain transaction data."""
    
    REQUIRED_FIELDS = {
        "tx_link": str  # Changed from tx_hash to tx_link
    }
    
    OPTIONAL_FIELDS = {
        "Time": str,
        "purpose": str,
        "amount in ETH": float,
        "amount in USD": float
    }
    
    # Map of explorer domains to chain names
    CHAIN_MAP = {
        "etherscan.io": "ETHEREUM",
        "polygonscan.com": "POLYGON",
        "optimistic.etherscan.io": "OPTIMISM"
    }
    
    def __init__(self, file_path: str):
        """Initialize parser with CSV file path."""
        self.file_path = file_path
        self.rows: List[ParsedRow] = []
    
    def _extract_tx_hash_and_chain(self, tx_link: str) -> Tuple[Optional[str], str]:
        """Extract transaction hash and chain from tx_link."""
        if not tx_link:
            return None, "ETHEREUM"  # Default to Ethereum if no link
            
        try:
            # Parse URL
            parsed_url = urlparse(tx_link)
            domain = parsed_url.netloc
            
            # Determine chain from domain
            chain = next((chain for domain_key, chain in self.CHAIN_MAP.items() 
                         if domain_key in domain), "ETHEREUM")
            
            # Extract tx hash from path
            path = parsed_url.path
            tx_hash = path.split('/')[-1]
            
            # Validate tx hash format
            if not tx_hash or not tx_hash.startswith('0x') or len(tx_hash) != 66:
                return None, chain
                
            return tx_hash, chain
            
        except Exception as e:
            logger.warning(f"Error parsing tx_link: {e}")
            return None, "ETHEREUM"
    
    def _clean_value(self, value: str, field_type: type) -> Any:
        """Clean and convert field value to appropriate type."""
        if not value or value.strip() == "":
            return None
            
        try:
            if field_type == float:
                # Remove currency symbols and convert to float
                cleaned = value.replace("USD", "").replace("ETH", "").replace("$", "").strip()
                if cleaned:
                    return float(cleaned)
                return None
            elif field_type == str:
                return value.strip()
            else:
                return field_type(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid value '{value}' for type {field_type.__name__}: {e}")
            return None
    
    def _validate_row(self, row: Dict[str, str], row_num: int) -> bool:
        """Validate required fields in a row."""
        for field, field_type in self.REQUIRED_FIELDS.items():
            if field not in row:
                logger.error(f"Missing required field '{field}' in row {row_num}")
                return False
            if not isinstance(self._clean_value(row[field], field_type), field_type):
                logger.error(f"Invalid type for field '{field}' in row {row_num}")
                return False
        return True
    
    def _clean_row(self, row: Dict[str, str], row_num: int) -> Optional[Dict[str, Any]]:
        """Clean and convert row data to appropriate types."""
        cleaned = {}
        
        # Clean required fields
        for field, field_type in self.REQUIRED_FIELDS.items():
            value = self._clean_value(row[field], field_type)
            if value is None:
                return None
            cleaned[field] = value
        
        # Clean optional fields
        for field, field_type in self.OPTIONAL_FIELDS.items():
            if field in row:
                value = self._clean_value(row[field], field_type)
                if value is not None:
                    cleaned[field] = value
        
        return cleaned
    
    def _determine_method(self, row: Dict[str, Any]) -> MethodType:
        """Determine which API method to use for this row."""
        # For now, we'll always generate both transaction and receipt calls
        return MethodType.GET_TRANSACTION
    
    def parse(self) -> List[ParsedRow]:
        """Parse and clean CSV file, returning list of ParsedRow objects."""
        try:
            with open(self.file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    if not self._validate_row(row, row_num):
                        continue
                    
                    cleaned_row = self._clean_row(row, row_num)
                    if cleaned_row is None:
                        continue
                    
                    # Extract tx hash and chain from tx_link
                    tx_hash, chain = self._extract_tx_hash_and_chain(cleaned_row["tx_link"])
                    if not tx_hash:
                        logger.warning(f"Could not extract valid tx_hash from row {row_num}")
                        continue
                    
                    # Add chain to cleaned data
                    cleaned_row["chain"] = chain
                    
                    method = self._determine_method(cleaned_row)
                    parsed_row = ParsedRow(
                        method=method,
                        params={"tx_hash": tx_hash},
                        raw_data=cleaned_row,
                        row_number=row_num
                    )
                    self.rows.append(parsed_row)
            
            logger.info(f"Successfully parsed {len(self.rows)} rows from {self.file_path}")
            return self.rows
            
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            return [] 