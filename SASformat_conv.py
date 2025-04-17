import streamlit as st
import pandas as pd
import pyreadstat
from pathlib import Path
import os
import tempfile # Required for handling single uploaded file

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("SAS XPT to SAS7BDAT Converter")
st.write("""
    Convert SAS XPT transport files (`.xpt`) to SAS7BDAT dataset files (`.sas7bdat`).
    You can either convert all `.xpt` files within a specified directory
    or upload and convert a single `.xpt` file.
""")
st.write(f"*(Current Date: {pd.Timestamp.now().strftime('%Y-%m-%d')})*") # Add current date info

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
conversion_mode = st.sidebar.radio(
    "Select Conversion Mode:",
    ("Convert Directory", "Convert Single File"),
    key="mode",
    help="Choose 'Convert Directory' to process all XPT files in a folder. Choose 'Convert Single File' to upload and convert one specific XPT file."
)

# --- Mode-Specific Inputs ---
input_dir_str = ""
output_dir_str = ""
uploaded_file = None

if conversion_mode == "Convert Directory":
    st.sidebar.subheader("Directory Conversion Settings")
    input_dir_str = st.sidebar.text_input(
        "Enter Input Directory Path (containing .xpt files):",
        key="input_dir",
        placeholder="e.g., C:\\path\\to\\xpt_files or /home/user/xpt_data"
    )
    output_dir_str = st.sidebar.text_input(
        "Enter Output Directory Path (for .sas7bdat files):",
        key="output_dir",
        placeholder="e.g., C:\\path\\to\\sas_files or /home/user/sas_output"
    )
else: # Convert Single File
    st.sidebar.subheader("Single File Conversion Settings")
    uploaded_file = st.sidebar.file_uploader(
        "Choose an XPT file to convert:",
        type=['xpt', 'XPT'],
        key="file_uploader"
    )
    output_dir_str = st.sidebar.text_input(
        "Enter Output Directory Path (where the .sas7bdat file will be saved):",
        key="single_output_dir",
        placeholder="e.g., C:\\path\\to\\sas_files or /home/user/sas_output"
    )

