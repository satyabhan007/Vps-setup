#!/bin/bash

# Endurance CRM - Automated Backup Script
# Purpose: Backup Postgres (State) and MinIO (Lakehouse)
# Frequency: Suggested every 6 hours via Cron

set -e

BACKUP_DIR="/root/backups/$(date +%Y-%m-%d_%H-%M)"
mkdir -p "$BACKUP_DIR"

echo "📦 Starting Sovereign Backup..."

# 1. Backup PostgreSQL (pgvector)
echo "💾 Backing up PostgreSQL..."
docker exec postgres pg_dump -U admin crm_db > "$BACKUP_DIR/crm_db_backup.sql"

# 2. Backup MinIO Lakehouse (Raw Logs)
echo "📦 Backing up MinIO Data..."
docker exec minio tar -czf - /data > "$BACKUP_DIR/lakehouse_backup.tar.gz"

# 3. Cleanup (Keep last 7 days)
find /root/backups/ -type d -mtime +7 -exec rm -rf {} +

echo "✅ Backup completed at $BACKUP_DIR"
echo "Next Step: Sync $BACKUP_DIR to remote S3 or cloud storage."
