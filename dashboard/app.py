#!/usr/bin/env python3
import json
import shlex
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCKER_DIR = ROOT / "docker"
STATIC_DIR = Path(__file__).resolve().parent / "static"
HOST = "127.0.0.1"
PORT = 5000
TIMEOUT = 30
CONTAINERS = [
    "vnf_nat",
    "vnf_dns",
    "vnf_firewall",
    "vnf_frr",
    "vnf_tc",
    "vnf_lb",
    "lb_backend1",
    "lb_backend2",
    "vnf_waf",
    "vnf_proxy",
    "vnf_ids",
    "vnf_cache",
    "cache_origin",
    "prometheus",
    "cadvisor",
    "grafana",
    "dozzle",
]


def docker(command):
    return {
        "kind": "docker",
        "cwd": str(DOCKER_DIR),
        "command": command,
    }


def host(hostname, command):
    quoted = shlex.quote(command)
    script = (
        f'pid=$(pgrep -f "mininet:{hostname}$" | head -n 1); '
        f'if [ -z "$pid" ]; then '
        f'echo "Mininet host {hostname} not found. Start vnf-topo.py first."; exit 2; '
        f'fi; '
        f'mnexec -a "$pid" sh -lc {quoted}'
    )
    return {
        "kind": "mininet",
        "cwd": str(ROOT),
        "command": script,
    }


def firewall_demo(command, summary, grep_pattern):
    quoted = shlex.quote(command)
    quoted_summary = shlex.quote(summary)
    quoted_pattern = shlex.quote(grep_pattern)
    script = (
        'pid=$(pgrep -f "mininet:h1$" | head -n 1); '
        'if [ -z "$pid" ]; then '
        'echo "Mininet host h1 not found. Start vnf-topo.py first."; exit 2; '
        'fi; '
        'docker exec vnf_firewall iptables -Z FORWARD; '
        f'mnexec -a "$pid" sh -lc {quoted}; '
        f'echo {quoted_summary}; '
        f'docker exec vnf_firewall iptables -L FORWARD -v -n | grep -E {quoted_pattern}'
    )
    return {
        "kind": "firewall",
        "cwd": str(ROOT),
        "command": script,
    }


def nat_demo(command, summary):
    quoted = shlex.quote(command)
    quoted_summary = shlex.quote(summary)
    script = (
        'pid=$(pgrep -f "mininet:h1$" | head -n 1); '
        'if [ -z "$pid" ]; then '
        'echo "Mininet host h1 not found. Start vnf-topo.py first."; exit 2; '
        'fi; '
        'docker exec vnf_nat iptables -t nat -Z 2>/dev/null || true; '
        f'mnexec -a "$pid" sh -lc {quoted}; '
        f'echo {quoted_summary}; '
        'docker exec vnf_nat iptables -t nat -L POSTROUTING -v -n'
    )
    return {
        "kind": "nat",
        "cwd": str(ROOT),
        "command": script,
    }


def tc_demo(command, summary):
    quoted = shlex.quote(command)
    quoted_summary = shlex.quote(summary)
    script = (
        'pid=$(pgrep -f "mininet:h1$" | head -n 1); '
        'if [ -z "$pid" ]; then '
        'echo "Mininet host h1 not found. Start vnf-topo.py first."; exit 2; '
        'fi; '
        'echo "=== HTB class statistics BEFORE ==="; '
        'docker exec vnf_tc tc -s class show dev eth1 | grep -E "class htb|Sent" || true; '
        f'mnexec -a "$pid" sh -lc {quoted}; '
        f'echo {quoted_summary}; '
        'echo "=== HTB class statistics AFTER ==="; '
        'docker exec vnf_tc tc -s class show dev eth1 | grep -E "class htb|Sent" || true'
    )
    return {
        "kind": "tc",
        "cwd": str(ROOT),
        "command": script,
    }


