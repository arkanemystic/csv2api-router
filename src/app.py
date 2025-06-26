import streamlit as st
import pandas as pd
import json
from pipeline.processor import PipelineProcessor
from pipeline.csv_parser import CSVParser
import tempfile
import os
import logging
import io
from pipeline.llm_client import extract_csv_from_text_with_llm

# Configure logger to write to the main log file
log_path = 'logs/csv2api_20250529.log'
os.makedirs(os.path.dirname(log_path), exist_ok=True)
file_handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in logger.handlers):
    logger.addHandler(file_handler)

st.set_page_config(page_title="CSV to API Router", page_icon="🔄", layout="wide")

def process_csv_with_llm(prompt, df, pipeline_processor):
    # Convert each row to a dict (with original column names)
    raw_rows = df.to_dict(orient='records')
    # Pass prompt and raw rows to the pipeline processor (which will call the LLM)
    function_name, api_calls = pipeline_processor.process_natural_language(prompt, raw_rows)
    return function_name, api_calls

def main():
    st.title("CSV to API Router 🔄")
    st.subheader("Convert messy CSV data into clean API calls for contract events")

    # Initialize session state
    if 'processor' not in st.session_state:
        logger.info("App.py: Initializing PipelineProcessor in session state.")
        st.session_state.processor = PipelineProcessor()
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 1. Upload CSV & Enter Instructions")
        uploaded_file = st.file_uploader("Choose a CSV file (with contract events)", type="csv")
        prompt = st.text_area(
            "Enter your instructions (e.g., 'Get all event details')",
            placeholder="e.g., Get event data from this CSV. The relevant columns are contract_address, event_signature, etc."
        )
        if uploaded_file and prompt:
            try:
                df = pd.read_csv(uploaded_file, engine='python', on_bad_lines='skip')
                st.markdown("#### CSV Preview (first 5 rows)")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button("Process CSV with LLM"):
                    with st.spinner("Processing with LLM..."):
                        try:
                            print('process_csv_with_llm: DataFrame columns:', list(df.columns))
                            function_name, formatted_rows = process_csv_with_llm(prompt, df, st.session_state.processor)
                            print(f'process_csv_with_llm: function_name={function_name}, num_api_calls={len(formatted_rows)}')
                            st.session_state.processed_data = {
                                'function': function_name,
                                'api_calls': formatted_rows
                            }
                            if formatted_rows:
                                st.success(f"Successfully processed {len(formatted_rows)} items for function '{function_name}'!")
                            else:
                                st.warning(f"Processing complete, but no API calls were successfully generated for function '{function_name}'. Check logs for details.")
                        
                        except Exception as e_inner:
                            logger.error(f"App.py: Error during CSV processing button action: {str(e_inner)}", exc_info=True)
                            st.error(f"Error during processing: {str(e_inner)}")
                            st.session_state.processed_data = None # Clear previous results
            except Exception as e_outer:
                logger.error(f"App.py: Error loading or previewing CSV: {str(e_outer)}", exc_info=True)
                st.error(f"Error loading/previewing file: {str(e_outer)}")

        st.markdown("### Or paste your data below (CSV, TSV, or table from Excel/Sheets):")
        pasted_data = st.text_area("Paste data here", height=200)

        if st.button("Process Pasted Data with LLM Extraction"):
            if pasted_data.strip():
                with st.spinner("Extracting CSV from pasted data using LLM..."):
                    try:
                        llm_csv = extract_csv_from_text_with_llm(pasted_data, debug=True)
                        print("Raw LLM CSV output:")
                        print(llm_csv)
                        print("Attempting to parse LLM CSV output...")
                        
                        # Parse CSV and process only if successful
                        df = pd.read_csv(
                            io.StringIO(llm_csv),
                            engine='python',
                            on_bad_lines='skip',
                            names=['chain', 'tx_hash', 'expense_category'],
                            header=0  # First line is header
                        )
                        
                        # Ensure we have all required columns
                        required_columns = ['chain', 'tx_hash', 'expense_category']
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        if missing_columns:
                            raise ValueError(f"Missing required columns: {missing_columns}")
                            
                        print('Final DataFrame columns (after normalization):', list(df.columns))
                        
                        # Show preview
                        st.dataframe(df.head())
                        
                        # Only process if we have a prompt
                        if prompt:
                            function_name, api_calls = process_csv_with_llm(prompt, df, st.session_state.processor)
                            st.session_state.processed_data = {
                                'function': function_name,
                                'api_calls': api_calls
                            }
                            if api_calls:
                                st.success(f"Successfully processed {len(api_calls)} items for function '{function_name}'!")
                            else:
                                st.warning(f"Processing complete, but no API calls were successfully generated for function '{function_name}'. Check logs for details.")
                        else:
                            st.warning("Please enter a prompt to process the pasted data.")
                    except Exception as e:
                        st.error(f"Failed to extract or parse CSV from LLM output: {e}")
                        logger.error(f"Error processing pasted data: {e}", exc_info=True)

    with col2:
        st.markdown("### 2. View API Call Parameters")
        if st.session_state.processed_data and st.session_state.processed_data['api_calls']:
            st.markdown(f"#### API Function: `{st.session_state.processed_data['function']}`")
            st.markdown("##### Parameters for API Calls:")
            
            display_data = []
            for i, row in enumerate(st.session_state.processed_data['api_calls']):
                # row is expected to be {'row': row_num, 'api_calls': [ ... ]}
                api_calls = row.get('api_calls', [])
                for api_call in api_calls:
                    flat = {'#': i + 1, 'row': row.get('row')}
                    flat['method'] = api_call.get('method')
                    params = api_call.get('params', {})
                    # Add each parameter as its own column
                    for k, v in params.items():
                        flat[k] = v
                    display_data.append(flat)

            if display_data:
                st.dataframe(pd.DataFrame(display_data), use_container_width=True)

            if st.download_button(
                "Download Results (JSON)",
                data=json.dumps(st.session_state.processed_data, indent=2),
                file_name="llm_processed_api_calls.json",
                mime="application/json"
            ):
                st.success("Downloaded results!")
        elif st.session_state.processed_data: # It exists but api_calls might be empty
            st.info("Processing resulted in no valid API calls to display. Check logs if this is unexpected.")
        else:
            st.info("Upload a CSV and enter instructions to see results here.")

if __name__ == "__main__":
    # Basic logging configuration for the app itself
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
