#!/bin/sh

LOG_DIR="/dns-logs"
QUERY_LOG="${LOG_DIR}/queries.log"

cleanup_logs() {
	mkdir -p "$LOG_DIR"
	: > "$QUERY_LOG"
}

stop_dns() {
	kill "$DNS_LOG_PID" 2>/dev/null || true
	wait "$DNS_LOG_PID" 2>/dev/null || true
	cleanup_logs
	exit 0
}

cleanup_logs
trap 'stop_dns' INT TERM
trap 'cleanup_logs' EXIT

coredns -conf ./Corefile 2>&1 | tee -a "$QUERY_LOG" &
DNS_LOG_PID=$!
wait "$DNS_LOG_PID"
