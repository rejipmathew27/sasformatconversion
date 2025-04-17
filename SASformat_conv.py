import streamlit as st
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr, isinstalled
import rpy2.rinterface_lib.callbacks
import logging
import os
import tempfile

# Configure R's output to be captured by Python's logging
# This helps in debugging R errors within the Streamlit environment
logging.basicConfig(level=logging.INFO)
rpy2.rinterface_lib.callbacks.consolewrite_print = lambda s: logging.info(f"R Console: {s}")
rpy2.rinterface_lib.callbacks.consolewrite_warnerror = lambda s: logging.error(f"R Error/Warning: {s}")

# --- R Setup ---
try:
    # Check if 'haven' package is installed in R
    if not isinstalled('haven'):
        st.warning("R package 'haven' is not installed. Attempting to install...")
        # Import the 'utils' package for installation
        utils = importr('utils')
        # Choose a CRAN mirror (0 corresponds to the Cloud mirror)
        utils.chooseCRANmirror(ind=0)
        # Install 'haven'
        utils.install_packages('haven')
        st.success("Successfully installed 'haven'. Please refresh the page if needed.")

    # Import the 'haven' package
    haven = importr('haven')
    st.sidebar.success("R 'haven' package loaded successfully.")

except Exception as e:
    st.error(f"Error setting up R environment or loading/installing 'haven': {e}")
    st.error("Please ensure R is installed and accessible by rpy2, and that you have permissions to install R packages if needed.")
    st.stop() # Stop execution if R setup fails

# --- Streamlit App UI ---
st.title("XPT to SAS7BDAT Converter")
st.write("Upload a SAS Transport file (.xpt) and convert it to a SAS Data Set file (.sas7bdat) using the R 'haven' package.")

uploaded_file = st.file_uploader("Choose an .xpt file", type="xpt")
output_filename_base = st.text_input("Enter desired output filename (without extension)", "output_data")

convert_button = st.button("Convert File")

# --- Conversion Logic ---
if convert_button and uploaded_file is not None and output_filename_base:
    try:
        # Create temporary files safely
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xpt") as temp_xpt:
            temp_xpt.write(uploaded_file.getvalue())
            temp_xpt_path = temp_xpt.name

        # Define the output path in a temporary directory as well
        temp_dir = tempfile.mkdtemp()
        output_sas_path = os.path.join(temp_dir, f"{output_filename_base}.sas7bdat")

        st.info(f"Reading XPT file: {uploaded_file.name}")
        st.info(f"Temporary XPT path: {temp_xpt_path}")
        st.info(f"Output SAS path: {output_sas_path}")

        # --- R Conversion using rpy2 ---
        try:
            # Read the .xpt file using haven::read_xpt
            r_code_read = f"data <- haven::read_xpt('{temp_xpt_path.replace('\\', '/')}')" # Ensure forward slashes for R paths
            robjects.r(r_code_read)
            st.success("Successfully read XPT file into R.")

            # Write the data to .sas7bdat using haven::write_sas
            r_code_write = f"haven::write_sas(data, '{output_sas_path.replace('\\', '/')}')" # Ensure forward slashes
            robjects.r(r_code_write)
            st.success(f"Successfully wrote SAS7BDAT file: {output_filename_base}.sas7bdat")

            # --- Provide Download Link ---
            with open(output_sas_path, "rb") as f:
                st.download_button(
                    label=f"Download {output_filename_base}.sas7bdat",
                    data=f,
                    file_name=f"{output_filename_base}.sas7bdat",
                    mime="application/octet-stream" # A generic binary mime type
                )

        except Exception as r_error:
            st.error(f"Error during R processing: {r_error}")
            # Attempt to capture more detailed R error messages if possible
            try:
                # Get the last R error message
                get_last_error = robjects.r('geterrmessage()')
                st.error(f"Last R error message: {get_last_error[0]}")
            except Exception as e_r_err:
                st.warning(f"Could not retrieve specific R error message: {e_r_err}")


    except Exception as e:
        st.error(f"An error occurred during file handling or conversion: {e}")

    finally:
        # --- Cleanup Temporary Files ---
        if 'temp_xpt_path' in locals() and os.path.exists(temp_xpt_path):
            try:
                os.remove(temp_xpt_path)
                # st.info(f"Cleaned up temporary XPT file: {temp_xpt_path}") # Optional: for debugging
            except Exception as e_clean_xpt:
                st.warning(f"Could not remove temporary XPT file {temp_xpt_path}: {e_clean_xpt}")

        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                # Remove the generated SAS file first
                if 'output_sas_path' in locals() and os.path.exists(output_sas_path):
                    os.remove(output_sas_path)
                # Then remove the temporary directory
                os.rmdir(temp_dir)
                # st.info(f"Cleaned up temporary directory: {temp_dir}") # Optional: for debugging
            except Exception as e_clean_dir:
                st.warning(f"Could not remove temporary directory {temp_dir}: {e_clean_dir}")


elif convert_button:
    st.warning("Please upload an .xpt file and provide an output filename.")

st.sidebar.markdown("---")
st.sidebar.header("Requirements")
st.sidebar.markdown("""
* **Python:** `streamlit`, `rpy2`
* **R:** Base R installation
* **R Package:** `haven`
""")
st.sidebar.markdown("---")
st.sidebar.header("Notes")
st.sidebar.markdown("""
* This app requires R to be installed on the system where Streamlit is running.
* `rpy2` must be configured correctly to find your R installation.
* The R package `haven` is required. The script attempts to install it if missing, but this might require specific permissions or network access depending on your environment.
* Running this on platforms like Streamlit Community Cloud requires specifying R and its packages in the deployment configuration (e.g., using a `packages.txt` file for R packages).
""")
