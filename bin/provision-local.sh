#!/bin/bash

# Run from your local machine to create certs for development.

# TODO: create the .htpasswd file
touch .htpasswd;

openssl genrsa -out web/local-puzzle-massive-CA.key 2048

openssl req -x509 -new -nodes \
  -key web/local-puzzle-massive-CA.key \
  -sha256 -days 356 \
  -config web/local-puzzle-massive-CA.cnf \
  -out web/local-puzzle-massive-CA.pem


openssl req -new -sha256 -nodes -newkey rsa:2048 \
	-config web/local-puzzle-massive.csr.cnf \
	-out web/local-puzzle-massive.csr \
	-keyout web/local-puzzle-massive.key

openssl x509 -req -CAcreateserial -days 356 -sha256 \
	-in web/local-puzzle-massive.csr \
	-CA web/local-puzzle-massive-CA.pem \
	-CAkey web/local-puzzle-massive-CA.key \
	-out web/local-puzzle-massive.crt \
	-extfile web/v3.ext


#openssl dhparam -out web/dhparam.pem 2048

# Signal that the certs should now exist.
# The web/puzzle-massive.conf.sh checks if this file exists in
# order to uncomment the lines in the nginx conf for ssl_certificate fields.
touch .has-certs web/puzzle-massive.conf.sh
