#!/bin/bash

# Обновление пакетов и установка необходимых зависимостей
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

# Клонирование репозитория
git clone https://github.com/kshypachov/web-client_trembita_sync.git
cd web-client_trembita_sync

# Создание и активация виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание Unit файла для systemd
SERVICE_FILE=/etc/systemd/system/flask-app.service

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Flask Application
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="FLASK_APP=web-client_trembita_sync"
Environment="FLASK_ENV=development"
ExecStart=$(pwd)/venv/bin/flask run --host=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка systemd для применения изменений
sudo systemctl daemon-reload

# Включение и запуск Flask-приложения
sudo systemctl enable flask-app
sudo systemctl start flask-app