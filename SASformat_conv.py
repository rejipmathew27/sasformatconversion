import streamlit as st
import os
import subprocess
import tempfile

st.title("XPT to SAS7BDAT Converter (via R + haven)")
st.write("Upload a `.xpt` file and either download or run the generated R script to convert it to `.sas7bdat`.")

uploaded_file = st.file_uploader("Upload your .xpt file", type=["xpt"])

if uploaded_file is not None:
    # Save uploaded file to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        xpt_path = os.path.join(tmpdir, uploaded_file.name)
        with open(xpt_path, "wb") as f:
            f.write(uploaded_file.read())

        base_filename = os.path.splitext(uploaded_file.name)[0]
        output_filename = f"{base_filename}.sas7bdat"
        output_path = os.path.join(tmpdir, output_filename)
        r_script_path = os.path.join(tmpdir, f"convert_{base_filename}.R")

        # Generate R script content
        r_script = f"""
if (!requireNamespace("haven", quietly = TRUE)) {{
    install.packages("haven", repos = "https://cloud.r-project.org")
}}

library(haven)
data <- read_xpt("{xpt_path.replace(os.sep, '/')}")
write_sas(data, "{output_path.replace(os.sep, '/')}")
"""

        # Show R script
        st.subheader("Generated R Script")
        st.code(r_script, language="r")

        # Download R script
        st.download_button(
            label="Download R Script",
            data=r_script,
            file_name=f"convert_{base_filename}.R",
            mime="text/plain"
        )

        # Option to run R script
        if st.button("Run R Script Now (Requires R Installed)"):
            with open(r_script_path, "w") as rfile:
                rfile.write(r_script)

            try:
                result = subprocess.run(
                    ["Rscript", r_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                st.success("R script executed successfully!")
                st.text(result.stdout)

                # Download link for .sas7bdat output
                if os.path.exists(output_path):
                    with open(output_path, "rb") as out_file:
                        st.download_button(
                            label="Download Converted .sas7bdat File",
                            data=out_file,
                            file_name=output_filename,
                            mime="application/octet-stream"
                        )
                else:
                    st.warning("Conversion complete, but output file not found.")

            except subprocess.CalledProcessError as e:
                st.error("Error occurred while running the R script:")
                st.code(e.stderr)