TESTS = [
    {
        "id": "lab-start",
        "group": "Lab Control",
        "category": "Docker compose controls",
        "title": "Start all services",
        "description": "Starts all Docker Compose services for the SDN-VNF lab.",
        "commands": ["docker compose up -d"],
        "spec": docker("docker compose up -d"),
    },
    {
        "id": "lab-stop",
        "group": "Lab Control",
        "category": "Docker compose controls",
        "title": "Stop all services",
        "description": "Stops the Docker Compose services and removes orphan containers.",
        "commands": ["docker compose down --remove-orphans"],
        "spec": docker("docker compose down --remove-orphans"),
    },
    {
        "id": "lab-compose-ps",
        "group": "Lab Control",
        "category": "Docker compose controls",
        "title": "Show compose status",
        "description": "Prints Docker Compose service status in the output panel.",
        "commands": ["docker compose ps"],
        "spec": docker("docker compose ps"),
    },
    {
        "id": "dns-normal",
        "group": "DNS",
        "category": "Normal resolution",
        "title": "Resolve google.com",
        "description": "Shows that h1 can use the DNS VNF for name resolution.",
        "commands": ["h1 nslookup google.com 10.0.0.100"],
        "spec": host("h1", "nslookup google.com 10.0.0.100"),
    },
    {
        "id": "dns-hua",
        "group": "DNS",
        "category": "Normal resolution",
        "title": "Resolve hua.gr",
        "description": "Resolves the university domain through the DNS VNF.",
        "commands": ["h1 nslookup hua.gr 10.0.0.100"],
        "spec": host("h1", "nslookup hua.gr 10.0.0.100"),
    },
    {
        "id": "dns-github",
        "group": "DNS",
        "category": "Normal resolution",
        "title": "Resolve github.com",
        "description": "Shows that the DNS VNF can forward external domain queries.",
        "commands": ["h1 nslookup github.com 10.0.0.100"],
        "spec": host("h1", "nslookup github.com 10.0.0.100"),
    },
    {
        "id": "dns-suspicious",
        "group": "IDS",
        "category": "DNS alert detection",
        "title": "Detect phishing and malware DNS queries",
        "description": "Sends suspicious DNS queries and then prints the IDS alert output.",
        "commands": [
            "h1 nslookup phishing.test 10.0.0.100",
            "h1 nslookup malware.test 10.0.0.100",
            "sh docker logs --tail 30 vnf_ids",
        ],
        "spec": docker(
            "pid=$(pgrep -f \"mininet:h1$\" | head -n 1); "
            "if [ -z \"$pid\" ]; then echo \"Mininet host h1 not found. Start vnf-topo.py first.\"; exit 2; fi; "
            "mnexec -a \"$pid\" nslookup phishing.test 10.0.0.100 || true; "
            "mnexec -a \"$pid\" nslookup malware.test 10.0.0.100 || true; "
            "docker logs --tail 30 vnf_ids"
        ),
    },
    {
        "id": "dns-suspicious-extra",
        "group": "IDS",
        "category": "DNS alert detection",
        "title": "Detect casino and blocked DNS queries",
        "description": "Sends more suspicious DNS queries and then prints the IDS alert output.",
        "commands": [
            "h1 nslookup casino.test 10.0.0.100",
            "h1 nslookup blocked.test 10.0.0.100",
            "sh docker logs --tail 30 vnf_ids",
        ],
        "spec": docker(
            "pid=$(pgrep -f \"mininet:h1$\" | head -n 1); "
            "if [ -z \"$pid\" ]; then echo \"Mininet host h1 not found. Start vnf-topo.py first.\"; exit 2; fi; "
            "mnexec -a \"$pid\" nslookup casino.test 10.0.0.100 || true; "
            "mnexec -a \"$pid\" nslookup blocked.test 10.0.0.100 || true; "
            "docker logs --tail 30 vnf_ids"
        ),
    },
    {
        "id": "dns-ids-alerts",
        "group": "IDS",
        "category": "DNS alert detection",
        "title": "Show recent DNS alerts",
        "description": "Prints recent IDS output after suspicious DNS queries.",
        "commands": ["sh docker logs --tail 30 vnf_ids"],
        "spec": docker("docker logs --tail 30 vnf_ids"),
    },
    {
        "id": "proxy-allowed",
        "group": "Proxy",
        "category": "Allowed examples",
        "title": "Allow normal domain",
        "description": "Client explicitly uses the Proxy VNF with -x. The domain is allowed.",
        "commands": ["h1 curl -x http://10.0.0.10:3128 -I http://example.com"],
        "spec": host("h1", "curl -x http://10.0.0.10:3128 -I http://example.com"),
    },
    {
        "id": "proxy-allowed-file",
        "group": "Proxy",
        "category": "Allowed examples",
        "title": "Allow safe file type",
        "description": "Allowed because .txt is not one of the blocked file extensions.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 \"http://example.com/?file=report.txt\""
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 \"http://example.com/?file=report.txt\"",
        ),
    },
    {
        "id": "proxy-allowed-keyword",
        "group": "Proxy",
        "category": "Allowed examples",
        "title": "Allow safe keyword",
        "description": "Allowed because the URL does not contain blocked words like casino, malware, or phishing.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 \"http://example.com/?topic=education\""
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 \"http://example.com/?topic=education\"",
        ),
    },
    {
        "id": "proxy-domain-block",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by domain: youtube.com",
        "description": "Client explicitly uses the Proxy VNF with -x. youtube.com is blocked by domain ACL.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://youtube.com"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://youtube.com",
        ),
    },
    {
        "id": "proxy-facebook-block",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by domain: facebook.com",
        "description": "Requests facebook.com through the explicit Proxy VNF.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://facebook.com"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://facebook.com",
        ),
    },
    {
        "id": "proxy-file-block",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by file type: .exe",
        "description": "Requests a .exe file through the explicit Proxy VNF.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://example.com/test.exe"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://example.com/test.exe",
        ),
    },
    {
        "id": "proxy-zip-block",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by file type: .zip",
        "description": "Requests a .zip file through the explicit Proxy VNF.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://example.com/archive.zip"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://example.com/archive.zip",
        ),
    },
    {
        "id": "proxy-keyword-casino",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by keyword: casino",
        "description": "Requests a URL containing a blocked keyword through the explicit Proxy VNF.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://example.com/casino"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://example.com/casino",
        ),
    },
    {
        "id": "proxy-keyword-phishing",
        "group": "Proxy",
        "category": "Blocked examples",
        "title": "Block by keyword: phishing",
        "description": "Requests a URL containing a blocked keyword through the explicit Proxy VNF.",
        "commands": [
            "h1 curl -I -x http://10.0.0.10:3128 http://example.com/phishing"
        ],
        "spec": host(
            "h1",
            "curl -I -x http://10.0.0.10:3128 http://example.com/phishing",
        ),
    },
    {
        "id": "ids-proxy-alert",
        "group": "IDS",
        "category": "Proxy alert detection",
        "title": "Detect repeated proxy blocks",
        "description": "Creates repeated blocked proxy attempts, then prints recent IDS alert output.",
        "commands": [
            "h1 curl -x http://10.0.0.10:3128 -o /dev/null http://facebook.com",
            "h1 curl -x http://10.0.0.10:3128 -o /dev/null http://facebook.com",
            "h1 curl -x http://10.0.0.10:3128 -o /dev/null http://facebook.com",
            "sh docker logs --tail 30 vnf_ids",
        ],
        "spec": docker(
            "pid=$(pgrep -f \"mininet:h1$\" | head -n 1); "
            "if [ -z \"$pid\" ]; then echo \"Mininet host h1 not found. Start vnf-topo.py first.\"; exit 2; fi; "
            "mnexec -a \"$pid\" curl -s -x http://10.0.0.10:3128 -o /dev/null http://facebook.com; "
            "mnexec -a \"$pid\" curl -s -x http://10.0.0.10:3128 -o /dev/null http://facebook.com; "
            "mnexec -a \"$pid\" curl -s -x http://10.0.0.10:3128 -o /dev/null http://facebook.com; "
            "docker logs --tail 30 vnf_ids"
        ),
    },
    {
        "id": "ids-waf-alert",
        "group": "IDS",
        "category": "WAF alert detection",
        "title": "Detect WAF SQL injection block",
        "description": "Sends a SQL injection request to the WAF, then prints the IDS alert output.",
        "commands": [
            "h1 curl -o /dev/null \"http://10.0.0.11:8080/?id=1%27%20OR%20%271%27%3D%271\"",
            "sh docker logs --tail 30 vnf_ids",
        ],
        "spec": docker(
            "pid=$(pgrep -f \"mininet:h1$\" | head -n 1); "
            "if [ -z \"$pid\" ]; then echo \"Mininet host h1 not found. Start vnf-topo.py first.\"; exit 2; fi; "
            "mnexec -a \"$pid\" curl -s -o /dev/null \"http://10.0.0.11:8080/?id=1%27%20OR%20%271%27%3D%271\" || true; "
            "docker logs --tail 30 vnf_ids"
        ),
    },
    {
        "id": "waf-normal",
        "group": "WAF",
        "category": "Allowed examples",
        "title": "Allow normal web request",
        "description": "Sends a clean request to the WAF-protected web app. Expected output includes HTTP 200.",
        "commands": ["h1 curl -I http://10.0.0.11:8080/"],
        "spec": host("h1", "curl -I http://10.0.0.11:8080/"),
    },
    {
        "id": "waf-safe-query",
        "group": "WAF",
        "category": "Allowed examples",
        "title": "Allow safe query parameter",
        "description": "Sends a normal query string that should not match attack rules.",
        "commands": ["h1 curl -I \"http://10.0.0.11:8080/?page=home\""],
        "spec": host("h1", "curl -I \"http://10.0.0.11:8080/?page=home\""),
    },
    {
        "id": "waf-sqli",
        "group": "WAF",
        "category": "Blocked examples",
        "title": "Block SQL injection",
        "description": "Blocks a payload that tries to manipulate a database query: id=1' OR '1'='1.",
        "commands": [
            "h1 curl -G -I --data-urlencode \"id=1' OR '1'='1\" http://10.0.0.11:8080/"
        ],
        "spec": host(
            "h1",
            "curl -G -I --data-urlencode \"id=1' OR '1'='1\" http://10.0.0.11:8080/",
        ),
    },
    {
        "id": "waf-xss",
        "group": "WAF",
        "category": "Blocked examples",
        "title": "Block XSS payload",
        "description": "Blocks a payload that tries to inject JavaScript into the web page.",
        "commands": [
            "h1 curl -G -I --data-urlencode \"q=<script>alert(1)</script>\" http://10.0.0.11:8080/"
        ],
        "spec": host(
            "h1",
            "curl -G -I --data-urlencode \"q=<script>alert(1)</script>\" http://10.0.0.11:8080/",
        ),
    },
    {
        "id": "waf-path-traversal",
        "group": "WAF",
        "category": "Blocked examples",
        "title": "Block path traversal",
        "description": "Blocks a payload that tries to access server files like /etc/passwd.",
        "commands": [
            "h1 curl -G -I --data-urlencode \"file=../../etc/passwd\" http://10.0.0.11:8080/"
        ],
        "spec": host(
            "h1",
            "curl -G -I --data-urlencode \"file=../../etc/passwd\" http://10.0.0.11:8080/",
        ),
    },
    {
        "id": "lb-distribution",
        "group": "Load Balancer",
        "category": "Normal distribution",
        "title": "Show backend distribution",
        "description": "Sends repeated requests through the Load Balancer VNF.",
        "commands": ["h1 sh -c 'for i in 1 2 3 4 5 6; do curl -s http://10.0.0.8/ | grep Backend; done'"],
        "spec": host("h1", "for i in 1 2 3 4 5 6; do curl -s http://10.0.0.8/ | grep Backend; done"),
    },
    {
        "id": "lb-least-conn",
        "group": "Load Balancer",
        "category": "Least connections use case",
        "title": "Prefer backend with fewer active connections",
        "description": "Opens a slow request, then sends new requests while one backend is busy.",
        "commands": [
            "h1 sh -c 'curl -s http://10.0.0.8/slow >/dev/null & sleep 1; for i in 1 2 3 4 5 6; do curl -s http://10.0.0.8/ | grep Backend; done'"
        ],
        "spec": host(
            "h1",
            "echo \"Opening one slow request to occupy a backend...\"; "
            "curl -s http://10.0.0.8/slow >/tmp/lb_slow.out & "
            "slow=$!; "
            "sleep 1; "
            "echo \"New requests while the slow connection is active:\"; "
            "for i in 1 2 3 4 5 6; do curl -s http://10.0.0.8/ | grep Backend; done; "
            "kill $slow 2>/dev/null || true; "
            "wait $slow 2>/dev/null || true",
        ),
    },
    {
        "id": "cache-hit",
        "group": "Edge Cache",
        "category": "Cache behavior",
        "title": "h1 caches large file",
        "description": "h1 requests the same large file twice. First clean run: MISS then HIT. Later runs may be HIT then HIT.",
        "commands": [
            "h1 curl -s -I http://10.0.0.30/bigfile.dat",
            "h1 curl -s -I http://10.0.0.30/bigfile.dat",
        ],
        "spec": host("h1", "curl -s -I http://10.0.0.30/bigfile.dat; curl -s -I http://10.0.0.30/bigfile.dat"),
    },
    {
        "id": "cache-homepage",
        "group": "Edge Cache",
        "category": "Cache behavior",
        "title": "h1 caches HTML page",
        "description": "h1 requests the origin HTML page twice. The Edge Cache stores the page response, not only files.",
        "commands": [
            "h1 curl -s -I http://10.0.0.30/",
            "h1 curl -s -I http://10.0.0.30/",
        ],
        "spec": host("h1", "curl -s -I http://10.0.0.30/; curl -s -I http://10.0.0.30/"),
    },
    {
        "id": "cache-h2-homepage",
        "group": "Edge Cache",
        "category": "Cache behavior",
        "title": "h2 reuses cached HTML page",
        "description": "h2 requests the same HTML page. If h1 cached it before, h2 can receive it from the shared Edge Cache.",
        "commands": [
            "h2 curl -s -I http://10.0.0.30/",
            "h2 curl -s -I http://10.0.0.30/",
        ],
        "spec": host("h2", "curl -s -I http://10.0.0.30/; curl -s -I http://10.0.0.30/"),
    },
    {
        "id": "firewall-policy",
        "group": "Firewall",
        "category": "Policy inspection",
        "title": "Show default deny and allow rules",
        "description": "Prints the active iptables policy: default DROP with selected allowed traffic.",
        "commands": ["sh docker exec vnf_firewall iptables -S"],
        "spec": docker("docker exec vnf_firewall iptables -S"),
    },
    {
        "id": "firewall-counters",
        "group": "Firewall",
        "category": "Policy inspection",
        "title": "Show firewall counters",
        "description": "Prints packet counters for forwarded traffic and helps prove which rules are being hit.",
        "commands": ["sh docker exec vnf_firewall iptables -L FORWARD -v -n"],
        "spec": docker("docker exec vnf_firewall iptables -L FORWARD -v -n"),
    },
    {
        "id": "firewall-allow-http",
        "group": "Firewall",
        "category": "Allowed traffic tests",
        "title": "Allow HTTP port 80",
        "description": "Generates HTTP traffic and then shows that the TCP dpt:80 allow rule was hit.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 curl -s -I --max-time 5 http://example.com >/dev/null || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "curl -s -I --max-time 5 http://example.com >/dev/null || true",
            "ALLOWED: HTTP port 80 is explicitly permitted by the Firewall VNF.",
            "tcp dpt:80",
        ),
    },
    {
        "id": "firewall-allow-https",
        "group": "Firewall",
        "category": "Allowed traffic tests",
        "title": "Allow HTTPS port 443",
        "description": "Generates HTTPS traffic and then shows that the TCP dpt:443 allow rule was hit.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 curl -s -I --max-time 5 https://example.com >/dev/null || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "curl -s -I --max-time 5 https://example.com >/dev/null || true",
            "ALLOWED: HTTPS port 443 is explicitly permitted by the Firewall VNF.",
            "tcp dpt:443",
        ),
    },
    {
        "id": "firewall-allow-dns",
        "group": "Firewall",
        "category": "Allowed traffic tests",
        "title": "Allow DNS port 53",
        "description": "Generates DNS traffic and then shows that the UDP dpt:53 allow rule was hit.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 nslookup google.com 8.8.8.8 >/dev/null || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "nslookup google.com 8.8.8.8 >/dev/null || true",
            "ALLOWED: DNS port 53 is explicitly permitted by the Firewall VNF.",
            "udp dpt:53|tcp dpt:53",
        ),
    },
    {
        "id": "firewall-allow-icmp",
        "group": "Firewall",
        "category": "Allowed traffic tests",
        "title": "Allow limited ICMP",
        "description": "Generates ICMP traffic and then shows that the rate-limited ICMP allow rule was hit.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 ping -c 3 8.8.8.8 || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "ping -c 3 8.8.8.8 || true",
            "ALLOWED: ICMP is permitted with a rate limit by the Firewall VNF.",
            "icmp",
        ),
    },
    {
        "id": "firewall-block-ssh",
        "group": "Firewall",
        "category": "Blocked traffic tests",
        "title": "Block SSH port 22",
        "description": "Generates SSH traffic. No allow rule exists for TCP 22, so it should hit the default deny path.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 nc -vz -w 3 8.8.8.8 22 || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "nc -vz -w 3 8.8.8.8 22 || true",
            "BLOCKED: TCP port 22 is not in the allow list, so it reaches VNF_FW_BLOCK/default DROP.",
            "Chain FORWARD|VNF_FW_BLOCK",
        ),
    },
    {
        "id": "firewall-block-custom",
        "group": "Firewall",
        "category": "Blocked traffic tests",
        "title": "Block custom port 9999",
        "description": "Generates traffic to a non-allowed custom port, which should be dropped by default policy.",
        "commands": [
            "sh docker exec vnf_firewall iptables -Z FORWARD",
            "h1 nc -vz -w 3 8.8.8.8 9999 || true",
            "sh docker exec vnf_firewall iptables -L FORWARD -v -n",
        ],
        "spec": firewall_demo(
            "nc -vz -w 3 8.8.8.8 9999 || true",
            "BLOCKED: TCP port 9999 is not in the allow list, so it reaches VNF_FW_BLOCK/default DROP.",
            "Chain FORWARD|VNF_FW_BLOCK",
        ),
    },
    {
        "id": "frr-routes",
        "group": "FRR Router",
        "category": "Routing proof",
        "title": "Show router routes",
        "description": "Prints the routing table inside the FRR Router VNF.",
        "commands": ["sh docker exec vnf_frr ip route"],
        "spec": docker("docker exec vnf_frr ip route"),
    },
    {
        "id": "frr-interfaces",
        "group": "FRR Router",
        "category": "Routing proof",
        "title": "Show router interfaces",
        "description": "Shows that the router has one interface in each Mininet subnet.",
        "commands": ["sh docker exec vnf_frr ip -br addr show eth1; docker exec vnf_frr ip -br addr show eth2"],
        "spec": docker("docker exec vnf_frr ip -br addr show eth1; docker exec vnf_frr ip -br addr show eth2"),
    },
    {
        "id": "frr-h1-to-h3",
        "group": "FRR Router",
        "category": "Inter-subnet test",
        "title": "Route h1 to h3",
        "description": "Tests inter-subnet routing from h1 in 10.0.0.0/24 to h3 in 10.0.1.0/24.",
        "commands": ["h1 ping -c 3 10.0.1.3"],
        "spec": host("h1", "ping -c 3 10.0.1.3"),
    },
    {
        "id": "nat-chain-outbound",
        "group": "NAT",
        "title": "Outbound VNF chain (HTTP)",
        "description": (
            "Tests Internet access from h1 through the outbound chain: "
            "Router -> Firewall -> TC -> Proxy -> NAT. HTTP 200 is the success signal."
        ),
        "commands": [
            "h1 ip route get 8.8.8.8",
            "h1 curl -s -o /dev/null -w 'HTTP %{http_code}\\n' --max-time 10 http://example.com",
            "h1 curl -sI --max-time 10 http://example.com | head -n 8",
        ],
        "spec": host(
            "h1",
            "echo '=== Default route (outbound chain entry) ==='; "
            "ip route get 8.8.8.8; "
            "echo; "
            "echo '=== HTTP through Router -> Firewall -> TC -> Proxy -> NAT ==='; "
            "curl -s -o /dev/null -w 'HTTP status: %{http_code}\n' --max-time 10 http://example.com; "
            "echo; "
            "echo '=== Response headers (Via may show Proxy hop) ==='; "
            "curl -sI --max-time 10 http://example.com | sed -n '1,8p'",
        ),
    },
    {
        "id": "nat-masquerade",
        "group": "NAT",
        "title": "Prove MASQUERADE translation",
        "description": (
            "Generates outbound HTTP traffic and shows that NAT POSTROUTING "
            "MASQUERADE packet counters increase."
        ),
        "commands": [
            "sh docker exec vnf_nat iptables -t nat -Z",
            "h1 curl -s -o /dev/null --max-time 10 http://example.com",
            "sh docker exec vnf_nat iptables -t nat -L POSTROUTING -v -n",
        ],
        "spec": nat_demo(
            "curl -s -o /dev/null -w 'HTTP status: %{http_code}\n' --max-time 10 http://example.com",
            "NAT MASQUERADE counters after outbound HTTP traffic:",
        ),
    },
    {
        "id": "nat-rules",
        "group": "NAT",
        "title": "Show NAT rules",
        "description": "Prints the active NAT table rules and MASQUERADE counters on eth0.",
        "commands": ["sh docker exec vnf_nat iptables -t nat -L -v -n"],
        "spec": docker("docker exec vnf_nat iptables -t nat -L -v -n"),
    },
    {
        "id": "tc-apply-qos",
        "group": "Traffic Control",
        "title": "Apply QoS rules on eth1",
        "description": (
            "Re-applies HTB QoS on the TC VNF. Use this if you see noqueue instead of htb. "
            "vnf-topo.py also applies rules automatically on startup."
        ),
        "commands": [
            "sh docker exec vnf_tc sh /scripts/apply_qos.sh",
            "sh docker exec vnf_tc tc qdisc show dev eth1",
        ],
        "spec": docker(
            "docker exec vnf_tc sh -c "
            "'/scripts/apply_qos.sh 2>&1; echo; echo \"=== qdisc ===\"; tc qdisc show dev eth1; "
            "echo; echo \"=== classes ===\"; tc -s class show dev eth1'"
        ),
    },
    {
        "id": "tc-policy",
        "group": "Traffic Control",
        "title": "Show QoS policy (HTB)",
        "description": (
            "Shows the active HTB qdisc, classes (1:10 high-priority, 1:20 default), "
            "and filters for ICMP/HTTP/HTTPS/DNS on eth1."
        ),
        "commands": [
            "sh docker exec vnf_tc tc qdisc show dev eth1",
            "sh docker exec vnf_tc tc -s class show dev eth1",
            "sh docker exec vnf_tc tc filter show dev eth1",
        ],
        "spec": docker(
            "docker exec vnf_tc sh -c "
            "'echo \"=== qdisc ===\"; tc qdisc show dev eth1; "
            "echo; echo \"=== HTB classes ===\"; tc -s class show dev eth1; "
            "echo; echo \"=== filters ===\"; tc filter show dev eth1'"
        ),
    },
    {
        "id": "tc-http-priority",
        "group": "Traffic Control",
        "title": "Prove HTTP uses high-priority class 1:10",
        "description": (
            "Generates HTTP traffic from h1 through the outbound chain. "
            "Class 1:10 Sent bytes/packets should increase (HTTP port 80 filter)."
        ),
        "commands": [
            "sh docker exec vnf_tc tc -s class show dev eth1",
            "h1 curl -s -o /dev/null --max-time 10 http://example.com",
            "sh docker exec vnf_tc tc -s class show dev eth1",
        ],
        "spec": tc_demo(
            "curl -s -o /dev/null -w 'HTTP status: %{http_code}\n' --max-time 10 http://example.com",
            "HTTP traffic should increase class 1:10 (high-priority) counters:",
        ),
    },
    {
        "id": "tc-class-stats",
        "group": "Traffic Control",
        "title": "Show live class statistics",
        "description": (
            "Prints per-class Sent bytes/packets on eth1. "
            "Run after the HTTP priority demo to see accumulated traffic."
        ),
        "commands": ["sh docker exec vnf_tc tc -s class show dev eth1"],
        "spec": docker("docker exec vnf_tc tc -s class show dev eth1"),
    },
    {
        "id": "tool-grafana",
        "group": "Monitoring / Tools",
        "category": "Open web UIs",
        "title": "Open Grafana",
        "description": "Opens Grafana dashboards. Login is admin / admin unless changed.",
        "commands": ["http://localhost:3000"],
        "url": "http://localhost:3000",
    },
    {
        "id": "tool-prometheus",
        "group": "Monitoring / Tools",
        "category": "Open web UIs",
        "title": "Open Prometheus",
        "description": "Opens Prometheus for metrics queries and target status.",
        "commands": ["http://localhost:9090"],
        "url": "http://localhost:9090",
    },
    {
        "id": "tool-dozzle",
        "group": "Monitoring / Tools",
        "category": "Open web UIs",
        "title": "Open Dozzle",
        "description": "Opens Dozzle to view Docker container logs in the browser.",
        "commands": ["http://localhost:8088"],
        "url": "http://localhost:8088",
    },
    {
        "id": "tool-cadvisor",
        "group": "Monitoring / Tools",
        "category": "Open web UIs",
        "title": "Open cAdvisor",
        "description": "Opens cAdvisor for container resource metrics.",
        "commands": ["http://localhost:8080"],
        "url": "http://localhost:8080",
    },
]


