# csv2api-router
Modular Python pipeline that processes CSVs or unstructured text, extracts API-relevant data, and routes it to Python functions for execution. This project leverages local LLM capabilities via Ollama for data processing and supports both batch and interactive modes with full logging and audit support.

## Features
- Process CSV files and unstructured text
- Local LLM processing using Ollama (deepseek-coder model)
- Automated API call identification and parameter extraction
- Support for multiple blockchain APIs (Ethereum, Polygon, BSC)
- Batch and interactive processing modes
- Comprehensive logging and audit trail
- Asynchronous API execution

## Architecture
The pipeline follows a three-stage architecture:
1. **Data Extraction** (`extractor.py`): Parses input sources and extracts relevant data
2. **LLM Processing** (`processor.py`): Uses local Ollama model to identify required API calls
3. **API Routing** (`router.py`): Executes identified API calls with proper parameters

## Project Structure
```
csv2api-router
├── src
│   ├── pipeline          # Contains the core processing logic
│   │   ├── extractor.py  # Extracts data from CSVs and text
│   │   ├── processor.py  # LLM-based data processing via Ollama
│   │   └── router.py     # API call routing and execution
│   ├── utils            # Utility functions and helpers
│   │   └── logger.py    # Structured logging with audit support
│   ├── config           # Configuration settings
│   │   └── settings.py  # Project settings
│   └── main.py         # CLI entry point
├── tests               # Unit tests
│   ├── test_extractor.py
│   ├── test_processor.py
│   └── test_router.py
├── requirements.txt    # Python dependencies
└── setup.py           # Project setup configuration
```

## Prerequisites
- Python 3.9 or higher
- Ollama installed and running locally with the deepseek-coder model
- Required Python packages (see requirements.txt)

## Installation

1. Install Ollama and the deepseek-coder model:
```bash
# Install Ollama (if not already installed)
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the deepseek-coder model
ollama pull deepseek-coder
```

2. Clone and set up the project:
```bash
# Clone the repository
git clone https://github.com/yourusername/csv2api-router.git
cd csv2api-router

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Model Configuration

This project uses the deepseek-coder model via Ollama for API call identification. The model is configured with:
- Temperature: 0.0 (deterministic responses)
- Maximum prediction length: 512 tokens
- Stop sequence: \n\n (double newline)

These settings ensure consistent and reliable API call generation while maintaining accuracy.

## Usage

1. Start the Ollama service:
```bash
ollama serve
```

2. Run the pipeline:
```bash
# Process a CSV file
python src/main.py process --input dataset/sample.csv --output results.json

# Interactive mode
python src/main.py interactive
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Logging

The project maintains two types of logs:
- `logs/csv2api_YYYYMMDD.log`: General application logs
- `logs/audit_YYYYMMDD.jsonl`: Detailed audit trail of all API calls

## License

This project is licensed under the MIT License - see the LICENSE file for details.