#!/bin/sh

LOG_DIR="/cache-logs"

cleanup_logs() {
	mkdir -p "$LOG_DIR"
	: > "${LOG_DIR}/access.log"
	: > "${LOG_DIR}/error.log"
}

cleanup_logs
trap 'cleanup_logs; exit 0' INT TERM
trap 'cleanup_logs' EXIT

echo "[CACHE] Edge Cache VNF starting"
echo "[CACHE] Logs: ${LOG_DIR}/access.log"
exec nginx -g "daemon off;"
