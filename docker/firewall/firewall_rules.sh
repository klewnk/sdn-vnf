#!/bin/sh

sysctl -w net.ipv4.ip_forward=1

iptables -F
iptables -X

iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -p tcp --dport 80 -j ACCEPT
iptables -A FORWARD -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -p tcp --dport 53 -j ACCEPT

iptables -A FORWARD -p icmp -m limit --limit 1/s -j ACCEPT
iptables -A FORWARD -j LOG --log-prefix "VNF_FW_BLOCK: "