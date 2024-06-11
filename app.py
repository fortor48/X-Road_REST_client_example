import sys

from flask import Flask, render_template, request, jsonify
from flask_bootstrap import Bootstrap
import requests
from urllib.parse import quote
import chardet
import io
import httpx
import json
import utils



# Установка правильной кодировки для stdout
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)
Bootstrap(app)  # Инициализация Flask-Bootstrap4

base_url = "http://127.0.0.1:8000/person/name/"


@app.route('/', methods=['GET', 'POST'])
def serch_user():
    if request.method == 'POST':
        print("test")
        search_field = request.form.get('search_field')
        search_value = request.form.get('search_value')

        try:
            data = utils.get_person_from_service(search_field, search_value)
        except Exception as e:
            return render_template('error.html', error_message=e)
        return render_template('list_person.html', data=data)

    return render_template('search_form.html')


@app.route('/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            form_data = request.get_json()

            response = utils.service_add_person(form_data)
            resp = jsonify({"message": response.body}), response.status_code
            return resp
        except Exception as e:
            resp = jsonify(message='Ошибка при создании записи: {}'.format(str(e))), 422
            return resp

    return render_template('create_person.html')


@app.route('/edit', methods = ['POST'])
def edit_user():
    data = request.get_json()
    try:
        http_resp = utils.edit_person_in_service(data)
    except Exception as e:
        resp = jsonify({f"message": "Data NOT received successfully", "error": e}), 500
        return resp
    return jsonify({"message": http_resp.body}), http_resp.status_code





@app.route('/delete', methods = ['POST'])
def delete_person():
    data = request.get_json()
    try:
        http_resp = utils.service_delete_person(data)
    except Exception as e:
        resp = jsonify({f"message": "Data NOT received successfully", "error": e}), 500
        return resp
    return jsonify({"message": http_resp.body}), http_resp.status_code



if __name__ == '__main__':
    #sys.stdout.reconfigure(encoding='utf-8')
    app.run(debug=True)