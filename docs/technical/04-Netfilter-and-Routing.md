# Netfilter, Routing, and Different Packet Paths

> Understanding how packets take different routes through the kernel based on their destination and firewall rules

## Overview

Not all packets follow the same path! Depending on the routing decision and netfilter rules, packets can:
- **Go to local application** (local delivery)
- **Be forwarded to another host** (routing/forwarding)
- **Be dropped** (firewall)
- **Be duplicated** (TEE target)
- **Be modified** (NAT, mangling)
- **Be sent to userspace** (nfqueue)

---

## The Complete Netfilter Hook Diagram

```
                 PACKET ARRIVES (eth0)
                         ↓
                  ┌──────────────┐
                  │   PRE        │
                  │   ROUTING    │
                  └──────┬───────┘
                         │
                    [ROUTING]
                    DECISION
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │              │          │              │
    │    INPUT     │          │   FORWARD    │
    │              │          │              │
    └──────┬───────┘          └──────┬───────┘
           │                         │
           ▼                         │
    ┌─────────────┐                  │
    │   LOCAL     │                  │
    │   PROCESS   │                  │
    └──────┬──────┘                  │
           │                         │
           ▼                         │
    ┌──────────────┐                 │
    │              │                 │
    │    OUTPUT    │                 │
    │              │                 │
    └──────┬───────┘                 │
           │                         │
           └────────────┬────────────┘
                        │
                   [ROUTING]
                   DECISION
                        │
                        ▼
                 ┌──────────────┐
                 │     POST     │
                 │   ROUTING    │
                 └──────┬───────┘
                        │
                        ▼
                 PACKET LEAVES (eth1)
```

---

## Netfilter Hook Points

### 1. PREROUTING Hook

**When**: As soon as packet is received, before routing decision

**Tables** (in order):
1. **raw** - Connection tracking bypass
2. **mangle** - Packet modification
3. **nat** - DNAT (Destination NAT)

**Use Cases**:
- **DNAT**: Redirect incoming packets to different destination
- **Port forwarding**: External port → internal server
- **Load balancing**: Distribute to multiple backends
- **Packet marking**: Mark for later processing
- **Connection tracking bypass**: Exclude specific traffic

**Example Rules**:
```bash
# Port forwarding: External port 80 → internal 192.168.1.100:8080
iptables -t nat -A PREROUTING -p tcp --dport 80 \
    -j DNAT --to-destination 192.168.1.100:8080

# Mark packets for QoS
iptables -t mangle -A PREROUTING -p tcp --dport 22 \
    -j MARK --set-mark 1

# Bypass connection tracking for specific traffic (performance)
iptables -t raw -A PREROUTING -p tcp --dport 80 \
    -j NOTRACK
```

### 2. INPUT Hook

**When**: After routing decision, for packets destined to local machine

**Tables** (in order):
1. **mangle** - Packet modification
2. **filter** - Filtering (ACCEPT/DROP)
3. **security** - SELinux
4. **nat** - DNAT (rare, usually in PREROUTING)

**Use Cases**:
- **Firewall**: Allow/block incoming connections
- **Rate limiting**: Prevent DoS
- **Logging**: Log suspicious traffic

**Example Rules**:
```bash
# Default policy: DROP
iptables -P INPUT DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH from specific subnet
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# Rate limit incoming connections
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute \
    --limit-burst 100 -j ACCEPT

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "INPUT DROP: "
iptables -A INPUT -j DROP
```

### 3. FORWARD Hook

**When**: After routing decision, for packets being routed/forwarded

**Tables** (in order):
1. **mangle** - Packet modification
2. **filter** - Filtering
3. **security** - SELinux

**Use Cases**:
- **Router/firewall ACLs**: Control what can be forwarded
- **Inter-VLAN filtering**
- **DMZ rules**

**Example Rules**:
```bash
# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Default policy: DROP
iptables -P FORWARD DROP

# Allow established connections
iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow internal to external
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# Allow external to DMZ (specific ports only)
iptables -A FORWARD -i eth0 -o eth2 -p tcp --dport 80 -j ACCEPT
iptables -A FORWARD -i eth0 -o eth2 -p tcp --dport 443 -j ACCEPT

# Block everything else
iptables -A FORWARD -j DROP
```

