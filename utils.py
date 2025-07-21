import configparser
import uuid
import re
from urllib.parse import quote
import requests
# from requests import Response

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
        # Check if the environment variable USE_ENV_CONFIG is set to true
        use_env_config = os.getenv("USE_ENV_CONFIG", "false").lower() == "true"

        if not use_env_config:
            # If USE_ENV_CONFIG is not set to true, read the config file
            self.parser = configparser.ConfigParser(interpolation=None)
            self.parser.read(filename)
        else:
            # If USE_ENV_CONFIG is true, ignore config file
            self.parser = None

        # Function to get value from environment variable or config file
        def get_config_value(section, option, default=None, required=False):
            env_var = f"{section.upper()}_{option.upper()}"
            if use_env_config:
                # If using environment variables, read only from them
                value = os.getenv(env_var, default)
            else:
                # If USE_ENV_CONFIG is empty, use only config file
                value = self.parser.get(section, option, fallback=default)

            # Check if parameter is required
            if required and not value:
                err_str = f"Error: Environment variable '{section.upper()}_{option.upper()}' is required. Please provide a value."
                logger.critical(err_str)
                raise ValueError(err_str)

            return value

        # Reading configuration
        # X-Road section
        self.xroad_protocol = get_config_value('xroad', 'protocol', required=True)
        self.xroad_host = get_config_value('xroad', 'host', required=True)
        #self.trembita_purpose = get_config_value('xroad', 'purpose_id', '')
        self.cert_path = get_config_value('xroad', 'cert_path', 'certs')
        self.asic_path = get_config_value('xroad', 'asic_path', 'asic')
        self.cert_file = get_config_value('xroad', 'cert_file', 'cert.pem')
        self.key_file = get_config_value('xroad', 'key_file', 'key.pem')
        self.xroad_cert_file = get_config_value('xroad', 'xroad_cert_file' , 'xroad.pem')
        # Client subsystem identifiers
        self.client_instance = get_config_value('client', 'instance', required=True)
        self.client_org_type = get_config_value('client', 'memberClass', required=True)
        self.client_org_code = get_config_value('client', 'memberCode', required=True)
        self.client_org_sub = get_config_value('client', 'subsystemCode', required=True)
        # Service identifiers
        self.service_instance = get_config_value('service', 'instance', required=True)
        self.service_org_type = get_config_value('service', 'memberClass', required=True)
        self.service_org_code = get_config_value('service', 'memberCode', required=True)
        self.service_org_sub = get_config_value('service', 'subsystemCode', required=True)
        self.service_org_name = get_config_value('service', 'serviceCode', required=True)
        self.service_org_version = get_config_value('service', 'serviceVersion')
        # Logging parameters
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

    # If log_filename is not provided, log to console
    if log_filename:
        # Logging to file
        logging.basicConfig(
            filename=log_filename,
            filemode=log_filemode,
            format=log_format,
            datefmt=log_datefmt,
            level=getattr(logging, log_level, logging.INFO)
        )
        logger.info("Logging configured")
    else:
        # Console logging for Docker
        logging.basicConfig(
            format=log_format,
            datefmt=log_datefmt,
            level=log_level,
            handlers=[logging.StreamHandler()]  # Output to stdout
        )


