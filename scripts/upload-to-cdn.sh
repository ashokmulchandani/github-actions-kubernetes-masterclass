#!/bin/bash
# Upload frontend static files to S3 (CDN will serve them globally)
#
# Usage: bash scripts/upload-to-cdn.sh
#
# What this does:
#   1. Syncs frontend files (CSS, JS, images) to S3 bucket
#   2. CloudFront automatically picks them up
#   3. Users worldwide get files from nearest edge server

S3_BUCKET="s3://skillpulse-static-assets-ashok"

echo "=============================="
echo "📦 Uploading static files to CDN"
echo "=============================="

# Upload CSS
echo "  Uploading CSS..."
aws s3 sync frontend/css $S3_BUCKET/css --cache-control "max-age=86400"

# Upload JS
echo "  Uploading JS..."
aws s3 sync frontend/js $S3_BUCKET/js --cache-control "max-age=86400"

# Upload HTML
echo "  Uploading HTML..."
aws s3 cp frontend/index.html $S3_BUCKET/index.html --cache-control "max-age=3600"

echo ""
echo "=============================="
echo "✅ Upload complete!"
echo "   Files available at: https://$(aws cloudfront list-distributions --query 'DistributionList.Items[0].DomainName' --output text)"
echo "=============================="
