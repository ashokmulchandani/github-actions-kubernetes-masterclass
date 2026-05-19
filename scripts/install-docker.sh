#!/bin/bash
echo "Installing Docker..."
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
newgrp docker
echo "Docker installed successfully!"
docker --version
