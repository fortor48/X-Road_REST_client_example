import configparser
import uuid
import re
from urllib.parse import quote
import requests
from requests import Response

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime


class Response:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body

    def __repr__(self):
        return f"Response(status_code={self.status_code}, body={self.body})"


class Config:
    def __init__(self, filename):
        self.parser = configparser.ConfigParser()
        self.parser.read(filename)

        # Присваивание конфигурационных параметров как атрибутов класса
        self.trembita_protocol = self.parser.get('trembita', 'protocol')
        self.trembita_host = self.parser.get('trembita', 'host')
        self.cert_path = self.parser.get('trembita', 'cert_path')
        self.trembita_purpose = self.parser.get('trembita', 'purpose_id')

        self.client_instance = self.parser.get('client', 'instance_name')
        self.client_org_type = self.parser.get('client', 'member_class')
        self.client_org_code = self.parser.get('client', 'member_code')
        self.client_org_sub = self.parser.get('client', 'subsystem_code')

        self.service_instance = self.parser.get('service', 'instance_name')
        self.service_org_type = self.parser.get('service', 'member_class')
        self.service_org_code = self.parser.get('service', 'member_code')
        self.service_org_sub = self.parser.get('service', 'subsystem_code')
        self.service_org_name = self.parser.get('service', 'service_code')
        self.service_org_version = self.parser.get('service', 'service_version')

    def get(self, section, option):
        return self.parser.get(section, option)


def download_asic_from_trembita(asics_dir: str, queryId: str, config_instance):
    # https: // sec1.gov / signature? & queryId = abc12345 & xRoadInstance = EE & memberClass = ENT & memberCode =
    # CLIENT1 & subsystemCode = SUB
    query_params = {
        "queryId": queryId,
        "xRoadInstance": config_instance.client_instance,
        "memberClass": config_instance.client_org_type,
        "memberCode": config_instance.client_org_code,
        "subsystemCode": config_instance.client_org_sub
    }

    if config_instance.trembita_protocol == "https":
        url = f"https://{config_instance.trembita_host}/signature"

        # Отправляем GET-запрос для скачивания файла
        response = requests.get(url, stream=True, params=query_params,
                                cert=(f"{config_instance.cert_path}/crt.pem", f"{config_instance.cert_path}/key.pem"),
                                verify=f"{config_instance.cert_path}/trembita.pem")

        # Проверяем, успешно ли выполнен запрос
        if response.status_code == 200:
            # Пытаемся получить имя файла из заголовка Content-Disposition
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                # Паттерн для извлечения имени файла
                filename_match = re.findall('filename="(.+)"', content_disposition)
                if filename_match:
                    local_filename = filename_match[0]
                else:
                    local_filename = 'downloaded_file.ext'
            else:
                # Если заголовка нет, используем имя по умолчанию
                local_filename = 'downloaded_file.ext'

            # Открываем локальный файл в режиме записи байтов
            with open(f"{asics_dir}/{local_filename}", 'wb') as file:
                # Проходим по частям ответа и записываем их в файл
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f'Файл успешно скачан и сохранен как {local_filename}')
        else:
            print(f'Не удалось скачать файл. Статус код: {response.status_code}')
    else:
        raise ValueError("This function works only when trembita_protocol is https!!")


