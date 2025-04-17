import streamlit as st
import os
import subprocess
import zipfile
from pathlib import Path
from io import BytesIO
import pandas as pd
import tempfile

st.set_page_config(page_title="XPT to SAS7BDAT Converter", layout="centered")
st.title("📦 XPT to SAS7BDAT Converter (via R + haven)")

st.write("""
This app converts `.xpt` files to `.sas7bdat` using R and the **haven** package.

### You can:
- 📂 Specify a folder containing `.xpt` files
- 📤 Upload `.xpt` files manually
- 🎯 Select which files to convert
- 💾 Optionally save output to disk
""")

conversion_method = st.radio("Choose Input Method:", ["Folder Path", "Upload Files"])
save_output = st.checkbox("Save converted files to server (in session folder)")

xpt_files = []
source_label = ""
input_dir = None

if conversion_method == "Folder Path":
    folder_path = st.text_input("Enter full path to folder containing .xpt files")
    show_path = st.button("Show Folder Path")

    if folder_path:
        input_dir = Path(folder_path).expanduser().resolve()

        if show_path:
            st.info(f"📁 Full folder path: `{input_dir}`")

        if input_dir.exists() and input_dir.is_dir():
            xpt_files = sorted(list(input_dir.glob("*.xpt")))
            source_label = f"from folder: `{input_dir}`"
        else:
            st.error("Invalid folder path.")

elif conversion_method == "Upload Files":
    uploaded = st.file_uploader("Upload one or more `.xpt` files", type=["xpt"], accept_multiple_files=True)
    if uploaded:
        input_dir = Path(tempfile.mkdtemp())
        for file in uploaded:
            file_path = input_dir / file.name
            file_path.write_bytes(file.read())
        xpt_files = sorted(input_dir.glob("*.xpt"))
        source_label = "from uploaded files"

# File selection
selected_files = []

if xpt_files:
    st.success(f"✅ Found {len(xpt_files)} .xpt file(s) {source_label}")

    file_df = pd.DataFrame({
        "File Name": [f.name for f in xpt_files],
        "Size (KB)": [round(f.stat().st_size / 1024, 2) for f in xpt_files]
    })
    st.dataframe(file_df, use_container_width=True)

    selected_file_names = st.multiselect(
        "Select files to convert",
        options=[f.name for f in xpt_files],
        default=[f.name for f in xpt_files]
    )
    selected_files = [f for f in xpt_files if f.name in selected_file_names]

if selected_files:
    output_dir = Path(tempfile.mkdtemp()) if conversion_method == "Upload Files" else input_dir / "converted_sas7bdat"
    output_dir.mkdir(exist_ok=True)

    # R script generation
    r_script_lines = [
        'if (!requireNamespace("haven", quietly = TRUE)) {',
        '  install.packages("haven", repos = "https://cloud.r-project.org")',
        '}',
        'library(haven)'
    ]

    for xpt_file in selected_files:
        out_file = output_dir / (xpt_file.stem + ".sas7bdat")
        r_script_lines.append(f'data <- read_xpt("{xpt_file.as_posix()}")')
        r_script_lines.append(f'write_sas(data, "{out_file.as_posix()}")\n')

    r_script = "\n".join(r_script_lines)
    st.subheader("Generated R Script")
    st.code(r_script, language="r")

    if st.button("🚀 Run Conversion"):
        r_script_path = output_dir / "convert_selected.R"
        r_script_path.write_text(r_script)

        try:
            result = subprocess.run(
                ["Rscript", str(r_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            st.success("🎉 Conversion completed successfully!")
            st.text(result.stdout)

            converted_files = [output_dir / (f.stem + ".sas7bdat") for f in selected_files]

            if converted_files:
                st.subheader("📥 Download Converted Files")

                for file in converted_files:
                    with open(file, "rb") as f:
                        st.download_button(
                            label=f"Download {file.name}",
                            data=f.read(),
                            file_name=file.name,
                            mime="application/octet-stream"
                        )

                # ZIP download
                zip_buf = BytesIO()
                with zipfile.ZipFile(zip_buf, "w") as zf:
                    for f in converted_files:
                        zf.write(f, arcname=f.name)
                st.download_button(
                    "Download All as ZIP",
                    data=zip_buf.getvalue(),
                    file_name="converted_sas7bdat.zip",
                    mime="application/zip"
                )

                if save_output:
                    saved_dir = Path.cwd() / "saved_converted_output"
                    saved_dir.mkdir(exist_ok=True)
                    for f in converted_files:
                        (saved_dir / f.name).write_bytes(f.read_bytes())
                    st.success(f"✔️ Files also saved to: `{saved_dir}`")

        except subprocess.CalledProcessError as e:
            st.error("❌ Error running R script:")
            st.code(e.stderr)
