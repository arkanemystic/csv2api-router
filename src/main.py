import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from src.pipeline.csv_cleaner import clean_and_classify_csv
from src.pipeline.batch_caller import for_loop_caller, get_successful_results
from src.pipeline.api_functions import tag_as_expense, get_transaction, get_receipt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Map of function names to actual functions
API_FUNCTIONS = {
    'tag_as_expense': tag_as_expense,
    'get_transaction': get_transaction,
    'get_receipt': get_receipt
}

def main():
    parser = argparse.ArgumentParser(description='Process CSV file and generate API calls')
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path')
    parser.add_argument('-w', '--workers', type=int, default=4, help='Number of worker threads')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    try:
        # Step 1: Clean and classify CSV
        function_name, cleaned_rows = clean_and_classify_csv(str(input_path))
        logger.info(f"Classified CSV as {function_name} with {len(cleaned_rows)} rows")
        
        # Get the appropriate API function
        api_function = API_FUNCTIONS.get(function_name)
        if not api_function:
            logger.error(f"Unknown function: {function_name}")
            return
        
        # Step 2: Process rows using the batch caller
        results, failed_rows = for_loop_caller(
            cleaned_rows=cleaned_rows,
            api_function=api_function,
            max_retries=3
        )
        
        # Get successful results
        successful_results = get_successful_results(results)
        
        # Log summary
        if successful_results:
            logger.info(f"Successfully processed {len(successful_results)} rows")
            logger.info(f"Failed rows: {failed_rows}")
            logger.info({
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "processing",
                "status": "success",
                "details": {
                    "input": {"extracted_count": len(cleaned_rows)},
                    "output": {"processed_count": len(successful_results)},
                    "failed_rows": failed_rows
                }
            })
        else:
            logger.info("No rows were successfully processed")
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return

if __name__ == "__main__":
    main()