def generate_key_cert(key: str, crt: str, path: str):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Создание объекта для сертификата
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "UA"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Kiev"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Kiev"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "The Best Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.com"),
    ])

    # Создание самоподписанного сертификата
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
        # Сертификат будет действителен в течение одного года
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Сохранение приватного ключа в файл
    key_full_path = f"{path}/{key}"

    with open(key_full_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Сохранение сертификата в файл
    crt_full_path = f"{path}/{crt}"

    with open(crt_full_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def get_uxp_headers_from_config(config_instance) -> dict:
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

    return {
        uxp_client_header_name: uxp_client_header_value,
        uxp_service_header_name: uxp_service_header_value
    }


def get_uxp_query_params() -> dict:
    uxp_query_id_name = "queryId"
    uxp_user_id_name = "userId"

    uxp_query_id_value = str(uuid.uuid4())
    uxp_user_id_value = "Flask_client"  # можна задати будьяке значення, при обміні це імʼя
    # буде збережено на ШБО, та його можна буде побачити наприклад за допомогою веріфаєра.

    return {
        uxp_query_id_name: uxp_query_id_value,
        uxp_user_id_name: uxp_user_id_value
    }


def get_base_trembita_uri(config_instance) -> str:
    if config_instance.trembita_protocol == "https":
        uri = f"https://{config_instance.trembita_host}/restapi"
    else:
        uri = f"http://{config_instance.trembita_host}/restapi"
    return uri


def get_person_from_service(parameter: str, value: str, config_instance) -> list:
    base_uri = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = f"{base_uri}/{parameter}/{value}"
    encoded_url = quote(url, safe=':/')
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.get(encoded_url, headers=headers, params=query_params,
                                    cert=(f"{config_instance.cert_path}/crt.pem", f"{config_instance.cert_path}/key.pem"),
                                    verify=f"{config_instance.cert_path}/trembita.pem")
        else:
            response = requests.get(encoded_url, headers=headers, params=query_params)

        download_asic_from_trembita("asic", query_params.get('queryId'), config_instance)
    except Exception as e:
        raise ValueError(f"Error while sending HTTP GET: {e}")

    if response.status_code == 200:
        json_data = response.json()
        message_list = json_data.get('message', [])
        return message_list

    raise ValueError(f"Recieved HTTP code: {response.status_code}, error message: {response.text}")


def edit_person_in_service(data: dict, config_instance) -> Response:
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()
    url = base_url

    try:
        if config_instance.trembita_protocol == "https":
            response = requests.put(url, json=data, headers=headers, params=query_params,
                                    cert=(f"{config_instance.cert_path}/crt.pem", f"{config_instance.cert_path}/key.pem"),
                                    verify=f"{config_instance.cert_path}/trembita.pem")
        else:
            response = requests.put(url, json=data, headers=headers, params=query_params)

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error while sending HTTP PUT: {e}")

    if not response.content:
        json_body = {"message": "Nothing to display"}
        return Response(status_code=response.status_code, body=json_body)

    return Response(status_code=response.status_code, body=response.json())


def service_delete_person(data: dict, config_instance) -> Response:
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = base_url + "/unzr/" + str(data["unzr"])
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.delete(url, headers=headers, params=query_params,
                                    cert=(f"{config_instance.cert_path}/crt.pem", f"{config_instance.cert_path}/key.pem"),
                                    verify=f"{config_instance.cert_path}/trembita.pem")
        else:
            response = requests.delete(url, headers=headers, params=query_params)
    except Exception as e:
        json_body = {"Error while sending HTTP DELETE": f"{e}"}
        return Response(status_code=500, body=json_body)

    return Response(status_code=response.status_code, body=response.json())


def service_add_person(data: dict, config_instance) -> Response:
    base_url = get_base_trembita_uri(config_instance)
    headers = get_uxp_headers_from_config(config_instance)
    query_params = get_uxp_query_params()

    url = base_url
    try:
        if config_instance.trembita_protocol == "https":
            response = requests.post(url, json=data, headers=headers, params=query_params,
                                    cert=(f"{config_instance.cert_path}/crt.pem", f"{config_instance.cert_path}/key.pem"),
                                    verify=f"{config_instance.cert_path}/trembita.pem")
        else:
            response = requests.post(url, json=data, headers=headers, params=query_params)
    except Exception as e:
        json_body = {"Error while sending HTTP POST": f"{e}"}
        return Response(status_code=500, body=json_body)
    return Response(status_code=response.status_code, body=response.json())