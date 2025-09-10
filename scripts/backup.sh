#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p backups
docker exec -t postgres pg_dump -U spooky spooky > backups/db-$TS.sql
echo "Backup written to backups/db-$TS.sql"
