import streamlit as st
import pandas as pd
import json
from pipeline.processor import PipelineProcessor
from pipeline.csv_parser import CSVParser
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

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
                df = pd.read_csv(uploaded_file)
                st.markdown("#### CSV Preview (first 5 rows)")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button("Process CSV with LLM"):
                    with st.spinner("Processing with LLM..."):
                        try:
                            function_name, formatted_rows = process_csv_with_llm(prompt, df, st.session_state.processor)
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

    with col2:
        st.markdown("### 2. View API Call Parameters")
        if st.session_state.processed_data and st.session_state.processed_data['api_calls']:
            st.markdown(f"#### API Function: `{st.session_state.processed_data['function']}`")
            st.markdown("##### Parameters for API Calls:")
            
            # Create a list of dictionaries for DataFrame conversion
            display_data = []
            for i, params_dict in enumerate(st.session_state.processed_data['api_calls']):
                if isinstance(params_dict, dict):
                    item = {'#': i + 1}
                    item.update(params_dict)
                    display_data.append(item)
                else:
                    st.warning(f"Malformed API call parameters at index {i}: {params_dict}")
            
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
