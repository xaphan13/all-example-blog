#!/usr/bin/env bash
# Backup de la base de datos: pg_dump comprimido + rotación.
#
# Uso:  ./scripts/backup_db.sh [directorio]     (default: ./backups)
#
# Cron sugerido en el servidor (diario a las 3 AM):
#   0 3 * * * cd /opt/diegolonio.com && ./scripts/backup_db.sh >> backups/backup.log 2>&1
#
# Restaurar un backup (con la BD vacía):
#   gunzip -c backups/diegolonio-FECHA.sql.gz | \
#     docker compose -f docker-compose.prod.yml exec -T db psql -U diegolonio -d diegolonio
set -euo pipefail

# Raíz del proyecto, para que compose encuentre sus archivos aunque
# el script se llame desde otra carpeta (p. ej. desde cron)
cd "$(dirname "$0")/.."

BACKUP_DIR="${1:-backups}"
KEEP_DAYS=14

mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/diegolonio-$(date +%Y-%m-%d_%H%M).sql.gz"

# -T: sin TTY, necesario para que funcione en cron.
# El dump sale por stdout y se comprime aquí afuera.
docker compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U diegolonio -d diegolonio | gzip > "$FILE"

echo "$(date -Is) backup OK: $FILE ($(du -h "$FILE" | cut -f1))"

# Rotación: borra los backups con más de KEEP_DAYS días
find "$BACKUP_DIR" -name 'diegolonio-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
