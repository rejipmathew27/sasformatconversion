import streamlit as st
import os

st.title("XPT to SAS7BDAT Converter (R Script Generator)")
st.write("Upload a `.xpt` file and get an R script to convert it to `.sas7bdat` using the `haven` package.")

uploaded_file = st.file_uploader("Upload your .xpt file", type=["xpt"])

if uploaded_file is not None:
    # Display the uploaded file name
    st.success(f"Uploaded file: {uploaded_file.name}")

    xpt_filename = uploaded_file.name
    base_filename = os.path.splitext(xpt_filename)[0]
    output_filename = f"{base_filename}.sas7bdat"

    # Generate R script
    r_script = f"""
# Required package
if (!requireNamespace("haven", quietly = TRUE)) {{
    install.packages("haven")
}}

library(haven)

# Read the XPT file
data <- read_xpt("{xpt_filename}")

# Write to SAS7BDAT format
write_sas(data, "{output_filename}")
"""

    st.code(r_script, language="r")

    # Allow user to download the R script
    st.download_button(
        label="Download R Script",
        data=r_script,
        file_name=f"convert_{base_filename}.R",
        mime="text/plain"
    )
