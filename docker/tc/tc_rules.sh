#!/bin/bash

IFACE=${IFACE:-eth1}

echo "Waiting for $IFACE to appear..."
# Περιμένει μέχρι το Mininet (OVS) να καρφώσει την eth1 στο container
while ! ip link show "$IFACE" > /dev/null 2>&1; do
  sleep 1
done

echo "$IFACE is up! Applying QoS rules..."

# 1. Καθαρισμός παλιών κανόνων
tc qdisc del dev "$IFACE" root 2>/dev/null

# 2. Ενεργοποίηση HTB 
tc qdisc add dev "$IFACE" root handle 1: htb default 20

# 3. Δημιουργία της κεντρικής "Σωλήνας" (100Mbps)
tc class add dev "$IFACE" parent 1: classid 1:1 htb rate 100mbit

# 4. ΚΛΑΣΗ 10: VIP (50-100Mbps)
tc class add dev "$IFACE" parent 1:1 classid 1:10 htb rate 50mbit ceil 100mbit prio 1

# 5. ΚΛΑΣΗ 20: Αργή/Προεπιλεγμένη (1-10Mbps)
tc class add dev "$IFACE" parent 1:1 classid 1:20 htb rate 1mbit ceil 10mbit prio 2

# 6. ΦΙΛΤΡΑ
# Ping
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip protocol 1 0xff flowid 1:10
# HTTP
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 80 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 80 0xffff flowid 1:10
# HTTPS (Και τα δύο!)
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 443 0xffff flowid 1:10
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip sport 443 0xffff flowid 1:10
# DNS
tc filter add dev "$IFACE" protocol ip parent 1:0 prio 1 u32 match ip dport 53 0xffff flowid 1:10

echo "QoS Rules Applied Successfully!"

# 7. Διατήρηση του container ζωντανού
tail -f /dev/null