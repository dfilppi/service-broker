#!/bin/bash

# Download Vault
cd /tmp
curl -o vault.zip https://releases.hashicorp.com/vault/0.10.2/vault_0.10.2_linux_amd64.zip
unzip vault.zip
rm vault.zip
