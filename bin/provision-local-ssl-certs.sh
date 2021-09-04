#!/usr/bin/env bash
set -eu -o pipefail

LOCALHOST_CA_KEY=${HOME}/localhost-CA.key
LOCALHOST_CA_PEM=${HOME}/localhost-CA.pem

if [ -e .env ]; then
  # shellcheck source=/dev/null
  source .env
else
  echo "no .env file. Just using defaults."
fi

EMAIL=${EMAIL_SENDER-"somebody@localhost"}
ORGNAME=${SITE_TITLE-"Puzzle Massive"}
DOMAIN_NAME=${DOMAIN_NAME-"localhost"}

function usage {
  cat <<USAGE
Usage: ${0} [-h] [-k <localhost-CA.key>] [-p <localhost-CA.pem>]

Options:
  -h            Show help
  -k            Path to localhost CA key file [default: ${LOCALHOST_CA_KEY}]
  -p            Path to localhost CA pem file [default: ${LOCALHOST_CA_PEM}]

Create your own certificate authority (CA) and make and trust certificates for
Puzzle Massive development.
USAGE
  exit 0;
}

while getopts ":hk:p:" opt; do
  case ${opt} in
    h )
      usage;
      ;;
    k )
      LOCALHOST_CA_KEY=${OPTARG};
      ;;
    p )
      LOCALHOST_CA_PEM=${OPTARG};
      ;;
  esac;
done;
shift "$((OPTIND-1))";

tmp_localhost_CA_config=$(mktemp --suffix=.config)
cat <<LOCALHOST_CA_CONFIG > $tmp_localhost_CA_config
[ req ]
default_bits           = 2048
prompt                 = no
default_md             = sha256
distinguished_name     = req_distinguished_name

[ req_distinguished_name ]
commonName             = localhost
organizationName       = ${ORGNAME}
countryName            = US
localityName           = Local Llama Town
organizationalUnitName = bin/provision-local-ssl-certs.sh
stateOrProvinceName    = Local
emailAddress           = ${EMAIL}
name                   = dev
LOCALHOST_CA_CONFIG

tmp_local_development_csr_config=$(mktemp --suffix=.config)
cat <<LOCAL_DEVELOPMENT_CSR_CONFIG > $tmp_local_development_csr_config
[ req ]
default_bits           = 2048
default_keyfile        = localhost.key
prompt                 = no
default_md             = sha256
distinguished_name     = dn
req_extensions         = req_ext
x509_extensions        = v3_ca

[ dn ]
commonName             = localhost
emailAddress           = ${EMAIL}
name                   = Dev
countryName            = US
stateOrProvinceName    = Local
localityName           = Local Llama Town
organizationName       = ${ORGNAME}
organizationalUnitName = bin/provision-local-ssl-certs.sh

[req_ext]
subjectAltName         = @alt_names

[v3_ca]
subjectAltName         = @alt_names
authorityKeyIdentifier = keyid,issuer
basicConstraints       = CA:FALSE
keyUsage               = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment

[alt_names]
DNS.1                  = 127.0.0.1
DNS.2                  = localhost
DNS.3                  = ${DOMAIN_NAME}
LOCAL_DEVELOPMENT_CSR_CONFIG

if (test ! -f "${LOCALHOST_CA_KEY}"); then
  echo "Creating localhost certificate authority key at ${LOCALHOST_CA_KEY}";
  openssl genrsa -out "${LOCALHOST_CA_KEY}" 2048;
fi

if (test ! -f "${LOCALHOST_CA_PEM}" && test -f "${LOCALHOST_CA_KEY}"); then
  echo "Creating localhost certificate authority pem at ${LOCALHOST_CA_PEM}";
  openssl req -x509 -new -nodes \
    -key "${LOCALHOST_CA_KEY}" \
    -sha256 -days 356 \
    -config $tmp_localhost_CA_config \
    -out "${LOCALHOST_CA_PEM}"
fi

tmp_local_development_csr=$(mktemp --suffix=.csr)
openssl req -new -sha256 -nodes -newkey rsa:2048 \
	-config $tmp_local_development_csr_config \
	-out $tmp_local_development_csr \
	-keyout web/localhost.key

openssl x509 -req -CAcreateserial -days 356 -sha256 \
	-in $tmp_local_development_csr \
	-CA "${LOCALHOST_CA_PEM}" \
	-CAkey "${LOCALHOST_CA_KEY}" \
	-out web/localhost.crt

#openssl dhparam -out web/dhparam.pem 2048

# Signal that the certs should now exist.
# The web/snippets/ssl_certificate-ssl_certificate_key.nginx.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/snippets/ssl_certificate-ssl_certificate_key.nginx.conf.sh
