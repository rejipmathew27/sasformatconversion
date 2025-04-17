import streamlit as st
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr # Only import 'importr' initially
import rpy2.rinterface_lib.callbacks
import logging
import os
import tempfile

# Configure R's output to be captured by Python's logging
# This helps in debugging R errors within the Streamlit environment
logging.basicConfig(level=logging.INFO)
rpy2.rinterface_lib.callbacks.consolewrite_print = lambda s: logging.info(f"R Console: {s}")
rpy2.rinterface_lib.callbacks.consolewrite_warnerror = lambda s: logging.error(f"R Error/Warning: {s}")

# --- Streamlit App UI ---
st.title("XPT to SAS7BDAT Converter")
st.write("Upload a SAS Transport file (.xpt) and convert it to a SAS Data Set file (.sas7bdat) using the R 'haven' package.")

uploaded_file = st.file_uploader("Choose an .xpt file", type="xpt")
output_filename_base = st.text_input("Enter desired output filename (without extension)", "output_data")

convert_button = st.button("Convert File")

# --- Conversion Logic ---
if convert_button and uploaded_file is not None and output_filename_base:
    r_is_ok = False
    haven_loaded = False
    haven = None # Initialize haven to None

    # --- Step 1: Try basic R interaction ---
    try:
        st.info("Initializing R interface...")
        # Check R version as a simple test
        r_version = robjects.r('R.version.string')
        st.info(f"R Version Check OK: {r_version[0]}")
        r_is_ok = True # Mark basic R interaction as successful
    except Exception as e_r_init:
        st.error(f"Error during basic R initialization/interaction: {e_r_init}")
        st.error("This might indicate a problem with rpy2 context or finding R.")
        st.stop()

    # --- Step 2: If basic R works, try loading 'haven' ---
    if r_is_ok:
        try:
            st.info("Loading 'haven' package...")
            # Import the 'haven' package *here*
            haven = importr('haven')
            st.sidebar.success("R 'haven' package loaded successfully for this conversion.")
            haven_loaded = True # Mark haven loading as successful
        except Exception as e_haven_load:
            st.error(f"Error loading R package 'haven': {e_haven_load}")
            st.error("This often relates to rpy2 contextvars or conversion rules issues.")
            st.stop() # Stop execution if haven loading fails

    # --- Step 3: Proceed only if R is OK and haven is loaded ---
    if r_is_ok and haven_loaded and haven is not None:
        # --- Proceed with file handling and conversion ---
        temp_xpt_path = None
        temp_dir = None
        output_sas_path = None
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
                # Ensure paths use forward slashes for R
                r_temp_xpt_path = temp_xpt_path.replace('\\', '/')
                r_output_sas_path = output_sas_path.replace('\\', '/')

                # Read the .xpt file using haven::read_xpt
                # Use the 'haven' object imported above
                st.info("Calling R: haven::read_xpt...")
                # Assign the R function to a Python variable for clarity
                read_xpt_r = robjects.r(f"haven::read_xpt('{r_temp_xpt_path}')")
                # Assign the result to an R variable 'data' in the R global environment
                robjects.r.assign("data", read_xpt_r)
                st.success("Successfully read XPT file into R.")

                # Write the data to .sas7bdat using haven::write_sas
                st.info("Calling R: haven::write_sas...")
                # Call write_sas directly using the haven object or via robjects.r
                # Using robjects.r might be slightly more robust in some contexts
                r_code_write = f"haven::write_sas(data, '{r_output_sas_path}')"
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
            # Use the paths defined within the main try block
            if temp_xpt_path and os.path.exists(temp_xpt_path):
                try:
                    os.remove(temp_xpt_path)
                except Exception as e_clean_xpt:
                    st.warning(f"Could not remove temporary XPT file {temp_xpt_path}: {e_clean_xpt}")

            if output_sas_path and os.path.exists(output_sas_path):
                 try:
                    os.remove(output_sas_path)
                 except Exception as e_clean_sas:
                    st.warning(f"Could not remove temporary SAS file {output_sas_path}: {e_clean_sas}")

            if temp_dir and os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
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
* R and required packages should be installed via `apt.txt` and `setup.sh`/`install_packages.R` for deployment.
* `rpy2` interacts with R; runtime errors can occur if the R environment has issues.
""")
