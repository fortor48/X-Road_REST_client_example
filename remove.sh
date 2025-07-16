#!/bin/bash

DAEMON_NAME=x-road_rest_client_example
WORKING_FOLDER=X-Road_REST_client_example

# Function to read values from config.ini
function read_ini() {
    FILENAME=$1
    SECTION=$2
    KEY=$3
    awk -F "=" '/\['$SECTION'\]/{a=1}a==1&&$1~/'$KEY'/{print $2;exit}' $FILENAME
}

# Check if config.ini file exists
CONFIG_FILE="config.ini"
if [[ ! -f $CONFIG_FILE ]]; then
    echo "config.ini file not found!"
    exit 1
fi

# Read the filename parameter from the [logging] section
LOG_FILE=$(read_ini $CONFIG_FILE "logging" "filename")

# Stop and disable the Flask application
sudo systemctl stop $DAEMON_NAME
sudo systemctl disable $DAEMON_NAME

# Remove the log file
if [[ -f $LOG_FILE ]]; then
    sudo rm $LOG_FILE
    echo "Log file $LOG_FILE successfully removed."
else
    echo "Log file $LOG_FILE not found."
fi
sudo rm -f $LOG_FILE

# Remove the systemd unit file
sudo rm /etc/systemd/system/$DAEMON_NAME.service

# Reload systemd to apply changes
sudo systemctl daemon-reload

# Remove the repository and virtual environment
cd ../
sudo rm -rf $WORKING_FOLDER

# Remove installed packages
#sudo apt remove -y git python3 python3-pip python3-venv

# Clean up the system from unused packages and dependencies
sudo apt autoremove -y
sudo apt clean

echo "$DAEMON_NAME and all its dependencies have been successfully removed."