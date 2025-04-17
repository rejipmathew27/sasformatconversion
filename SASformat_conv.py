import streamlit as st
import os
import subprocess
import zipfile
from pathlib import Path
from io import BytesIO
import pandas as pd

st.title("Batch XPT to SAS7BDAT Converter (R + haven)")
st.write("""
Enter a folder path containing `.xpt` files. The app will:
- List the `.xpt` files found
- Convert all of them using R + haven
- Let you download the converted `.sas7bdat` files
""")

folder_path = st.text_input("Enter full path to folder containing .xpt files")
save_output = st.checkbox("Save converted files to server (in session folder)")

if folder_path:
    input_dir = Path(folder_path)

    if not input_dir.exists() or not input_dir.is_dir():
        st.error("Provided path does not exist or is not a directory.")
    else:
        xpt_files = sorted(list(input_dir.glob("*.xpt")))

        if not xpt_files:
            st.warning("No .xpt files found in the specified folder.")
        else:
            st.success(f"Found {len(xpt_files)} .xpt file(s) in: `{folder_path}`")

            # Show file names
            file_data = [{"File Name": f.name, "Size (KB)": round(f.stat().st_size / 1024, 2)} for f in xpt_files]
            st.dataframe(pd.DataFrame(file_data))

            # Output folder
            output_dir = input_dir / "converted_sas7bdat"
            output_dir.mkdir(exist_ok=True)

            # R script generation
            r_script_lines = [
                'if (!requireNamespace("haven", quietly = TRUE)) {',
                '  install.packages("haven", repos = "https://cloud.r-project.org")',
                '}',
                'library(haven)'
            ]

            for xpt_file in xpt_files:
                out_file = output_dir / (xpt_file.stem + ".sas7bdat")
                r_script_lines.append(
                    f'data <- read_xpt("{xpt_file.as_posix()}")'
                )
                r_script_lines.append(
                    f'write_sas(data, "{out_file.as_posix()}")\n'
                )

            r_script = "\n".join(r_script_lines)

            st.subheader("Generated R Script")
            st.code(r_script, language="r")

            if st.button("Run Conversion in R"):
                r_script_path = input_dir / "convert_all.R"
                r_script_path.write_text(r_script)

                try:
                    result = subprocess.run(
                        ["Rscript", str(r_script_path)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    st.success("Conversion completed!")
                    st.text(result.stdout)

                    converted_files = list(output_dir.glob("*.sas7bdat"))

                    if converted_files:
                        st.subheader("Download Converted Files")

                        for file in converted_files:
                            with open(file, "rb") as f:
                                st.download_button(
                                    label=f"Download {file.name}",
                                    data=f.read(),
                                    file_name=file.name,
                                    mime="application/octet-stream"
                                )

                        # Zip all files
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zipf:
                            for file in converted_files:
                                zipf.write(file, arcname=file.name)
                        st.download_button(
                            "Download All as ZIP",
                            data=zip_buffer.getvalue(),
                            file_name="converted_sas7bdat_files.zip",
                            mime="application/zip"
                        )

                        if save_output:
                            st.success(f"Files saved to: {output_dir}")

                except subprocess.CalledProcessError as e:
                    st.error("Error while executing R script:")
                    st.code(e.stderr)
