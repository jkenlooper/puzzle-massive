#!/bin/bash

# Run from your local machine to create certs for development.

# TODO: create the .htpasswd file
touch .htpasswd;

openssl genrsa -des3 -out web/rootCA.key 2048
openssl req -x509 -new -nodes -key web/rootCA.key -sha256 -days 1024 -out web/rootCA.pem


openssl req -new -sha256 -nodes -newkey rsa:2048 \
	-config web/server.csr.cnf \
	-out web/server.csr \
	-keyout web/server.key

openssl x509 -req -CAcreateserial -days 500 -sha256 \
	-in web/server.csr \
	-CA web/rootCA.pem \
	-CAkey web/rootCA.key \
	-out web/server.crt \
	-extfile web/v3.ext


openssl dhparam -out web/dhparam.pem 2048
