# SDN-VNF Demo Tests

This folder contains repeatable Mininet CLI tests for the thesis demo.

## Service Chain

Outbound traffic from `h1`/`h2` follows this routing chain:

```text
h1/h2 -> Router (10.0.0.2) -> Firewall (10.0.0.3) -> TC (10.0.0.5) -> Proxy (10.0.0.10) -> NAT (10.0.0.4)
```

IDS (`10.0.0.9`) inspects the same `br0` traffic via OVS port mirroring (passive hop).

## Before Running

Rebuild NAT/TC after chain fixes:

```bash
cd /mnt/c/Users/kkola/Desktop/vnf/sdn-vnf/docker
docker compose build vnf_nat vnf_tc
docker compose up -d --build
```

Start the topology:

```bash
cd /mnt/c/Users/kkola/Desktop/vnf/sdn-vnf
sudo python2 vnf-topo.py
```

Verify the chain inside Mininet:

```text
mininet> h1 tracepath -n 8.8.8.8
mininet> h1 curl -v --connect-timeout 10 http://93.184.216.34
```

Open IDS logs in another terminal:

```bash
docker logs -f vnf_ids
```

Optional logs:

```bash
docker logs -f vnf_waf
docker logs -f vnf_proxy
docker logs -f vnf_lb
docker logs -f vnf_cache
```

## Run The Demo Tests

Inside the Mininet CLI:

```text
mininet> source tests/mininet_demo_tests.mn
```

## Expected Results

The DNS tests should trigger IDS suspicious DNS alerts.

The Proxy tests should return `403` and trigger an IDS repeated proxy block alert after three blocked attempts.

The WAF tests should show:

```text
waf normal: 200
waf sql injection: 403
waf xss: 403
```

The Load Balancer tests should show either `Backend 1` or `Backend 2`, proving that the request passed through the LB to a backend server.

The Edge Cache test downloads `bigfile.dat` twice through `vnf_cache`. The cache logs should show the first request as `MISS` and the second request as `HIT`.

The validation commands print live NAT, Firewall, and TC rules from their containers.