# def download_asic_from_trembita(queryId: str, config_instance):
#     # https://sec1.gov/signature?&queryId=abc12345&xRoadInstance=SEVDEIR-TEST&memberClass=GOV&memberCode=
#     # 12345678&subsystemCode=SUB
#     # Retrieve ASIC container from the Trembita security server using a GET request
#     asics_dir = config_instance.asic_path  # Get the ASIC directory path from the config file
#
#     query_params = {
#         "queryId": queryId,
#         "xRoadInstance": config_instance.client_instance,
#         "memberClass": config_instance.client_org_type,
#         "memberCode": config_instance.client_org_code,
#         "subsystemCode": config_instance.client_org_sub
#     }
#
#     if config_instance.trembita_protocol == "https":
#         url = f"https://{config_instance.trembita_host}/signature"
#         logger.info(f"Attempting to download ASIC from Trembita using URL: {url} and parameters: {query_params}")
#
#         try:
#             # Send a GET request to download the message archive file
#             response = requests.get(url, stream=True, params=query_params,
#                                     cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
#                                           os.path.join(config_instance.cert_path, config_instance.key_file)),
#                                     verify=os.path.join(config_instance.cert_path, config_instance.tembita_cert_file))
#             response.raise_for_status()
#
#             logger.info(f"Successfully received response from server with status code: {response.status_code}")
#
#             # Attempt to get the filename from Content-Disposition header
#             content_disposition = response.headers.get('Content-Disposition')
#             if content_disposition:
#                 # Pattern to extract filename
#                 filename_match = re.findall('filename="(.+)"', content_disposition)
#                 if filename_match:
#                     local_filename = filename_match[0]
#                 else:
#                     local_filename = 'downloaded_file.ext'
#             else:
#                 # If no header, use default filename
#                 local_filename = 'downloaded_file.ext'
#
#             # Open local file in write-binary mode
#             with open(f"{asics_dir}/{local_filename}", 'wb') as file:
#                 # Iterate over response chunks and write to file
#                 for chunk in response.iter_content(chunk_size=8192):
#                     file.write(chunk)
#             logger.info(f'File successfully downloaded and saved as: {local_filename}')
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error occurred while downloading the file: {e}")
#             raise
#     else:
#         logger.error("Function download_asic_from_trembita works only with https protocol")
#         raise ValueError("This function works only if Trembita uses the https protocol")

