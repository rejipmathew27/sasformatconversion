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

# Sidebar instructions and options
with st.sidebar:
    st.markdown("## 📋 Instructions")
    st.write("""
1. Choose an input method (upload files or use folder).
2. Upload or locate `.xpt` files.
3. Select specific files to convert.
4. Click **Run Conversion** to generate `.sas7bdat` files.
5. Download files individually or as ZIP.
    """)
    
    conversion_method = st.radio(
        "Choose Input Method:",
        ["Folder Path", "Upload Files"],
        index=1  # Default = "Upload Files"
    )

    save_output = st.checkbox("Save converted files to server")

xpt_files = []
source_label = ""
input_dir = None

# === Folder Path Option ===
if conversion_method == "Folder Path":
    with st.sidebar:
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

# === Upload Option ===
elif conversion_method == "Upload Files":
    with st.sidebar:
        uploaded = st.file_uploader("Upload one or more `.xpt` files", type=["xpt"], accept_multiple_files=True)
    if uploaded:
        input_dir = Path(tempfile.mkdtemp())
        for file in uploaded:
            file_path = input_dir / file.name
            file_path.write_bytes(file.read())
        xpt_files = sorted(input_dir.glob("*.xpt"))
        source_label = "from uploaded files"

# === File Selection ===
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

# === Conversion ===
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
    st.subheader("🧪 Generated R Script")
    st.code(r_script, language="r")

    if st.button("🚀 Run Conversion"):
        r_script_path = output_dir / "convert_selected.R"
        r_script_
