#!/bin/bash

# Creating a systemd unit file for the system service
SERVICE_NAME=x-road_rest_client_example
SERVICE_FILE=/etc/systemd/system/$SERVICE_NAME.service
GIT_REPO=https://github.com/fortor48/X-Road_REST_client_example.git
WORKING_FOLDER=X-Road_REST_client_example

# Updating packages and installing required dependencies
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

# Cloning the repository
git clone $GIT_REPO
cd $WORKING_FOLDER

# Creating and activating a virtual environment
python3 -m venv venv
source venv/bin/activate

# Installing dependencies
pip install -r requirements.txt

# Creating the systemd unit file
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Flask Application
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reloading systemd to apply the changes
sudo systemctl daemon-reload

# Enabling and providing instructions to start the web client
sudo systemctl enable $SERVICE_NAME
echo "✔️ Service $SERVICE_NAME is enabled."
echo "ℹ️  Please fill the configuration file if needed."
echo "▶️  Start service with:"
echo "    sudo systemctl start $SERVICE_NAME"