def generate_key_cert_rsa(key: str, crt: str, path: str):
    # RSA key and certificate generation
    logger.info("Generating RSA key and certificate")
    logger.debug(f"Key filename: {key}, certificate filename: {crt}, directory: {path}")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create x509 object for certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BD"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dhaka"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Dhaka"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "The Best Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.com"),
    ])

    # Create self-signed certificate
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
        # Certificate is valid for 1 year
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Save private key to file
    key_full_path = os.path.join(path, key)
    try:
        with open(key_full_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        logger.info(f"Key saved at {key_full_path}")

        # Save certificate to file
        crt_full_path = os.path.join(path, crt)

        with open(crt_full_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        logger.info(f"Certificate saved at {crt_full_path}")
    except IOError as e:
        logger.error(f"Error saving key or certificate: {e}")
        raise


def generate_key_cert(key: str, crt: str, path: str):
    # Private key and certificate generation
    logger.info("Generating ECDSA key and certificate")
    logger.debug(f"Key filename: {key}, certificate filename: {crt}, directory: {path}")

    # Generate ECDSA private key
    private_key = ec.generate_private_key(ec.SECP256R1())

    # Create x509 object for certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "BD"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dhaka"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Dhaka"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "The Best Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.com"),
    ])

    # Create self-signed certificate
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
        # Certificate is valid for 1 year
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Save private key to file
    key_full_path = os.path.join(path, key)
    try:
        with open(key_full_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        logger.info(f"Key saved at {key_full_path}")

        # Save certificate to file
        crt_full_path = os.path.join(path, crt)
        with open(crt_full_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        logger.info(f"Certificate saved at {crt_full_path}")
    except IOError as e:
        logger.error(f"Error saving key or certificate: {e}")
        raise

# def get_uxp_headers_from_config(config_instance) -> dict:
#     # Build UXP headers for requests
#     logger.debug("Constructing UXP headers")
#     uxp_client_header_name = "UXP-Client"
#     uxp_service_header_name = "UXP-Service"
#     uxp_sevice_purpose_id = "Uxp-Purpose-Ids"
#
#     uxp_client_header_value = (
#         f"{config_instance.client_instance}/"
#         f"{config_instance.client_org_type}/"
#         f"{config_instance.client_org_code}/"
#         f"{config_instance.client_org_sub}"
#     )
#
#     base_service_value = (
#         f"{config_instance.service_instance}/"
#         f"{config_instance.service_org_type}/"
#         f"{config_instance.service_org_code}/"
#         f"{config_instance.service_org_sub}/"
#         f"{config_instance.service_org_name}"
#     )
#
#     if config_instance.service_org_version:
#         uxp_service_header_value = f"{base_service_value}/{config_instance.service_org_version}"
#     else:
#         uxp_service_header_value = base_service_value
#
#     purpose_id_value = config_instance.trembita_purpose
#
#     headers = {
#         uxp_client_header_name: uxp_client_header_value,
#         uxp_service_header_name: uxp_service_header_value,
#         uxp_sevice_purpose_id: purpose_id_value
#     }
#     logger.debug(f"UXP headers constructed: {headers}")
#     return headers

def get_xroad_headers_from_config(config_instance) -> dict:
    # Build X-Road headers for requests
    logger.debug("Constructing X-Road headers")
    xroad_client_header_name = "X-Road-Client"
    xroad_query_id_header_name = "X-Road-Id"
    xroad_query_user_id_header_name = "X-Road-UserId"
    xroad_query_issue_header_name = "X-Road-Issue"
    ##uxp_sevice_purpose_id = "Uxp-Purpose-Ids"

    xroad_client_header_value = (
        f"{config_instance.client_instance}/"
        f"{config_instance.client_org_type}/"
        f"{config_instance.client_org_code}/"
        f"{config_instance.client_org_sub}"
    )

    xroad_query_id_header_value = f"{config_instance.client_instance}-" + str(uuid.uuid4())

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
        # uxp_sevice_purpose_id: purpose_id_value
    }
    logger.debug(f"X-Road headers constructed: {headers}")
    return headers

# def get_uxp_query_params() -> dict:
#     # Generate unique query parameters for UXP
#     logger.debug("Generating UXP query parameters")
#     uxp_query_id_name = "queryId"
#     uxp_user_id_name = "userId"
#
#     uxp_query_id_value = str(uuid.uuid4())
#     uxp_user_id_value = "Flask_client"  # any value can be set; during exchange this name
#     # will be stored by the security server and visible, e.g., via the UXP Verifier transaction tool
#
#     params = {
#         uxp_query_id_name: uxp_query_id_value,
#         uxp_user_id_name: uxp_user_id_value
#     }
#
#     logger.debug(f"UXP query parameters generated: {params}")
#     return params


# def get_base_trembita_uri(config_instance) -> str:
#     # Compose base URI for Trembita service access
#     logger.debug("Composing base Trembita URL for the client")
#     if config_instance.trembita_protocol == "https":
#         uri = f"https://{config_instance.trembita_host}/restapi"
#     else:
#         uri = f"http://{config_instance.trembita_host}/restapi"
#     logger.debug(f"Base Trembita URI: {uri}")
#     return uri


def get_base_xroad_uri(config_instance) -> str:
    # Compose base URI for calling service via X-Road security server
    logger.debug("Composing base X-Road URL for the client")
    if config_instance.xroad_protocol == "https":
        uri = f"https://{config_instance.xroad_host}:8443"
    else:
        uri = f"http://{config_instance.xroad_host}:8080"
    logger.debug(f"Base X-Road service calling URI: {uri}")
    return uri

def get_rest_xroad_uri(config_instance) -> str:
    # Compose full URI for REST API request via security server
    logger.debug("Composing full REST URL for X-Road client")
    uri = get_base_xroad_uri(config_instance) + (
        f"/r1/{config_instance.service_instance}/"
        f"{config_instance.service_org_type}/"
        f"{config_instance.service_org_code}/"
        f"{config_instance.service_org_sub}/"
        f"{config_instance.service_org_name}"
    )
    logger.debug(f"REST X-Road service calling URI: {uri}")
    return uri


def get_person_from_service(parameter: str, value: str, config_instance) -> list:
    # Retrieve person information by parameter via X-Road service
    base_uri = get_rest_xroad_uri(config_instance) + "/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None  # get_uxp_query_params()

    url = f"{base_uri}/{parameter}/{value}"
    encoded_url = quote(url, safe=':/')
    logger.info(f"Retrieving person information with parameter: {parameter} and value: {value}")
    try:
        if config_instance.xroad_protocol == "https":
            # Send HTTPS request to retrieve person data
            response = requests.get(encoded_url, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.xroad_cert_file))

            #download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Send HTTP request to retrieve person data
            response = requests.get(encoded_url, headers=headers, params=query_params)


    except Exception as e:
        logger.error(f"Error retrieving person information: {e}")
        raise ValueError(f"Error while sending HTTP GET: {e}")

    if response.status_code == 200:
        json_data = response.json()
        message_list = json_data.get('message', [])
        logger.info("Request for person information processed")
        logger.debug(f"Received person data: {message_list}")
        return message_list
    logger.error(f"Received HTTP code: {response.status_code}, error message: {response.text}")
    raise ValueError(f"Received HTTP code: {response.status_code}, error message: {response.text}")


