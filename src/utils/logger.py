import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class AuditLogger:
    """Handles audit logging with structured output."""
    
    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir or 'logs'
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration with file and console handlers."""
        # Create logs directory if it doesn't exist
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create logger instance
        self.logger = logging.getLogger('csv2api')
        
        # Add file handlers
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Regular log file
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'csv2api_{timestamp}.log')
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Audit log file (JSON format)
        audit_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'audit_{timestamp}.jsonl')
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(audit_handler)
        
    def _format_audit_log(self, 
                         event_type: str, 
                         details: Dict[str, Any], 
                         status: str = 'success') -> str:
        """Format an audit log entry as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'status': status,
            'details': details
        }
        return json.dumps(log_entry)
    
    def log_api_call(self, 
                     method: str, 
                     params: Dict[str, Any], 
                     response: Optional[Dict[str, Any]] = None,
                     error: Optional[str] = None) -> None:
        """Log an API call with its details."""
        details = {
            'method': method,
            'params': params
        }
        
        if response:
            details['response'] = response
            self.logger.info(
                self._format_audit_log('api_call', details)
            )
        elif error:
            details['error'] = error
            self.logger.error(
                self._format_audit_log('api_call', details, status='error')
            )
    
    def log_extraction(self, 
                      source: str, 
                      extracted_data: Dict[str, Any],
                      error: Optional[str] = None) -> None:
        """Log data extraction results."""
        details = {
            'source': source,
            'extracted_data': extracted_data
        }
        
        if error:
            details['error'] = error
            self.logger.error(
                self._format_audit_log('extraction', details, status='error')
            )
        else:
            self.logger.info(
                self._format_audit_log('extraction', details)
            )
    
    def log_processing(self,
                      input_data: Dict[str, Any],
                      output_data: Dict[str, Any],
                      error: Optional[str] = None) -> None:
        """Log data processing results."""
        details = {
            'input': input_data,
            'output': output_data
        }
        
        if error:
            details['error'] = error
            self.logger.error(
                self._format_audit_log('processing', details, status='error')
            )
        else:
            self.logger.info(
                self._format_audit_log('processing', details)
            )

# Create a global logger instance
logger = AuditLogger()

# Convenience functions
def log_info(message: str) -> None:
    """Log an informational message."""
    logger.logger.info(message)

def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.logger.warning(message)

def log_error(message: str) -> None:
    """Log an error message."""
    logger.logger.error(message)

def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.logger.debug(message)

def log_api_call(method: str, 
                 params: Dict[str, Any], 
                 response: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None) -> None:
    """Log an API call with its details."""
    logger.log_api_call(method, params, response, error)

def log_extraction(source: str, 
                  extracted_data: Dict[str, Any],
                  error: Optional[str] = None) -> None:
    """Log data extraction results."""
    logger.log_extraction(source, extracted_data, error)

def log_processing(input_data: Dict[str, Any],
                  output_data: Dict[str, Any],
                  error: Optional[str] = None) -> None:
    """Log data processing results."""
    logger.log_processing(input_data, output_data, error)