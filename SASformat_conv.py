# app.py
import streamlit as st
import pandas as pd
import pyreadstat
import xport
import io  # For handling byte streams in memory
import traceback  # For detailed error output

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
        with st.spinner("Reading XPT file... This might take a moment for large files."):
            datasets = xport.to_dataframe(uploaded_file)

        if not datasets:
            st.error("No datasets found in the uploaded XPT file.")
        else:
            st.success(f"Successfully read XPT file. Found {len(datasets)} dataset(s).")

            # Dataset Selection
            if len(datasets) == 1:
                selected_key = list(datasets.keys())[0]
            else:
                selected_key = st.selectbox(
                    "Multiple datasets found. Please select one to convert:",
                    options=list(datasets.keys())
                )

            df = datasets[selected_key]
            st.info(f"Selected dataset: `{selected_key}` with {df.shape[0]} rows and {df.shape[1]} columns.")

            if st.checkbox("Show Data Preview (first 5 rows)"):
                st.dataframe(df.head())

            # Convert to SAS7BDAT using pyreadstat
            with st.spinner("Converting to SAS7BDAT format..."):
                sas_buffer = io.BytesIO()

                pyreadstat.write_sas7bdat(
                    df,
                    sas_buffer,
                    column_labels=df.columns.tolist(),
                    file_label=f"Converted from {uploaded_file.name} - Dataset {selected_key}"
                )
                sas_buffer.seek(0)

            st.success("Conversion successful!")

            # Prepare output filename
            base_name = uploaded_file.name.lower().replace(".xpt", "")
            if len(datasets) > 1:
                output_filename = f"{base_name}_{selected_key.lower()}.sas7bdat"
            else:
                output_filename = f"{base_name}.sas7bdat"

            st.download_button(
                label=f"Download {output_filename}",
                data=sas_buffer,
                file_name=output_filename,
                mime='application/octet-stream'
            )

    except Exception as e:
        st.error("An unexpected error occurred during the conversion process.")
        st.error(str(e))
        if st.checkbox("Show detailed error traceback"):
            st.code(traceback.format_exc())

else:
    st.info("Please upload an XPT file to start the conversion.")

# --- Footer/Instructions ---
st.markdown("---")
st.markdown("""
**How to use:**
1. Upload a SAS XPORT (`.xpt`) file using the uploader above.
2. If multiple datasets are found, choose the one you'd like to convert.
3. Optionally preview the dataset.
4. Click the 'Download' button to save the converted `.sas7bdat` file.

**Libraries Used:**
- `streamlit` for the user interface.
- `xport` for reading `.xpt` files.
- `pandas` for handling data.
- `pyreadstat` for writing `.sas7bdat` files.
""")

st.sidebar.info(
    "**Note for Developers:**\n"
    "Include this in your `requirements.txt`:\n"
    "```\n"
    "streamlit\n"
    "pandas\n"
    "pyreadstat\n"
    "xport\n"
    "setuptools\n"
    "```"
)
