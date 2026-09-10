#!/bin/bash

IFACE=${IFACE:-eth1}

echo "Waiting for $IFACE to appear..."
while ! ip link show "$IFACE" > /dev/null 2>&1; do
  sleep 1
done

/scripts/apply_qos.sh || echo "Initial QoS apply failed; vnf-topo.py will re-apply after ovs-docker add-port."

exec tail -f /dev/null
