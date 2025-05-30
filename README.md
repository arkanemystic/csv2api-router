# CSV to API Router

A Python tool that processes CSV files containing blockchain transaction data and generates appropriate API calls based on the content.

## Features

- **Smart CSV Processing**: Automatically detects transaction types and appropriate API functions
- **Multi-Chain Support**: Detects blockchain networks from explorer URLs (Ethereum, Polygon, Optimism, Arbitrum, Base)
- **Batch Processing**: Efficiently processes multiple transactions in parallel
- **Robust Error Handling**: Retries failed operations and provides detailed logging
- **No LLM Dependencies**: Uses heuristics instead of LLM calls for better performance

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/csv2api-router.git
cd csv2api-router
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Process a CSV file:
```bash
python3 -m src.main -i /path/to/your/transactions.csv
```

### CSV Format

The tool expects a CSV file with the following columns:
- `tx_link`: URL to the transaction on a blockchain explorer
- `purpose`: (Optional) Purpose of the transaction
- `amount in ETH`: (Optional) Amount in ETH
- `amount in USD`: (Optional) Amount in USD

Example CSV:
```csv
tx_link,purpose,amount in ETH,amount in USD
https://etherscan.io/tx/0x123...,Equipment,0.5,1000
https://polygonscan.com/tx/0x456...,Cloud Services,100,50
```

### Supported API Functions

The tool automatically selects the appropriate API function based on the CSV content:

1. **tag_as_expense**
   - Used when rows contain purpose and amount fields
   - Generates API calls with transaction details and expense information

2. **get_transaction**
   - Used for basic transaction lookups
   - Generates API calls to fetch transaction details

3. **get_receipt**
   - Used for transaction receipt lookups
   - Generates API calls to fetch transaction receipts

### API Call Format

The tool generates API calls in the following format:

```json
{
  "method": "tag_as_expense",
  "params": {
    "tx_hash": "0x...",
    "chain": "ETHEREUM",
    "purpose": "Equipment",
    "amount_in_eth": 0.5,
    "amount_in_usd": 1000
  },
  "timestamp": "2024-03-14T12:00:00.000Z"
}
```

## Project Structure

```
csv2api-router/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── pipeline/
│       ├── __init__.py
│       ├── api_functions.py
│       ├── batch_caller.py
│       └── csv_cleaner.py
├── dataset/
│   └── ten_case_test.csv
├── requirements.txt
└── README.md
```

### Key Components

- **csv_cleaner.py**: Handles CSV parsing, cleaning, and function selection
- **api_functions.py**: Defines API call generation functions
- **batch_caller.py**: Manages parallel processing of rows
- **main.py**: Entry point and CLI interface

## Development

### Adding New API Functions

1. Add the function to `api_functions.py`
2. Update the `FunctionType` enum in `csv_cleaner.py`
3. Add the function to `API_FUNCTIONS` in `main.py`

### Adding New Chain Support

Update the `CHAIN_MAP` in `csv_cleaner.py`:
```python
CHAIN_MAP = {
    "etherscan.io": "ETHEREUM",
    "polygonscan.com": "POLYGON",
    # Add new chains here
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.