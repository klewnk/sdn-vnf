#!/bin/sh

LOG_DIR="/var/log/squid"
ACCESS_LOG="${LOG_DIR}/access.log"
CACHE_LOG="${LOG_DIR}/cache.log"

cleanup_logs() {
	mkdir -p "$LOG_DIR"
	: > "$ACCESS_LOG"
	: > "$CACHE_LOG"
	rm -f /var/run/squid.pid
}

stop_proxy() {
	kill "$SQUID_PID" 2>/dev/null || true
	wait "$SQUID_PID" 2>/dev/null || true
	cleanup_logs
	exit 0
}

cleanup_logs
trap 'stop_proxy' INT TERM
trap 'cleanup_logs' EXIT

squid -N -d 1 -f /etc/squid/squid.conf &
SQUID_PID=$!
wait "$SQUID_PID"
