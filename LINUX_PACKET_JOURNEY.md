# The Journey of a Network Packet Through the Linux Kernel

> A comprehensive guide to understanding how packets flow through the Linux network stack - from NIC hardware to application layer and back. Perfect for building educational games and visualizations!

## Table of Contents

1. [Overview](#overview)
2. [The Receiving Path (RX)](#the-receiving-path-rx)
3. [The Transmitting Path (TX)](#the-transmitting-path-tx)
4. [Key Kernel Subsystems](#key-kernel-subsystems)
5. [Packet Transformation & Duplication](#packet-transformation--duplication)
6. [Game Design Ideas](#game-design-ideas)

---

## Overview

### The Big Picture

```
┌─────────────────── RECEIVE PATH (RX) ────────────────────┐
│                                                           │
│  NIC Hardware → DMA → Ring Buffer → Driver → Softirq →   │
│  → Network Stack → L2 (Ethernet) → L3 (IP) → L4 (TCP) →  │
│  → Socket Buffer → Application (L7)                       │
│                                                           │
└───────────────────────────────────────────────────────────┘

┌─────────────────── TRANSMIT PATH (TX) ────────────────────┐
│                                                           │
│  Application → Socket → L4 → L3 → L2 → QoS/Traffic       │
│  → Driver → DMA → Ring Buffer → NIC Hardware             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## The Receiving Path (RX)

### Stage 1: NIC Hardware - The Portal

When a packet arrives at your machine:

1. **Physical Signal**: Electrical/optical signals arrive on the wire
2. **Frame Detection**: NIC detects frame boundaries
3. **Validation**: NIC checks:
   - Frame Check Sequence (FCS/CRC)
   - Destination MAC address
4. **Filtering**: Hardware filters (if configured):
   - VLAN filtering
   - Packet steering (RSS - Receive Side Scaling)
   - Hardware offload features

**RSS (Receive Side Scaling)**: Distributes packets across multiple RX queues based on hash of packet headers

### Stage 2: DMA Transfer - The Memory Portal

**Key Structure**: Ring Buffer (circular queue in RAM)

```
Ring Buffer:
┌──────┬──────┬──────┬──────┬──────┬──────┐
│ Desc │ Desc │ Desc │ Desc │ Desc │ Desc │  <- Descriptors
└──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
┌──────┬──────┬──────┬──────┬──────┬──────┐
│ SKB  │ SKB  │ SKB  │ SKB  │ SKB  │ SKB  │  <- Packet Buffers
└──────┴──────┴──────┴──────┴──────┴──────┘
```

**Process**:
1. Driver pre-allocates ring buffers in memory
2. NIC uses **DMA (Direct Memory Access)** to write packet directly to RAM
3. No CPU involvement - efficient!
4. NIC writes packet to next available ring buffer slot

**Key Data Structure**: `sk_buff` (socket buffer) - the packet's journey container

### Stage 3: Interrupt & NAPI - The Alarm

**NAPI (New API)** - Modern & Efficient:
```
NIC → IRQ → Driver disables IRQ → Polling Mode
```

**Benefits**:
- Under high load, switches to polling instead of interrupts
- Prevents "interrupt storm"
- Processes multiple packets per poll

### Stage 4: Driver Layer - The First Gate

**Process**:
1. Driver retrieves packet from ring buffer
2. Allocates and fills `sk_buff` structure
3. Sets up packet metadata (timestamp, device, protocol)
4. Calls `netif_receive_skb()` or `napi_gro_receive()`

**GRO (Generic Receive Offload)**:
- Combines multiple packets into larger ones
- Reduces per-packet overhead
- "Magical packet fusion!"

### Stage 5: Network Stack Entry

**Function**: `netif_receive_skb()` → `__netif_receive_skb_core()`

**Key Operations**:
1. **Packet Taps**: tcpdump/wireshark hook here via `AF_PACKET` sockets
2. **RPS (Receive Packet Steering)**: Software load balancing across CPUs
3. **Bridge Check**: Is this interface part of a bridge?
4. **Protocol Demultiplexing**: Reads `EtherType` field:
   - `0x0800` → IPv4
   - `0x86DD` → IPv6
   - `0x0806` → ARP

### Stage 6: L2 Processing - The Ethernet Realm

**Key Checks**:
1. Destination MAC validation
2. VLAN Processing
3. Bridge Processing (if applicable):

```
Bridge Decision:
┌────────────┐
│  Packet    │
└─────┬──────┘
      │
      ▼
┌─────────────┐      Yes    ┌──────────┐
│  Local MAC? │─────────────→│ Go to L3 │
└─────┬───────┘              └──────────┘
      │ No
      ▼
┌─────────────┐      Yes    ┌──────────┐
│ Known MAC?  │─────────────→│ Forward  │
└─────┬───────┘              └──────────┘
      │ No
      ▼
┌──────────────┐
│ Flood all    │
│ ports        │
└──────────────┘
```

### Stage 7: L3 Processing - The IP Realm

**Entry Point**: `ip_rcv()` in `net/ipv4/ip_input.c`

#### Initial Checks
- IP header checksum validation
- Header length checks
- TTL check (Time To Live)
- Version check (IPv4 vs IPv6)

#### Netfilter Hook - PREROUTING

**First magical checkpoint!**

```
┌────────────────────────────────────┐
│  NETFILTER PREROUTING              │
│  (iptables -t raw/mangle/nat)      │
└────────────┬───────────────────────┘
             │
      ┌──────┴──────┐
      │  Decision   │
      └──────┬──────┘
             │
     ┌───────┼───────┐
     ▼       ▼       ▼
   ACCEPT  DROP  QUEUE
```

**Possible Actions**:
- **ACCEPT**: Continue
- **DROP**: Discard packet
- **DNAT**: Change destination
- **MARK**: Mark packet for later processing
- **CONNTRACK**: Track connection state

#### Routing Decision

**The Big Question**: What to do with this packet?

```
┌───────────────────────────┐
│  Routing Decision         │
└───────────┬───────────────┘
            │
    ┌───────┴────────┐
    │  Destination?  │
    └───────┬────────┘
            │
    ┌───────┴────────────┐
    │                    │
    ▼                    ▼
┌────────┐          ┌────────────┐
│ LOCAL  │          │  FORWARD   │
│ (for   │          │  (routing) │
│  us!)  │          │            │
└───┬────┘          └─────┬──────┘
    │                     │
    ▼                     ▼
ip_local_deliver    ip_forward
```

#### Path A - Local Delivery

```
ip_local_deliver()
├── Netfilter: INPUT chain
├── IP options processing
├── Defragmentation (if needed)
└── Protocol demux (TCP/UDP/ICMP/etc.)
```

#### Path B - Forwarding (Router Mode)

```
ip_forward()
├── Check: Is forwarding enabled?
├── Check: TTL > 1? (decrement it)
├── Netfilter: FORWARD chain
├── Fragmentation (if needed)
└── Send to output path
```

### Stage 8: L4 Processing - The Transport Realm

#### For TCP:

```
tcp_v4_rcv()
├── TCP header validation
├── Checksum verification
├── Socket lookup (src_ip, src_port, dst_ip, dst_port)
├── State machine processing
│   ├── SYN → new connection
│   ├── ACK → existing connection
│   └── FIN → close connection
├── Sequence number validation
├── Window management
├── Data queuing
└── ACK generation
```

#### For UDP:

```
udp_rcv()
├── UDP header validation
├── Checksum verification
├── Socket lookup (dst_ip, dst_port)
├── Queue to socket buffer
└── Wake up application
```

### Stage 9: Socket Layer - The Application Gate

**Process**:
1. Packet added to socket's receive queue
2. If application is waiting (`recv()`, `read()`), wake it up
3. If buffer full, drop packet

### Stage 10: Application Layer (L7) - The Final Destination

**System Call**: `recv()`, `recvfrom()`, `read()`, `recvmsg()`

1. Application makes system call
2. Kernel copies data from socket buffer to userspace buffer
3. `sk_buff` is freed
4. Application processes data

**The packet has reached its destination!** 🎯

---

## The Transmitting Path (TX)

### Stage 1: Application Sends

**System Call**: `send()`, `sendto()`, `write()`, `sendmsg()`

1. Application provides data buffer and destination
2. Kernel allocates `sk_buff`
3. Copies data from userspace to kernel buffer

### Stage 2: Socket Layer

**For TCP**:
- Check socket state (ESTABLISHED?)
- Flow control check
- Copy data to send buffer
- TCP segmentation
- Trigger transmission

**For UDP**:
- Build UDP header
- Calculate checksum
- Pass to IP layer

### Stage 3: L4 Processing

**TCP adds**:
- Source/destination port
- Sequence number
- ACK number
- Window size
- Flags (SYN, ACK, PSH, FIN)
- Checksum

**UDP adds**:
- Source/destination port
- Length
- Checksum

### Stage 4: L3 Processing - IP Layer

```
ip_output()
├── Build IP header
│   ├── Version, IHL, TOS
│   ├── Total length
│   ├── ID, flags, fragment offset
│   ├── TTL, protocol
│   ├── Checksum
│   └── Source/destination IP
├── Routing lookup
├── Netfilter: OUTPUT chain
└── Continue to post-routing
```

### Stage 5: Routing

Determines:
1. Which interface to send from
2. Next hop IP address
3. MTU (Maximum Transmission Unit)

### Stage 6: Netfilter POSTROUTING

**This is where SNAT happens!**
- Private IP → Public IP translation
- Port translation (PAT/NAT)
- Connection tracking updates

### Stage 7: L2 Processing

**ARP Resolution** (if needed):
```
Need MAC for next hop
├── Check ARP cache
├── If not found:
│   ├── Send ARP request
│   └── Queue packet
└── If found: Use MAC
```

**Build Ethernet Header**:
- Destination MAC (6 bytes)
- Source MAC (6 bytes)
- EtherType (2 bytes): 0x0800 for IPv4

### Stage 8: Traffic Control (QoS) - The Queue Master

**Queue Disciplines (qdiscs)**:
```
┌─────────────────────────────┐
│  Traffic Control            │
│  ┌─────────┐                │
│  │ Root    │  qdisc         │
│  │ qdisc   │                │
│  └────┬────┘                │
│       │                     │
│  ┌────┴────┬────────┐       │
│  ▼         ▼        ▼       │
│ Queue1  Queue2  Queue3      │
└─────────────────────────────┘
```

**Common qdiscs**:
- **pfifo_fast**: Default, 3 priority bands
- **HTB**: Rate limiting
- **SFQ**: Fairness
- **FQ_CODEL**: Modern, reduces bufferbloat

### Stage 9: Device Driver

1. Check TX queue status
2. Set up DMA mapping
3. Build TX descriptor
4. Apply hardware offloads (TSO, checksum)
5. Write descriptor to TX ring
6. Notify hardware

### Stage 10: NIC Transmission

1. NIC reads TX descriptor via DMA
2. NIC reads packet data via DMA
3. NIC applies hardware offloads
4. NIC adds Ethernet FCS
5. NIC transmits on wire

**The packet has left the building!** 🚀

---

## Key Kernel Subsystems

### 1. Netfilter / iptables - The Filter & Transformer

**Hook Points**:
```
PREROUTING → [routing] → FORWARD → POSTROUTING
                ↓
             INPUT → [local] → OUTPUT
```

**Tables** (priority order):
1. **raw**: Connection tracking exclusions
2. **mangle**: Packet modification (TOS, TTL, MARK)
3. **nat**: Network Address Translation
4. **filter**: Packet filtering (ACCEPT, DROP)

**Example Rules**:
```bash
# Drop incoming SSH from specific IP
iptables -A INPUT -p tcp --dport 22 -s 1.2.3.4 -j DROP

# SNAT outgoing packets
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Mark packets for QoS
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j MARK --set-mark 1

# Duplicate packets (TEE target)
iptables -t mangle -A PREROUTING -j TEE --gateway 10.0.0.100
```

### 2. Routing Subsystem

**Routing Tables**:
```bash
# View routing table
ip route show

# Add route
ip route add 10.0.0.0/8 via 192.168.1.254

# Policy routing
ip rule add from 10.0.0.0/8 lookup 100
ip route add default via 192.168.2.1 table 100
```

### 3. Bridge - The L2 Switch

**MAC Learning**:
```
Packet arrives with source MAC aa:bb:cc:dd:ee:ff
├── Learn: MAC is on this port
└── Store in forwarding database (FDB)

Packet with destination MAC
├── Lookup in FDB
├── Found → forward to specific port
└── Not found → flood all ports
```

### 4. Network Namespaces - The Multiverse

Each namespace has its own:
- Network interfaces
- Routing tables
- Firewall rules
- Sockets

```bash
# Create namespace
ip netns add ns1

# Execute in namespace
ip netns exec ns1 ip link list
```

---

## Packet Transformation & Duplication

### 1. NAT - The Teleporter

**SNAT (Source NAT)**:
```
Before: src=192.168.1.100:5000 → dst=8.8.8.8:53
After:  src=203.0.113.10:12345 → dst=8.8.8.8:53
```

**DNAT (Destination NAT)**:
```
Before: src=203.0.113.50:5000 → dst=203.0.113.10:80
After:  src=203.0.113.50:5000 → dst=192.168.1.100:8080
```

### 2. Packet Duplication - The Clone Spell

**TEE Target**:
```bash
# Send copy to monitoring host
iptables -t mangle -A PREROUTING -j TEE --gateway 10.0.0.100
```

**Process**:
1. Original packet continues normal path
2. Clone created with `skb_clone()`
3. Clone routed to TEE gateway

**Multicast**:
```
Sender → 224.0.0.1 (multicast group)
├── Router duplicates packet
├── Copy → Host A
├── Copy → Host B
└── Copy → Host C
```

### 3. Packet Mangling

**Modify TTL**:
```bash
iptables -t mangle -A PREROUTING -j TTL --ttl-inc 1
```

**Modify TOS/DSCP** (QoS):
```bash
iptables -t mangle -A PREROUTING -p tcp --dport 22 \
   -j DSCP --set-dscp-class EF
```

### 4. Fragmentation - The Splicing

**When packet > MTU**:
```
Original (3000 bytes):
┌──────────────────────────────────────┐
│ IP Header │ Data (2980 bytes)        │
└──────────────────────────────────────┘

After fragmentation (MTU 1500):
┌────────────────────────┐
│ IP Hdr │ Fragment 1    │ (1480 bytes)
├────────────────────────┤
│ IP Hdr │ Fragment 2    │ (1500 bytes)
└────────────────────────┘
```

### 5. Encapsulation - The Wrapper

**VXLAN**:
```
┌────────────────────────────────────────────────────┐
│ Outer Eth │ Outer IP │ UDP │ VXLAN │ Inner frame │
└────────────────────────────────────────────────────┘
```

**GRE**:
```
┌─────────────────────────────────────────┐
│ Outer IP │ GRE Hdr │ Inner IP │ Payload│
└─────────────────────────────────────────┘
```

---

## Game Design Ideas

### Core Concept: "Kernel Mage: The Packet Journey"

#### Theme
You are a **Packet Mage** guiding packets through the mystical realms of the Linux Kernel.

#### Realms (Game Levels)

1. **The Hardware Realm** (NIC & DMA)
2. **The Driver's Gate** (Device Driver)
3. **The Ethernet Valley** (L2)
4. **The IP Mountain** (L3)
5. **The Transport Tower** (L4)
6. **The Socket Sanctuary** (Socket Layer)
7. **The Application Summit** (L7)

#### Magic Spells (Based on Real Operations)

- **Clone Spell**: Duplicate packets (TEE, multicast)
- **Transform Spell**: NAT translation
- **Invisibility Spell**: DROP in iptables
- **Teleport Spell**: DNAT
- **Time Spell**: TTL modification
- **Shield Spell**: Firewall rules
- **Fusion Spell**: GRO/GSO
- **Splitting Spell**: Fragmentation
- **Speed Spell**: QoS priority
- **Portal Spell**: Tunneling

#### Challenges

1. **Routing Maze**: Find correct interface
2. **Firewall Boss Fight**: Navigate iptables rules
3. **Buffer Overflow**: Manage queues under load
4. **ARP Quest**: Resolve MAC before timeout
5. **MTU Puzzle**: Fragment correctly
6. **Multicast Mission**: Duplicate to multiple destinations
7. **NAT Translation**: Transform addresses
8. **QoS Priority Queue**: Sort by importance

#### Enemies/Obstacles

- **DROP demons**: Firewall rules
- **TTL decay**: Time running out
- **Buffer dragons**: Full queues
- **Checksum goblins**: Validation failures
- **Fragment trolls**: Reassembly issues
- **Loop serpents**: Routing loops
- **Storm elementals**: Broadcast storms

#### Power-ups

- **Checksum Bypass**: Hardware offload
- **Fast Path**: Route cache hit
- **NAPI Mode**: Efficient polling
- **Jumbo Frame**: Increased MTU
- **TSO/GRO**: Hardware acceleration

#### Visualization Example

```
┌────────────────────────────────────────┐
│  Packet Mage                           │
│  HP: [======    ] (buffer space)       │
│  TTL: 64        Location: IP Layer     │
├────────────────────────────────────────┤
│     NIC → Driver → L2 → [L3] → L4     │
│                        ▲               │
│                       YOU              │
│                                        │
│  Current Challenge:                    │
│  ┌──────────────────────────────────┐ │
│  │  Netfilter Checkpoint            │ │
│  │  Rule: DROP port 22              │ │
│  │  [1] Try different port          │ │
│  │  [2] Use ACCEPT spell            │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

---

## Quick Reference

### RX Path (Summary)
```
Wire → NIC → DMA → Ring → IRQ → Driver →
netif_receive_skb → L2 → PREROUTING → Routing →
INPUT/FORWARD → L4 → Socket → Application
```

### TX Path (Summary)
```
Application → Socket → L4 → OUTPUT → Routing →
POSTROUTING → L2 → ARP → QoS → Driver →
TX Ring → DMA → NIC → Wire
```

### Netfilter Hooks Order
1. PREROUTING (incoming)
2. INPUT (to local) / FORWARD (routing)
3. OUTPUT (from local)
4. POSTROUTING (outgoing)

### Key Files in Kernel
- `net/core/dev.c` - Core network device
- `net/ipv4/ip_input.c` - IPv4 input
- `net/ipv4/ip_output.c` - IPv4 output
- `net/netfilter/` - Netfilter framework
- `net/sched/` - Traffic control

---

**May your packets always find their destination!** ✨🚀📦
