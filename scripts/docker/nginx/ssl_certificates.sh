#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Generate self-signed SSL certs
mkdir ${DIR}/certs
cat > ${DIR}/certs/req.cnf <<EOF
[v3_req]
keyUsage = critical, digitalSignature, keyAgreement
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = picobrew.com
DNS.2 = www.picobrew.com
DNS.3 = localhost
EOF

openssl req -x509 -sha256 -newkey rsa:2048 -nodes -keyout ${DIR}/certs/domain.key \
    -days 1825  -out  ${DIR}/certs/domain.crt  -subj "/CN=chiefwigms_Picobrew_Pico CA"

openssl req -newkey rsa:2048 -nodes -subj "/CN=picobrew.com" \
    -keyout  ${DIR}/certs/server.key -out  ${DIR}/certs/server.csr

openssl x509 \
    -CA ${DIR}/certs/domain.crt -CAkey ${DIR}/certs/domain.key -CAcreateserial \
    -in ${DIR}/certs/server.csr \
    -req -days 1825 -out ${DIR}/certs/server.crt -extfile ${DIR}/certs/req.cnf \
    -extensions v3_req

cat ${DIR}/certs/server.crt ${DIR}/certs/domain.crt > ${DIR}/certs/bundle.crt