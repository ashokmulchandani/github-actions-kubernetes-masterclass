#!/bin/bash
echo "=============================="
echo "Setting up EC2 for SkillPulse"
echo "=============================="

bash scripts/install-docker.sh
bash scripts/install-kind.sh
bash scripts/install-kubectl.sh

echo "=============================="
echo "Setup complete! Now run: make up"
echo "=============================="

# Install Go tools for linting (optional)
# go install honnef.co/go/tools/cmd/staticcheck@latest
