# The Journey of a Network Packet Through the Linux Kernel

> A comprehensive guide to understanding how packets flow through the Linux network stack - from NIC hardware to application layer and back. Perfect for building educational games and visualizations!

## About This Documentation

This documentation provides an **accurate, detailed** exploration of how the Linux kernel processes network packets. It includes:
- ✓ Real function names and file locations
- ✓ Actual code flows (not just concepts)
- ✓ Different scenarios and edge cases
- ✓ Performance optimizations explained
- ✓ Educational game design concepts

**Important**: Early versions incorrectly described separate "L2" and "L3" stages. The kernel actually uses **protocol demultiplexing** - `__netif_receive_skb_core()` looks up the protocol handler directly based on EtherType. This documentation has been corrected based on kernel source research.

---

## Documentation Structure

This guide is organized into focused documents:

### 1. [RX Path - Receive Journey](docs/01-RX-Path.md)
Complete packet receive path with real kernel functions:
- NIC hardware → DMA → Ring Buffer
- Interrupts & NAPI
- Protocol demultiplexing (the actual flow!)
- Netfilter PRE_ROUTING
- Routing decision (local vs forward)
- L4 processing (TCP/UDP)
- Socket delivery → Application

**Learn**: `netif_receive_skb()`, `__netif_receive_skb_core()`, `ip_rcv()`, `tcp_v4_rcv()`

### 2. [Network Optimizations](docs/02-Network-Optimizations.md)
Performance features that make Linux networking fast:
- **NAPI** - Interrupt mitigation
- **GRO** - Generic Receive Offload
- **RSS** - Receive Side Scaling (hardware)
- **RPS/RFS** - Receive Packet Steering (software)
- **GSO/TSO** - Segmentation offload
- **XPS** - Transmit Packet Steering
- Checksum offloading
- Zero-copy techniques

**Learn**: How these optimizations work, when to use them, how to tune them

### 3. [TX Path - Transmit Journey](docs/03-TX-Path.md)
Complete packet transmit path with real kernel functions:
- Application → System call
- Socket layer → TCP/UDP
- IP layer → Header construction
- Netfilter OUTPUT & POSTROUTING
- Routing → Next hop selection
- ARP resolution → MAC address
- Traffic Control (QoS)
- Device driver → DMA → NIC

**Learn**: `tcp_sendmsg()`, `ip_queue_xmit()`, `dev_queue_xmit()`, qdisc system

### 4. [Netfilter & Routing - Different Paths](docs/04-Netfilter-and-Routing.md)
Not all packets follow the same path! Understand:
- **Netfilter hook points**: PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING
- **Routing decisions**: Local delivery vs forwarding
- **NAT**: DNAT and SNAT (when and where)
- **Connection tracking**: Stateful firewalls
- **Different scenarios**:
  - Local delivery (normal)
  - Forwarding (router mode)
  - DNAT port forwarding
  - Packet dropped by firewall
  - Packet duplication (TEE)
  - Locally generated traffic
  - Loopback traffic

**Learn**: iptables, routing tables, policy routing, connection tracking

### 5. [Game Design - "Kernel Mage"](docs/05-Game-Design.md)
Educational game concept based on packet journey:
- 9 realms (NIC → Application)
- Magic spells based on real features (GRO, NAT, TSO)
- Boss fights (Netfilter checkpoints)
- Learning mechanics
- Multiplayer modes
- Implementation ideas

**Learn**: How to make networking concepts fun and engaging!

---

## The Big Picture

### Receive Path (Simplified)

```
Physical Wire
    ↓
NIC Hardware (Frame validation, DMA to ring buffer)
    ↓
Interrupt/NAPI (Driver notification)
    ↓
Driver Processing (GRO, checksum validation)
    ↓
netif_receive_skb() → __netif_receive_skb_core()
    ↓
PROTOCOL DEMULTIPLEXING (lookup handler for IPv4/IPv6/ARP/etc)
    ↓
ip_rcv() - IP validation, checksum
    ↓
Netfilter PREROUTING (DNAT, packet marking)
    ↓
Routing Decision: ip_route_input()
    ↓
    ├─→ Local delivery: ip_local_deliver()
    │       ↓
    │   Netfilter INPUT
    │       ↓
    │   L4: tcp_v4_rcv() or udp_rcv()
    │       ↓
    │   Socket buffer
    │       ↓
    │   Application (recv system call)
    │
    └─→ Forwarding: ip_forward()
            ↓
        Netfilter FORWARD
            ↓
        Netfilter POSTROUTING (SNAT)
            ↓
        Transmit on output interface
```

### Transmit Path (Simplified)

```
Application (send system call)
    ↓
Socket layer (sock_sendmsg)
    ↓
L4: tcp_sendmsg() or udp_sendmsg()
    ↓
L3: ip_queue_xmit() - Build IP header
    ↓
Netfilter OUTPUT (Filtering)
    ↓
Routing: ip_route_output() - Find output interface
    ↓
Netfilter POSTROUTING (SNAT/MASQUERADE)
    ↓
Neighbor resolution (ARP lookup)
    ↓
Add L2 header (Ethernet)
    ↓
Traffic Control / QoS (tc qdiscs)
    ↓
Device driver (TX ring setup)
    ↓
NIC Hardware (DMA, TSO, checksum offload)
    ↓
Physical Wire
```

---

## Key Insights

### 1. No Separate "L2" and "L3" Stages
The kernel doesn't process Ethernet separately from IP. Instead:
- Driver strips Ethernet header with `eth_type_trans()`
- `__netif_receive_skb_core()` immediately demultiplexes to protocol handler
- For IPv4 packets, `ip_rcv()` is called directly

