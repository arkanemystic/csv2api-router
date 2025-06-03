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

def generate_api_calls_from_prompt_and_csv(prompt: str, csv_data: list, debug: bool = False):
    """
    Use the LLM to infer the correct API function and produce clean, structured rows from a messy CSV and a user prompt.
    Returns a tuple: (function_name, cleaned_rows)
    """
    import subprocess
    import json
    import re
    # Prepare a prompt for the LLM
    system_prompt = (
        "You are a smart API assistant. "
        "Given a user instruction and a list of messy CSV rows, "
        "output a JSON object with two fields: 'function' (the function name to call, e.g. 'tag_as_expense') "
        "and 'rows' (a list of cleaned dicts, one per row, with keys matching the function arguments). "
        "Infer the correct function and map/clean the columns as needed. Output only valid JSON, no explanations."
    )
    user_prompt = f"""Instruction: {prompt}\nCSV Data (as JSON list):\n{json.dumps(csv_data, indent=2)}"""
    full_prompt = f"<system>{system_prompt}</system>\n<user>{user_prompt}</user>"
    try:
        result = subprocess.run(
            ["ollama", "run", "codellama:latest"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        if debug:
            logger.info(f"Raw LLM output: {result.stdout}")
        # Remove markdown/code block markers
        json_str = result.stdout.strip()
        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
        # Find the first complete JSON object
        first_brace = json_str.find('{')
        if first_brace == -1:
            logger.error("No JSON object found in LLM output")
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
            logger.error("Could not find complete JSON object in LLM output")
            return None
        if debug:
            logger.info(f"Cleaned LLM JSON string: {json_str}")
        # Parse JSON
        obj = json.loads(json_str)
        if not isinstance(obj, dict) or 'function' not in obj or 'rows' not in obj:
            logger.error("LLM output missing 'function' or 'rows' fields")
            return None
        function_name = obj['function']
        cleaned_rows = obj['rows']
        return (function_name, cleaned_rows)
    except subprocess.TimeoutExpired:
        logger.error("Ollama command timed out for LLM CSV cleaning")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in LLM CSV cleaning: {e}")
        return None

def generate_api_call_list_from_prompt_and_csv(prompt: str, csv_data: list, debug: bool = False):
    """
    Use the LLM to infer a list of API calls from a prompt and messy CSV.
    Returns a list of dicts: [{function: ..., params: {...}}, ...]
    """
    import subprocess
    import json
    import re
    system_prompt = (
        "You are a smart API assistant. "
        "Given a user instruction and a list of messy CSV rows, output a JSON array. "
        "Each item should be an API call: {'function': <function_name>, 'params': {...}}. "
        "For each row: "
        "- If the row has a valid contract address (42 chars, starts with 0x, hex), call 'get_abi' with 'contract_address'. "
        "- If the row has a valid transaction hash (66 chars, starts with 0x, hex), call 'get_receipt' with 'tx_hash'. "
        "- Only call 'get_events' if the user prompt specifically requests event logs and the row has both a valid contract address and an event signature. "
        "- Ignore rows with missing, empty, or invalid hashes/addresses. "
        "Do NOT call get_events unless the user prompt specifically requests event logs for those contracts and events. "
        "Example input:\n"
        "[{'contract_address': '0xabc...', 'event thingy': 'Transfer(address,uint256)'}, ...]\n"
        "Example output:\n"
        "[{'function': 'get_abi', 'params': {'contract_address': '0xabc...'}}]\n"
        "Output only valid JSON, no explanations."
    )
    user_prompt = f"""Instruction: {prompt}\nCSV Data (as JSON list):\n{json.dumps(csv_data, indent=2)}"""
    full_prompt = f"<system>{system_prompt}</system>\n<user>{user_prompt}</user>"
    try:
        result = subprocess.run(
            ["ollama", "run", "codellama:latest"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=90
        )
        if debug:
            logger.info(f"Raw LLM output: {result.stdout}")
        # Log full LLM output for debugging
        try:
            with open("logs/csv2api_llm_output.log", "a") as f:
                f.write(f"\n---\nPrompt:\n{full_prompt}\nOutput:\n{result.stdout}\n---\n")
        except Exception as log_exc:
            logger.warning(f"Failed to write LLM output log: {log_exc}")
        json_str = result.stdout.strip()
        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
        # Find the first complete JSON array
        first_bracket = json_str.find('[')
        if first_bracket == -1:
            logger.error("No JSON array found in LLM output")
            return None, "No JSON array found in LLM output. Raw output: " + json_str
        # Find matching closing bracket
        bracket_count = 0
        for i in range(first_bracket, len(json_str)):
            if json_str[i] == '[':
                bracket_count += 1
            elif json_str[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    json_str = json_str[first_bracket:i+1]
                    break
        else:
            logger.error("Could not find complete JSON array in LLM output")
            return None, "Could not find complete JSON array in LLM output. Raw output: " + json_str
        if debug:
            logger.info(f"Cleaned LLM JSON string: {json_str}")
        try:
            api_calls = json.loads(json_str)
        except Exception as e:
            # Try to fix single-quoted dicts to valid JSON
            import ast
            try:
                # Use ast.literal_eval to parse Python dict/list safely
                api_calls = ast.literal_eval(json_str)
                # Convert back to JSON string and parse to ensure all keys/values are valid JSON
                api_calls = json.loads(json.dumps(api_calls))
                logger.warning("LLM output was not valid JSON, but was parsed as Python and converted to JSON.")
            except Exception as e2:
                logger.error(f"Failed to parse LLM JSON: {e2}")
                return None, f"Failed to parse LLM JSON: {e2}. Raw output: {json_str}"
        if not isinstance(api_calls, list):
            logger.error("LLM output is not a list")
            return None, "LLM output is not a list. Raw output: " + str(api_calls)
        # Validate each item is a dict with 'function' and 'params', try to coerce string items
        valid_api_calls = []
        errors = []
        for idx, item in enumerate(api_calls):
            if isinstance(item, dict):
                if 'function' in item and 'params' in item:
                    valid_api_calls.append(item)
                else:
                    msg = f"API call at index {idx} missing 'function' or 'params': {item}"
                    logger.error(msg)
                    errors.append(msg)
            elif isinstance(item, str):
                # Try to coerce string to dict
                msg = f"API call at index {idx} is a string: {item}. Attempting to coerce."
                logger.warning(msg)
                errors.append(msg)
                valid_api_calls.append({"function": item, "params": {}})
            else:
                msg = f"API call at index {idx} is not a dict or string: {item}"
                logger.error(msg)
                errors.append(msg)
        if not valid_api_calls:
            logger.error("No valid API call dicts found in LLM output")
            return None, "No valid API call dicts found in LLM output. Errors: " + "; ".join(errors)
        if errors:
            return valid_api_calls, "Some API calls were malformed and coerced/skipped. Errors: " + "; ".join(errors)
        return valid_api_calls, None
    except subprocess.TimeoutExpired:
        logger.error("Ollama command timed out for LLM API call list")
        return None, "Ollama command timed out for LLM API call list"
    except Exception as e:
        logger.error(f"Error in LLM API call list: {e}")
        return None, f"Error in LLM API call list: {e}"

if __name__ == "__main__":
    # Test the function
    test_hash = "0x1234567890123456789012345678901234567890123456789012345678901234"
    result = call_ollama(test_hash, debug=True)
    print(json.dumps(result, indent=2))
