#!/bin/bash

# This script is intended to be called by cron. 
# It explicitly sets a conda environment and run a python script using absolute file  paths. 

# NOTE: Adapt to whatever server this is running on
PROJ_DIR="/home/zbv/code/CATT/03-Other/transit-analysis/log-gtfsrt"

# 1. Source the conda initialization script directly
source /home/zbv/miniforge3/etc/profile.d/conda.sh

# 2. Activate your specific environment
conda activate gtfsrt

# 3. Run your script using absolute paths
time python "$PROJ_DIR/src/download_gtfs_realtime.py" "$PROJ_DIR/output/gtfs-realtime/gtfs-rt" "$PROJ_DIR/config.json" --exclude_stop_updates 