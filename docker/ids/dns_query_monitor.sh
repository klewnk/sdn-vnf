#!/bin/sh

LOG_FILE="/dns-logs/queries.log"
RED=$(printf '\033[31m')
RESET=$(printf '\033[0m')

echo "[IDS] DNS query monitor waiting for ${LOG_FILE}"

mkdir -p /dns-logs
touch "$LOG_FILE"

while [ ! -f "$LOG_FILE" ]; do
	sleep 1
done

echo "[IDS] DNS query monitor active"

tail -n 0 -F "$LOG_FILE" | while read -r line; do
	echo "$line" | grep -q "\[INFO\]" || continue
	echo "$line" | grep -Eiq "malware\.test|phishing\.test|casino\.test|blocked\.test" || continue

	DOMAIN=$(echo "$line" | sed -n 's/.*"\(A\|AAAA\) IN \([^ ]*\).*/\2/p')
	SOURCE=$(echo "$line" | awk '{print $2}' | cut -d: -f1)
	echo "$SOURCE" | grep -Eq "^10\.0\.[01]\.[0-9]+$" || continue

	printf '%s[IDS] ALERT: Suspicious DNS query from %s: %s%s\n' "$RED" "$SOURCE" "$DOMAIN" "$RESET"
done
