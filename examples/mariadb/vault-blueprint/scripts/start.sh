#!/bin/sh

nohup /tmp/vault server -dev -dev-listen-address=0.0.0.0:8200 -dev-root-token-id=root &
