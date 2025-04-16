import streamlit as st
import pyreadstat
import tempfile
import os

st.set_page_config(page_title="XPT to SAS7BDAT Converter", layout="centered")
st.title("📁 Convert .xpt to .sas7bdat")

uploaded_file = st.file_uploader("Upload a .xpt file", type=["xpt"])

if uploaded_file is not None:
    file_name = uploaded_file.name
    st.success(f"Uploaded: {file_name}")
    
    if st.button("Convert"):
        try:
            # Save uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xpt") as temp_input:
                temp_input.write(uploaded_file.read())
                temp_input_path = temp_input.name

            # Output file path
            temp_output_path = temp_input_path.replace(".xpt", ".sas7bdat")

            # Read .xpt and write .sas7bdat
            df, meta = pyreadstat.read_xport(temp_input_path)
            pyreadstat.write_sas7bdat(df, temp_output_path)

            # Download button
            with open(temp_output_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download .sas7bdat file",
                    data=f,
                    file_name=file_name.replace(".xpt", ".sas7bdat"),
                    mime="application/octet-stream"
                )

            # Cleanup
            os.remove(temp_input_path)
            os.remove(temp_output_path)

        except Exception as e:
            st.error(f"Error: {e}")