### 4. OUTPUT Hook

**When**: After local process generates packet, before routing decision

**Tables** (in order):
1. **raw** - Connection tracking bypass
2. **mangle** - Packet modification
3. **nat** - DNAT (rare)
4. **filter** - Filtering
5. **security** - SELinux

**Use Cases**:
- **Outbound firewall**: Control what local processes can send
- **Application filtering**: Block specific applications
- **Forced routing**: Mark packets for policy routing

**Example Rules**:
```bash
# Block outbound connections to specific IP
iptables -A OUTPUT -d 1.2.3.4 -j DROP

# Allow only specific user to make outbound SSH
iptables -A OUTPUT -p tcp --dport 22 -m owner --uid-owner 1000 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 22 -j DROP

# Mark packets from specific application
iptables -A OUTPUT -m owner --uid-owner 1001 -j MARK --set-mark 2
```

### 5. POSTROUTING Hook

**When**: After routing decision, just before packet leaves

**Tables** (in order):
1. **mangle** - Packet modification
2. **nat** - SNAT (Source NAT)

**Use Cases**:
- **SNAT/MASQUERADE**: Change source IP (NAT gateway)
- **Final packet modifications**

**Example Rules**:
```bash
# MASQUERADE (dynamic SNAT for DHCP interfaces)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# SNAT (static source IP)
iptables -t nat -A POSTROUTING -o eth0 \
    -j SNAT --to-source 203.0.113.10

# Multiple source IPs (load balance)
iptables -t nat -A POSTROUTING -o eth0 \
    -j SNAT --to-source 203.0.113.10-203.0.113.20
```

---

## Different Packet Paths - Scenarios

### Scenario 1: Local Delivery (Normal)

**Example**: HTTP request to web server on this machine

```
eth0: Packet arrives (dst=192.168.1.100:80)
    ↓
PREROUTING hook
    ├─ Connection tracking
    └─ ACCEPT
    ↓
Routing decision: ip_route_input()
    ├─ Lookup: 192.168.1.100 in local table
    └─ Match! → dst->input = ip_local_deliver
    ↓
INPUT hook
    ├─ iptables -A INPUT rules
    └─ ACCEPT
    ↓
ip_local_deliver_finish()
    ↓
tcp_v4_rcv() → socket → apache process
```

**Commands to verify**:
```bash
# Check if IP is local
ip addr show | grep 192.168.1.100

# Check INPUT rules
iptables -L INPUT -v -n

# Check connection tracking
conntrack -L | grep 192.168.1.100
```

### Scenario 2: Forwarding (Router)

**Example**: Linux box routing between networks

```
eth0: Packet arrives (dst=10.0.0.50, src=192.168.1.100)
    ↓
PREROUTING hook
    ├─ DNAT? No
    └─ ACCEPT
    ↓
Routing decision: ip_route_input()
    ├─ Lookup: 10.0.0.50 not in local table
    ├─ Check main routing table
    ├─ Match: 10.0.0.0/8 via eth1
    └─ dst->input = ip_forward
    ↓
ip_forward()
    ├─ Check: net.ipv4.ip_forward = 1? YES
    ├─ Decrement TTL
    └─ Continue
    ↓
FORWARD hook
    ├─ iptables -A FORWARD rules
    └─ ACCEPT
    ↓
POSTROUTING hook
    ├─ SNAT? YES → src=192.168.1.100 becomes src=10.0.0.1
    └─ ACCEPT
    ↓
eth1: Packet leaves (dst=10.0.0.50, src=10.0.0.1)
```

**Enable forwarding**:
```bash
# Temporary
sysctl -w net.ipv4.ip_forward=1

# Permanent
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

### Scenario 3: DNAT Port Forwarding

**Example**: External request to public IP port 80 → internal server 192.168.1.100:8080

```
eth0: Packet arrives (dst=203.0.113.10:80, src=1.2.3.4:5000)
    ↓
