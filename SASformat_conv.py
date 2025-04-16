import streamlit as st
import pyreadstat
import os

st.set_page_config(page_title="XPT to SAS7BDAT Converter", layout="centered")
st.title("📁 Convert .xpt to .sas7bdat")

uploaded_file = st.file_uploader("Upload a .xpt file", type=["xpt"])

if uploaded_file is not None:
    file_name = uploaded_file.name
    st.success(f"Uploaded: {file_name}")
    
    if st.button("Convert"):
        try:
            # Read the .xpt file
            df, meta = pyreadstat.read_xport(uploaded_file)

            # Create output filename
            output_filename = file_name.replace(".xpt", ".sas7bdat")

            # Save as .sas7bdat
            pyreadstat.write_sas7bdat(df, output_filename)

            # Offer download
            with open(output_filename, "rb") as f:
                st.download_button(
                    label="Download .sas7bdat file",
                    data=f,
                    file_name=output_filename,
                    mime="application/octet-stream"
                )

            # Cleanup
            os.remove(output_filename)

        except Exception as e:
            st.error(f"Error: {e}")
