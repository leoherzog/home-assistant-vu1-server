#!/usr/bin/with-contenv bashio

# Set the log level
export LOG_LEVEL=$(bashio::config 'log_level')

# Start the Python application
python3 -m ha-vu1