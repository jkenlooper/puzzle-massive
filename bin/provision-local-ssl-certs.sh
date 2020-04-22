#!/usr/bin/env bash
set -eu -o pipefail

LOCALHOST_CA_KEY=${HOME}/localhost-CA.key
LOCALHOST_CA_PEM=${HOME}/localhost-CA.pem

function usage {
  cat <<USAGE
Usage: ${0} [-h] [-k <localhost-CA.key>] [-p <localhost-CA.pem>]

Options:
  -h            Show help
  -k            Path to localhost CA key file [default: ${LOCALHOST_CA_KEY}]
  -p            Path to localhost CA pem file [default: ${LOCALHOST_CA_PEM}]

Create your own certificate authority (CA) and make and trust certificates for
local development.
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

if (test ! -f "${LOCALHOST_CA_KEY}"); then
  echo "Creating localhost certificate authority key at ${LOCALHOST_CA_KEY}";
  openssl genrsa -out "${LOCALHOST_CA_KEY}" 2048;
fi

if (test ! -f "${LOCALHOST_CA_PEM}" && test -f "${LOCALHOST_CA_KEY}"); then
  echo "Creating localhost certificate authority pem at ${LOCALHOST_CA_PEM}";
  openssl req -x509 -new -nodes \
    -key "${LOCALHOST_CA_KEY}" \
    -sha256 -days 356 \
    -config web/localhost-CA.config \
    -out "${LOCALHOST_CA_PEM}"
fi

openssl req -new -sha256 -nodes -newkey rsa:2048 \
	-config web/local-development.csr.config \
	-out web/local-development.csr \
	-keyout web/local-puzzle-massive.key

openssl x509 -req -CAcreateserial -days 356 -sha256 \
	-in web/local-development.csr \
	-CA "${LOCALHOST_CA_PEM}" \
	-CAkey "${LOCALHOST_CA_KEY}" \
	-out web/local-puzzle-massive.crt

#openssl dhparam -out web/dhparam.pem 2048

# Signal that the certs should now exist.
# The web/puzzle-massive.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/puzzle-massive.conf.sh
