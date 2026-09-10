#!/bin/sh

WAF_LOG_DIR="/waf-logs"
NGINX_ACCESS_LOG="${WAF_LOG_DIR}/nginx/access.log"
LAST_EVENT_FILE="/tmp/waf_last_event"
RED=$(printf '\033[31m')
RESET=$(printf '\033[0m')

echo "[IDS] WAF block monitor waiting for ${NGINX_ACCESS_LOG}"

while [ ! -f "$NGINX_ACCESS_LOG" ]; do
	sleep 1
done

echo "[IDS] WAF block monitor active"
: > "$LAST_EVENT_FILE"

tail -n 0 -F "$NGINX_ACCESS_LOG" 2>/dev/null | while read -r line; do
	echo "$line" | grep -Eq '" 403 ' || continue

	SOURCE=$(echo "$line" | awk '{print $1}')
	echo "$SOURCE" | grep -Eq "^10\.0\.[01]\.[0-9]+$" || continue

	REQUEST=$(echo "$line" | sed -n 's/.*"\(GET\|POST\|PUT\|DELETE\|OPTIONS\) \([^"]*\) [^"]*".*/\1 \2/p')
	[ -n "$REQUEST" ] || REQUEST="blocked HTTP request"

	EVENT="${SOURCE} ${REQUEST}"
	if [ "$EVENT" = "$(cat "$LAST_EVENT_FILE" 2>/dev/null)" ]; then
		continue
	fi
	echo "$EVENT" > "$LAST_EVENT_FILE"

	printf '%s[IDS] ALERT: WAF blocked suspicious request from %s: %s%s\n' "$RED" "$SOURCE" "$REQUEST" "$RESET"
done
