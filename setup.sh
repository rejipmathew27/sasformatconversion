#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Install R Packages ---
# This script assumes that R itself has already been installed
# via the apt.txt file (r-base, r-base-dev).
# It runs an R script (install_packages.R) which contains
# the actual R commands to install packages from CRAN.

echo "Running R script to install packages..."

# Execute the R script to install 'haven'
# Ensure install_packages.R is in the same directory (root of your repo)
Rscript install_packages.R

echo "R package installation script finished."

# --- Add any other setup commands below if needed ---

