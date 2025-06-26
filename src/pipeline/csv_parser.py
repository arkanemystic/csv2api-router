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
    GET_EVENTS = "get_events"

@dataclass
class ParsedRow:
    """Data class for parsed and cleaned CSV row data."""
    method: MethodType
    params: Dict[str, Any]
    raw_data: Dict[str, Any]
    row_number: int

class CSVParser:
    """Parser for CSV files containing blockchain contract and event data."""
    
    # Fields for contract and event data
    COLUMN_MAPPINGS = {
        "contract_address": ["contract_address", "address", "contract"],
        "event_name_raw": ["event thingy", "event_name", "event", "event_signature_raw"],
        "event_params_raw": ["extra_info", "params", "parameters", "event_params_hint"]
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
        self.actual_columns: Dict[str, str] = {}
    
    def _map_columns(self, headers: List[str]):
        """Map CSV headers to our expected column names."""
        self.actual_columns = {}
        for expected, possible_names in self.COLUMN_MAPPINGS.items():
            found = next((h for h in headers if h.lower() in [pn.lower() for pn in possible_names]), None)
            if found:
                self.actual_columns[expected] = found
                logger.info(f"Mapped canonical key '{expected}' to CSV column '{found}'")
            else:
                logger.warning(f"Could not find CSV column mapping for canonical key '{expected}'")
    
    def _get_value_from_csv_row(self, csv_row_dict: Dict[str, str], canonical_key: str) -> Optional[str]:
        """Get a value from a row using our column mappings."""
        actual_col_name = self.actual_columns.get(canonical_key)
        if actual_col_name:
            return csv_row_dict.get(actual_col_name)
        return None
    
    def _get_mapped_raw_data(self, csv_row_dict: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """
        Creates a dictionary from the CSV row using canonical keys.
        Values are raw strings from the CSV, stripped. This becomes ParsedRow.raw_data.
        """
        mapped_data = {'csv_row_number': row_num}
        for canonical_key in self.COLUMN_MAPPINGS.keys():
            value = self._get_value_from_csv_row(csv_row_dict, canonical_key)
            mapped_data[canonical_key] = str(value).strip() if value is not None else None
        
        logger.debug(f"Row {row_num}: Mapped raw data for LLM: {mapped_data}")
        return mapped_data
    
    def parse(self) -> List[ParsedRow]:
        """Parse and clean CSV file, returning list of ParsedRow objects."""
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f: # utf-8-sig for potential BOM
                first_line = f.readline().strip()
                f.seek(0)
                delimiter = '\t' if '\t' in first_line and ',' not in first_line else ','
                
                reader = csv.DictReader(f, delimiter=delimiter)
                if not reader.fieldnames:
                    logger.error("CSV file appears to be empty or has no headers.")
                    return []
                
                self._map_columns(reader.fieldnames)
                logger.info(f"CSV headers mapped: {self.actual_columns}")
                
                for row_num, csv_row_dict in enumerate(reader, 1):
                    try:
                        logger.debug(f"Processing CSV row {row_num}: {csv_row_dict}")
                        
                        # Create the raw_data payload for the LLM
                        raw_data_for_llm = self._get_mapped_raw_data(csv_row_dict, row_num)

                        # Basic check: if no mapped data was found at all, it's likely an empty/bad row
                        if all(v is None for k, v in raw_data_for_llm.items() if k != 'csv_row_number'):
                            logger.warning(f"Row {row_num} appears empty after mapping, skipping: {csv_row_dict}")
                            continue
                            
                        # The 'params' for ParsedRow can be simple, as llm_client will use raw_data_for_llm
                        # These params are more like hints or quick access if needed before LLM.
                        parsed_row_params = {
                            "contract_address_hint": raw_data_for_llm.get("contract_address"),
                            "event_signature_raw_hint": raw_data_for_llm.get("event_name_raw"),
                            "event_params_raw_hint": raw_data_for_llm.get("event_params_raw")
                        }

                        parsed_row = ParsedRow(
                            method=MethodType.GET_EVENTS,
                            params=parsed_row_params,
                            raw_data=raw_data_for_llm, # Crucial: this goes to the LLM
                            row_number=row_num
                        )
                        self.rows.append(parsed_row)
                        logger.info(f"Successfully created ParsedRow for row {row_num} (contract hint: {raw_data_for_llm.get('contract_address')})")
                        
                    except Exception as e:
                        logger.error(f"Error processing CSV row {row_num}: {str(e)}. Row data: {csv_row_dict}", exc_info=True)
                        continue
            
            logger.info(f"CSVParser: Successfully created {len(self.rows)} ParsedRow objects from {self.file_path}")
            return self.rows
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.file_path}")
            return []
        except Exception as e:
            logger.error(f"Error parsing CSV file {self.file_path}: {e}", exc_info=True)
            return [] 

    def parse_from_dicts(self, list_of_dicts: List[Dict[str, Any]]) -> List[ParsedRow]:
        """Parse already-cleaned data (list of dicts) into ParsedRow objects."""
        self.rows = []
        if not list_of_dicts:
            return []
        headers: List[str] = list(list_of_dicts[0].keys())
        self._map_columns(headers)
        for row_num, row_dict in enumerate(list_of_dicts, 1):
            raw_data_for_llm = self._get_mapped_raw_data(row_dict, row_num)
            if all(v is None for k, v in raw_data_for_llm.items() if k != 'csv_row_number'):
                continue
            parsed_row_params = {
                "contract_address_hint": raw_data_for_llm.get("contract_address"),
                "event_signature_raw_hint": raw_data_for_llm.get("event_name_raw"),
                "event_params_raw_hint": raw_data_for_llm.get("event_params_raw")
            }
            parsed_row = ParsedRow(
                method=MethodType.GET_EVENTS,
                params=parsed_row_params,
                raw_data=raw_data_for_llm,
                row_number=row_num
            )
            self.rows.append(parsed_row)
        return self.rows 