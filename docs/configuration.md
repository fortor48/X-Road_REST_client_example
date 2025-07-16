## Web Client Configuration

To configure the web client:
1. Create a configuration file named `config.ini` in the root directory of the web client, with the following content:

```ini
[trembita]

# Protocol used for interaction with the X-Road system (https or http)
# HTTPS requires mutual authentication with certificates between the client and X-Road security server
protocol = https

# Hostname, FQDN, or local IP address of X-Road security server
# Possible values: 192.168.1.1, bndx-ss.example.gov.ua
host = your_securityserver_host

# Purpose ID for processing personal data when interacting with services using Trembita Personal Data Access Monitoring Subsystem.
# May be omitted or commented out if this subsystem is not used.
# purpose_id = your_purpose_id

# Path to SSL keys and certificates for interaction with X-Road security server (directory will be created if it doesn't exist)
cert_path = path/to/your/certificates

# Path to save ASiC files containing downloaded messages (directory will be created if it doesn't exist)
asic_path = path/to/save/asic/files

# Filename for the certificate to be generated if not found in cert_path
cert_file = cert_name.pem

# Filename for the key to be generated if not found in cert_path
key_file = key.pem

# Filename of the X-Road security server's certificate required for HTTPS with mutual authentication. Must be placed in cert_path
trembita_cert_file = securityserver.pem  

# Full identifier of the X-Road client subsystem used for sending request messages
[client]
# xRoadInstance (e.g., BD or BD-POC)
instance = BD-POC

# memberClass (e.g., GOV)
memberClass = GOV

# memberCode – Identifying code of the client organization
memberCode = your_client_member_code

# subsystemCode – X-Road subsystem code of the client organization used for requests
subsystemCode = your_client_subsystem_code

# Full identifier of the X-Road service to which request messages are sent
[service]
# xRoadInstance (e.g., BD or BD-POC)
instance = BD-POC

# memberClass (e.g., GOV)
memberClass = GOV

# memberCode – Identifying code of the provider organization
memberCode = your_service_member_code

# subsystemCode – X-Road subsystem code of the provider organization where the service is published
subsystemCode = your_service_subsystem_code

# serviceCode – code of the service published in the X-Road system
serviceCode = your_service_code

# serviceVersion – version of the service, if available (usually omitted if the service has no version)
serviceVersion = your_service_version

[logging]
# Path to the log file
filename = path/to/x-road_rest_client_example.log

# filemode defines how the log file is opened:
# 'a' – append to existing file
# 'w' – overwrite the file each time the program starts
filemode = a

# format defines the format of log messages:
# %(asctime)s – timestamp of the log entry
# %(name)s – logger name
# %(levelname)s – logging level
# %(message)s – log message text
# %(pathname)s – file path from where the log was triggered
# %(lineno)d – line number in the file where the log was triggered
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s

# dateformat defines the date format in log messages.
# Examples:
# %Y-%m-%d %H:%M:%S – 2023-06-25 14:45:00
# %d-%m-%Y %H:%M:%S – 25-06-2023 14:45:00
dateformat = %Y-%m-%d %H:%M:%S

# level sets the logging verbosity. The most detailed is DEBUG; default is INFO
# DEBUG – detailed logs useful for debugging (includes request/response contents)
# INFO – general execution status information
# WARNING – potential issue warnings
# ERROR – errors that prevent normal operation
# CRITICAL – critical errors that cause application shutdown
level = DEBUG
```

##
This guide was created with support from the international technical assistance project “Bangladesh e-governance (BGD)”.
