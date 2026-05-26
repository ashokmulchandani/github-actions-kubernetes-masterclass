#!/bin/bash
# Load test to trigger HPA auto-scaling
# This floods the backend with requests so CPU spikes → HPA adds pods
#
# Tools: 'hey' (simple HTTP load generator)
# Install: go install github.com/rakyll/hey@latest
#   or:    sudo apt-get install hey
#
# Usage:
#   bash scripts/load-test.sh              (default: 1000 requests, 50 concurrent)
#   bash scripts/load-test.sh 5000 100     (custom: 5000 requests, 100 concurrent)

REQUESTS=${1:-1000}
CONCURRENCY=${2:-50}
TARGET=${3:-"http://localhost:8888/api/skills"}

echo "=============================="
echo "🔥 Load Test Starting"
echo "=============================="
echo "  Target:      $TARGET"
echo "  Requests:    $REQUESTS"
echo "  Concurrency: $CONCURRENCY"
echo "=============================="
echo ""

# Check if 'hey' is installed
if ! command -v hey &> /dev/null; then
    echo "Installing 'hey' load testing tool..."
    go install github.com/rakyll/hey@latest 2>/dev/null || {
        echo "❌ 'hey' not found. Install with:"
        echo "   go install github.com/rakyll/hey@latest"
        echo "   or: sudo apt-get install hey"
        exit 1
    }
fi

# Show current HPA status before test
echo "📊 HPA Status BEFORE test:"
kubectl get hpa -n skillpulse
echo ""

# Run load test
echo "🚀 Sending $REQUESTS requests ($CONCURRENCY concurrent)..."
echo ""
hey -n $REQUESTS -c $CONCURRENCY $TARGET

echo ""
echo "=============================="
echo "⏳ Waiting 30 seconds for HPA to react..."
echo "=============================="
sleep 30

# Show HPA status after test
echo ""
echo "📊 HPA Status AFTER test:"
kubectl get hpa -n skillpulse
echo ""
echo "📊 Pods AFTER test:"
kubectl get pods -n skillpulse
echo ""
echo "=============================="
echo "✅ Load test complete!"
echo "   Watch scaling: kubectl get hpa -n skillpulse --watch"
echo "=============================="
