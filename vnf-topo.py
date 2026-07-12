# -*- coding: utf-8 -*-
from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import os

def shell(cmd):
    return os.popen(cmd).read().strip()

def setupRouterVnf(router_default_route):
    eth1Ip = '10.0.0.2'
    eth2Ip = '10.0.1.2'

    info('*** Adding Docker Router VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_frr --ipaddress={}/24'.format(eth1Ip))
    os.system('ovs-docker add-port br1 eth2 vnf_frr --ipaddress={}/24'.format(eth2Ip))

    os.system('docker exec vnf_frr ip route del default')
    os.system('docker exec vnf_frr ip route add default via {}'.format(router_default_route))

    return (eth1Ip, eth2Ip)

def setupFirewallVnf(firewall_default_route, prev_vnf_ip):
    eth1Ip = '10.0.0.3'

    info('*** Adding Docker Firewall VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_firewall --ipaddress={}/24'.format(eth1Ip))

    os.system('docker exec vnf_firewall ip route del default')
    os.system('docker exec vnf_firewall ip route add default via {}'.format(firewall_default_route))

    subnet2IpRange = '10.0.1.0/24'
    subnet2Gateway = prev_vnf_ip
    subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
    os.system('docker exec vnf_firewall {}'.format(subnet2IpRouteCmd))

    return eth1Ip

def setupNatVnf(prev_vnf_ip):
    eth1Ip = '10.0.0.4'

    info('*** Adding Docker NAT VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_nat --ipaddress={}/24'.format(eth1Ip))

    subnet2IpRange = '10.0.1.0/24'
    subnet2Gateway = prev_vnf_ip
    subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
    os.system('docker exec vnf_nat {}'.format(subnet2IpRouteCmd))

    return eth1Ip

def setupTCVnf(tc_default_route, prev_vnf_ip):
    eth1Ip = '10.0.0.5'

    info('*** Adding Docker Traffic Shaping VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_tc --ipaddress={}/24'.format(eth1Ip))

    os.system('docker exec vnf_tc ip route del default')
    os.system('docker exec vnf_tc ip route add default via {}'.format(tc_default_route))

    subnet2IpRange = '10.0.1.0/24'
    subnet2Gateway = prev_vnf_ip
    subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
    os.system('docker exec vnf_tc {}'.format(subnet2IpRouteCmd))

    return eth1Ip

def setupDNSVnf(dns_default_route):
    eth1Ip = '10.0.0.100'
    eth2Ip = '10.0.1.100'

    info('*** Adding Docker DNS VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_dns --ipaddress={}/24'.format(eth1Ip))
    os.system('ovs-docker add-port br1 eth2 vnf_dns --ipaddress={}/24'.format(eth2Ip))

    os.system('docker exec vnf_dns ip route del default')
    os.system('docker exec vnf_dns ip route add default via {}'.format(dns_default_route))

    return (eth1Ip, eth2Ip)


def setupLbVnf():
    eth1Ip = '10.0.0.8'
    eth2Ip = '10.0.1.8'

    info('*** Adding Docker Load Balancer VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_lb --ipaddress={}/24'.format(eth1Ip))
    os.system('ovs-docker add-port br1 eth2 vnf_lb --ipaddress={}/24'.format(eth2Ip))

def setupIdsVnf(ids_default_route):
    eth1Ip = '10.0.0.9'

    info('*** Adding Docker IDS (Snort) VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_ids --ipaddress={}/24'.format(eth1Ip))

    os.system('docker exec vnf_ids ip route del default')
    os.system('docker exec vnf_ids ip route add default via {}'.format(ids_default_route))

    return eth1Ip

def setupIdsMirror(sourcePort='veth_br0'):
    info('*** Setting up OVS mirror to IDS VNF\n')

    idsIfIndex = shell("docker exec vnf_ids sh -c 'cat /sys/class/net/eth1/iflink' 2>/dev/null")
    if not idsIfIndex:
        info('*** IDS mirror skipped: could not find vnf_ids eth1 peer\n')
        return

    idsOvsPort = shell("""ip -o link | awk -F': ' '$1=="%s"{print $2}' | cut -d@ -f1""" % idsIfIndex)
    if not idsOvsPort:
        info('*** IDS mirror skipped: could not resolve OVS port for vnf_ids\n')
        return

    os.system('ovs-vsctl clear bridge br0 mirrors')
    os.system(
        'ovs-vsctl -- --id=@src get port "{0}" '
        '-- --id=@ids get port "{1}" '
        '-- --id=@m create mirror name=ids_mirror select-src-port=@src select-dst-port=@src output-port=@ids '
        '-- set bridge br0 mirrors=@m'.format(sourcePort, idsOvsPort)
    )
    info('*** IDS mirror active on br0: {} -> {}\n'.format(sourcePort, idsOvsPort))

def setupProxyVnf(proxy_default_route, prev_vnf_ip):
    eth1Ip = '10.0.0.10'

    info('*** Adding Docker Web Proxy VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_proxy --ipaddress={}/24'.format(eth1Ip))

    os.system('docker exec vnf_proxy sysctl -w net.ipv4.ip_forward=1')

    os.system('docker exec vnf_proxy iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3129')
    os.system('docker exec vnf_proxy ip route del default')
    os.system('docker exec vnf_proxy ip route add default via {}'.format(proxy_default_route))

    subnet2IpRange = '10.0.1.0/24'
    subnet2Gateway = prev_vnf_ip
    subnet2IpRouteCmd = 'ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway)
    os.system('docker exec vnf_proxy {}'.format(subnet2IpRouteCmd))

    return eth1Ip

