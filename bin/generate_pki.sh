#!/bin/sh

certsdir=/home/pi/picobrew_pico/certs
domain1=picobrew.com
domain2=www.picobrew.com

mkdir /home/pi/picobrew_pico/certs

cat > $certsdir/req.cnf <<EOF
[v3_req]
keyUsage = critical, digitalSignature, keyAgreement
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = $domain1
DNS.2 = $domain2
EOF

openssl req -x509 -sha256 -newkey rsa:2048 -nodes -keyout $certsdir/domain.key -days 1825  -out  $certsdir/domain.crt  -subj "/CN=Picobrewers Root CA"

openssl req -newkey rsa:2048 -nodes -subj "/CN=picobrew.com" \
      -keyout  $certsdir/server.key -out  $certsdir/server.csr

openssl x509 \
        -CA $certsdir/domain.crt -CAkey $certsdir/domain.key -CAcreateserial \
       -in $certsdir/server.csr \
       -req -days 1825 -out  $certsdir/server.crt  -extfile $certsdir/req.cnf -extensions v3_req

cat  $certsdir/server.crt  $certsdir/domain.crt >  $certsdir/bundle.crt

