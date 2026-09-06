#!/bin/bash

IFACE=${IFACE:-eth1}

echo 1 > /proc/sys/net/ipv4/ip_forward

echo "Waiting for $IFACE to appear..."
while ! ip link show "$IFACE" > /dev/null 2>&1; do
  sleep 1
done

echo "$IFACE is up! Applying QoS rules..."

tc qdisc del dev "$IFACE" root 2>/dev/null

# HTB classes: high-priority traffic gets more bandwidth than the default class.
tc qdisc add dev "$IFACE" root handle 1: htb default 20

tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 100mbit

tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 50mbit ceil 100mbit prio 1

tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 10mbit prio 2

# Prioritize ICMP, HTTP, HTTPS, and DNS.
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip protocol 1 0xff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 80 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 80 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 443 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 443 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 53 0xffff flowid 1:10

echo "QoS Rules Applied Successfully!"

tail -f /dev/null