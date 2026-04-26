#!/bin/sh

# 1. Ενεργοποίηση Routing (Χωρίς αυτό το VNF δεν περνάει πακέτα)
sysctl -w net.ipv4.ip_forward=1

# 2. Καθαρισμός παλιών κανόνων
iptables -F
iptables -X

# 3. Γενική Πολιτική: Κόβουμε τα πάντα στα FORWARD (Whitelisting approach)
iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 4. Κανόνας "Μνήμης" (Stateful): Επιτρέπει την επιστροφή των πακέτων
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# 5. Επιτρέπουμε το Web (HTTP/HTTPS) - Πόρτες 80 & 443
iptables -A FORWARD -p tcp --dport 80 -j ACCEPT
iptables -A FORWARD -p tcp --dport 443 -j ACCEPT

# 6. Επιτρέπουμε το DNS (για να βρίσκουν οι host τα sites)
iptables -A FORWARD -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -p tcp --dport 53 -j ACCEPT

# 7. Περιορισμός Ping (ICMP Rate Limit) - Η δική σου βελτίωση!
iptables -A FORWARD -p icmp -m limit --limit 1/s -j ACCEPT

# 8. Καταγραφή των "παράνομων" προσπαθειών (Logging)
iptables -A FORWARD -j LOG --log-prefix "VNF_FW_BLOCK: "