import logging
from typing import List, Dict, Any, Callable, TypeVar, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class ExecutionResult:
    """Data class for execution results."""
    success: bool
    data: Optional[R]
    error: Optional[str]
    row_number: int
    timestamp: datetime

class BatchExecutor:
    """Utility for executing functions on batches of data with error handling."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize executor with number of worker threads."""
        self.max_workers = max_workers
    
    def _execute_single(
        self,
        func: Callable[[T], R],
        data: T,
        row_number: int
    ) -> ExecutionResult:
        """Execute a single function call with error handling."""
        try:
            result = func(data)
            return ExecutionResult(
                success=True,
                data=result,
                error=None,
                row_number=row_number,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error processing row {row_number}: {str(e)}")
            return ExecutionResult(
                success=False,
                data=None,
                error=str(e),
                row_number=row_number,
                timestamp=datetime.utcnow()
            )
    
    def execute(
        self,
        func: Callable[[T], R],
        data_list: List[T],
        row_numbers: Optional[List[int]] = None
    ) -> List[ExecutionResult]:
        """
        Execute function on list of data items in parallel.
        
        Args:
            func: Function to execute on each data item
            data_list: List of data items to process
            row_numbers: Optional list of row numbers for logging
            
        Returns:
            List of ExecutionResult objects
        """
        if row_numbers is None:
            row_numbers = list(range(1, len(data_list) + 1))
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_row = {
                executor.submit(
                    self._execute_single,
                    func,
                    data,
                    row_num
                ): row_num
                for data, row_num in zip(data_list, row_numbers)
            }
            
            # Process results as they complete
            for future in as_completed(future_to_row):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    row_num = future_to_row[future]
                    logger.error(f"Unexpected error processing row {row_num}: {str(e)}")
                    results.append(ExecutionResult(
                        success=False,
                        data=None,
                        error=str(e),
                        row_number=row_num,
                        timestamp=datetime.utcnow()
                    ))
        
        # Sort results by row number
        results.sort(key=lambda x: x.row_number)
        return results
    
    def get_successful_results(self, results: List[ExecutionResult]) -> List[R]:
        """Extract successful results from execution results."""
        return [r.data for r in results if r.success and r.data is not None]
    
    def get_failed_rows(self, results: List[ExecutionResult]) -> List[int]:
        """Get list of row numbers that failed processing."""
        return [r.row_number for r in results if not r.success] 