#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/axiom"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="axiom_pg_${TIMESTAMP}.sql.gz"
RETAIN_DAYS=7

mkdir -p "$BACKUP_DIR"

# Dump from inside the Docker container, compress on the fly
docker exec axiom-postgres pg_dump -U axiom axiom | gzip > "$BACKUP_DIR/$FILENAME"

echo "Backup written: $BACKUP_DIR/$FILENAME"

# Prune old backups
find "$BACKUP_DIR" -name "axiom_pg_*.sql.gz" -mtime +$RETAIN_DAYS -delete
echo "Old backups pruned (>${RETAIN_DAYS} days)"

# Alert
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ "$TELEGRAM_BOT_TOKEN" != "your_token_here" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      -d text="?? AXIOM backup complete: ${FILENAME}" > /dev/null
fi
