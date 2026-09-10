#!/bin/sh

IFACE=${IFACE:-eth1}
RATE=${RATE:-1mbit}
BURST=${BURST:-32kbit}
LATENCY=${LATENCY:-400ms}

tc qdisc del dev "$IFACE" root 2>/dev/null
tc qdisc add dev "$IFACE" root tbf rate $RATE burst $BURST latency $LATENCY
exec /bin/sh
