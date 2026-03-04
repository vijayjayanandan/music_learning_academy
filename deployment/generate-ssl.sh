#!/usr/bin/env bash
# Generate self-signed SSL certificates for local/dev use.
# For production, use Let's Encrypt or a real CA.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SSL_DIR="$SCRIPT_DIR/ssl"

mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/C=US/ST=Local/L=Dev/O=MusicAcademy/CN=localhost"

echo "SSL certificates generated in $SSL_DIR/"
echo "  - cert.pem (certificate)"
echo "  - key.pem  (private key)"
