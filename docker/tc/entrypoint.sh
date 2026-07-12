#!/bin/sh

# Apply basic traffic shaping on eth0 (or override with ENV)
IFACE=${IFACE:-eth1}
RATE=${RATE:-1mbit}
BURST=${BURST:-32kbit}
LATENCY=${LATENCY:-400ms}

# Clear any existing qdisc
tc qdisc del dev "$IFACE" root 2>/dev/null

# Apply shaping using TBF
tc qdisc add dev "$IFACE" root tbf rate $RATE burst $BURST latency $LATENCY

# Keep container alive
exec /bin/sh