# --- Conversion Button ---
st.sidebar.divider()
if st.sidebar.button("Convert File(s)", key="convert_button"):

    # --- Output Directory Validation (Common for both modes) ---
    output_path = None
    valid_output_dir = False
    if not output_dir_str:
        st.error("⚠️ Please provide the Output Directory Path.")
    else:
        try:
            output_path = Path(output_dir_str)
            # Attempt to create the directory now to validate the path
            output_path.mkdir(parents=True, exist_ok=True)
            st.info(f"Output directory set to: {output_path.resolve()}")
            valid_output_dir = True
        except Exception as e:
             st.error(f"❌ Invalid or inaccessible Output Directory Path: {output_dir_str}. Error: {e}")

    if valid_output_dir:
        # --- Execute Logic Based on Mode ---
        if conversion_mode == "Convert Directory":
            # --- Input Directory Validation ---
            valid_input_dir = False
            if not input_dir_str:
                st.error("⚠️ Please provide the Input Directory Path for Directory Conversion mode.")
            else:
                input_path = Path(input_dir_str)
                if not input_path.is_dir():
                    st.error(f"❌ Input path is not a valid directory: {input_dir_str}")
                else:
                    valid_input_dir = True
                    st.info(f"Input directory set to: {input_path.resolve()}")

            if valid_input_dir:
                 # --- Run Directory Conversion Logic ---
                 st.subheader(f"Converting Directory: {input_path.resolve()}")
                 try:
                    # Find all .xpt files (case-insensitive search using glob)
                    xpt_files = list(input_path.glob('[!.]*[xX][pP][tT]'))
                    # Filter out hidden files (starting with '.') just in case

                    if not xpt_files:
                        st.warning(f"⚠️ No `.xpt` files found in the input directory: {input_path.resolve()}")
                    else:
                        st.write(f"Found {len(xpt_files)} `.xpt` file(s) to convert.")

                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        success_count = 0
                        error_count = 0
                        error_details = []
                        results_container = st.container() # To hold success/error messages

                        for i, xpt_file_path in enumerate(xpt_files):
                            base_filename = xpt_file_path.stem # Gets filename without extension
                            output_filename = f"{base_filename}.sas7bdat"
                            output_file_path = output_path / output_filename

                            status_text.text(f"Processing ({i+1}/{len(xpt_files)}): {xpt_file_path.name} -> {output_filename}...")

                            try:
                                # --- CORRECTED READ CALL ---
                                # Read XPT file (Removed the problematic encoding argument)
                                df, meta = pyreadstat.read_xpt(str(xpt_file_path))
                                # --------------------------

                                # Prepare metadata (access meta AFTER it's returned)
                                column_labels = getattr(meta, 'column_names_to_labels', None)
                                file_label = getattr(meta, 'file_label', None)
                                # You could extract more metadata from 'meta' if needed, e.g., formats:
                                # variable_formats = getattr(meta, 'variable_formats', None)
                                # Use it in write_sas7bdat if the parameter exists

                                # Write SAS7BDAT file
                                pyreadstat.write_sas7bdat(
                                    df,
                                    str(output_file_path),
                                    column_labels=column_labels,
                                    file_label=file_label
                                    # Add other relevant metadata parameters if needed and supported
                                )

                                results_container.success(f"✅ Converted: {xpt_file_path.name} -> {output_filename}")
                                success_count += 1

                            except Exception as e:
                                results_container.error(f"❌ Error converting {xpt_file_path.name}: {e}")
                                error_count += 1
                                error_details.append(f"{xpt_file_path.name}: {e}")

                            # Update progress bar
                            progress_bar.progress((i + 1) / len(xpt_files))

                        # --- Summary ---
                        status_text.text("Directory conversion process finished.")
                        st.divider()
                        st.subheader("Conversion Summary")
                        st.success(f"Successfully converted files: {success_count}")
                        if error_count > 0:
                            st.error(f"Files with errors: {error_count}")
                            with st.expander("Show Error Details"):
                                for detail in error_details:
                                    st.code(detail)
                        else:
                           if success_count > 0:
                               st.info("No errors encountered during conversion.")

                 except Exception as e:
                    st.error(f"❌ An unexpected error occurred during the directory conversion process: {e}")

        elif conversion_mode == "Convert Single File":
            # --- Input File Validation ---
            if uploaded_file is None:
                st.error("⚠️ Please upload an XPT file for Single File Conversion mode.")
            else:
                 # --- Run Single File Conversion Logic ---
                st.subheader(f"Converting Single File: {uploaded_file.name}")
                st.info(f"Output will be saved to: {output_path.resolve()}")

                temp_file_path = None # Initialize path for temp file
                try:
                    # Ensure output directory exists (double-check)
                    output_path.mkdir(parents=True, exist_ok=True)

                    # Prepare output file path
                    base_filename = Path(uploaded_file.name).stem
                    output_filename = f"{base_filename}.sas7bdat"
                    output_file_path = output_path / output_filename

                    status_text = st.empty()
                    status_text.text(f"Processing: {uploaded_file.name} -> {output_filename}...")

                    # Save uploaded file to a temporary file because pyreadstat needs a path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xpt") as tmp:
                        tmp.write(uploaded_file.getvalue()) # Write bytes from uploaded file
                        temp_file_path = tmp.name # Get the path of the temp file

                    # Check if temp file was created
                    if not temp_file_path or not os.path.exists(temp_file_path):
                         raise FileNotFoundError("Failed to create temporary file for processing.")

                    # --- CORRECTED READ CALL ---
                    # Read temporary XPT file (Removed the problematic encoding argument)
                    df, meta = pyreadstat.read_xpt(temp_file_path)
                    # --------------------------

                    # Prepare metadata (access meta AFTER it's returned)
                    column_labels = getattr(meta, 'column_names_to_labels', None)
                    file_label = getattr(meta, 'file_label', None)
                    # variable_formats = getattr(meta, 'variable_formats', None) # Example

                    # Write SAS7BDAT file
                    pyreadstat.write_sas7bdat(
                        df,
                        str(output_file_path),
                        column_labels=column_labels,
                        file_label=file_label
                        # Add other parameters like variable_formats if needed
                    )
                    status_text.empty() # Clear processing message
                    st.success(f"✅ Successfully converted **{uploaded_file.name}** to **{output_filename}** in directory `{output_path.resolve()}`")

                except Exception as e:
                    status_text.empty() # Clear processing message
                    st.error(f"❌ Error converting {uploaded_file.name}: {e}")
                finally:
                    # Clean up the temporary file if it was created
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.remove(temp_file_path)
                        except Exception as e_clean:
                            # Log or warn if cleanup fails, but don't let it crash the app
                            st.warning(f"Could not remove temporary file {temp_file_path}: {e_clean}")

# --- Instructions ---
st.sidebar.divider()
st.sidebar.markdown("**How to Use:**")
if conversion_mode == "Convert Directory":
    st.sidebar.markdown(
        """
        1.  Select **Convert Directory** mode above.
        2.  Enter the full path to the folder containing your `.xpt` files in the **Input Directory Path** field.
        3.  Enter the full path to the folder where you want the `.sas7bdat` files to be saved in the **Output Directory Path** field. (The folder will be created if it doesn't exist).
        4.  Click the **Convert File(s)** button.
        5.  Progress and results will be displayed on the main page.
        """
    )
else: # Convert Single File
    st.sidebar.markdown(
        """
        1.  Select **Convert Single File** mode above.
        2.  Click **'Browse files'** to upload your single `.xpt` file.
        3.  Enter the full path to the folder where you want the converted `.sas7bdat` file to be saved in the **Output Directory Path** field. (The folder will be created if it doesn't exist).
        4.  Click the **Convert File(s)** button.
        5.  The result will be displayed on the main page.
        """
    )
