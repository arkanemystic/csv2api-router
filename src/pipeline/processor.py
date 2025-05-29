import os
from typing import Dict, List, Union
import aiohttp
import logging
import json
from pathlib import Path

class LLMProcessor:
    """Process extracted data using LLM to identify and structure API calls."""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.logger = logging.getLogger(__name__)
        self.ollama_base_url = ollama_base_url
        self.supported_apis = {
            'transaction': ['get_transaction', 'get_receipt'],
            'token': ['get_balance', 'get_transfers'],
            'contract': ['get_abi', 'get_events']
        }
    
    def _create_prompt(self, data: Dict) -> str:
        """Create a prompt for the LLM based on the input data."""
        tx_hash = data.get('tx_hash')
        if not tx_hash:
            return '''{"api_calls": []}'''
            
        prompt = f"""Given this transaction hash: {tx_hash}

Generate exactly these two API calls using that exact hash:
1. get_transaction call to fetch transaction details
2. get_receipt call to get transaction status

Return this exact JSON format:
{{
  "api_calls": [
    {{
      "method": "get_transaction",
      "params": {{
        "tx_hash": "{tx_hash}"
      }}
    }},
    {{
      "method": "get_receipt",
      "params": {{
        "tx_hash": "{tx_hash}"
      }}
    }}
  ]
}}

Return only the JSON above. No other text. Use the exact hash shown."""
        
        return prompt
    
    async def _call_ollama(self, prompt: str) -> str:
        """Make API call to local Ollama instance."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-r1",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Use 0 temperature for deterministic responses
                    "num_predict": 512   # Ensure we get enough tokens for the response
                }
            }
            
            try:
                async with session.post(f"{self.ollama_base_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        raise Exception(f"Ollama API returned status {response.status}")
                    
                    result = await response.json()
                    return result["response"]
                    
            except Exception as e:
                self.logger.error(f"Error calling Ollama API: {e}")
                raise
    
    async def process_data(self, extracted_data: Union[Dict, List[Dict]]) -> List[Dict]:
        """
        Process extracted data using LLM to identify required API calls.
        
        Args:
            extracted_data: Dictionary or list of dictionaries containing extracted data
            
        Returns:
            List of identified API calls with parameters
        """
        if isinstance(extracted_data, dict):
            extracted_data = [extracted_data]
            
        all_api_calls = []
        
        for data in extracted_data:
            try:
                prompt = self._create_prompt(data)
                self.logger.info(f"DEBUG: LLM Prompt:\n{prompt}")
                
                # Call local Ollama instance
                response_text = await self._call_ollama(prompt)
                self.logger.info(f"DEBUG: LLM Response:\n{response_text}")
                
                # Parse the response
                try:
                    # Try to find JSON in the response
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        result = json.loads(json_str)
                    else:
                        self.logger.error(f"No JSON found in LLM response: {response_text}")
                        raise json.JSONDecodeError("No JSON found in response", response_text, 0)
                    
                    api_calls = result.get('api_calls', [])
                    self.logger.info(f"DEBUG: Parsed API calls: {json.dumps(api_calls, indent=2)}")
                    
                    # Validate and filter API calls
                    validated_calls = []
                    for call in api_calls:
                        method = call.get('method')
                        if not method:
                            self.logger.error(f"Missing method in API call: {call}")
                            continue
                            
                        if not self.validate_api_call(call):
                            self.logger.error(f"Invalid API call parameters: {call}")
                            continue
                            
                        category = next((cat for cat, methods in self.supported_apis.items() 
                                      if method in methods), None)
                        
                        if category:
                            # Add metadata to the API call
                            call['category'] = category
                            call['chain'] = data.get('chain', 'ETHEREUM')
                            validated_calls.append(call)
                        else:
                            self.logger.error(f"Unsupported API method identified: {method}")
                    
                    all_api_calls.extend(validated_calls)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse LLM response as JSON: {response_text}")
                    self.logger.error(f"JSON Error: {str(e)}")
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error processing data with LLM: {str(e)}")
                continue
        
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

async def process_with_llm(extracted_data: Union[Dict, List[Dict]], 
                         ollama_base_url: str = "http://localhost:11434") -> List[Dict]:
    """
    Process extracted data using LLM to identify and structure API calls.
    
    Args:
        extracted_data: Dictionary or list of dictionaries containing extracted data
        ollama_base_url: URL of the Ollama API server (default: http://localhost:11434)
        
    Returns:
        List of structured API calls
    """
    processor = LLMProcessor(ollama_base_url=ollama_base_url)
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