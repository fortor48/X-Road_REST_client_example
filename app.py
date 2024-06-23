import sys
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_bootstrap import Bootstrap
import utils
import os



# Установка правильной кодировки для stdout
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
crt_directory = "certs"
asic_derectory = "asic"
key = "key.pem"
cert = "crt.pem"

ASIC_DIR = os.path.join(os.getcwd(), 'asic')

# Проверяем, существует ли директория
if not os.path.exists(crt_directory):
    # Создаем директорию, если её нет
    os.makedirs(crt_directory)
    print(f"Директория '{crt_directory}' была создана.")
else:
    print(f"Директория '{crt_directory}' уже существует.")

# Проверяем, существует ли директория
if not os.path.exists(asic_derectory):
    # Создаем директорию, если её нет
    os.makedirs(asic_derectory)
    print(f"Директория '{asic_derectory}' была создана.")
else:
    print(f"Директория '{asic_derectory}' уже существует.")

private_key_full_path = f"{crt_directory}/{key}"
certificate_full_path = f"{crt_directory}/{cert}"

if not os.path.exists(private_key_full_path) or not os.path.exists(certificate_full_path):
    utils.generate_key_cert(key, cert, crt_directory)


def get_files_with_metadata(directory):
    files_metadata = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        creation_time = os.path.getctime(filepath)
        creation_time_str = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
        files_metadata.append({
            'name': filename,
            'creation_time': creation_time_str
        })
    return files_metadata


app = Flask(__name__)
Bootstrap(app)  # Инициализация Flask-Bootstrap4

conf = utils.Config('config.ini')


@app.route('/', methods=['GET', 'POST'])
def serch_user():
    if request.method == 'POST': # Прийшов запит з даними від форми (на пошук за одним з параметрів), обробляемо
        print("test")
        search_field = request.form.get('search_field')
        search_value = request.form.get('search_value')

        try:
            data = utils.get_person_from_service(search_field, search_value, conf)
        except Exception as e:
            return render_template('error.html', error_message=e,  current_page='index')
        return render_template('list_person.html', data=data,  current_page='index')

    return render_template('search_form.html',  current_page='index') # Прийшов GET запит, просто віддаємо веб сторінку


@app.route('/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST': # Прийшов запит з даними від форми (на створеня особи), обробляемо
        try:
            form_data = request.get_json()

            response = utils.service_add_person(form_data, conf)
            resp = jsonify({"message": response.body}), response.status_code
            return resp
        except Exception as e:
            resp = jsonify(message='Ошибка при создании записи: {}'.format(str(e))), 422
            return resp

    return render_template('create_person.html',  current_page='create') # Прийшов GET запит, просто віддаємо веб сторінку


@app.route('/edit', methods = ['POST'])
def edit_user():
    data = request.get_json()
    try:
        http_resp = utils.edit_person_in_service(data, conf)
    except Exception as e:
        resp = jsonify({f"message": "Data NOT received successfully", "error": e}), 500
        return resp
    return jsonify({"message": http_resp.body}), http_resp.status_code


@app.route('/delete', methods = ['POST'])
def delete_person():
    data = request.get_json()
    try:
        http_resp = utils.service_delete_person(data, conf)
    except Exception as e:
        resp = jsonify({f"message": "Data NOT received successfully", "error": e}), 500
        return resp
    return jsonify({"message": http_resp.body}), http_resp.status_code

@app.route('/files')
def list_files():
    try:
        files = []
        for filename in os.listdir(asic_derectory):
            filepath = os.path.join(asic_derectory, filename)
            if os.path.isfile(filepath):
                creation_time = datetime.fromtimestamp(os.path.getctime(filepath))
                files.append({
                    'name': filename,
                    'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S')
                })

        # Sort files by creation time (descending order)
        files = sorted(files, key=lambda x: x['creation_time'], reverse=True)

        return render_template('list_files_run_away.html', files=files, current_page='files')
    except Exception as e:
        return render_template('error.html', error_message=e, current_page='files')

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(ASIC_DIR, filename, as_attachment=True)
    except Exception as e:
        return render_template('error.html', error_message=e, current_page='files')


if __name__ == '__main__':
    #sys.stdout.reconfigure(encoding='utf-8')
    app.run(debug=True)