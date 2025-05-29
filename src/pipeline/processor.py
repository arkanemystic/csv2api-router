import os
from typing import Dict, List, Union
import logging
import json
from pathlib import Path
from .llm_client import generate_api_calls, SUPPORTED_APIS

class LLMProcessor:
    """Process extracted data using LLM to identify and structure API calls."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_apis = SUPPORTED_APIS  # Use the same API definitions as llm_client
    
    async def process_data(self, extracted_data: Union[Dict, List[Dict]]) -> List[Dict]:
        """Process extracted data using LLM to identify required API calls."""
        if isinstance(extracted_data, dict):
            extracted_data = [extracted_data]
            
        all_api_calls = []
        
        for data in extracted_data:
            try:
                tx_hash = data.get('tx_hash')
                chain = data.get('chain', 'ETHEREUM')
                
                if not tx_hash:
                    self.logger.warning("No transaction hash provided")
                    continue
                
                # Generate API calls with chain information
                result = generate_api_calls(tx_hash=tx_hash, chain=chain)
                
                if not result:
                    self.logger.error(f"Failed to generate API calls for tx_hash: {tx_hash}")
                    continue
                
                api_calls = result.get('api_calls', [])
                
                # Validate each API call
                validated_calls = []
                for call in api_calls:
                    try:
                        if not call.get('method'):
                            self.logger.error("Missing method in API call: %s", call)
                            continue
                            
                        if not self.validate_api_call(call):
                            self.logger.error("Invalid API call parameters: %s", call)
                            continue
                            
                        # Find API category
                        category = next((cat for cat, methods in self.supported_apis.items() 
                                       if call['method'] in methods), None)
                                       
                        if not category:
                            self.logger.error("Unsupported API method: %s", call['method'])
                            continue
                            
                        # Use chain from API call or fall back to data's chain
                        call_chain = call.get('chain') or chain
                        
                        # Update with category and ensure chain is set
                        call.update({
                            'category': category,
                            'chain': call_chain
                        })
                        validated_calls.append(call)
                        
                    except Exception as e:
                        self.logger.error(f"Error validating API call: {str(e)}")
                        continue
                
                all_api_calls.extend(validated_calls)
                
            except Exception as e:
                self.logger.error("Error processing data: %s", str(e))
        
        return all_api_calls

    def validate_api_call(self, api_call: Dict) -> bool:
        """Validate that an API call has all required parameters."""
        required_params = {
            'get_transaction': ['tx_hash'],
            'get_receipt': ['tx_hash'],
            'get_balance': ['address', 'token_address'],
            'get_transfers': ['address'],
            'get_abi': ['contract_address'],
            'get_events': ['contract_address', 'event_name']
        }
        
        method = api_call.get('method')
        params = api_call.get('params', {})
        
        if method not in required_params:
            return False
            
        return all(param in params for param in required_params[method])

# Helper function for external use
async def process_with_llm(extracted_data: Union[Dict, List[Dict]]) -> List[Dict]:
    """
    Process extracted data using LLM to identify and structure API calls.
    
    Args:
        extracted_data: Dictionary or list of dictionaries containing extracted data
        
    Returns:
        List of structured API calls
    """
    processor = LLMProcessor()
    return await processor.process_data(extracted_data)

if __name__ == "__main__":
    import asyncio
    
    # Example usage
    test_data = {
        "tx_hash": "0x123abc...",
        "chain": "ETHEREUM",
        "raw_text": "Check the transaction status and get the receipt"
    }
    
    async def test():
        result = await process_with_llm(test_data)
        print(json.dumps(result, indent=2))
        
    asyncio.run(test())