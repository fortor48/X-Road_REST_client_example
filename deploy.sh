#!/bin/bash

# Створення Unit файлу системної служби для systemd
SERVICE_NAME=x-road_rest_client_example
SERVICE_FILE=/etc/systemd/system/$SERVICE_NAME.service
GIT_REPO=https://github.com/fortor48/X-Road_REST_client_example.git
WORKING_FOLDER=X-Road_REST_client_example

# Оновлення пакетів і встановлення необхідних залежностей
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

# Клонування репозиторію
git clone $GIT_REPO
cd $WORKING_FOLDER

# Створення та активація віртуального оточення
python3 -m venv venv
source venv/bin/activate

# Встановлення залежностей
pip install -r requirements.txt


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

# Перезавантаження systemd для застосування змін
sudo systemctl daemon-reload

# Увімкнення та запуск вебклієнту
sudo systemctl enable $SERVICE_NAME
echo "✔️ Service $SERVICE_NAME is enabled."
echo "ℹ️  Please fill the configuration file if needed."
echo "▶️  Start service with:"
echo "    sudo systemctl start $SERVICE_NAME"

