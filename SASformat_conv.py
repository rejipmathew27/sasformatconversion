# app.py
import streamlit as st
import pandas as pd
import pyreadstat
import xport
import io  # Required for handling byte streams in memory
import traceback # For showing detailed errors if needed

# --- Streamlit App Configuration ---
st.set_page_config(page_title="XPT to SAS7BDAT Converter", layout="centered")

st.title("XPT to SAS7BDAT File Converter")
st.write("Upload a SAS XPORT (.xpt) file and download it as a SAS7BDAT file.")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Choose an XPT file",
    type=["xpt"],
    help="Select the SAS XPORT (.xpt) file you want to convert."
)

# --- Conversion Logic ---
if uploaded_file is not None:
    st.write(f"Uploaded file: `{uploaded_file.name}`")

    try:
        # --- Reading XPT using xport library ---
        # Use a spinner for user feedback during potentially long reads
        with st.spinner("Reading XPT file... This might take a moment for large files."):
            # xport.to_dataframe reads from a file-like object (like uploaded_file)
            # It returns a dictionary where keys are dataset names and values are DataFrames
            datasets = xport.to_dataframe(uploaded_file)

        if not datasets:
            st.error("Could not find any datasets within the uploaded XPT file.")
        else:
            st.success(f"Successfully read XPT file. Found {len(datasets)} dataset(s).")

            # --- Select Dataset if Multiple Exist ---
            if len(datasets) == 1:
                # If only one dataset, use it directly
                selected_key = list(datasets.keys())[0]
                df = datasets[selected_key]
                st.info(f"Processing dataset: `{selected_key}`")
            else:
                # If multiple datasets, let the user choose
                dataset_keys = list(datasets.keys())
                selected_key = st.selectbox(
                    "Multiple datasets found. Please select the one to convert:",
                    options=dataset_keys,
                    index=0 # Default to the first one
                )
                df = datasets[selected_key]
                st.info(f"Selected dataset for conversion: `{selected_key}`")

            st.write(f"Dataset `{selected_key}` has {df.shape[0]} rows and {df.shape[1]} columns.")

            # Display a preview of the data
            if st.checkbox(f"Show Data Preview (first 5 rows of '{selected_key}')"):
                st.dataframe(df.head())

            # --- Writing SAS7BDAT using pyreadstat ---
            with st.spinner("Converting to SAS7BDAT format..."):
                # Create an in-memory bytes buffer to hold the SAS7BDAT data
                sas_buffer = io.BytesIO()

                # Write the selected DataFrame to the buffer in SAS7BDAT format
                # Using column names as labels is a common practice
                pyreadstat.write_sas7bdat(
                    df,
                    sas_buffer,
                    column_labels=df.columns.tolist(),
                    file_label=f"Converted from {uploaded_file.name} - Dataset {selected_key}" # Optional: add a file label
                    # Add other metadata options here if needed and available, e.g., variable_formats
                )

                # Reset the buffer's position to the beginning so it can be read for download
                sas_buffer.seek(0)

            st.success("Conversion successful!")

            # --- Download Button ---
            # Generate a reasonable output filename
            base_name = uploaded_file.name.lower().split('.xpt')[0]
            # If multiple datasets were present, include the selected dataset key in the name
            if len(datasets) > 1:
                 output_filename = f"{base_name}_{selected_key.lower()}.sas7bdat"
            else:
                 output_filename = f"{base_name}.sas7bdat"


            st.download_button(
                label=f"Download {output_filename}",
                data=sas_buffer, # The bytes data from the buffer
                file_name=output_filename,
                mime='application/octet-stream' # Use application/octet-stream for generic binary data
                # mime='application/x-sas-data' # More specific, but octet-stream is safer
            )

    except xport.XportError as xe:
         st.error(f"Error reading the XPT file structure:")
         st.error(xe)
         st.info("Please ensure the uploaded file is a valid SAS XPORT Version 5 file.")
         if st.checkbox("Show detailed error traceback"):
            st.code(traceback.format_exc())
    except Exception as e:
        st.error(f"An unexpected error occurred during the conversion process:")
        st.error(e)
        # Optionally show full traceback for debugging
        if st.checkbox("Show detailed error traceback"):
             st.code(traceback.format_exc())

else:
    st.info("Please upload an XPT file to start the conversion.")

# --- Footer/Instructions ---
st.markdown("---")
st.markdown("""
**How to use:**
1.  Click 'Browse files' or drag and drop your XPT file onto the uploader.
2.  If the XPT file contains multiple datasets, select the desired dataset from the dropdown.
3.  The app will read the file and prepare the SAS7BDAT version.
4.  (Optional) Check the box to preview the first few rows of the selected data.
5.  Click the 'Download *.sas7bdat' button to save the converted file.

**Libraries Used:**
* `streamlit` for the web application interface.
* `xport` for reading SAS XPORT (.xpt) files.
* `pandas` for data manipulation.
* `pyreadstat` for writing SAS (.sas7bdat) files.
""")

# --- Suggestion for deployment ---
st.sidebar.info(
    "**Note for Developers:**\n"
    "For deployment, ensure you have a `requirements.txt` file with at least:\n"
    "```\n"
    "streamlit\n"
    "pandas\n"
    "pyreadstat\n"
    "xport\n"
    "```"
)
