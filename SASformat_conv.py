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
st.write("Upload an XPT file and download it as a SAS7BDAT file.")

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
        # xport.to_dataframe reads from a file-like object (like uploaded_file)
        st.info("Reading XPT file...")
        datasets = xport.to_dataframe(uploaded_file)

        if not datasets:
            st.error("Could not find any datasets within the uploaded XPT file.")
        else:
            # Assume the first dataset in the dictionary is the one needed
            # (XPT files can potentially contain multiple datasets)
            first_dataset_key = list(datasets.keys())[0]
            df = datasets[first_dataset_key]
            st.success(f"Successfully read dataset '{first_dataset_key}' with {df.shape[0]} rows and {df.shape[1]} columns.")

            # Display a preview of the data
            if st.checkbox("Show Data Preview (first 5 rows)"):
                st.dataframe(df.head())

            # --- Writing SAS7BDAT using pyreadstat ---
            st.info("Converting to SAS7BDAT format...")

            # Create an in-memory bytes buffer to hold the SAS7BDAT data
            sas_buffer = io.BytesIO()

            # Write the DataFrame to the buffer in SAS7BDAT format
            # Note: Add column_labels=df.columns.tolist() if you want labels based on column names
            # You might need more specific metadata handling depending on the source XPT
            pyreadstat.write_sas7bdat(df, sas_buffer, column_labels=df.columns.tolist())

            # Reset the buffer's position to the beginning so it can be read for download
            sas_buffer.seek(0)

            st.success("Conversion successful!")

            # --- Download Button ---
            output_filename = uploaded_file.name.lower().replace(".xpt", ".sas7bdat")
            if not output_filename.endswith(".sas7bdat"): # Ensure correct extension
                 output_filename += ".sas7bdat"

            st.download_button(
                label=f"Download {output_filename}",
                data=sas_buffer, # The bytes data from the buffer
                file_name=output_filename,
                mime='application/octet-stream' # A common mime type for binary files
            )

    except Exception as e:
        st.error(f"An error occurred during the conversion process:")
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
2.  The app will automatically read the file and prepare the SAS7BDAT version.
3.  (Optional) Check the box to preview the first few rows of the data.
4.  Click the 'Download *.sas7bdat' button to save the converted file.

**Libraries Used:**
* `streamlit` for the web application interface.
* `xport` for reading SAS XPORT (.xpt) files.
* `pandas` for data manipulation (implicitly used by xport/pyreadstat).
* `pyreadstat` for writing SAS (.sas7bdat) files.
""")
