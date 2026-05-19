#!/bin/bash
echo "Installing Trivy..."
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://aquasecurity.github.io/trivy-repo/rpm/releases/
sudo yum install -y trivy
echo "Trivy installed successfully!"
trivy --version
