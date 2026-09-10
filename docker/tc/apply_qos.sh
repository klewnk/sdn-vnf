#!/bin/bash

IFACE=${IFACE:-eth1}

echo 1 > /proc/sys/net/ipv4/ip_forward

for _ in $(seq 1 15); do
  if ip link show "$IFACE" > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! ip link show "$IFACE" > /dev/null 2>&1; then
  echo "ERROR: interface $IFACE not found" >&2
  exit 1
fi

ip link set "$IFACE" up 2>/dev/null || true

tc qdisc del dev "$IFACE" root 2>/dev/null || true

tc qdisc add dev "$IFACE" root handle 1: htb default 20

tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 100mbit

tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 50mbit ceil 100mbit prio 1

tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 10mbit prio 2

tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip protocol 1 0xff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 80 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 80 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 443 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 443 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 53 0xffff flowid 1:10

echo "QoS rules applied on $IFACE"