PREROUTING hook
    ├─ NAT table: DNAT rule matches
    ├─ Change: dst=203.0.113.10:80 → dst=192.168.1.100:8080
    └─ Connection tracking records translation
    ↓
Routing decision: ip_route_input()
    ├─ Lookup: 192.168.1.100 (NEW destination after DNAT)
    ├─ Not local, in routing table: via eth1
    └─ dst->input = ip_forward
    ↓
FORWARD hook
    ├─ iptables -A FORWARD rules
    └─ ACCEPT
    ↓
POSTROUTING hook
    ├─ SNAT? Maybe (if needed)
    └─ ACCEPT
    ↓
eth1: Packet leaves (dst=192.168.1.100:8080, src=1.2.3.4:5000)
```

**Return path** (important!):
```
eth1: Reply arrives (src=192.168.1.100:8080, dst=1.2.3.4:5000)
    ↓
PREROUTING hook
    ├─ Connection tracking: Finds original connection
    ├─ Reverse NAT: src=192.168.1.100:8080 → src=203.0.113.10:80
    └─ ACCEPT
    ↓
Routing decision
    └─ dst->input = ip_forward
    ↓
FORWARD hook
    └─ ACCEPT (related to established connection)
    ↓
POSTROUTING hook
    └─ ACCEPT
    ↓
eth0: Packet leaves (src=203.0.113.10:80, dst=1.2.3.4:5000)
```

**Setup**:
```bash
# Port forwarding rule
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j DNAT --to-destination 192.168.1.100:8080

# Allow forwarding
iptables -A FORWARD -p tcp -d 192.168.1.100 --dport 8080 \
    -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
```

### Scenario 4: Packet Dropped by Firewall

**Example**: Blocked SSH connection

```
eth0: Packet arrives (dst=192.168.1.100:22, src=1.2.3.4:5000)
    ↓
PREROUTING hook
    └─ ACCEPT
    ↓
Routing decision
    └─ dst->input = ip_local_deliver (local destination)
    ↓
INPUT hook
    ├─ Rule 1: -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT
    │   └─ No match (src is 1.2.3.4, not in 10.0.0.0/8)
    ├─ Rule 2: -A INPUT -j DROP
    │   └─ MATCH!
    └─ DROP
    ↓
Packet discarded, sk_buff freed
    ↓
[END - packet never reaches application]
```

**No reply sent** (vs REJECT which sends ICMP):
```bash
# DROP: Silent discard
iptables -A INPUT -p tcp --dport 22 -j DROP

# REJECT: Send ICMP port unreachable
iptables -A INPUT -p tcp --dport 22 -j REJECT --reject-with icmp-port-unreachable

# REJECT: Send TCP RST
iptables -A INPUT -p tcp --dport 22 -j REJECT --reject-with tcp-reset
```

### Scenario 5: Packet Duplication (TEE)

**Example**: Mirror traffic to monitoring host

```
eth0: Packet arrives (dst=192.168.1.100:80)
    ↓
PREROUTING hook
    ├─ Rule: -j TEE --gateway 10.0.0.100
    ├─ CLONE packet: skb_clone()
    ├─ Original: Continue normal path
    └─ Clone: Route to 10.0.0.100
    ↓
[ORIGINAL PACKET PATH]
Routing → INPUT → tcp_v4_rcv → application

[CLONED PACKET PATH]
Routing to 10.0.0.100 → POSTROUTING → eth1
```

**Setup**:
```bash
# Mirror all traffic to monitoring host
iptables -t mangle -A PREROUTING -j TEE --gateway 10.0.0.100

# Mirror only HTTP traffic
iptables -t mangle -A PREROUTING -p tcp --dport 80 \
    -j TEE --gateway 10.0.0.100
```

### Scenario 6: Locally Generated Traffic

**Example**: Application on this machine sends HTTP request

```
Application: send(sock, data, ...)
    ↓
tcp_sendmsg()
    ↓
ip_queue_xmit()
    ↓
OUTPUT hook
    ├─ iptables -A OUTPUT rules
    └─ ACCEPT
    ↓
Routing decision: ip_route_output()
    ├─ Lookup: 8.8.8.8
    ├─ Match: default via 192.168.1.1 dev eth0
    └─ Set next hop, output device
    ↓
