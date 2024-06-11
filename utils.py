import requests
from requests import Response
from urllib.parse import quote

base_url = "http://127.0.0.1:8000/person/"


class Response:
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body

    def __repr__(self):
        return f"Response(status_code={self.status_code}, body={self.body})"

def get_person_from_service(parameter: str, value: str) -> list:
    url = base_url + parameter + "/" + value
    encoded_url = quote(url, safe=':/')
    try:
        response = requests.get(encoded_url)
    except Exception as e:
        raise ValueError("Error while sending HTTP GET")

    if response.status_code == 200:
        json_data = response.json()
        message_list = json_data.get('message', [])
        return message_list

    raise ValueError(f"Recieved HTTP code: {response.status_code}, error message: {response.text}")


def edit_person_in_service(data: dict) -> Response:
    url = base_url
    try:
        response = requests.put(url, json=data)
        #response.raise_for_status()  # Это вызовет исключение, если статус код будет 4xx или 5xx
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error while sending HTTP PUT: {e}")

    if not response.content:
        json_body = {"message": "Nothing to display"}
        return Response(status_code=response.status_code, body=json_body)

    return Response(status_code=response.status_code, body=response.json())


def service_delete_person(data: dict) -> Response:

    url = base_url + "unzr/" + str(data["unzr"])
    try:
        response = requests.delete(url)
    except Exception as e:
        json_body = {"Error while sending HTTP DELETE": f"{e}"}
        return Response(status_code=500, body=json_body)

    return Response(status_code=response.status_code, body=response.json())


def service_add_person(data: dict) -> Response:

    url = base_url
    try:
        response = requests.post(url, json=data)
    except Exception as e:
        json_body = {"Error while sending HTTP POST": f"{e}"}
        return Response(status_code=500, body=json_body)
    return Response(status_code=response.status_code, body=response.json())