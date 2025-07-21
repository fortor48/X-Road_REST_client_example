import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_bootstrap import Bootstrap

import utils
import os
import logging
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased


# Reading application parameters from config file
conf = utils.Config('config.ini')

# Logging setup
try:
    utils.configure_logging(conf)
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully.")
except Exception as e:
    # If an error occurs during logging setup, terminate the application
    print(f"Logging configuration error: {e}")
    sys.exit(1)

logger.debug("Starting application initialization")

# Initialize directories for certificate files
crt_directory = conf.cert_path
asic_directory = conf.asic_path
key = conf.key_file
cert = conf.cert_file

# Create certificate and ASIC directories if they don't exist
utils.create_dir_if_not_exist(crt_directory)
utils.create_dir_if_not_exist(asic_directory)

# Paths to keys and certificates
private_key_full_path = os.path.join(crt_directory, key)
certificate_full_path = os.path.join(crt_directory, cert)

# If key or certificate not found, generate them
if not os.path.exists(private_key_full_path) or not os.path.exists(certificate_full_path):
    logger.info(f"Key: {key} or certificate {cert} not found in directory {crt_directory}")
    utils.generate_key_cert(key, cert, crt_directory)

if conf.telemetry_enabled == "true" :
    logger.info("Telemetry enabled")
    # Set up tracer provider with service name
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({SERVICE_NAME: conf.telemetry_own_service_name}),
            sampler=TraceIdRatioBased(float(conf.telemetry_sample_ratio))
        )
    )

    otlp_exporter = OTLPSpanExporter(
        endpoint=conf.telemetry_endpoint,  # OTLP gRPC port by default
        insecure=True  # No TLS (if Collector has no mTLS)
    )

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

# Initialize Flask application
app = Flask(__name__)
if conf.telemetry_enabled == "true" :
    # Instrument Flask (automatically wraps routes in spans)
    RequestsInstrumentor().instrument()
    FlaskInstrumentor().instrument_app(app)

Bootstrap(app)
logger.info("Flask application initialized.")

# Handle HTTP requests to the home page
@app.route('/', methods=['GET', 'POST'])
def search_user():
    logger.debug(f"Received {'POST' if request.method == 'POST' else 'GET'} request to '/' route.")
    if request.method == 'POST':  # Handle POST request for person search form
        search_field = request.form.get('search_field')
        search_value = request.form.get('search_value')

        logger.debug(f"Received search parameters: {search_field} : {search_value}")

        try:
            # Query for person information
            data = utils.get_person_from_service(search_field, search_value, conf)
        except Exception as e:
            # In case of error, render error page
            logger.error(f"Error occurred: {str(e)}")
            return render_template('error.html', error_message=e, current_page='index')
        return render_template('list_person.html', data=data, current_page='index')

    # If GET request, render the search form
    return render_template('search_form.html', current_page='index')

# Handle person creation
@app.route('/create', methods=['GET', 'POST'])
def create_user():
    logger.debug(f"Received {'POST' if request.method == 'POST' else 'GET'} request to '/create' route.")
    if request.method == 'POST':  # Handle POST request to create a new person
        try:
            form_data = request.get_json()  # Read form data
            logger.debug(f"Received creation request with parameters: {form_data}")
            # Call function to add new person
            response = utils.service_add_person(form_data, conf)
            resp = jsonify(message=response.body), response.status_code
            return resp
        except Exception as e:
            logger.debug(f"Error occurred: {str(e)}")
            resp = jsonify(message=f'Error creating person object: {str(e)}'), 422
            return resp

    # If GET request, render person creation form
    return render_template('create_person.html', current_page='create')

# Handle person data editing
@app.route('/edit', methods = ['POST'])
def edit_user():
    logger.debug("Received POST request to '/edit' route.")
    data = request.get_json()  # Get edit data
    logger.debug(f"Received edit data: {data}")
    try:
        # Call function to edit person data
        http_resp = utils.edit_person_in_service(data, conf)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        resp = jsonify(message=f"Error processing edit request: {str(e)}"), 500
        return resp
    return jsonify(message=http_resp.body), http_resp.status_code

# Handle person deletion
@app.route('/delete', methods = ['POST'])
def delete_person():
    logger.debug("Received POST request to '/delete' route.")
    data = request.get_json()   # Get person data to delete
    logger.debug(f"Received deletion request: {data}")
    try:
        # Call function to delete person
        http_resp = utils.service_delete_person(data, conf)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        resp = jsonify(message=f"Error processing deletion request: {str(e)}"), 500
        return resp
    return jsonify(message= http_resp.body), http_resp.status_code

# Handle certificate download
@app.route('/download_cert/<filename>')
def download_cert(filename):
    logger.debug(f"Received GET request to '/download_cert/{filename}' route.")
    CERT_DIR = os.path.join(os.getcwd(), crt_directory)
    safe_filename = os.path.basename(filename)  # File name validation for security
    try:
        return send_from_directory(CERT_DIR, safe_filename, as_attachment=True)  # Send certificate
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return render_template('error.html', error_message=e, current_page='certs')

# Handle certificate list display
@app.route('/certs')
def list_certs():
    logger.debug("Received GET request to '/certs' route.")
    try:
        # Get list of certificates in directory
        files = []
        for filename in os.listdir(crt_directory):
            filepath = os.path.join(crt_directory, filename)
            if os.path.isfile(filepath):
                creation_time = datetime.fromtimestamp(os.path.getctime(filepath))
                files.append({
                    'name': filename,
                    'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S')
                })

        # Sort certificates by creation date in descending order
        files = sorted(files, key=lambda x: x['creation_time'], reverse=True)
        logger.debug("Certificate list retrieved successfully.")

        return render_template('list_certs.html', files=files, current_page='certs')
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return render_template('error.html', error_message=e, current_page='certs')

# Application entry point
if __name__ == '__main__':
    # Run Flask application in debug mode
    logger.info("Launching Flask application.")
    app.run(debug=True)
    logger.info("Flask application stopped.")