TESTS_BY_ID = {test["id"]: test for test in TESTS}


def run_spec(spec):
    result = subprocess.run(
        ["bash", "-lc", spec["command"]],
        cwd=spec["cwd"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    return {
        "exitCode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": spec["command"],
    }


def container_status():
    result = subprocess.run(
        ["bash", "-lc", "docker ps --format '{{.Names}}'"],
        cwd=str(DOCKER_DIR),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    running = set(result.stdout.splitlines()) if result.returncode == 0 else set()
    return {
        "containers": [
            {
                "name": name,
                "running": name in running,
            }
            for name in CONTAINERS
        ],
        "error": result.stderr if result.returncode != 0 else "",
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, content, content_type="application/json"):
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, indent=2), "application/json")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, (STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self._send(200, (STATIC_DIR / "styles.css").read_bytes(), "text/css")
            return
        if path == "/app.js":
            self._send(200, (STATIC_DIR / "app.js").read_bytes(), "application/javascript")
            return
        if path == "/api/tests":
            self._json(
                200,
                [
                    {
                        "id": item["id"],
                        "group": item["group"],
                        "title": item["title"],
                        "description": item["description"],
                        "category": item.get("category", "Demo commands"),
                        "commands": item["commands"],
                        "url": item.get("url"),
                    }
                    for item in TESTS
                ],
            )
            return
        if path == "/api/status":
            self._json(200, container_status())
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/run":
            self._json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            test_id = payload["id"]
            test = TESTS_BY_ID[test_id]
            self._json(200, run_spec(test["spec"]))
        except KeyError:
            self._json(400, {"error": "Unknown or missing test id"})
        except subprocess.TimeoutExpired as exc:
            self._json(
                408,
                {
                    "error": f"Command timed out after {TIMEOUT}s",
                    "stdout": exc.stdout or "",
                    "stderr": exc.stderr or "",
                },
            )
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"VNF dashboard running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
