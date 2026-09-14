# SDN-VNF Lab

A laboratory environment for implementing and evaluating **Virtual Network Functions (VNFs)** using **Mininet, Open vSwitch and Docker**.

The project includes ten VNFs, a web dashboard with predefined demonstration scenarios, and a command-line test suite for functional testing.

---

## Architecture

The experimental environment consists of a Mininet virtual network connected through Open vSwitch to Docker-based VNFs. Each VNF provides a specific network function and can be demonstrated through the web dashboard or tested using the CLI test suite.

---

## VNFs

- **Router** — Provides routing between network subnets using FRRouting (FRR).
- **Firewall** — Filters and controls network traffic using iptables rules.
- **NAT** — Performs network address translation for outbound traffic using MASQUERADE.
- **DNS** — Provides DNS resolution and filtering using CoreDNS.
- **Proxy** — Provides HTTP proxying and content filtering using Squid.
- **IDS** — Detects and monitors suspicious network activity using Snort.
- **WAF** — Protects web applications from malicious requests using Nginx, ModSecurity and OWASP CRS.
- **Load Balancer** — Distributes HTTP requests between backend servers using Nginx.
- **Edge Cache** — Temporarily stores HTTP content to serve repeated requests from cache using Nginx.
- **Traffic Control** — Shapes and prioritizes network traffic using Linux `tc` and HTB.

## Requirements

The project is intended for **Ubuntu 22.04+**.

Required software:

- Git
- Python 3
- Docker
- Docker Compose
- Mininet
- Open vSwitch

### Install dependencies

```bash
sudo apt update
sudo apt install -y git python3 python3-pip docker.io docker-compose-v2 mininet openvswitch-switch
```

Start Docker and Open vSwitch:

```bash
sudo systemctl enable --now docker
sudo systemctl enable --now openvswitch-switch
```

Verify the installation:

```bash
python3 --version
docker --version
docker compose version
mn --version
ovs-vsctl --version
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/klewnk/sdn-vnf.git
cd sdn-vnf
```

Build and start the VNF containers:

```bash
cd docker
sudo docker compose up -d --build
cd ..
```

Check that the containers are running:

```bash
sudo docker ps
```

---

## Run the Environment

Start the Mininet topology from the project root:

```bash
sudo python3 vnf-topo.py
```

The Mininet CLI will open and the experimental environment will be ready for testing.

---

## Web Dashboard

The project includes a **Flask-based web dashboard** with predefined **demo scenarios** for the implemented VNFs.

The dashboard allows the user to select a VNF, execute its corresponding demonstration scenario, and immediately view the generated commands and output results. It provides a simple interface for presenting and functionally testing the VNFs without manually running each demonstration through the CLI.

Start the dashboard from the project root:

```bash
python3 dashboard/app.py
```

Open the dashboard in your browser:

**http://localhost:5000**

---

## CLI Tests

The project also includes a reproducible command-line test suite that can be executed **directly from the Mininet CLI, without using the dashboard**.

After starting the Mininet topology:

```text
mininet> source tests/mininet_demo_tests.mn
```

The test suite covers:

- connectivity
- DNS resolution and filtering
- routing
- proxy filtering
- WAF protection
- load balancing
- edge caching
- NAT
- firewall rules
- traffic control
- IDS alerts

---

## Monitoring

The Docker environment includes the following monitoring tools:

| Tool | Purpose | Open in Browser |
|---|---|---|
| **Prometheus** | Metrics collection | http://localhost:9090 |
| **Grafana** | Metrics visualization | http://localhost:3000 |
| **cAdvisor** | Container resource monitoring | http://localhost:8080 |
| **Dozzle** | Docker container log monitoring | http://localhost:8088 |

These services are started together with the Docker Compose environment.

---

## Project Structure

```text
sdn-vnf/
├── docker/
│   ├── docker-compose.yaml
│   ├── prometheus.yml
│   ├── router/
│   ├── firewall/
│   ├── nat/
│   ├── dns/
│   ├── proxy/
│   ├── ids/
│   ├── waf/
│   ├── lb/
│   ├── cache/
│   └── tc/
├── dashboard/
│   ├── app.py
│   └── static/
├── tests/
│   └── mininet_demo_tests.mn
├── vnf-topo.py
└── README.md
```

---

## Stop the Environment

Exit Mininet:

```text
mininet> exit
```

Stop the Docker services:

```bash
cd docker
sudo docker compose down
```

If Mininet requires cleanup:

```bash
sudo mn -c
```

---

## Repository

Source code, configuration files, tests and documentation are available in the GitHub repository:

**https://github.com/klewnk/sdn-vnf**
