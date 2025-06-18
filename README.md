# CSV2API-Router

## **Purpose**
This project provides a pipeline that takes a CSV file and a natural language prompt from the user, and maps each row of the CSV to one or more API calls, using both the data and the user’s intent. It leverages an LLM (Mistral Instruct via Ollama) to infer the correct API(s) and parameter mappings, supporting flexible, prompt-driven automation.

---

## **Key Features**
- **Natural Language API Routing:** Users can describe what they want to do in plain English (e.g., “Fill all accounts”, “Tag as expense”, “Get receipts”).
- **LLM-Driven Inference:** The LLM analyzes the prompt and the CSV headers to decide which API(s) to call and how to map columns to parameters.
- **Robust Data Cleaning:** The pipeline standardizes and cleans CSV data before processing.
- **Extensible API Support:** Easily add new API functions and parameter mappings.
- **Streamlit UI:** User-friendly web interface for uploading CSVs, entering prompts, and viewing results.
- **Detailed Logging:** All steps are logged for traceability and debugging.

---

## **Directory Structure**
```
csv2api-router/
├── app.py                  # Streamlit web app entry point
├── src/
│   ├── main.py             # (CLI or script entry point, if used)
│   ├── pipeline/
│   │   ├── processor.py    # Main pipeline logic (LLM, mapping, orchestration)
│   │   ├── llm_client.py   # LLM invocation and API call generation
│   │   ├── csv_cleaner.py  # CSV cleaning and normalization
│   │   ├── csv_parser.py   # CSV parsing and canonicalization
│   │   ├── extractor.py    # Data extraction from CSV/text
│   │   ├── api_functions.py# (API function definitions, if used)
│   │   └── ...             # Other pipeline utilities
│   ├── utils/
│   │   └── logger.py       # Logging setup
│   └── config/
│       └── settings.py     # Configurations
├── tests/                  # Unit tests
├── dataset/                # Example/test CSVs
├── requirements.txt        # Python dependencies
└── README.md               # (To be generated)
```

---

## **Core Pipeline Flow**

### 1. **User Input**
- User uploads a CSV file and enters a natural language prompt via the Streamlit UI.

### 2. **CSV Cleaning & Parsing**
- The CSV is cleaned and standardized (`csv_cleaner.py`, `csv_parser.py`).
- Column names are normalized, and each row is converted to a dictionary.

### 3. **LLM-Driven Mapping Plan**
- The pipeline sends the **user prompt** and the **CSV headers** (not all rows) to the LLM.
- The LLM returns a **mapping plan**: which API(s) to call, and how to map columns to required parameters.

### 4. **API Call Construction**
- The code applies the mapping plan to every row, constructing API call dictionaries.
- If the LLM returns placeholders or empty values, the code fills them with sensible defaults (e.g., `'ETHEREUM'` for `chain`, random string for `tx_hash`).

### 5. **Output & Reporting**
- The resulting API calls are displayed in the UI and/or returned as JSON.
- The pipeline summarizes which API methods were actually generated.

---

## **Supported API Functions (Example)**
- `fill_account_by`: `{ "account_id", "amount" }`
- `get_transaction`: `{ "chain", "tx_hash" }`
- `tag_as_expense`: `{ "chain", "tx_hash", "expense_category" }`
- `get_receipt`: `{ "chain", "tx_hash" }`
- `list_chains`: `{}`

---

## **LLM Integration**
- Uses **Mistral Instruct** via **Ollama** (local LLM runner).
- The LLM is only called once per prompt+CSV (for efficiency).
- The prompt strictly instructs the LLM to output only valid JSON, with no comments or markdown.

---

## **Extensibility**
- **Add new APIs:** Update the `SUPPORTED_APIS` dictionary in `llm_client.py` and `processor.py`.
- **Custom field mappings:** Adjust the LLM prompt or mapping logic as needed.
- **UI/CLI:** The Streamlit app can be extended, or a CLI can be used via `main.py`.

---

## **Testing**
- Unit tests are in the `tests/` directory.
- Tests cover prompt-to-API inference, CSV cleaning, and error handling.

---

## **Typical Usage Example**
1. User uploads a CSV with columns: `account_id, amount, name, ...`
2. User enters prompt: “Fill all accounts”
3. The LLM returns a mapping plan: use `fill_account_by` with `account_id` and `amount`
4. The pipeline generates, for each row:
   ```json
   {
     "method": "fill_account_by",
     "params": { "account_id": "acct-123", "amount": 100.0 }
   }
   ```
5. The UI displays the results and a summary: `API calls generated for methods: fill_account_by`

---

## **Caveats & Notes**
- The LLM must be running and accessible via Ollama.
- The pipeline expects the CSV to have headers that can be mapped to API parameters.
- If the LLM returns placeholders or empty values, the code attempts to fill them, but real data is preferred.
