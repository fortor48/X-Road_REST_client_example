# Проєкт Взаємодії з Трембітою

Цей проєкт демонструє взаємодію з системою Трембіта через Python. Включає функції для завантаження ASIC файлів, генерації ключів і сертифікатів, а також відправки запитів до сервісів для управління інформацією про користувачів.

## Зміст

- [Встановлення](#Встановлення)
- [Конфігурація](#конфігурація)
- [Використання](#використання)
  - [Завантаження ASIC файлу](#завантаження-asic-файлу)
  - [Генерація ключа і сертифіката](#генерація-ключа-і-сертифіката)
  - [Отримання інформації про користувача](#отримання-інформації-про-користувача)
  - [Редагування інформації про користувача](#редагування-інформації-про-користувача)
  - [Видалення користувача](#видалення-користувача)
  - [Додавання користувача](#додавання-користувача)
  - [Отримання метаданих файлів](#отримання-метаданих-файлів)
- [Логування](#логування)
- [Ліцензія](#ліцензія)

## Встановлення

### Ручне встеновлення

1. Клонуйте репозиторій:

    ```bash
    git clone https://github.com/kshypachov/web-client_trembita_sync.git
    ```

2. Перейдіть в директорію проєкту:

    ```bash
    cd web-client_trembita_sync
    ```

3. Встановіть залежності:

    ```bash
    pip install -r requirements.txt
    ```

### Встановлення за допомогою скрипту

## Конфігурація

Створіть файл конфігурації `config.ini` в корені проєкту з наступним вмістом:

```ini
[trembita]

# Протокол, який використовується для взаємодії з Трембіта (https або http)
protocol = https

# Хост системи Трембіта
# можливі варіанти: 192.168.1.1, trembita.example.gov.ua
host = your_trembita_host

# Ідентифікатор мети для взаємодії з Трембіта через ПМДПД, може бути не заданим якщо обмін відбувається без використання цього модулю.
purpose_id = your_purpose_id

# Шлях до ssl сертифікатів для взаємодії з Трембіта (директорія буде створена, якщо вона не існує)
cert_path = path/to/your/certificates

# Шлях для збереження ASIC файлів (директорія буде створена, якщо вона не існує)
asic_path = path/to/save/asic/files

[client]
# xRoadInstance (SEVDEIR чи SEVDEIR-TEST)
instance_name = your_client_instance

# memberClass (GOV) 
member_class = your_client_member_class

# memberCode - код ЄДРПОУ організації-клієнта
member_code = your_client_member_code

# subsystemCode - код підсистеми ШБО організації-клієнта, що буде використовуватись для запитів
subsystem_code = your_client_subsystem_code

[service]
# xRoadInstance (SEVDEIR чи SEVDEIR-TEST)
instance_name = your_service_instance

# memberClass (GOV) 
member_class = your_service_member_class

# memberCode - код ЄДРПОУ організації-клієнта
member_code = your_service_member_code
 
# subsystemCode - код підсистеми ШБО організації-постачальника, на якій опубліковано сервіс
subsystem_code = your_service_subsystem_code

# serviceCode - назва сервісу, що опублікований на ШБО організації-постачальника
service_code = your_service_code

# serviceVersion - версія сервісу, якщо є (зазвичай сервіс не має версії). Якщо сервіс не має версії - не задавати значення
service_version = your_service_version

[logging]
# Шлях до файлу логування
filename = path/to/client.log

# filemode визначає режим, в якому буде відкритий файл логування.
# 'a' - дописувати до існуючого файлу
# 'w' - перезаписувати файл кожен раз
filemode = a

# format визначає формат повідомлень логування.
# %(asctime)s - час створення запису
# %(name)s - ім'я логгера
# %(levelname)s - рівень логування
# %(message)s - текст повідомлення
# %(pathname)s - шлях до файлу, звідки було зроблено виклик
# %(lineno)d - номер рядка у файлі, звідки було зроблено виклик
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s

# dateformat визначає формат дати в повідомленнях логування.
# Можливі формати можуть бути такими, як:
# %Y-%m-%d %H:%M:%S - 2023-06-25 14:45:00
# %d-%m-%Y %H:%M:%S - 25-06-2023 14:45:00
dateformat = %Y-%m-%d %H:%M:%S

# level визначає рівень логування.
# DEBUG - докладна інформація, корисна для налагодження
# INFO - загальна інформація про хід програми
# WARNING - попередження про можливі проблеми
# ERROR - помилки, які завадили нормальному виконанню
# CRITICAL - критичні помилки, що призводять до завершення програми
level = DEBUG
```

## Використання

### Завантаження ASIC файлу

Для завантаження ASIC файлу використовуйте функцію `download_asic_from_trembita`:

```python
from your_module import download_asic_from_trembita, Config

config = Config('config.ini')
download_asic_from_trembita('path/to/save/asic/files', 'query_id', config)
```

### Генерація ключа і сертифіката

Для генерації ключа і сертифіката використовуйте функцію `generate_key_cert`:

```python
from your_module import generate_key_cert

generate_key_cert('key.pem', 'cert.pem', 'path/to/save/keys')
```

### Отримання інформації про користувача

Для отримання інформації про користувача використовуйте функцію `get_person_from_service`:

```python
from your_module import get_person_from_service, Config

config = Config('config.ini')
person_info = get_person_from_service('parameter', 'value', config)
print(person_info)
```

### Редагування інформації про користувача

Для редагування інформації про користувача використовуйте функцію `edit_person_in_service`:

```python
from your_module import edit_person_in_service, Config

config = Config('config.ini')
response = edit_person_in_service({'field': 'value'}, config)
print(response)
```

### Видалення користувача

Для видалення користувача використовуйте функцію `service_delete_person`:

```python
from your_module import service_delete_person, Config

config = Config('config.ini')
response = service_delete_person({'unzr': 'user_id'}, config)
print(response)
```

### Додавання користувача

Для додавання користувача використовуйте функцію `service_add_person`:

```python
from your_module import service_add_person, Config

config = Config('config.ini')
response = service_add_person({'field': 'value'}, config)
print(response)
```

### Отримання метаданих файлів

Для отримання метаданих файлів в директорії використовуйте функцію `get_files_with_metadata`:

```python
from your_module import get_files_with_metadata

files_metadata = get_files_with_metadata('path/to/directory')
print(files_metadata)
```

## Логування

Логування налаштовано з використанням параметрів, вказаних у `config.ini`. Всі логи зберігаються у файлі, вказаному в конфігурації.

## Ліцензія

Цей проєкт ліцензований під ліцензією MIT. Дивіться файл [LICENSE](LICENSE) для деталей.
```