POSTROUTING hook
    ├─ SNAT? Maybe
    └─ ACCEPT
    ↓
Neighbor resolution (ARP for 192.168.1.1)
    ↓
Add Ethernet header
    ↓
dev_queue_xmit() → driver → NIC → wire
```

### Scenario 7: Loopback Traffic

**Example**: Application connects to 127.0.0.1

```
Application: connect(sock, 127.0.0.1:80)
    ↓
tcp_sendmsg()
    ↓
ip_queue_xmit()
    ↓
OUTPUT hook
    └─ ACCEPT
    ↓
Routing decision
    ├─ Lookup: 127.0.0.1 in local table
    └─ Device: lo (loopback)
    ↓
POSTROUTING hook
    └─ ACCEPT (no NAT for loopback)
    ↓
Loopback device (software only, no hardware)
    ↓
Packet loops back immediately
    ↓
PREROUTING hook
    └─ ACCEPT
    ↓
INPUT hook
    └─ ACCEPT
    ↓
tcp_v4_rcv() → socket → application
```

**No physical transmission!** All in software.

---

## Connection Tracking (conntrack)

### What is Connection Tracking?

**Tracks state of network connections** to enable:
- Stateful firewall rules
- NAT (both SNAT and DNAT)
- Related connections (e.g., FTP data channel)

### Connection States

```c
enum ip_conntrack_status {
    IPS_EXPECTED     = (1 << 0),  // Expected (related) connection
    IPS_SEEN_REPLY   = (1 << 1),  // Reply packets seen
    IPS_ASSURED      = (1 << 2),  // Connection established
    IPS_CONFIRMED    = (1 << 3),  // Entry confirmed
    IPS_SRC_NAT      = (1 << 4),  // Source NAT applied
    IPS_DST_NAT      = (1 << 5),  // Destination NAT applied
    // ... more
};
```

### Conntrack States (for iptables)

| State | Description |
|-------|-------------|
| **NEW** | First packet of a new connection |
| **ESTABLISHED** | Part of an existing connection (reply seen) |
| **RELATED** | New connection related to existing (e.g., FTP data) |
| **INVALID** | Packet doesn't belong to any connection |

### Conntrack Example

**TCP Connection**:
```bash
# Initial SYN
conntrack entry created: NEW
tcp      6 120 SYN_SENT src=192.168.1.100 dst=8.8.8.8 sport=5000 dport=80

# SYN-ACK received
State changes to: ESTABLISHED
tcp      6 300 ESTABLISHED src=192.168.1.100 dst=8.8.8.8 sport=5000 dport=80

# After traffic in both directions
Flag added: ASSURED
tcp      6 300 ESTABLISHED src=192.168.1.100 dst=8.8.8.8 sport=5000 dport=80 [ASSURED]
```

**With NAT**:
```bash
conntrack -L
tcp      6 300 ESTABLISHED src=192.168.1.100 dst=8.8.8.8 sport=5000 dport=80 \
         src=8.8.8.8 dst=203.0.113.10 sport=80 dport=12345 [ASSURED] mark=0 use=1
         ^^^^^^^^^^^^ ORIGINAL ^^^^^^^^^^^^    ^^^^^^^^^^^^ REPLY ^^^^^^^^^^^^
```

### Using Connection Tracking in iptables

```bash
# Allow established and related connections (stateful firewall)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Only allow NEW connections from specific source
iptables -A INPUT -m state --state NEW -s 10.0.0.0/8 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m state --state INVALID -j DROP
```

### Bypass Connection Tracking (Performance)

**For high-traffic servers**:
```bash
# Bypass conntrack for HTTP traffic (no NAT/stateful firewall needed)
iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
iptables -t raw -A OUTPUT -p tcp --sport 80 -j NOTRACK

# Also need to accept in filter table
iptables -A INPUT -m state --state UNTRACKED -j ACCEPT
iptables -A OUTPUT -m state --state UNTRACKED -j ACCEPT
```

**Benefits**: Lower CPU usage, higher throughput

**View conntrack stats**:
```bash
# Current connections
conntrack -L

