import configparser
import uuid
import re
from urllib.parse import quote
import requests
#from requests import Response

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import datetime
import os
import logging
import sys

logger = logging.getLogger(__name__)


class CustomResponse:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body

    def __repr__(self):
        return f"Response(status_code={self.status_code}, body={self.body})"


class Config:
    def __init__(self, filename):
        # Перевіряємо, чи встановлена змінна оточення USE_ENV_CONFIG в true
        use_env_config = os.getenv("USE_ENV_CONFIG", "false").lower() == "true"

        if not use_env_config:
            # Якщо змінна USE_ENV_CONFIG не встановлена в true, читаємо конфігураційний файл
            self.parser = configparser.ConfigParser(interpolation=None)
            self.parser.read(filename)
        else:
            # Якщо змінна USE_ENV_CONFIG встановлена в true, ігноруємо конфігураційний файл
            self.parser = None

        # Функція для отримання значення з змінної оточення або конфігураційного файлу
        def get_config_value(section, option, default=None, required=False):
            env_var = f"{section.upper()}_{option.upper()}"
            if use_env_config:
                # Якщо використовуємо змінні оточення, зчитуємо значення тільки з них
                value = os.getenv(env_var, default)
            else:
                # Якщо змінна USE_ENV_CONFIG пуста, використовуємо тільки файл конфігурації
                value = self.parser.get(section, option, fallback=default)

            # Перевірка на обов'язковість параметра
            if required and not value:
                err_str = f"Помилка: Змінна оточення '{section.upper()}_{option.upper()}' є обовʼязковою. Задайте її значення будь ласка."
                logger.critical(err_str)
                raise ValueError(err_str)#

            return value

        # Зчитування конфігурації
        # Секція Трембіта
        self.trembita_protocol = get_config_value('trembita', 'protocol', required=True)
        self.trembita_host = get_config_value('trembita', 'host', required=True)
        self.trembita_purpose = get_config_value('trembita', 'purpose_id', '')
        self.cert_path = get_config_value('trembita', 'cert_path', 'certs')
        self.asic_path = get_config_value('trembita', 'asic_path', 'asic')
        self.cert_file = get_config_value('trembita', 'cert_file', 'cert.pem')
        self.key_file = get_config_value('trembita', 'key_file', 'key.pem')
        self.tembita_cert_file = get_config_value('trembita', 'trembita_cert_file' , 'trembita.pem')
        # Секція ідентифікаторів клієнтської підсистеми
        self.client_instance = get_config_value('client', 'instance', required=True)
        self.client_org_type = get_config_value('client', 'memberClass', required=True)
        self.client_org_code = get_config_value('client', 'memberCode', required=True)
        self.client_org_sub = get_config_value('client', 'subsystemCode', required=True)
        # Секція ідентифікаторів сервісу
        self.service_instance = get_config_value('service', 'instance', required=True)
        self.service_org_type = get_config_value('service', 'memberClass', required=True)
        self.service_org_code = get_config_value('service', 'memberCode', required=True)
        self.service_org_sub = get_config_value('service', 'subsystemCode', required=True)
        self.service_org_name = get_config_value('service', 'serviceCode', required=True)
        self.service_org_version = get_config_value('service', 'serviceVersion')
        # Параметри логування
        self.log_filename = get_config_value('logging', 'filename')
        self.log_filemode = get_config_value('logging', 'filemode', 'a')
        self.log_format = get_config_value('logging', 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_dateformat = get_config_value('logging', 'dateformat', '%Y-%m-%d %H:%M:%S')
        self.log_level = get_config_value('logging', 'level', 'INFO', required=True)


    def get(self, section, option):
        return self.parser.get(section, option)


def configure_logging(config_instance):
    log_filename = config_instance.log_filename
    log_filemode = config_instance.log_filemode
    log_format = config_instance.log_format
    log_datefmt = config_instance.log_dateformat
    log_level = config_instance.log_level

    #Якщо log_filename не передано, логування відбувається у консоль.
    if log_filename:
        # Логування у файл
        logging.basicConfig(
            filename=log_filename,
            filemode=log_filemode,
            format=log_format,
            datefmt=log_datefmt,
            level=getattr(logging, log_level, logging.INFO)
        )
        logger.info("Логування налаштовано")

    else:
        # Логування в консоль для Docker
        logging.basicConfig(
            format=log_format,
            datefmt=log_datefmt,
            level=log_level,
            handlers=[logging.StreamHandler()]  # Вывод в stdout
        )

def download_asic_from_trembita(queryId: str, config_instance):
    # https: // sec1.gov / signature? & queryId = abc12345 & xRoadInstance = SEVDEIR-TEST & memberClass = GOV & memberCode =
    # 12345678 & subsystemCode = SUB
    # Отримання ASIC контейнера з ШБО за допомогою GET-запиту
    asics_dir = config_instance.asic_path  # Отримуємо з конфігураційного файлу шлях до директорії, куди слід зберігати asic контейнери

    query_params = {
        "queryId": queryId,
        "xRoadInstance": config_instance.client_instance,
        "memberClass": config_instance.client_org_type,
        "memberCode": config_instance.client_org_code,
        "subsystemCode": config_instance.client_org_sub
    }

    if config_instance.trembita_protocol == "https":
        url = f"https://{config_instance.trembita_host}/signature"
        logger.info(f"Спроба завантажити ASIC з ШБО з URL: {url} та параметрами: {query_params}")

        try:
            # Надсилаємо GET-запит для завантаження файлу з архівом повідомлень
            response = requests.get(url, stream=True, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))
            response.raise_for_status()

            logger.info(f"Успішно отримано відповідь від сервера з кодом: {response.status_code}")

            # Спроба отримати ім'я файлу з заголовку Content-Disposition
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                # Паттерн для визначення імені файлу
                filename_match = re.findall('filename="(.+)"', content_disposition)
                if filename_match:
                    local_filename = filename_match[0]
                else:
                    local_filename = 'downloaded_file.ext'
            else:
                # Якщо заголовку немає, використовуємо ім'я за замовчуванням
                local_filename = 'downloaded_file.ext'

            # Відкриваємо локальний файл в режимі запису байтів
            with open(f"{asics_dir}/{local_filename}", 'wb') as file:
                # Проходимо по частинах відповіді і записуємо їх у файл
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logger.info(f'Файл успішно завантажено та збережено як:  {local_filename}')
        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка під час завантаження файлу: {e}")
            raise
    else:
        logger.error("Функція download_asic_from_trembita працює тільки з протоколом https")
        raise ValueError("Ця функція процює тільки якщо протокол роботи з ШБО Трембіти - https")


