#!/bin/bash
echo "Setting up daily backup cron job..."

SCRIPT_PATH="/home/ec2-user/github-actions-kubernetes-masterclass/scripts/backup-to-s3.sh"

# Add cron job - runs every day at 2:00 AM
(crontab -l 2>/dev/null; echo "0 2 * * * bash $SCRIPT_PATH >> /var/log/backup.log 2>&1") | crontab -

echo "Cron job added! Backup will run daily at 2:00 AM"
echo "Check logs at: /var/log/backup.log"
crontab -l