def edit_person_in_service(data: dict, config_instance) -> CustomResponse:
    # Edit person information via X-Road service
    base_url = get_rest_xroad_uri(config_instance) + "/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None  # get_uxp_query_params()
    url = base_url

    logger.debug(f"Editing person information: {data}")
    try:
        if config_instance.xroad_protocol == "https":
            # Send HTTPS request to update person information
            response = requests.put(url, json=data, headers=headers, params=query_params,
                                    cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                          os.path.join(config_instance.cert_path, config_instance.key_file)),
                                    verify=os.path.join(config_instance.cert_path, config_instance.xroad_cert_file))

            #download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Send HTTP request to update person information
            response = requests.put(url, json=data, headers=headers, params=query_params)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error editing person information: {e}")
        raise ValueError(f"Error while sending HTTP PUT: {e}")

    if not response.content:
        json_body = {"message": "Nothing to display"}
        logger.info("Edit complete, received empty response.")
        return CustomResponse(status_code=response.status_code, body=json_body)

    logger.info(f"Edit complete, received response: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def service_delete_person(data: dict, config_instance) -> CustomResponse:
    # Delete person information via X-Road service
    base_url = get_rest_xroad_uri(config_instance) + "/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None  # get_uxp_query_params()

    url = f"{base_url}/unzr/{data['unzr']}"

    logger.info(f"Deleting person with UNZR id: {data['unzr']}")
    try:
        if config_instance.xroad_protocol == "https":
            # Send HTTPS request to delete person
            response = requests.delete(url, headers=headers, params=query_params,
                                       cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                             os.path.join(config_instance.cert_path, config_instance.key_file)),
                                       verify=os.path.join(config_instance.cert_path,
                                                           config_instance.xroad_cert_file))

            # download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Send HTTP request to delete person
            response = requests.delete(url, headers=headers, params=query_params)
    except Exception as e:
        json_body = {"Error while sending HTTP DELETE": f"{e}"}
        logger.error(f"Error deleting person: {e}")
        return CustomResponse(status_code=500, body=json_body)

    logger.info(f"Delete complete, received response: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def service_add_person(data: dict, config_instance) -> CustomResponse:
    # Add a new person via the X-Road service
    base_url = get_rest_xroad_uri(config_instance) + "/person"
    headers = get_xroad_headers_from_config(config_instance)
    query_params = None  # get_uxp_query_params()

    url = base_url
    logger.info(f"Adding new person: {data}")
    try:
        if config_instance.xroad_protocol == "https":
            # Send HTTPS request to add new person
            response = requests.post(url, json=data, headers=headers, params=query_params,
                                     cert=(os.path.join(config_instance.cert_path, config_instance.cert_file),
                                           os.path.join(config_instance.cert_path, config_instance.key_file)),
                                     verify=os.path.join(config_instance.cert_path, config_instance.xroad_cert_file))

            # download_asic_from_trembita(query_params.get('queryId'), config_instance)
        else:
            # Send HTTP request to add new person
            response = requests.post(url, json=data, headers=headers, params=query_params)

        if response.status_code > 400:
            logger.error(f"An error occurred while adding the person, status code: {response.status_code}")

    except Exception as e:
        json_body = {"Error while sending HTTP POST": f"{e}"}
        logger.error(f"Error occurred while adding new person: {e}")
        return CustomResponse(status_code=500, body=json_body)

    logger.info(f"Add request processed successfully, response received: {response.json()}")
    return CustomResponse(status_code=response.status_code, body=response.json())


def create_dir_if_not_exist(dir_path: str):
    # Create directory if it doesn't exist
    logger.info(f"Checking existence of directory: {dir_path}")
    if not os.path.exists(dir_path):
        # Create the directory if it's missing
        os.makedirs(dir_path)
        logger.info(f"Directory '{dir_path}' has been created.")
    else:
        logger.info(f"Directory '{dir_path}' already exists.")


def get_files_with_metadata(directory):
    # Retrieve list of files with metadata from the specified directory
    logger.info(f"Retrieving file metadata from directory: {directory}")
    files_metadata = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        creation_time = os.path.getctime(filepath)
        creation_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        files_metadata.append({
            'name': filename,
            'creation_time': creation_time_str
        })
    logger.info(f"File metadata retrieved: {files_metadata}")
    return files_metadata
