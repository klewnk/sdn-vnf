#!/bin/sh

echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null || true

iptables -t nat -F 2>/dev/null || true
iptables -P FORWARD ACCEPT 2>/dev/null || true
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true

exec /bin/sh