def generate_key_cert_rsa(key: str, crt: str, path: str):
    # Генерація особистого ключа та сертифіката
    logger.info("Генерація ключа та сертифіката")
    logger.debug(f"Імʼя файлу ключа: {key}, імʼя файлу сертифіката: {crt}, директорія: {path}")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Створення x509 об'єкту для сертифікату
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "UA"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Kyiv"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Kyiv"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "The Best Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.com"),
    ])

    # Створення самопідписаного сертифікату
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Сертифікат буде чинним протягом одного року
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Збереження особистого ключа у файл
    key_full_path = os.path.join(path, key)
    try:
        with open(key_full_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        logger.info(f"Ключ збережено у {key_full_path}")

        # Збереження сертифіката у файл
        crt_full_path = os.path.join(path, crt)

        with open(crt_full_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        logger.info(f"Сертифікат збережено у {crt_full_path}")
    except IOError as e:
        logger.error(f"Помилка під час збереження ключа або сертифікату: {e}")
        raise


def generate_key_cert(key: str, crt: str, path: str):
    # Генерація особистого ключа та сертифіката
    logger.info("Генерація ключа та сертифіката ECDSA")
    logger.debug(f"Імʼя файлу ключа: {key}, імʼя файлу сертифіката: {crt}, директорія: {path}")

    # Генерація приватного ключа ECDSA
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Створення x509 об'єкту для сертифікату
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "UA"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Kyiv"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Kyiv"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "The Best Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.com"),
    ])

    # Створення самопідписаного сертифікату
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Сертифікат буде чинним протягом одного року
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Збереження особистого ключа у файл
    key_full_path = os.path.join(path, key)
    try:
        with open(key_full_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        logger.info(f"Ключ збережено у {key_full_path}")

        # Збереження сертифіката у файл
        crt_full_path = os.path.join(path, crt)
        with open(crt_full_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        logger.info(f"Сертифікат збережено у {crt_full_path}")
    except IOError as e:
        logger.error(f"Помилка під час збереження ключа або сертифікату: {e}")
        raise

def get_uxp_headers_from_config(config_instance) -> dict:
    # Формування заголовків UXP для запитів
    logger.debug("Формування заголовків UXP")
    uxp_client_header_name = "UXP-Client"
    uxp_service_header_name = "UXP-Service"
    uxp_sevice_purpose_id = "Uxp-Purpose-Ids"

    uxp_client_header_value = (
        f"{config_instance.client_instance}/"
        f"{config_instance.client_org_type}/"
        f"{config_instance.client_org_code}/"
        f"{config_instance.client_org_sub}"
    )

    base_service_value = (
        f"{config_instance.service_instance}/"
        f"{config_instance.service_org_type}/"
        f"{config_instance.service_org_code}/"
        f"{config_instance.service_org_sub}/"
        f"{config_instance.service_org_name}"
    )

    if config_instance.service_org_version:
        uxp_service_header_value = f"{base_service_value}/{config_instance.service_org_version}"
    else:
        uxp_service_header_value = base_service_value

    purpose_id_value = config_instance.trembita_purpose

    headers = {
        uxp_client_header_name: uxp_client_header_value,
        uxp_service_header_name: uxp_service_header_value,
        uxp_sevice_purpose_id: purpose_id_value
    }
    logger.debug(f"Заголовки UXP сформовано: {headers}")
    return headers

def get_xroad_headers_from_config(config_instance) -> dict:
    # Формування заголовків UXP для запитів
    logger.debug("Формування заголовків UXP")
    xroad_client_header_name = "X-Road-Client"
    xroad_query_id_header_name = "X-Road-Id"
    xroad_query_user_id_header_name = "X-Road-UserId"
    xroad_query_issue_header_name = "X-Road-Issue"
    ##uxp_service_header_name = "UXP-Service"
    ##uxp_sevice_purpose_id = "Uxp-Purpose-Ids"

    xroad_client_header_value = (
        f"{config_instance.client_instance}/"
        f"{config_instance.client_org_type}/"
        f"{config_instance.client_org_code}/"
        f"{config_instance.client_org_sub}"
    )

    xroad_query_id_header_value = f"{config_instance.client_instance}-"+str(uuid.uuid4())

    xroad_query_user_id_header_value = "Flask_client"  # Any value can be set. During message exchange
    # this user id will be stored by security server within message log

    # xroad_query_issue_header_value = "example0"  # Identifies received application, issue or document that
    # was the cause of the service request. This field may be used by the client information system
    # to connect service requests (and responses) to working procedures.

    #base_service_value = (
    #    f"{config_instance.service_instance}/"
    #    f"{config_instance.service_org_type}/"
    #    f"{config_instance.service_org_code}/"
    #    f"{config_instance.service_org_sub}/"
    #    f"{config_instance.service_org_name}"
    #)

    #if config_instance.service_org_version:
    #    uxp_service_header_value = f"{base_service_value}/{config_instance.service_org_version}"
    #else:
    #    uxp_service_header_value = base_service_value

    #purpose_id_value = config_instance.trembita_purpose

    headers = {
        xroad_client_header_name: xroad_client_header_value,
        xroad_query_id_header_name: xroad_query_id_header_value,
        xroad_query_user_id_header_name: xroad_query_user_id_header_value,
        # xroad_query_issue_header_name: xroad_query_issue_header_value,
        #uxp_service_header_name: uxp_service_header_value,
        #uxp_sevice_purpose_id: purpose_id_value
    }
    logger.debug(f"Заголовки UXP сформовано: {headers}")
    return headers

def get_uxp_query_params() -> dict:
    # Генерація унікальних параметрів запиту для UXP
    logger.debug("Генерація UXP параметрів запиту")
    uxp_query_id_name = "queryId"
    uxp_user_id_name = "userId"

    uxp_query_id_value = str(uuid.uuid4())
    uxp_user_id_value = "Flask_client"  # можна задати будь-яке значення, при обміні це імʼя
    # буде збережено на ШБО, та його можна буде побачити, наприклад, за допомогою інструмента перевірки транзакцій UXP Verifier.

    params = {
        uxp_query_id_name: uxp_query_id_value,
        uxp_user_id_name: uxp_user_id_value
    }

    logger.debug(f"UXP параметри запиту згенеровано: {params}")
    return params


def get_base_trembita_uri(config_instance) -> str:
    # Формування базового URI для доступу до сервісу Трембіта
    logger.debug("Формування базового URL ШБО Трембіти клієнта")
    if config_instance.trembita_protocol == "https":
        uri = f"https://{config_instance.trembita_host}/restapi"
    else:
        uri = f"http://{config_instance.trembita_host}/restapi"
    logger.debug(f"Базовий URI Trembita: {uri}")
    return uri


def get_base_xroad_uri(config_instance) -> str:
    # Формування базового URI для доступу до сервісу Трембіта
    logger.debug("Формування базового URL ШБО Трембіти клієнта")
    if config_instance.trembita_protocol == "https":
        uri = f"https://{config_instance.trembita_host}:8443"
    else:
        uri = f"http://{config_instance.trembita_host}:8080"
    logger.debug(f"Базовий URI Trembita: {uri}")
    return uri

def get_rest_xroad_uri(config_instance) -> str:
    # Composing the URI for REST API call via security server using base URI
    logger.debug("Формування базового URL ШБО Трембіти клієнта")
    uri = get_base_xroad_uri(config_instance) + f"/r1/{config_instance.service_instance}/{config_instance.service_org_type}/{config_instance.service_org_code}/{config_instance.service_org_sub}/{config_instance.service_org_name}"
    logger.debug(f"Базовий URI Trembita: {uri}")
    return uri


def get_person_from_service(parameter: str, value: str, config_instance) -> list:
    # Отримання інформації про особу за параметром через сервіс Трембіта
    base_uri = get_rest_xroad_uri(config_instance)+f"/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None # get_uxp_query_params()

    url = f"{base_uri}/{parameter}/{value}"
    encoded_url = quote(url, safe=':/')
    logger.info(f"Отримання інформації про особу з сервісу за параметром: {parameter} та значенням: {value}")
    try:
        if config_instance.trembita_protocol == "https":
            # Відправлення HTTPS запиту для отримання даних про особу
            response = requests.get(encoded_url, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Відправлення HTTP запиту для отримання даних про особу
            response = requests.get(encoded_url, headers=headers, params=query_params)


    except Exception as e:
        logger.error(f"Помилка під час отримання інформації про особу: {e}")
        raise ValueError(f"Error while sending HTTP GET: {e}")

    if response.status_code == 200:
        json_data = response.json()
        message_list = json_data.get('message', [])
        logger.info("Запит на отримання інформації оброблено")
        logger.debug(f"Отримано інформацію про особу: {message_list}")
        return message_list
    logger.error(f"Отримано HTTP код: {response.status_code}, повідомлення про помилку: {response.text}")
    raise ValueError(f"Recieved HTTP code: {response.status_code}, error message: {response.text}")


def edit_person_in_service(data: dict, config_instance) -> CustomResponse:
    # Редагування інформації про особу через сервіс Трембіта
    base_url = get_rest_xroad_uri(config_instance)+f"/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None #get_uxp_query_params()
    url = base_url

    logger.debug(f"Редагування інформації про особу: {data}")
    try:
        if config_instance.trembita_protocol == "https":
            # Відправлення HTTPS запиту для редагування інформації про особу
            response = requests.put(url, json=data, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Відправлення HTTP запиту для редагування інформації про особу
            response = requests.put(url, json=data, headers=headers, params=query_params)

    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка під час редагування інформації про особу: {e}")
        raise ValueError(f"Error while sending HTTP PUT: {e}")

    if not response.content:
        json_body = {"message": "Nothing to display"}
        logger.info("Редагування завершено, отримана пуста відповідь.")
        return CustomResponse(status_code=response.status_code, body=json_body)

    logger.info(f"Редагування завершено, отримано відповідь: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def service_delete_person(data: dict, config_instance) -> CustomResponse:
    # Видалення інформації про особу через сервіс Трембіта
    base_url = get_rest_xroad_uri(config_instance)+f"/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None #get_uxp_query_params()

    url = f"{base_url}/unzr/{data['unzr']}"

    logger.info(f"Видалення інформації про особу з id: {data['unzr']}")
    try:
        if config_instance.trembita_protocol == "https":
            # Відправлення HTTPS запиту для видалення особи
            response = requests.delete(url, headers=headers, params=query_params,
                                       cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                             os.path.join(config_instance.cert_path, config_instance.key_file)),
                                       verify=os.path.join(config_instance.cert_path,
                                                           config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Відправлення HTTP запиту для видалення особи
            response = requests.delete(url, headers=headers, params=query_params)
    except Exception as e:
        json_body = {"Error while sending HTTP DELETE": f"{e}"}
        logger.error(f"Помилка під час видалення інформації про особу: {e}")
        return CustomResponse(status_code=500, body=json_body)

    logger.info(f"Видалення завершено, отримано відповідь: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def service_add_person(data: dict, config_instance) -> CustomResponse:
    # Додавання нової особи через сервіс Трембіта
    base_url = get_rest_xroad_uri(config_instance)+f"/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None #get_uxp_query_params()

    url = base_url
    logger.info(f"Додавання нової особи: {data}")
    try:
        if config_instance.trembita_protocol == "https":
            # Відправлення HTTPS запиту для додавання нової особи
            response = requests.post(url, json=data, headers=headers, params=query_params,
                                     cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                           os.path.join(config_instance.cert_path, config_instance.key_file)),
                                     verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Відправлення HTTP запиту для додавання нової особи
            response = requests.post(url, json=data, headers=headers, params=query_params)

        if response.status_code > 400:
            logger.error(f"Виникла помилка при додаванні особи, код: {response.status_code}")

    except Exception as e:
        json_body = {"Error while sending HTTP POST": f"{e}"}
        logger.error(f"Помилка під час додавання нової особи: {e}")
        return CustomResponse(status_code=500, body=json_body)

    logger.info(f"Обробку запиту додавання завершено, отримано відповідь: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def create_dir_if_not_exist(dir_path: str):
    # Створення директорії, якщо вона не існує
    logger.info(f"Перевірка існування директорії: {dir_path}")
    if not os.path.exists(dir_path):
        # Створюємо директорію, якщо її немає
        os.makedirs(dir_path)
        logger.info(f"Директорія '{dir_path}' була створена.")
    else:
        logger.info(f"Директорія '{dir_path}' вже існує.")


def get_files_with_metadata(directory):
    # Отримання списку файлів з метаданими у вказаній директорії
    logger.info(f"Отримання метаданих файлів у директорії: {directory}")
    files_metadata = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        creation_time = os.path.getctime(filepath)
        creation_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        files_metadata.append({
            'name': filename,
            'creation_time': creation_time_str
        })
    logger.info(f"Метадані файлів отримано: {files_metadata}")
    return files_metadata
