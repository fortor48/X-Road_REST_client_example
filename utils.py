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
from cryptography.hazmat.primitives import serialization
import datetime
import os
import logging

logger = logging.getLogger(__name__)


class CustomResponse:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body

    def __repr__(self):
        return f"Response(status_code={self.status_code}, body={self.body})"


class Config:
    def __init__(self, filename):
        self.parser = configparser.ConfigParser(interpolation=None)
        self.parser.read(filename)

        # Зчитування конфігураційних параметрів як атрибутів класу
        # Секція параметрів взаємодії з шлюзом безпечного обміну Трембіти
        self.trembita_protocol = self.parser.get('trembita', 'protocol')
        self.trembita_host = self.parser.get('trembita', 'host')
        self.trembita_purpose = self.parser.get('trembita', 'purpose_id')  # For MDPD
        self.cert_path = self.parser.get('trembita', 'cert_path')
        self.asic_path = self.parser.get('trembita', 'asic_path')
        self.cert_file = self.parser.get('trembita', 'cert_file')
        self.key_file = self.parser.get('trembita', 'key_file')
        self.tembita_cert_file = self.parser.get('trembita', 'trembita_cert_file')
        # Секція ідентифікаторів клієнтської підсистеми Трембіти
        self.client_instance = self.parser.get('client', 'instance')
        self.client_org_type = self.parser.get('client', 'memberClass')
        self.client_org_code = self.parser.get('client', 'memberCode')
        self.client_org_sub = self.parser.get('client', 'subsystemCode')
        # Секція ідентифікаторів сервісу
        self.service_instance = self.parser.get('service', 'instance')
        self.service_org_type = self.parser.get('service', 'memberClass')
        self.service_org_code = self.parser.get('service', 'memberCode')
        self.service_org_sub = self.parser.get('service', 'subsystemCode')
        self.service_org_name = self.parser.get('service', 'serviceCode')
        self.service_org_version = self.parser.get('service', 'serviceVersion')
        # Секція параметрів логування роботи додатку
        self.log_filename = self.parser.get('logging', 'filename')
        self.log_filemode = self.parser.get('logging', 'filemode')
        self.log_format = self.parser.get('logging', 'format')
        self.log_dateformat = self.parser.get('logging', 'dateformat')
        self.log_level = self.parser.get('logging', 'level')

    def get(self, section, option):
        return self.parser.get(section, option)


def configure_logging(config_instance):
    log_filename = config_instance.log_filename
    log_filemode = config_instance.log_filemode
    log_format = config_instance.log_format
    log_datefmt = config_instance.log_dateformat
    log_level = config_instance.log_level

    logging.basicConfig(
        filename=log_filename,
        filemode=log_filemode,
        format=log_format,
        datefmt=log_datefmt,
        level=getattr(logging, log_level, logging.DEBUG)
    )
    logger.info("Логування налаштовано")


def download_asic_from_trembita(queryId: str, config_instance):
    # https: // sec1.gov / signature? & queryId = abc12345 & xRoadInstance = SEVDEIR-TEST & memberClass = GOV & memberCode =
    # 12345678 & subsystemCode = SUB

    asics_dir = config_instance.asic_path  # Отримуємо з конфігураційного файлу путь до директорії куди слід зберігати asic контейнери

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
            # Надсилаємо GET-запит для завантаження файла з архівом повідомлень
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


def generate_key_cert(key: str, crt: str, path: str):
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

        # Збереження сертифікату у файл
        crt_full_path = os.path.join(path, crt)

        with open(crt_full_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        logger.info(f"Сертифікат збережено у {crt_full_path}")
    except IOError as e:
        logger.error(f"Помилка під час збереження ключа або сертифікату: {e}")
        raise


def get_uxp_headers_from_config(config_instance) -> dict:
    logger.debug("Формування заголовків UXP")
    uxp_client_header_name = "UXP-Client"
    uxp_service_header_name = "UXP-Service"

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

    headers = {
        uxp_client_header_name: uxp_client_header_value,
        uxp_service_header_name: uxp_service_header_value
    }
    logger.debug(f"Заголовки UXP сформовано: {headers}")
    return headers


def get_uxp_query_params() -> dict:
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
    logger.debug("Формування базового URL ШБО Трембіти клієнта")
    if config_instance.trembita_protocol == "https":
        uri = f"https://{config_instance.trembita_host}/restapi"
    else:
        uri = f"http://{config_instance.trembita_host}/restapi"
    logger.debug(f"Базовий URI Trembita: {uri}")
    return uri


def get_person_from_service(parameter: str, value: str, config_instance) -> list:
    base_uri = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = f"{base_uri}/{parameter}/{value}"
    encoded_url = quote(url, safe=':/')
    logger.info(f"Отримання інформації про особу з сервісу за параметром: {parameter} та значенням: {value}")
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.get(encoded_url, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
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
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()
    url = base_url

    logger.debug(f"Редагування інформації про особу: {data}")
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.put(url, json=data, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
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
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = f"{base_url}/unzr/{data['unzr']}"

    logger.info(f"Видалення інформації про особу з id: {data['unzr']}")
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.delete(url, headers=headers, params=query_params,
                                       cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                             os.path.join(config_instance.cert_path, config_instance.key_file)),
                                       verify=os.path.join(config_instance.cert_path,
                                                           config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            response = requests.delete(url, headers=headers, params=query_params)
    except Exception as e:
        json_body = {"Error while sending HTTP DELETE": f"{e}"}
        logger.error(f"Помилка під час видалення інформації про особу: {e}")
        return CustomResponse(status_code=500, body=json_body)

    logger.info(f"Видалення завершено, отримано відповідь: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def service_add_person(data: dict, config_instance) -> CustomResponse:
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = base_url
    logger.info(f"Додавання нової особи: {data}")
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.post(url, json=data, headers=headers, params=query_params,
                                     cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                           os.path.join(config_instance.cert_path, config_instance.key_file)),
                                     verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))

            download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
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
    logger.info(f"Перевірка існування директорії: {dir_path}")
    if not os.path.exists(dir_path):
        # Створюємо директорію, якщо її немає
        os.makedirs(dir_path)
        logger.info(f"Директорія '{dir_path}' була створена.")
    else:
        logger.info(f"Директорія '{dir_path}' вже існує.")


def get_files_with_metadata(directory):
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
