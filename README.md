# Trembita Interaction Project

Этот проект демонстрирует взаимодействие с системой Трембита через Python. Включает функции для загрузки ASIC файлов, генерации ключей и сертификатов, а также отправки запросов к сервисам для управления информацией о пользователях.

## Оглавление

- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
  - [Загрузка ASIC файла](#загрузка-asic-файла)
  - [Генерация ключа и сертификата](#генерация-ключа-и-сертификата)
  - [Получение информации о пользователе](#получение-информации-о-пользователе)
  - [Редактирование информации о пользователе](#редактирование-информации-о-пользователе)
  - [Удаление пользователя](#удаление-пользователя)
  - [Добавление пользователя](#добавление-пользователя)
  - [Получение метаданных файлов](#получение-метаданных-файлов)
- [Логирование](#логирование)
- [Лицензия](#лицензия)

## Установка

1. Клонируйте репозиторий:

    ```bash
    git clone https://github.com/ваш_пользователь/трембита-проект.git
    ```

2. Перейдите в директорию проекта:

    ```bash
    cd трембита-проект
    ```

3. Установите зависимости:

    ```bash
    pip install -r requirements.txt
    ```

## Конфигурация

Создайте файл конфигурации `config.ini` в корне проекта со следующим содержимым:

```ini
[trembita]
protocol = https
host = your_trembita_host
purpose_id = your_purpose_id
cert_path = path/to/your/certificates
asic_path = path/to/save/asic/files

[client]
instance_name = your_client_instance
member_class = your_client_member_class
member_code = your_client_member_code
subsystem_code = your_client_subsystem_code

[service]
instance_name = your_service_instance
member_class = your_service_member_class
member_code = your_service_member_code
subsystem_code = your_service_subsystem_code
service_code = your_service_code
service_version = your_service_version

[logging]
filename = trembita.log
filemode = a
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
dateformat = %Y-%m-%d %H:%M:%S
level = DEBUG
```

## Использование

### Загрузка ASIC файла

Для загрузки ASIC файла используйте функцию `download_asic_from_trembita`:

```python
from your_module import download_asic_from_trembita, Config

config = Config('config.ini')
download_asic_from_trembita('path/to/save/asic/files', 'query_id', config)
```

### Генерация ключа и сертификата

Для генерации ключа и сертификата используйте функцию `generate_key_cert`:

```python
from your_module import generate_key_cert

generate_key_cert('key.pem', 'cert.pem', 'path/to/save/keys')
```

### Получение информации о пользователе

Для получения информации о пользователе используйте функцию `get_person_from_service`:

```python
from your_module import get_person_from_service, Config

config = Config('config.ini')
person_info = get_person_from_service('parameter', 'value', config)
print(person_info)
```

### Редактирование информации о пользователе

Для редактирования информации о пользователе используйте функцию `edit_person_in_service`:

```python
from your_module import edit_person_in_service, Config

config = Config('config.ini')
response = edit_person_in_service({'field': 'value'}, config)
print(response)
```

### Удаление пользователя

Для удаления пользователя используйте функцию `service_delete_person`:

```python
from your_module import service_delete_person, Config

config = Config('config.ini')
response = service_delete_person({'unzr': 'user_id'}, config)
print(response)
```

### Добавление пользователя

Для добавления пользователя используйте функцию `service_add_person`:

```python
from your_module import service_add_person, Config

config = Config('config.ini')
response = service_add_person({'field': 'value'}, config)
print(response)
```

### Получение метаданных файлов

Для получения метаданных файлов в директории используйте функцию `get_files_with_metadata`:

```python
from your_module import get_files_with_metadata

files_metadata = get_files_with_metadata('path/to/directory')
print(files_metadata)
```

## Логирование

Логирование настроено с использованием параметров, указанных в `config.ini`. Все логи сохраняются в файле, указанном в конфигурации.

## Лицензия

Этот проект лицензирован под лицензией MIT. Смотрите файл [LICENSE](LICENSE) для подробностей.
```
