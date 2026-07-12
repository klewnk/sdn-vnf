#!/bin/sh

echo "[IDS] Starting IDS monitors"
echo "[IDS] Launching proxy block monitor"
/usr/local/bin/proxy_block_monitor.sh &
echo "[IDS] Launching DNS query monitor"
/usr/local/bin/dns_query_monitor.sh &
echo "[IDS] Launching WAF block monitor"
/usr/local/bin/waf_block_monitor.sh &

echo "[IDS] Waiting for eth1 from Mininet/OVS"
while ! ip link show eth1 >/dev/null 2>&1; do
	sleep 1
done

echo "[IDS] eth1 found, starting Snort"
touch /tmp/ids.alert
tail -F /tmp/ids.alert &
exec snort -i eth1 -A alert_fast -l /tmp -q -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules
