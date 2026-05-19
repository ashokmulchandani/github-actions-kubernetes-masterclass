#!/bin/bash
echo "Starting SonarQube container..."
docker run -d \
  --name sonarqube \
  -p 9000:9000 \
  sonarqube:community

echo "SonarQube starting at http://localhost:9000"
echo "Default login: admin / admin"
echo "Wait 1-2 minutes for it to fully start..."
