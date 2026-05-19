#!/bin/bash
echo "Backing up database to S3..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
S3_BUCKET="s3://skillpulse-backups-ashok"

mkdir -p $BACKUP_DIR

# Dump database
kubectl exec -n skillpulse mysql-0 -- mysqldump -uskillpulse -pskillpulse123 skillpulse > $BACKUP_DIR/skillpulse_$TIMESTAMP.sql

# Upload to S3
aws s3 cp $BACKUP_DIR/skillpulse_$TIMESTAMP.sql $S3_BUCKET/backups/skillpulse_$TIMESTAMP.sql

# Clean local file (optional)
rm $BACKUP_DIR/skillpulse_$TIMESTAMP.sql

echo "Backup uploaded to $S3_BUCKET/backups/skillpulse_$TIMESTAMP.sql"
echo "Done!"
