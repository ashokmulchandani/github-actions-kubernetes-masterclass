#!/bin/bash
echo "=============================="
echo "Scanning Docker Images for Vulnerabilities"
echo "=============================="

echo ""
echo "--- Scanning Backend ---"
trivy image skillpulse-backend --severity HIGH,CRITICAL

echo ""
echo "--- Scanning Frontend ---"
trivy image skillpulse-frontend --severity HIGH,CRITICAL

echo ""
echo "=============================="
echo "Scan Complete!"
echo "=============================="
