import subprocess
import json
import re
import time
import logging
import os
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_APIS = {
    "get_transaction": {
        "params": ["tx_hash"]
    },
    "get_receipt": {
        "params": ["tx_hash"]
    }
}

def generate_single_api_call(method: str, tx_hash: str, chain: str, debug: bool = False) -> dict:
    """Generate a single API call using Ollama."""
    prompt = f"""<system>You are a JSON API call generator. Output only valid JSON objects, no explanations or markdown.</system>
<user>Generate a JSON object for a blockchain API call with method "{method}" and transaction hash "{tx_hash}" for {chain} chain. The JSON should have a "method" field and a "params" object containing the tx_hash.</user>"""
    
    try:
        # Call Ollama CLI
        result = subprocess.run(
            ["ollama", "run", "codellama:latest"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if debug:
            logger.info(f"Raw output: {result.stdout}")
        
        # Extract JSON from output
        json_str = result.stdout.strip()
        # Remove any markdown code block markers
        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
        
        # Find the first complete JSON object
        first_brace = json_str.find('{')
        if first_brace == -1:
            logger.error("No JSON object found in output")
            return None
            
        # Find matching closing brace
        brace_count = 0
        for i in range(first_brace, len(json_str)):
            if json_str[i] == '{':
                brace_count += 1
            elif json_str[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_str = json_str[first_brace:i+1]
                    break
        else:
            logger.error("Could not find complete JSON object")
            return None
        
        if debug:
            logger.info(f"Cleaned JSON string: {json_str}")
        
        # Parse JSON
        api_call = json.loads(json_str)
        
        # Validate structure
        if not isinstance(api_call, dict):
            raise ValueError("API call must be a JSON object")
        if "method" not in api_call:
            raise ValueError("API call must include 'method' field")
        if "params" not in api_call:
            raise ValueError("API call must include 'params' field")
        if not isinstance(api_call["params"], dict):
            raise ValueError("params must be a JSON object")
            
        # Ensure tx_hash is in params
        if "tx_hash" not in api_call["params"]:
            # Try to find tx_hash in any of the common parameter names
            for key in ["tx_hash", "transactionHash", "txn_hash", "hash", "txnHash"]:
                if key in api_call["params"]:
                    api_call["params"]["tx_hash"] = api_call["params"][key]
                    break
            else:
                raise ValueError("params must include 'tx_hash' field")
        
        return api_call
        
    except subprocess.TimeoutExpired:
        logger.error("Ollama command timed out")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating API call: {e}")
        return None

def call_ollama(tx_hash: str, chain: str = "ETHEREUM", debug: bool = False) -> List[dict]:
    """Generate blockchain API calls for a transaction hash."""
    if not tx_hash or not isinstance(tx_hash, str):
        logger.error("Invalid transaction hash")
        return []
    
    if not tx_hash.startswith("0x"):
        logger.error("Transaction hash must start with '0x'")
        return []
    
    api_calls = []
    max_retries = 3
    base_delay = 2
    
    for method in ["get_transaction", "get_receipt"]:
        for attempt in range(max_retries):
            try:
                api_call = generate_single_api_call(method, tx_hash, chain, debug)
                if api_call:
                    api_calls.append(api_call)
                    break
                else:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Failed to generate API call for method {method} after {max_retries} attempts")
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
    
    return api_calls

def generate_api_calls(tx_hash: str, chain: str = "ETHEREUM", debug: bool = False) -> List[dict]:
    """Wrapper function to generate API calls."""
    return call_ollama(tx_hash, chain, debug)

if __name__ == "__main__":
    # Test the function
    test_hash = "0x1234567890123456789012345678901234567890123456789012345678901234"
    result = call_ollama(test_hash, debug=True)
    print(json.dumps(result, indent=2))
