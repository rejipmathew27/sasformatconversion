


import streamlit as st 
import pandas as pd
import pyreadstat
from pathlib import Path
import os
import tempfile
import sys

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("SAS XPT to SAS7BDAT Converter")
st.write("""
Convert SAS XPT transport files (`.xpt`) to SAS7BDAT dataset files (`.sas7bdat`).
You can either convert all `.xpt` files within a specified directory
or upload and convert a single `.xpt` file.
""")

current_date = pd.Timestamp.now().strftime('%Y-%m-%d')
st.write(f"*(Current Date: {current_date})*")

# --- Debug Info ---
st.sidebar.subheader("Debug Info")
st.sidebar.write(f"Python Executable: `{sys.executable}`")
st.sidebar.write(f"Python Version: `{sys.version}`")
try:
    st.sidebar.write(f"Pyreadstat Version: `{pyreadstat.__version__}`")
    st.sidebar.write(f"Pyreadstat Location: `{pyreadstat.__file__}`")
    st.sidebar.write(f"Has 'read_xpt': `{hasattr(pyreadstat, 'read_xpt')}`")
    st.sidebar.write(f"Has 'read_xport': `{hasattr(pyreadstat, 'read_xport')}`")
    st.sidebar.write(f"Has 'write_sas7dat': `{hasattr(pyreadstat, 'write_sas7dat')}`")
except Exception as e:
    st.sidebar.error(f"Error fetching pyreadstat debug info: {e}")

# --- Sidebar Settings ---
st.sidebar.header("Configuration")
conversion_mode = st.sidebar.radio(
    "Select Conversion Mode:",
    ("Convert Directory", "Convert Single File"),
    key="mode"
)

input_dir_str = ""
output_dir_str = ""
uploaded_file = None

if conversion_mode == "Convert Directory":
    st.sidebar.subheader("Directory Conversion Settings")
    input_dir_str = st.sidebar.text_input("Input Directory Path:", placeholder="/path/to/xpt_files")
    output_dir_str = st.sidebar.text_input("Output Directory Path:", placeholder="/path/to/output")
else:
    st.sidebar.subheader("Single File Conversion Settings")
    uploaded_file = st.sidebar.file_uploader("Choose an XPT file", type=['xpt', 'XPT'])
    output_dir_str = st.sidebar.text_input("Output Directory Path:", placeholder="/path/to/output")

# --- Conversion Button ---
st.sidebar.divider()
if st.sidebar.button("Convert File(s)", key="convert_button"):

    # Validate output directory
    if not output_dir_str:
        st.error("⚠️ Please provide the Output Directory Path.")
    else:
        try:
            output_path = Path(output_dir_str)
            output_path.mkdir(parents=True, exist_ok=True)
            st.info(f"Output directory: `{output_path.resolve()}`")
        except Exception as e:
            st.error(f"❌ Invalid Output Directory Path: {e}")
            output_path = None

    if output_path:
        if conversion_mode == "Convert Directory":
            if not input_dir_str:
                st.error("⚠️ Please provide the Input Directory Path.")
            else:
                input_path = Path(input_dir_str)
                if not input_path.is_dir():
                    st.error("❌ Provided input path is not a valid directory.")
                else:
                    st.subheader(f"Converting Directory: {input_path.resolve()}")
                    try:
                        xpt_files = list(input_path.glob('[!.]*.[xX][pP][tT]'))
                        if not xpt_files:
                            st.warning("⚠️ No `.xpt` files found.")
                        else:
                            st.write(f"Found {len(xpt_files)} `.xpt` file(s).")
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            success_count, error_count = 0, 0
                            error_details = []

                            for i, xpt_file in enumerate(xpt_files):
                                base_name = xpt_file.stem
                                output_file = output_path / f"{base_name}.sas7bdat"
                                status_text.text(f"Processing {xpt_file.name}...")

                                try:
                                    df, meta = pyreadstat.read_xport(str(xpt_file))
                                    column_labels = getattr(meta, 'column_names_to_labels', None)
                                    file_label = getattr(meta, 'file_label', None)

                                    pyreadstat.write_sas7bdat(
                                        df,
                                        str(output_file),
                                        column_labels=column_labels,
                                        file_label=file_label
                                    )
                                    st.success(f"✅ {xpt_file.name} converted.")
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"❌ Failed to convert {xpt_file.name}: {e}")
                                    error_count += 1
                                    error_details.append(f"{xpt_file.name}: {e}")

                                progress_bar.progress((i + 1) / len(xpt_files))

                            status_text.text("✅ Conversion complete.")
                            st.divider()
                            st.subheader("Summary")
                            st.success(f"Converted: {success_count}")
                            if error_count:
                                st.error(f"Errors: {error_count}")
                                with st.expander("Error Details"):
                                    for detail in error_details:
                                        st.code(detail)

                    except Exception as e:
                        st.error(f"❌ Error during directory conversion: {e}")

        else:  # Single File
            if uploaded_file is None:
                st.error("⚠️ Please upload a `.xpt` file.")
            else:
                st.subheader(f"Converting: {uploaded_file.name}")
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xpt") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        temp_path = tmp.name

                    df, meta = pyreadstat.read_xport(temp_path)
                    column_labels = getattr(meta, 'column_names_to_labels', None)
                    file_label = getattr(meta, 'file_label', None)

                    output_file = output_path / f"{Path(uploaded_file.name).stem}.sas7bdat"
                    pyreadstat.write_sas7bdat(
                        df,
                        str(output_file),
                        column_labels=column_labels,
                        file_label=file_label
                    )

                    st.success(f"✅ File saved to `{output_file.resolve()}`")

                except Exception as e:
                    st.error(f"❌ Error converting file: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

# --- Instructions ---
st.sidebar.divider()
st.sidebar.markdown("**How to Use:**")
if conversion_mode == "Convert Directory":
    st.sidebar.markdown("""
1. Select **Convert Directory**.
2. Provide input/output folder paths.
3. Click **Convert File(s)**.
""")
else:
    st.sidebar.markdown("""
1. Select **Convert Single File**.
2. Upload a `.xpt` file.
3. Provide an output folder path.
4. Click **Convert File(s)**.
""")
