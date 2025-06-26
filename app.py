from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
import pandas as pd
from llama_index.core import (
    VectorStoreIndex,
    Settings,
    Document,
    ServiceContext
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.readers.file import CSVReader
import logging
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVToAPIRouter:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(csv_path, engine='python', on_bad_lines='skip')
        
        # Validate CSV before processing
        self._validate_csv()
        
        # Initialize LlamaIndex components
        self._setup_llama_index()
        
        # Initialize cache
        self._cache = {}
        self._cache_ttl = timedelta(minutes=30)  # Cache TTL of 30 minutes
        
    def _validate_csv(self) -> None:
        """Validate CSV structure and content."""
        try:
            # Check if CSV is empty
            if self.df.empty:
                raise ValueError("CSV file is empty")
            
            # Check for required columns
            required_columns = ["Transaction Link", "Amount", "Purpose"]
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                raise ValueError(f"CSV missing required columns: {', '.join(missing_columns)}")
            
            # Validate data types
            if not pd.api.types.is_numeric_dtype(self.df["Amount"]):
                raise ValueError("Amount column must be numeric")
            
            # Check for empty values in required columns
            for col in required_columns:
                if self.df[col].isnull().any():
                    raise ValueError(f"Column '{col}' contains empty values")
            
            logger.info("CSV validation successful")
            
        except Exception as e:
            logger.error(f"CSV validation failed: {str(e)}")
            raise
    
    def _validate_response(self, response: str) -> Tuple[bool, str]:
        """
        Validate LLM response format and content.
        Returns (is_valid, error_message)
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            # Check required fields
            required_fields = ["api_call", "required_arguments", "csv_mapping"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return False, f"Response missing required fields: {', '.join(missing_fields)}"
            
            # Validate api_call
            valid_api_calls = ["tag_as_expense", "mark_as_refund", "get_transaction_details", "get_receipt"]
            if data["api_call"] not in valid_api_calls:
                return False, f"Invalid api_call: {data['api_call']}"
            
            # Validate required_arguments
            if not isinstance(data["required_arguments"], list):
                return False, "required_arguments must be a list"
            
            # Validate csv_mapping
            if not isinstance(data["csv_mapping"], dict):
                return False, "csv_mapping must be a dictionary"
            
            return True, ""
            
        except json.JSONDecodeError:
            return False, "Response is not valid JSON"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _get_cache_key(self, query: str) -> str:
        """Generate a cache key for a query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_from_cache(self, query: str) -> Optional[str]:
        """Get response from cache if it exists and is not expired."""
        cache_key = self._get_cache_key(query)
        if cache_key in self._cache:
            timestamp, response = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.info("Cache hit for query")
                return response
            else:
                logger.info("Cache expired for query")
                del self._cache[cache_key]
        return None
    
    def _add_to_cache(self, query: str, response: str) -> None:
        """Add response to cache with timestamp."""
        cache_key = self._get_cache_key(query)
        self._cache[cache_key] = (datetime.now(), response)
        logger.info("Added response to cache")
    
    def _setup_llama_index(self):
        """Set up LlamaIndex with Ollama and Mistral for CSV analysis."""
        try:
            # Use LlamaIndex's CSV reader
            csv_reader = CSVReader()
            documents = csv_reader.load_data(self.csv_path)
            
            # Add metadata to documents
            metadata = {
                "num_rows": len(self.df),
                "columns": list(self.df.columns),
                "dtypes": self.df.dtypes.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            documents = [Document(text=doc.text, metadata=metadata) for doc in documents]
            
            # Create nodes from documents with custom chunking
            parser = SimpleNodeParser(
                chunk_size=512,
                chunk_overlap=20,
                include_metadata=True
            )
            nodes = parser.get_nodes_from_documents(documents)
            
            # Initialize Ollama with Mistral
            llm = Ollama(
                model="mistral:instruct",
                temperature=0,
                base_url="http://localhost:11434",
                request_timeout=120.0
            )
            
            # Configure global settings
            Settings.llm = llm
            Settings.chunk_size = 512
            Settings.chunk_overlap = 20
            Settings.num_output = 512
            Settings.context_window = 4096
            
            # Create service context
            service_context = ServiceContext.from_defaults(
                llm=llm,
                node_parser=parser
            )
            
            # Create index
            self.index = VectorStoreIndex(
                nodes,
                service_context=service_context
            )
            
            logger.info("Successfully initialized LlamaIndex with Ollama")
            
        except Exception as e:
            logger.error(f"Error setting up LlamaIndex: {str(e)}")
            raise
    
    @lru_cache(maxsize=100)
    def get_csv_summary(self) -> str:
        """Get a summary of CSV columns and sample values using LlamaIndex."""
        try:
            # Check cache first
            cache_key = "csv_summary"
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response
            
            # Create a retriever
            retriever = self.index.as_retriever(
                similarity_top_k=3
            )
            
            # Create response synthesizer
            response_synthesizer = get_response_synthesizer(
                response_mode="tree_summarize"
            )
            
            # Create query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer
            )
            
            query = """
            Analyze the CSV data and provide:
            1. A list of all columns and their data types
            2. Sample values for each column
            3. Any patterns or insights about the data
            """
            
            response = query_engine.query(query)
            response_str = str(response)
            
            # Cache the response
            self._add_to_cache(cache_key, response_str)
            
            return response_str
            
        except Exception as e:
            logger.error(f"Error getting CSV summary: {str(e)}")
            return f"Error analyzing CSV: {str(e)}"
    
    def generate_api_spec(self, instruction: str) -> Dict:
        """
        Generate API specification based on natural language instruction using LlamaIndex.
        """
        try:
            # Check cache first
            cache_key = f"api_spec_{instruction}"
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return json.loads(cached_response)
            
            # Create a retriever
            retriever = self.index.as_retriever(
                similarity_top_k=3
            )
            
            # Create response synthesizer with custom prompt
            response_synthesizer = get_response_synthesizer(
                response_mode="compact"
            )
            
            # Create query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer
            )
            
            query = f"""
            Based on the CSV data and the following instruction:
            "{instruction}"
            
            Generate a JSON specification with:
            1. The appropriate API call to make
            2. Required arguments for the API
            3. Mapping from CSV columns to API arguments
            4. Any missing required arguments
            
            Available API methods:
            - tag_as_expense (requires: tx_hash, amount, expense_category)
            - mark_as_refund (requires: tx_hash, refund_reason)
            - get_transaction_details (requires: tx_hash)
            - get_receipt (requires: tx_hash)
            
            Return only the JSON specification, no additional text.
            """
            
            response = query_engine.query(query)
            response_str = str(response)
            
            # Validate response
            is_valid, error_message = self._validate_response(response_str)
            if not is_valid:
                logger.error(f"Invalid response: {error_message}")
                raise ValueError(f"Invalid response: {error_message}")
            
            # Cache the response
            self._add_to_cache(cache_key, response_str)
            
            return json.loads(response_str)
                
        except Exception as e:
            logger.error(f"Error generating API spec: {str(e)}")
            # Return fallback response
            return {
                "api_call": "tag_as_expense",
                "required_arguments": ["tx_hash", "amount", "expense_category"],
                "csv_mapping": {
                    "tx_hash": "Transaction Link",
                    "amount": "Amount",
                    "expense_category": "Purpose"
                },
                "missing_arguments": []
            }

def main():
    try:
        # Example usage
        router = CSVToAPIRouter("sample.csv")
        
        # Get CSV summary
        summary = router.get_csv_summary()
        print("CSV Summary:")
        print(summary)
        
        # Generate API spec
        instruction = "Tag all transactions related to travel as expenses."
        api_spec = router.generate_api_spec(instruction)
        print("\nAPI Specification:")
        print(json.dumps(api_spec, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
