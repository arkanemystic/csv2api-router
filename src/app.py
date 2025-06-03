import streamlit as st
import pandas as pd
from pathlib import Path
import json
import sys
from pipeline.processor import PipelineProcessor

st.set_page_config(page_title="CSV to API Router", page_icon="🔄", layout="wide")

def main():
    st.title("CSV to API Router 🔄")
    st.subheader("Convert messy CSV data into clean API calls")
    
    # Initialize session state
    if 'processor' not in st.session_state:
        st.session_state.processor = PipelineProcessor()
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
        
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 1. Upload CSV & Enter Instructions")
        
        # File uploader
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        # Natural language prompt
        prompt = st.text_area(
            "Enter your instructions",
            placeholder="e.g., Tag these transactions as expenses. Chain is ETH, purpose is listed in the CSV."
        )
        
        if uploaded_file and prompt:
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Show preview of CSV
                st.markdown("#### CSV Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Process button
                if st.button("Process CSV"):
                    with st.spinner("Processing..."):
                        # Convert DataFrame to list of dicts
                        csv_data = df.to_dict('records')
                        
                        # Process the data
                        api_calls = st.session_state.processor.process_natural_language(
                            prompt, csv_data
                        )
                        # Store results
                        st.session_state.processed_data = {
                            'api_calls': api_calls
                        }
                        st.success(f"Successfully processed {len(api_calls)} API calls!")
                        
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    with col2:
        st.markdown("### 2. View Results")
        
        if st.session_state.processed_data:
            st.markdown(f"#### API Calls Inferred by LLM:")
            for i, call in enumerate(st.session_state.processed_data['api_calls'], 1):
                if isinstance(call, dict):
                    func = call.get('function', '<unknown>')
                    params = call.get('params', {})
                    param_str = ', '.join(f"{k}={v}" for k, v in params.items()) if isinstance(params, dict) else str(params)
                    st.markdown(f"**API Call {i}:** <span style='color:#228be6'><b>{func}</b></span>  ", unsafe_allow_html=True)
                    st.markdown(f"&nbsp;&nbsp;<b>Params:</b> {param_str}")
                else:
                    st.warning(f"Malformed API call at {i}: {call}")
            # Download button for results
            if st.download_button(
                "Download Results (JSON)",
                data=json.dumps(st.session_state.processed_data, indent=2),
                file_name="processed_results.json",
                mime="application/json"
            ):
                st.success("Downloaded results!")

if __name__ == "__main__":
    main()
