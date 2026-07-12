#!/bin/sh

# Squid is the authoritative source for "blocked by proxy" events. This
# monitor watches Squid access logs and raises an IDS alarm after repeated
# HTTP 403/TCP_DENIED responses for each Mininet host.

LOG_FILE="/proxy-logs/access.log"
THRESHOLD=3
STATE_FILE="/tmp/proxy_block_counts"
RED=$(printf '\033[31m')
YELLOW=$(printf '\033[33m')
RESET=$(printf '\033[0m')

echo "[IDS] Proxy block monitor waiting for ${LOG_FILE}"

while [ ! -f "$LOG_FILE" ]; do
	sleep 1
done

echo "[IDS] Proxy block monitor active"
: > "$STATE_FILE"

tail -n 0 -F "$LOG_FILE" | while read -r line; do
	echo "$line" | grep -Eq "TCP_DENIED/403| 403 " || continue

	SOURCE=$(echo "$line" | awk '{print $3}')
	echo "$SOURCE" | grep -Eq "^10\.0\.[01]\.[0-9]+$" || continue

	CURRENT=$(grep "^${SOURCE} " "$STATE_FILE" 2>/dev/null | awk '{print $2}')
	[ -n "$CURRENT" ] || CURRENT=0
	COUNT=$((CURRENT + 1))
	grep -v "^${SOURCE} " "$STATE_FILE" 2>/dev/null > "${STATE_FILE}.tmp" || true
	echo "$SOURCE $COUNT" >> "${STATE_FILE}.tmp"
	mv "${STATE_FILE}.tmp" "$STATE_FILE"

	printf '%s[IDS] Blocked proxy response observed for %s (%s/%s)%s\n' "$YELLOW" "$SOURCE" "$COUNT" "$THRESHOLD" "$RESET"

	if [ "$COUNT" -ge "$THRESHOLD" ]; then
		printf '%s[IDS] ALERT: Repeated blocked proxy access attempts by %s%s\n' "$RED" "$SOURCE" "$RESET"
		grep -v "^${SOURCE} " "$STATE_FILE" 2>/dev/null > "${STATE_FILE}.tmp" || true
		mv "${STATE_FILE}.tmp" "$STATE_FILE"
	fi
done