# Conntrack statistics
conntrack -S

# Conntrack limits
sysctl net.netfilter.nf_conntrack_max
cat /proc/sys/net/netfilter/nf_conntrack_count
```

---

## Routing Decisions

### Routing Tables

Linux supports **multiple routing tables**:
- **local** (255): Local and broadcast addresses
- **main** (254): Default routing table
- **default** (253): Empty by default

### Routing Lookup Process

```c
int ip_route_input(struct sk_buff *skb, __be32 daddr, __be32 saddr,
                   u8 tos, struct net_device *dev)
{
    // 1. Check local table
    if (ipv4_is_local(daddr)) {
        // Packet for us!
        skb_dst_set(skb, &rt->dst);
        rt->dst.input = ip_local_deliver;
        return 0;
    }

    // 2. Check if forwarding enabled
    if (!IN_DEV_FORWARD(in_dev)) {
        // Not a router, drop
        return -EINVAL;
    }

    // 3. Lookup in routing tables (main, then default)
    rt = ip_route_output_key(net, &fl4);
    if (rt) {
        skb_dst_set(skb, &rt->dst);
        rt->dst.input = ip_forward;  // Forward it
        return 0;
    }

    // 4. No route found
    return -ENETUNREACH;
}
```

### Policy Routing

**Multiple routing tables based on rules**:

```bash
# View routing rules
ip rule list
# 0:	from all lookup local
# 32766:	from all lookup main
# 32767:	from all lookup default

# Create custom routing table
echo "100 custom" >> /etc/iproute2/rt_tables

# Add routes to custom table
ip route add default via 192.168.2.1 table custom
ip route add 10.0.0.0/8 via 192.168.2.254 table custom

# Add rule: Traffic from 10.0.0.0/8 uses custom table
ip rule add from 10.0.0.0/8 lookup custom

# Add rule: Packets marked with 1 use custom table
ip rule add fwmark 1 lookup custom
```

**Use Case**: Different default gateways for different traffic

```bash
# Mark SSH traffic
iptables -t mangle -A OUTPUT -p tcp --dport 22 -j MARK --set-mark 1

# SSH uses ISP1, everything else uses ISP2
ip rule add fwmark 1 lookup isp1
ip route add default via 192.168.1.1 table isp1
ip route add default via 192.168.2.1 table main
```

---

## Summary of Different Paths

| Scenario | Path | Hooks Traversed |
|----------|------|-----------------|
| **Local delivery** | RX → PREROUTING → INPUT → App | PREROUTING, INPUT |
| **Forwarding** | RX → PREROUTING → FORWARD → POSTROUTING → TX | PREROUTING, FORWARD, POSTROUTING |
| **Local output** | App → OUTPUT → POSTROUTING → TX | OUTPUT, POSTROUTING |
| **Loopback** | App → OUTPUT → POSTROUTING → lo → PREROUTING → INPUT → App | All except FORWARD |
| **DNAT + Forward** | RX → PREROUTING (DNAT) → FORWARD → POSTROUTING → TX | PREROUTING, FORWARD, POSTROUTING |
| **Dropped** | RX → PREROUTING/INPUT/FORWARD → DROP | Depends on where dropped |
| **TEE duplicate** | Original: Normal path<br>Clone: → routing → TX | Clone follows output path |

---

## Key Takeaways

1. **Routing decides the path**: `ip_local_deliver` vs `ip_forward`

2. **Netfilter hooks are checkpoints**: Packets can be accepted, dropped, modified, or duplicated

3. **Connection tracking enables stateful firewall and NAT**

4. **Different scenarios skip different stages**:
   - Loopback never hits hardware
   - Dropped packets never reach application
   - Forwarded packets never hit INPUT/OUTPUT hooks

5. **NAT happens at specific hooks**:
   - DNAT: PREROUTING (or OUTPUT for local)
   - SNAT: POSTROUTING

6. **Policy routing allows complex routing decisions** based on source, mark, etc.

7. **Order matters**: raw → mangle → nat → filter

Understanding these paths is crucial for:
- Designing firewalls
- Troubleshooting routing issues
- Implementing NAT
- Building network visualizations and games!
