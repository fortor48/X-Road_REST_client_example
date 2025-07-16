# Deploying the Web Client in Docker

## Requirements

| Software        | Version    | Note                             |
|:----------------|:----------:|----------------------------------|
| Docker          | **20.10+** |                                  |
| Docker Compose  |   10.5+    | If you plan to use it            |
| Git             |            | For cloning the repository       |

## Environment Variables

The web client supports configuration via environment variables.  
Below are the main parameters:
- `USE_ENV_CONFIG` – Controls whether environment variables are used for configuration. If set to `true`, all parameters will be taken from environment variables instead of the `config.ini` file.
- `TREMBITA_PROTOCOL` – Protocol used to communicate with the X-Road system. Options: http or https. For example, http is for basic connectivity, and https for secure connectivity with authentication.
- `TREMBITA_PURPOSE_ID` – Purpose ID for processing personal data. This parameter is used for integration with the Personal Data Access Monitoring Subsystem (PDMDS) of the Trembita system.
- `TREMBITA_HOST` – Host or IP address of the X-Road security server that the client connects to. Can be an FQDN or local IP, e.g., 10.0.20.235.
- `CLIENT_INSTANCE` – Identifier of the client subsystem in the Trembita system. For example, SEVDEIR-TEST might be a test instance.
- `CLIENT_MEMBERCLASS` – Member class in X-Road, e.g., GOV typically used for government organizations.
- `CLIENT_MEMBERCODE` – Unique client code in X-Road. For example, 10000004 is the Organization identifier code of the client organization.
- `CLIENT_SUBSYSTEMCODE` – Subsystem code of the client organization in X-Road. Used to define the specific subsystem that will handle requests. For example, SUB_CLIENT.
- `SERVICE_INSTANCE` – Identifier of the service instance in X-Road, e.g., BD-POC, to which requests are sent.
- `SERVICE_MEMBERCLASS` – Member class for the service, usually the same as for the client (e.g., GOV).
- `SERVICE_MEMBERCODE` – Unique organization identifier code of the service provider organization, e.g., 10000004.
- `SERVICE_SERVICECODE` – Service code in X-Road. For example, getRegistryDataById is the code of the specific service published by the provider.
- `SERVICE_SUBSYSTEMCODE` – Subsystem code of the service provider organization in X-Road. For example, SUB_SERVICE.
- `SERVICE_SERVICEVERSION` – Version of the service from the provider in X-Road.
- `LOGGING_LEVEL` – Logging verbosity level. Possible values: DEBUG (most detailed), INFO, WARNING, ERROR, CRITICAL. DEBUG outputs the most information for debugging.
- `LOGGING_FILENAME` – Log file name. If this is empty, logs will be output to the console (stdout).

## Building the Docker Image

To build the Docker image:

1. Clone the repository:

```bash
git clone https://github.com/fortor48/X-Road_REST_client_example.git
```

2. Navigate to the web client directory:

```bash
cd X-Road_REST_client_example
```

3. Run the following command in the project root:

```bash
sudo docker build -t x-road_rest_client_example .
```

This command will create a Docker image named `x-road_rest_client_example`, using the Dockerfile in the current directory.

## Running and Using the Container with Environment Variables

To launch the container with the application:

```bash
sudo docker run -it --rm -p 5000:5000 \
    -e USE_ENV_CONFIG=true \
    -e TREMBITA_PROTOCOL=http \
    -e TREMBITA_PURPOSE_ID=1234567 \
    -e TREMBITA_HOST=10.0.20.235 \
    -e CLIENT_INSTANCE=BD-POC \
    -e CLIENT_MEMBERCLASS=GOV \
    -e CLIENT_MEMBERCODE=10000004 \
    -e CLIENT_SUBSYSTEMCODE=SUB_CLIENT \
    -e SERVICE_INSTANCE=BD-POC \
    -e SERVICE_MEMBERCLASS=GOV \
    -e SERVICE_MEMBERCODE=10000004 \
    -e SERVICE_SERVICECODE=py_sync \
    -e SERVICE_SUBSYSTEMCODE=SUB_SERVICE \
    -e LOGGING_LEVEL=DEBUG \
    x-road_rest_client_example
```

Where:
- `-p 5000:5000` maps port 5000 on your local machine to port 5000 inside the container.
- Other variables are listed in the [Environment Variables](#environment-variables) section.

If you plan to use only environment variables for configuration, make sure `USE_ENV_CONFIG=true` is set.

Example:

```bash
sudo docker run -it --rm -p 5000:5000 \
    -e USE_ENV_CONFIG=true \
    -e TREMBITA_PROTOCOL=http \
    -e TREMBITA_PURPOSE_ID=1234567 \
    -e TREMBITA_HOST=10.0.20.235 \
    -e CLIENT_INSTANCE=BD-POC \
    -e CLIENT_MEMBERCLASS=GOV \
    -e CLIENT_MEMBERCODE=10000004 \
    -e CLIENT_SUBSYSTEMCODE=SUB_CLIENT \
    -e SERVICE_INSTANCE=BD-POC \
    -e SERVICE_MEMBERCLASS=GOV \
    -e SERVICE_MEMBERCODE=10000004 \
    -e SERVICE_SERVICECODE=py_sync \
    -e SERVICE_SUBSYSTEMCODE=SUB_SERVICE \
    -e LOGGING_LEVEL=DEBUG \
    x-road_rest_client_example
```

### Running the Container with a Configuration File

You can run the container using a configuration file instead of environment variables.  
To do this, create a `config.ini` file in the web client directory and mount it:

```bash
docker run -it --rm -p 5000:5000 \
    -v $(pwd)/config.ini:/app/config.ini \
    x-road_rest_client_example
```
Where `-v $(pwd)/config.ini:/app/config.ini` mounts the local config file into the container at `/app/config.ini`.

### Example Configuration File `config.ini`:

```ini
[trembita]
protocol = https
host = 192.168.99.150
purpose_id = ""
cert_path = certs
asic_path = asic
cert_file = cert.pem
key_file = key.pem
trembita_cert_file = trembita.pem

[client]
instance = BD-POC
memberClass = GOV
memberCode = 10000003
subsystemCode = CLIENT

[service]
instance = BD-POC
memberClass = GOV
memberCode = 10000003
subsystemCode = SERVICE
serviceCode = python_ssl
serviceVersion =

[logging]
filename = /tmp/file.log
filemode = a
format = %(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s
dateformat = %H:%M:%S
level = DEBUG # info warning debug
```

If the environment variable `USE_ENV_CONFIG` is not set or is `false`, the web client will use the configuration file. Make sure the file is accessible in the container as shown above.

## Viewing Logs

If logging is configured to output to the console, you can view logs using:

```bash
docker logs <container_id>
```

If logs are saved to a file (via the `LOG_FILENAME` environment variable or configuration file), you can mount the local logging directory as follows:

```bash
docker run -it --rm -p 5000:5000 \
    -e LOGGING_FILENAME="/var/log/app.log" \
    -v $(pwd)/logs:/var/log \
    x-road_rest_client_example
```

Where `-v $(pwd)/logs:/var/log` mounts your local log directory inside the container.

##
The materials were created with support from the international technical assistance project “Bangladesh e-governance (BGD)”.