def setupWafVnf(waf_default_route, prev_vnf_ip):
    eth1Ip = '10.0.0.11' 

    info('*** Adding Docker WAF (ModSecurity) VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_waf --ipaddress={}/24'.format(eth1Ip))

    os.system('docker exec vnf_waf sysctl -w net.ipv4.ip_forward=1')

    os.system('docker exec vnf_waf ip route del default')
    os.system('docker exec vnf_waf ip route add default via {}'.format(waf_default_route))

    subnet2IpRange = '10.0.1.0/24'
    subnet2Gateway = prev_vnf_ip
    os.system('docker exec vnf_waf ip route add {} via {} dev eth1'.format(subnet2IpRange, subnet2Gateway))

    return eth1Ip


def setupCacheVnf():
    eth1Ip = '10.0.0.30'

    info('*** Adding Docker Edge Cache VNF\n')
    os.system('ovs-docker add-port br0 eth1 vnf_cache --ipaddress={}/24'.format(eth1Ip))

    return eth1Ip



def topology():
    setLogLevel('info')

    net = Mininet(controller=Controller, link=TCLink)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding hosts\n')
    host1 = net.addHost('h1', ip='10.0.0.6/24')
    host2 = net.addHost('h2', ip='10.0.0.7/24')
    host3 = net.addHost('h3', ip='10.0.1.3/24')

    info('*** Adding switch\n')
    switch = net.addSwitch('s1', failMode='standalone')

    info('*** Creating links\n')
    net.addLink(host1, switch)
    net.addLink(host2, switch)
    net.addLink(host3, switch)

    info('*** Starting network\n')
    net.start()

    setupWafVnf(waf_default_route='10.0.0.8', prev_vnf_ip='10.0.0.10')
    natIp = setupNatVnf(prev_vnf_ip='10.0.0.10') 
    proxyIp = setupProxyVnf(proxy_default_route=natIp, prev_vnf_ip='10.0.0.5')
    
    tcIp = setupTCVnf(tc_default_route=proxyIp, prev_vnf_ip='10.0.0.9')
    idsIp = setupIdsVnf(ids_default_route=tcIp)
    firewallIp = setupFirewallVnf(firewall_default_route=idsIp, prev_vnf_ip='10.0.0.2')
 
    (defaultRouteForEth1, defaultRouteForEth2) = setupRouterVnf(router_default_route=firewallIp)
    (dnsIp1, dnsIp2) = setupDNSVnf(dns_default_route=natIp)
    setupLbVnf()
    setupCacheVnf()
    os.system('ip link add veth_mininet type veth peer name veth_br0')

    info('*** Add port veth_mininet to s1\n')
    os.system('ovs-vsctl add-port s1 veth_mininet')
    os.system('ip link set veth_mininet up')

    info('*** Add port veth_br0 to br0\n')
    os.system('ovs-vsctl add-port br0 veth_br0')
    os.system('ip link set veth_br0 up')

    os.system('ip link add veth_mininet1 type veth peer name veth_br1')

    info('*** Add port veth_mininet1 to s1\n')
    os.system('ovs-vsctl add-port s1 veth_mininet1')
    os.system('ip link set veth_mininet1 up')

    info('*** Add port veth_br1 to br1\n')
    os.system('ovs-vsctl add-port br1 veth_br1')
    os.system('ip link set veth_br1 up')

    setupIdsMirror('veth_br0')

    # Use the router as the host default gateway so traffic enters the full
    # VNF chain instead of bypassing directly to the proxy.
    host1.cmd("ip route add default via {}".format(defaultRouteForEth1))
    host2.cmd("ip route add default via {}".format(defaultRouteForEth1))
    host3.cmd("ip route add default via {}".format(defaultRouteForEth2))

    for host in (host1, host2, host3):
        host.cmd('unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY')
    
    info('*** Setup DNS on hosts\n')
    # Mininet hosts share the host filesystem, so configure one reachable DNS VNF.
    host1.cmd('echo nameserver {} > /etc/resolv.conf'.format(dnsIp1))

    info('*** Testing network\n')
    CLI(net)

    info('*** Stopping network\n')
    net.stop()

    info('*** Cleanup\n')

    os.system('ovs-vsctl clear bridge br0 mirrors')
    os.system('ovs-vsctl del-port br0 veth_br0')
    os.system('ip link set veth_mininet down')
    os.system('ip link set veth_br0 down')
    os.system('ip link delete veth_mininet')
    os.system('ovs-docker del-port br0 eth1 vnf_nat')
    os.system('ovs-docker del-port br0 eth1 vnf_firewall')
    os.system('ovs-docker del-port br0 eth1 vnf_frr')
    os.system('ovs-docker del-port br0 eth1 vnf_tc')
    os.system('ovs-docker del-port br0 eth1 vnf_dns')
    os.system('ovs-docker del-port br1 eth2 vnf_dns')
    os.system('ovs-docker del-port br0 eth1 vnf_lb')
    os.system('ovs-docker del-port br1 eth2 vnf_lb')

    os.system('ovs-vsctl del-port br1 veth_br1')
    os.system('ip link set veth_mininet1 down')
    os.system('ip link set veth_br1 down')
    os.system('ip link delete veth_mininet1')
    os.system('ovs-docker del-port br1 eth2 vnf_frr')

    os.system('ovs-docker del-port br0 eth1 vnf_ids') 
    os.system('ovs-docker del-port br0 eth1 vnf_proxy') 
    os.system('ovs-docker del-port br0 eth1 vnf_waf')
    os.system('ovs-docker del-port br0 eth1 vnf_cache')
if __name__ == '__main__':
    topology()