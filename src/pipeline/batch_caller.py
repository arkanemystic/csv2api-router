import logging
from typing import List, Dict, Any, Callable, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class CallResult:
    """Result of a single API call."""
    success: bool
    row_number: int
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

def for_loop_caller(
    cleaned_rows: List[Dict],
    api_function: Callable,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Tuple[List[CallResult], List[int]]:
    """
    Process a list of cleaned rows by calling the given API function on each row.
    
    Args:
        cleaned_rows: List of dictionaries containing cleaned row data
        api_function: Function to call for each row
        max_retries: Maximum number of retries for failed calls
        retry_delay: Base delay between retries (will be multiplied by retry number)
        
    Returns:
        Tuple of (list of CallResult objects, list of failed row numbers)
    """
    results = []
    failed_rows = []
    
    for row_num, row in enumerate(cleaned_rows, 1):
        result = None
        last_error = None
        
        # Try the call with retries
        for attempt in range(max_retries):
            try:
                # Call the API function with the row data
                data = api_function(**row)
                result = CallResult(
                    success=True,
                    row_number=row_num,
                    data=data
                )
                break
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    # Wait before retrying
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    # All retries failed
                    result = CallResult(
                        success=False,
                        row_number=row_num,
                        error=last_error
                    )
                    failed_rows.append(row_num)
        
        # Log the result
        if result:
            if result.success:
                logger.info(f"Row {row_num}: Successfully processed")
            else:
                logger.error(f"Row {row_num}: Failed after {max_retries} attempts. Error: {result.error}")
            results.append(result)
    
    # Log summary
    total_rows = len(cleaned_rows)
    successful_rows = len([r for r in results if r.success])
    logger.info(f"Processed {total_rows} rows: {successful_rows} successful, {len(failed_rows)} failed")
    
    return results, failed_rows

def get_successful_results(results: List[CallResult]) -> List[Any]:
    """Extract data from successful results."""
    return [r.data for r in results if r.success and r.data is not None]

def get_failed_results(results: List[CallResult]) -> List[CallResult]:
    """Get failed results with their errors."""
    return [r for r in results if not r.success] 