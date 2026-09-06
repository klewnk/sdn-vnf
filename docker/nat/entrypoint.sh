#!/bin/sh
set -e

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -F
iptables -P FORWARD ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

exec /bin/sh
