# install_packages.R
#
# This script installs R packages required by the Streamlit application.
# It is intended to be called by setup.sh during the container build process
# on platforms like Streamlit Community Cloud.

# Specify the CRAN mirror to use (avoids interactive prompts)
# Using the RStudio Cloud mirror, which is globally distributed
options(repos = c(CRAN = "https://cran.rstudio.com/"))

# --- Install required packages ---

# Install 'haven' if it's not already installed
# 'haven' is needed for reading/writing SAS files (.xpt, .sas7bdat)
if (!requireNamespace("haven", quietly = TRUE)) {
  cat("Installing R package: haven\n")
  install.packages("haven", dependencies = TRUE)
} else {
  cat("R package 'haven' is already installed.\n")
}

# --- Add installations for other R packages below if needed ---
# Example:
# if (!requireNamespace("dplyr", quietly = TRUE)) {
#   cat("Installing R package: dplyr\n")
#   install.packages("dplyr", dependencies = TRUE)
# } else {
#   cat("R package 'dplyr' is already installed.\n")
# }

cat("Finished installing R packages.\n")