### 2. Netfilter Has 5 Hook Points
- **PREROUTING**: Before routing (for DNAT)
- **INPUT**: To local process
- **FORWARD**: Router/forwarding
- **OUTPUT**: From local process
- **POSTROUTING**: After routing (for SNAT)

### 3. Routing Decides the Path
`ip_route_input()` determines whether packet is:
- For us (`ip_local_deliver`) → goes through INPUT hook
- To forward (`ip_forward`) → goes through FORWARD hook

### 4. Connection Tracking is Central
Required for:
- Stateful firewalls (`-m state --state ESTABLISHED,RELATED`)
- NAT (remembering translations)
- Related connections (FTP data channel)

### 5. Optimizations are Everywhere
- **Hardware**: RSS, TSO, checksum offload
- **Driver**: NAPI, GRO
- **Software**: RPS, RFS, GSO
- Understanding these is key to performance

---

## Use Cases

### For Students
- Learn real Linux networking (not just theory)
- Understand what happens when you run `curl` or `ping`
- Prepare for networking certifications
- Computer science networking courses

### For System Administrators
- Debug network issues effectively
- Configure firewalls (`iptables`) correctly
- Optimize network performance
- Understand routing and NAT

### For Developers
- Build network tools (tcpdump, Wireshark alternatives)
- Implement BPF/XDP programs
- Create visualizations
- Develop educational games

### For Game Designers
- Use "Kernel Mage" concept as inspiration
- Understand how to gamify technical concepts
- Create engaging educational content

---

## Getting Started

### Quick Start - RX Path
1. Read **[RX Path](docs/01-RX-Path.md)** for complete receive flow
2. Look at **[Network Optimizations](docs/02-Network-Optimizations.md)** to understand NAPI, GRO, RSS
3. Check **[Netfilter & Routing](docs/04-Netfilter-and-Routing.md)** for different scenarios

### Quick Start - TX Path
1. Read **[TX Path](docs/03-TX-Path.md)** for complete transmit flow
2. Look at **[Network Optimizations](docs/02-Network-Optimizations.md)** for GSO, TSO, XPS
3. Check **[Netfilter & Routing](docs/04-Netfilter-and-Routing.md)** for NAT configuration

### Quick Start - Game Development
1. Read **[Game Design](docs/05-Game-Design.md)** for complete concept
2. Understand the RX and TX paths (realms in the game)
3. Map real kernel features to game mechanics

---

## Kernel Source Locations

### Core Files
- `net/core/dev.c` - Core device handling, `netif_receive_skb()`, `dev_queue_xmit()`
- `net/core/skbuff.c` - `sk_buff` management
- `net/core/neighbour.c` - ARP and neighbor discovery

### IPv4
- `net/ipv4/ip_input.c` - `ip_rcv()`, `ip_local_deliver()`
- `net/ipv4/ip_output.c` - `ip_output()`, `ip_queue_xmit()`
- `net/ipv4/route.c` - Routing tables
- `net/ipv4/tcp.c` - TCP socket operations
- `net/ipv4/tcp_ipv4.c` - `tcp_v4_rcv()`
- `net/ipv4/udp.c` - `udp_rcv()`, UDP operations

### Netfilter
- `net/netfilter/core.c` - Netfilter core
- `net/ipv4/netfilter/ip_tables.c` - iptables
- `net/netfilter/nf_conntrack_core.c` - Connection tracking

### Traffic Control
- `net/sched/` - Queue disciplines (qdiscs)
- `net/sched/sch_api.c` - TC API

### Device Drivers
- `drivers/net/ethernet/` - Various NIC drivers
- `drivers/net/ethernet/intel/e1000e/` - Intel e1000e (example)

---

## Tools for Exploration

### Packet Capture
```bash
# Capture packets
tcpdump -i eth0 -nn -vv

# Capture to file
tcpdump -i eth0 -w capture.pcap

# Analyze with tshark
tshark -r capture.pcap
```

### Network Statistics
```bash
# Interface stats
ip -s link show eth0

# Routing tables
ip route show
ip route show table all

# ARP cache
ip neigh show

# Connection tracking
conntrack -L
```

### Netfilter/iptables
```bash
# View rules
iptables -L -v -n
iptables -t nat -L -v -n
iptables -t mangle -L -v -n

# Trace packets
iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
```

### Performance Monitoring
```bash
# NIC settings
ethtool -k eth0  # Offload features
ethtool -g eth0  # Ring buffer sizes
ethtool -S eth0  # Statistics

# System tunables
sysctl -a | grep net.
```

---

## Contributing

Found an error? Have suggestions? This documentation aims to be:
- **Accurate**: Based on actual kernel source code
- **Educational**: Clear explanations with examples
- **Practical**: Useful for real-world scenarios

Feedback and corrections are welcome!

---

## Resources

### Official Documentation
- [Linux Kernel Networking Documentation](https://www.kernel.org/doc/html/latest/networking/)
- [Netfilter Project](https://www.netfilter.org/)

### Books
- "Understanding Linux Network Internals" by Christian Benvenuti
- "Linux Kernel Networking: Implementation and Theory" by Rami Rosen

### Online Resources
- Kernel source code browser: https://elixir.bootlin.com/linux/latest/source
- Packet flow diagram: https://en.wikipedia.org/wiki/Netfilter

---

## License

This documentation is created for educational purposes. Linux kernel is licensed under GPL-2.0.

---

**May your packets always find their destination!** ✨🚀📦
