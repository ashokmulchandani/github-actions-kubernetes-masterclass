#!/bin/bash
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: bash scripts/restore-db.sh <backup-file>"
    echo "Example: bash scripts/restore-db.sh backups/skillpulse_20260517_143022.sql"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File '$BACKUP_FILE' not found!"
    exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
kubectl exec -i -n skillpulse mysql-0 -- mysql -uskillpulse -pskillpulse123 skillpulse < $BACKUP_FILE

echo "Database restored successfully!"
