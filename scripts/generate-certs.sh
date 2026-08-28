#!/usr/bin/env bash
# Generate self-signed TLS certificates for search.yourdomain private infrastructure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="${SCRIPT_DIR}/../nginx/certs"

mkdir -p "${CERTS_DIR}"

echo "Generating private SSL certificate for search.yourdomain..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${CERTS_DIR}/search.yourdomain.key" \
  -out "${CERTS_DIR}/search.yourdomain.crt" \
  -subj "/C=US/ST=Private/L=HomeServer/O=PrivateInfra/OU=Search/CN=search.yourdomain" \
  -addext "subjectAltName=DNS:search.yourdomain,DNS:localhost,IP:127.0.0.1"

echo "Certificates generated successfully in ${CERTS_DIR}:"
echo "  - search.yourdomain.crt"
echo "  - search.yourdomain.key"
