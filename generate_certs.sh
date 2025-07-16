#!/bin/bash
set -e

GREEN="\033[32m"
RESET="\033[0m"

KEY_FILE_NAME="key.pem"
CERT_FILE_NAME="cert.pem"
CERTS_DIR="./certs"

KEY_FILE="$CERTS_DIR/$KEY_FILE_NAME"       # PKCS#8
CERT_FILE="$CERTS_DIR/$CERT_FILE_NAME"
SUBJ="/C=UA/ST=Kyiv/L=Kyiv/O=X-Road/OU=Dev/CN=localhost"

# Create the directory
mkdir -p "$CERTS_DIR"

# Generate an ECDSA private key in PKCS#8 format
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:prime256v1 -out "$KEY_FILE"

# Generate a self-signed certificate
openssl req -new -x509 -key "$KEY_FILE" -out "$CERT_FILE" -days 365 -subj "$SUBJ"

# Message
echo -e "${GREEN}Certificate and key (${CERT_FILE_NAME}, ${KEY_FILE_NAME}) have been generated in the ${CERTS_DIR} directory. You can now add the Trembita certificate and start the Docker container build. The file name should be passed via the TREMBITA_CERT_FILE environment variable.${RESET}"