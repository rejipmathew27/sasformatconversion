#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Print each command before executing it (useful for debugging)
set -x

# --- Install R Packages ---
echo "Running R script to install packages..."

# Execute the R script to install 'haven'
Rscript install_packages.R
# Check the exit code of the R script explicitly
if [ $? -ne 0 ]; then
  echo "ERROR: Rscript install_packages.R failed!"
  exit 1
fi
echo "R package installation script finished successfully."


# --- Install rpy2 using pip AFTER R is installed ---
echo "Installing rpy2 using pip..."

# Run pip install and check exit code
pip install rpy2
if [ $? -ne 0 ]; then
  echo "ERROR: pip install rpy2 failed!"
  exit 1
fi
echo "rpy2 installation finished successfully."


# --- Turn off command printing ---
set +x

echo "Setup script completed successfully."

# --- Add any other setup commands below if needed ---

