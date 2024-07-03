#!/bin/bash

# Функція для зчитування значень з config.ini
function read_ini() {
    FILENAME=$1
    SECTION=$2
    KEY=$3
    awk -F "=" '/\['$SECTION'\]/{a=1}a==1&&$1~/'$KEY'/{print $2;exit}' $FILENAME
}

# Перевірка наявності файлу config.ini
CONFIG_FILE="config.ini"
if [[ ! -f $CONFIG_FILE ]]; then
    echo "Файл config.ini не знайдено!"
    exit 1
fi

# Зчитування параметра filename з секції [logging]
LOG_FILE=$(read_ini $CONFIG_FILE "logging" "filename")

# Зупинка та вимкнення Flask-приложения
sudo systemctl stop flask-app
sudo systemctl disable flask-app

# Видалення файлу журналу
if [[ -f $LOG_FILE ]]; then
    sudo rm $LOG_FILE
    echo "Файл журналу $LOG_FILE успішно видалено."
else
    echo "Файл журналу $LOG_FILE не знайдено."
fi
sudo rm -f $LOG_FILE

# Видалення Unit файлу systemd
sudo rm /etc/systemd/system/flask-app.service

# Перезагрузка systemd для застосування змін
sudo systemctl daemon-reload

# Видалення репозиторію та віртуального оточення
cd ../
sudo rm -rf web-client_trembita_sync

# Видалення встановлених пакетів
sudo apt remove -y git python3 python3-pip python3-venv

# Очищення системи від непотрібних пакетів та залежностей
sudo apt autoremove -y
sudo apt clean

echo "Flask-приложение та всі його залежності успішно видалені."