#!/bin/bash
echo "Backing up MySQL database..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

kubectl exec -n skillpulse mysql-0 -- mysqldump -uskillpulse -pskillpulse123 skillpulse > $BACKUP_DIR/skillpulse_$TIMESTAMP.sql

echo "Backup saved to $BACKUP_DIR/skillpulse_$TIMESTAMP.sql"
echo "Backup complete!"
