#!/bin/bash

# Зупинка та вимкнення Flask-приложения
sudo systemctl stop flask-app
sudo systemctl disable flask-app

# Видалення Unit файлу systemd
sudo rm /etc/systemd/system/flask-app.service

# Перезагрузка systemd для застосування змін
sudo systemctl daemon-reload

# Видалення репозиторію та віртуального оточення
cd ../
rm -rf web-client_trembita_sync

# Видалення встановлених пакетів
sudo apt remove -y git python3 python3-pip python3-venv

# Очищення системи від непотрібних пакетів та залежностей
sudo apt autoremove -y
sudo apt clean

echo "Flask-приложение та всі його залежності успішно видалені."