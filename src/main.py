import asyncio
import argparse
import json
from pathlib import Path
from typing import Dict, List, Union, Optional
import os
from dotenv import load_dotenv

from pipeline.extractor import extract_api_calls
from pipeline.processor import process_with_llm
from pipeline.router import route_api_calls
from utils.logger import (
    log_info, 
    log_error,
    log_extraction,
    log_processing,
    log_api_call
)

# Load environment variables
load_dotenv()

async def process_file(file_path: Union[str, Path], 
                      interactive: bool = False,
                      api_key: Optional[str] = None) -> None:
    """
    Process a single file through the pipeline.
    
    Args:
        file_path: Path to the input file
        interactive: Whether to run in interactive mode
        api_key: Optional API key for blockchain explorers
    """
    try:
        # Extract data from file
        extracted_data = extract_api_calls(file_path)
        log_extraction(str(file_path), {'count': len(extracted_data)})
        
        if interactive:
            log_info(f"Extracted {len(extracted_data)} items from {file_path}")
            
        # Process with LLM
        api_calls = await process_with_llm(extracted_data)
        log_processing(
            {'extracted_count': len(extracted_data)},
            {'api_calls_count': len(api_calls)}
        )
        
        if interactive:
            log_info(f"Generated {len(api_calls)} API calls")
            
        # Execute API calls
        results = await route_api_calls(
            api_calls,
            api_key=api_key,
            batch_mode=not interactive
        )
        
        if interactive:
            # Print results in a readable format
            for result in (results if isinstance(results, list) else [results]):
                if result['success']:
                    log_info(
                        f"Successfully executed {result['method']} API call\n"
                        f"Result: {json.dumps(result['result'], indent=2)}"
                    )
                else:
                    log_error(
                        f"Failed to execute {result['method']} API call\n"
                        f"Error: {result['error']}"
                    )
        else:
            # Log results without printing
            for result in (results if isinstance(results, list) else [results]):
                log_api_call(
                    method=result['method'],
                    params=result.get('params', {}),
                    response=result.get('result'),
                    error=result.get('error')
                )
                
    except Exception as e:
        log_error(f"Error processing file {file_path}: {str(e)}")
        if interactive:
            print(f"Error: {str(e)}")

async def process_directory(directory: Union[str, Path],
                          pattern: str = "*.csv",
                          interactive: bool = False,
                          api_key: Optional[str] = None) -> None:
    """
    Process all matching files in a directory.
    
    Args:
        directory: Directory path to process
        pattern: Glob pattern for matching files
        interactive: Whether to run in interactive mode
        api_key: Optional API key for blockchain explorers
    """
    directory = Path(directory)
    for file_path in directory.glob(pattern):
        if interactive:
            print(f"\nProcessing {file_path}...")
        await process_file(file_path, interactive, api_key)

def main():
    parser = argparse.ArgumentParser(
        description="Process CSV and text files to extract and execute blockchain API calls"
    )
    parser.add_argument(
        "path",
        help="Path to file or directory to process"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode with detailed output"
    )
    parser.add_argument(
        "--pattern",
        "-p",
        default="*.csv",
        help="File pattern to match when processing directories (default: *.csv)"
    )
    parser.add_argument(
        "--api-key",
        help="API key for blockchain explorers. Can also be set via BLOCKCHAIN_API_KEY env var"
    )
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv("BLOCKCHAIN_API_KEY")
    
    path = Path(args.path)
    if path.is_file():
        asyncio.run(process_file(path, args.interactive, api_key))
    elif path.is_dir():
        asyncio.run(process_directory(path, args.pattern, args.interactive, api_key))
    else:
        print(f"Error: {args.path} does not exist")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())