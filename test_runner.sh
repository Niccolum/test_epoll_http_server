#!/usr/bin/bash

if [[ $UID != 0 ]]; then
    echo "Please run this script with sudo:"
    echo "sudo $0 $*"
    exit 1
fi

echo "Stopping previous if exists..."
sudo docker stop nshs || true && sudo docker rm nshs || true && sudo docker image rm niccolum_socket_http_server:1.0

echo "Running..."
sudo docker image build -t niccolum_socket_http_server:1.0 .
sudo docker container run --publish 8080:8080 --detach --name nshs niccolum_socket_http_server:1.0

echo "Run unit tests..."
sudo docker exec nshs python httptest.py

echo "Run stress testing..."
sudo docker exec nshs ab -n 50000 -c 100 -r http://localhost:8080/
