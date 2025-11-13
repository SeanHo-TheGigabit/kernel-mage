# Linux Kernel RX (Receive) Path

> The actual journey of a packet from wire to application, with real function names and kernel code flow.

## Overview

```
Physical Wire
    ↓
NIC Hardware (Frame detection, CRC check)
    ↓
DMA Transfer → Ring Buffer
    ↓
Interrupt/NAPI
    ↓
Driver: napi_gro_receive() or netif_receive_skb()
    ↓
__netif_receive_skb_core() [PROTOCOL DEMULTIPLEXING]
    ↓
Protocol Handler (e.g., ip_rcv for IPv4)
    ↓
Netfilter PRE_ROUTING
    ↓
Routing Decision (ip_route_input)
    ↓
├─→ ip_local_deliver → Netfilter INPUT → L4 Protocol → Socket → App
└─→ ip_forward → Netfilter FORWARD → ip_output
```

---

## Stage 1: NIC Hardware

**Physical Layer**:
1. Electrical/optical signals arrive on wire
2. NIC detects frame boundaries (preamble + SFD)
3. Receives frame data
4. Validates FCS (Frame Check Sequence / CRC32)
5. Checks destination MAC address:
   - Matches device MAC → accept
   - Broadcast (FF:FF:FF:FF:FF:FF) → accept
   - Multicast + subscribed → accept
   - Promiscuous mode → accept all

**Hardware Features**:
- **RSS (Receive Side Scaling)**: Hash packet headers, distribute to multiple RX queues
- **Checksum Offload**: NIC validates IP/TCP/UDP checksums
- **VLAN Filtering**: Hardware VLAN tag stripping

---

## Stage 2: DMA & Ring Buffer

**Ring Buffer Structure** (example: Intel e1000e):
```
┌──────────────────────────────────────┐
│  RX Descriptor Ring (in RAM)        │
│  ┌────┬────┬────┬────┬────┬────┐   │
│  │ D0 │ D1 │ D2 │ D3 │ D4 │ D5 │   │
│  └─│──┴─│──┴─│──┴─│──┴─│──┴─│──┘   │
│    │    │    │    │    │    │       │
│    ↓    ↓    ↓    ↓    ↓    ↓       │
│  [buf][buf][buf][buf][buf][buf]     │
│                                      │
│  Head ─────┘         Tail ──────┘    │
└──────────────────────────────────────┘
```

**Process**:
1. Driver pre-allocates RX ring buffers during initialization
2. Each descriptor contains physical address of buffer
3. NIC performs **DMA (Direct Memory Access)**:
   - Reads next descriptor
   - Writes packet data to buffer address
   - Writes back descriptor status
4. Updates head pointer
5. No CPU involvement!

**Key Data Structure**: `sk_buff` (socket buffer)

---

## Stage 3: Interrupt & NAPI

### Traditional Interrupts (Legacy)
```
NIC → Hardware IRQ → CPU → Driver IRQ Handler → Process Packet
```

**Problem**: High packet rate = interrupt storm = CPU overwhelmed

### NAPI (New API) - Modern Approach
```
NIC → IRQ → Driver: Disable IRQ, Schedule NAPI poll
                     ↓
                   NAPI Poll (softirq NET_RX_SOFTIRQ)
                     ↓
                   Process batch of packets
                     ↓
                   If more packets: continue polling
                   If done: Re-enable IRQ
```

**Benefits**:
- **Interrupt mitigation**: One interrupt, many packets
- **Polling under load**: Efficient when busy
- **Fairness**: Round-robin across devices

**Driver Code** (simplified):
```c
// IRQ handler
static irqreturn_t driver_irq_handler(int irq, void *data)
{
    struct napi_struct *napi = data;

    // Disable NIC interrupts
    disable_nic_interrupts();

    // Schedule NAPI poll
    napi_schedule(napi);

    return IRQ_HANDLED;
}

// NAPI poll function
static int driver_poll(struct napi_struct *napi, int budget)
{
    int work_done = 0;

    while (work_done < budget) {
        struct sk_buff *skb = get_packet_from_ring();
        if (!skb)
            break;

        napi_gro_receive(napi, skb);
        work_done++;
    }

    if (work_done < budget) {
        napi_complete(napi);
        enable_nic_interrupts();
    }

    return work_done;
}
```

---

## Stage 4: Driver Processing

### GRO (Generic Receive Offload)

**Function**: `napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)`

**Purpose**: Merge multiple small packets into one large packet before sending up the stack

**Example**:
```
Incoming: 10 × 1500-byte TCP segments
Without GRO: 10 separate sk_buffs → 10 × protocol processing overhead
With GRO: 1 × 15000-byte sk_buff → 1 × protocol processing overhead
```

**How it Works**:
1. Check if packet can merge with existing GRO flow
2. Match by: protocol + IP addresses + TCP ports
3. If match found: merge data, update headers
4. If no match or not mergeable: create new GRO flow
5. At end of NAPI poll: flush GRO list

**GRO Flush** → calls `netif_receive_skb()` for each packet

### sk_buff Setup

**Driver populates**:
```c
struct sk_buff *skb = alloc_skb(...);

// Called by driver to strip Ethernet header and set protocol
eth_type_trans(skb, dev);
// This does:
// 1. skb_pull(skb, ETH_HLEN) - strips 14-byte Ethernet header
// 2. Sets skb->protocol based on EtherType field:
//    - 0x0800 → ETH_P_IP (IPv4)
//    - 0x86DD → ETH_P_IPV6
//    - 0x0806 → ETH_P_ARP
// 3. Sets skb->dev = dev

skb->tstamp = ktime_get_real();  // timestamp
skb->pkt_type = PACKET_HOST;      // for us
```

---

## Stage 5: Protocol Demultiplexing - The REAL Flow

**Key Insight**: There's NO separate "L2 stage" and "L3 stage". The Ethernet header is stripped by `eth_type_trans()`, then `__netif_receive_skb_core()` immediately demultiplexes to the right protocol handler.

### Entry Point

```c
netif_receive_skb(skb)
  ↓
__netif_receive_skb(skb)  // handles RPS if enabled
  ↓
__netif_receive_skb_core(&skb, ...)  // THE DEMULTIPLEXER
```

**Location**: `net/core/dev.c`

### __netif_receive_skb_core() - Protocol Demultiplexing

**Actual Code Flow**:

```c
static int __netif_receive_skb_core(struct sk_buff **pskb, ...)
{
    struct sk_buff *skb = *pskb;
    struct packet_type *ptype, *pt_prev = NULL;

    // 1. DELIVER TO PACKET TAPS (tcpdump, wireshark)
    list_for_each_entry_rcu(ptype, &ptype_all, list) {
        if (ptype->dev == NULL || ptype->dev == skb->dev) {
            deliver_skb(skb, ptype, orig_dev);
        }
    }

    // 2. BRIDGE PROCESSING (if interface is bridge port)
    if (skb->dev->priv_flags & IFF_BRIDGE_PORT) {
        // Bridge code gets first look
        skb = br_handle_frame(skb);
        if (!skb)
            return NET_RX_SUCCESS;  // bridge consumed it
    }

    // 3. PROTOCOL-SPECIFIC HANDLER LOOKUP
    int hash = ntohs(skb->protocol) & PTYPE_HASH_MASK;
    list_for_each_entry_rcu(ptype, &ptype_base[hash], list) {
        if (ptype->type == skb->protocol) {
            // Found handler! Call it.
            deliver_skb(skb, ptype, orig_dev);
        }
    }
}

static inline int deliver_skb(struct sk_buff *skb,
                              struct packet_type *pt_prev,
                              struct net_device *orig_dev)
{
    // Invoke the protocol handler function
    return pt_prev->func(skb, skb->dev, pt_prev, orig_dev);
}
```

### Protocol Handler Registration

**How handlers are registered** (at kernel init):

```c
// IPv4 handler
static struct packet_type ip_packet_type = {
    .type = cpu_to_be16(ETH_P_IP),  // 0x0800
    .func = ip_rcv,                  // handler function
};

void __init ip_init(void)
{
    dev_add_pack(&ip_packet_type);
}

// ARP handler
static struct packet_type arp_packet_type = {
    .type = cpu_to_be16(ETH_P_ARP),  // 0x0806
    .func = arp_rcv,
};

// IPv6 handler
static struct packet_type ipv6_packet_type = {
    .type = cpu_to_be16(ETH_P_IPV6),  // 0x86DD
    .func = ipv6_rcv,
};
```

**Result**: When `__netif_receive_skb_core()` looks up protocol 0x0800, it finds `ip_rcv()` and calls it!

---

## Stage 6: IPv4 Processing - ip_rcv()

**Location**: `net/ipv4/ip_input.c`

### ip_rcv() - Entry Point

```c
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    struct net *net = dev_net(dev);

    // 1. SKB must have enough space for IP header
    if (!pskb_may_pull(skb, sizeof(struct iphdr)))
        goto inhdr_error;

    // 2. Get IP header
    struct iphdr *iph = ip_hdr(skb);

    // 3. Validate IP header
    if (iph->ihl < 5 || iph->version != 4)
        goto inhdr_error;

    // 4. Validate total length
    if (!pskb_may_pull(skb, iph->ihl * 4))
        goto inhdr_error;

    // 5. Validate IP checksum
    if (ip_fast_csum((u8 *)iph, iph->ihl))
        goto csum_error;

    // 6. Check length fields match
    if (skb->len < ntohs(iph->tot_len))
        goto inhdr_error;

    // 7. Trim any padding
    pskb_trim_rcsum(skb, ntohs(iph->tot_len));

    // 8. NETFILTER PRE_ROUTING HOOK
    return NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING,
                   net, NULL, skb, dev, NULL,
                   ip_rcv_finish);  // callback after netfilter

inhdr_error:
    IP_INC_STATS_BH(net, IPSTATS_MIB_INHDRERRORS);
    kfree_skb(skb);
    return NET_RX_DROP;
}
```

**Key Points**:
1. Validates IP header (version, length, checksum)
2. Calls **Netfilter PRE_ROUTING** hook
3. Registers `ip_rcv_finish()` as callback

---

## Stage 7: Netfilter PRE_ROUTING

**Hook Point**: `NF_INET_PRE_ROUTING`

**Possible Verdicts**:
- `NF_ACCEPT`: Continue to `ip_rcv_finish()`
- `NF_DROP`: Drop packet, free sk_buff
- `NF_STOLEN`: Handler took ownership
- `NF_QUEUE`: Send to userspace (nfqueue)

**iptables Rules Applied** (in order):
1. `iptables -t raw -A PREROUTING ...` (connection tracking bypass)
2. `iptables -t mangle -A PREROUTING ...` (packet modification)
3. `iptables -t nat -A PREROUTING ...` (DNAT)

**Connection Tracking**: If not bypassed, connection tracking happens here

---

## Stage 8: Routing Decision - ip_rcv_finish()

**Location**: `net/ipv4/ip_input.c`

```c
static int ip_rcv_finish(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);

    // 1. EARLY DEMUX (optimization)
    // Try to find socket directly without full routing lookup
    if (skb->sk == NULL) {
        const struct net_protocol *ipprot;
        ipprot = rcu_dereference(inet_protos[iph->protocol]);
        if (ipprot && ipprot->early_demux) {
            ipprot->early_demux(skb);  // might set skb->sk and skb_dst
        }
    }

    // 2. ROUTING TABLE LOOKUP (if not already done by early_demux)
    if (!skb_valid_dst(skb)) {
        int err = ip_route_input(skb, iph->daddr, iph->saddr,
                                 iph->tos, skb->dev);
        if (unlikely(err))
            goto drop;
    }

    // 3. IP OPTIONS PROCESSING
    if (iph->ihl > 5) {
        ip_rcv_options(skb, dev);
    }

    // 4. CALL ROUTING INPUT FUNCTION
    // dst->input is set by routing decision to either:
    //   - ip_local_deliver (for local destination)
    //   - ip_forward (for forwarding)
    return dst_input(skb);  // invokes skb_dst(skb)->input(skb)
}
```

### Routing Table Lookup: ip_route_input()

**Determines**:
1. Is this packet for us? → `dst->input = ip_local_deliver`
2. Is this packet to forward? → `dst->input = ip_forward`
3. Which output interface (for forwarding)?
4. Next hop IP address

**Routing Tables**:
```bash
# Local table (destinations on this machine)
ip route show table local

# Main routing table
ip route show table main
```

**Example Flow**:
```
Packet destination: 192.168.1.100
Local IPs: 192.168.1.100, 127.0.0.1
→ Match! Set dst->input = ip_local_deliver

Packet destination: 8.8.8.8
Local IPs: 192.168.1.100
→ No match. Check main routing table.
→ Default route: via 192.168.1.1 dev eth0
→ Set dst->input = ip_forward
→ Set next hop = 192.168.1.1
→ Set output dev = eth0
```

---

## Stage 9A: Local Delivery - ip_local_deliver()

**For packets destined to this machine**:

```c
int ip_local_deliver(struct sk_buff *skb)
{
    // 1. REASSEMBLY (if fragmented)
    if (ip_is_fragment(ip_hdr(skb))) {
        if (ip_defrag(skb, IP_DEFRAG_LOCAL_DELIVER))
            return 0;  // waiting for more fragments
    }

    // 2. NETFILTER INPUT HOOK
    return NF_HOOK(NFPROTO_IPV4, NF_INET_LOCAL_IN,
                   dev_net(skb->dev), NULL, skb, skb->dev, NULL,
                   ip_local_deliver_finish);
}
```

**Netfilter INPUT**: `iptables -A INPUT ...` rules apply here

### ip_local_deliver_finish() - L4 Demux

```c
static int ip_local_deliver_finish(struct net *net, struct sock *sk,
                                   struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);

    // Protocol demultiplexing
    int protocol = iph->protocol;
    const struct net_protocol *ipprot;

    // Lookup protocol handler
    ipprot = rcu_dereference(inet_protos[protocol]);

    if (ipprot) {
        // Call L4 protocol handler:
        // - IPPROTO_TCP (6) → tcp_v4_rcv()
        // - IPPROTO_UDP (17) → udp_rcv()
        // - IPPROTO_ICMP (1) → icmp_rcv()
        ret = ipprot->handler(skb);
    } else {
        // Unknown protocol: send ICMP protocol unreachable
        icmp_send(skb, ICMP_DEST_UNREACH, ICMP_PROT_UNREACH, 0);
        kfree_skb(skb);
    }

    return ret;
}
```

**Protocol Handler Registration**:
```c
static const struct net_protocol tcp_protocol = {
    .handler = tcp_v4_rcv,
    .early_demux = tcp_v4_early_demux,
};

static const struct net_protocol udp_protocol = {
    .handler = udp_rcv,
    .early_demux = udp_v4_early_demux,
};
```

---

## Stage 10: L4 Processing - TCP/UDP

### TCP: tcp_v4_rcv()

**Location**: `net/ipv4/tcp_ipv4.c`

```c
int tcp_v4_rcv(struct sk_buff *skb)
{
    struct tcphdr *th = tcp_hdr(skb);

    // 1. Validate TCP header
    if (skb->len < sizeof(struct tcphdr))
        goto discard_it;

    // 2. Checksum validation
    if (skb_checksum_init(skb, IPPROTO_TCP, ...))
        goto csum_error;

    // 3. SOCKET LOOKUP (4-tuple hash)
    sk = __inet_lookup_skb(&tcp_hashinfo, skb,
                          th->source, th->dest);

    if (!sk)
        goto no_tcp_socket;  // send RST

    // 4. Socket found! Lock it.
    bh_lock_sock(sk);

    // 5. TCP STATE MACHINE
    ret = 0;
    if (!sock_owned_by_user(sk)) {
        ret = tcp_v4_do_rcv(sk, skb);  // process packet
    } else {
        // Socket locked by userspace, queue for later
        sk_add_backlog(sk, skb);
    }

    bh_unlock_sock(sk);
    return ret;
}
```

**TCP State Machine** (simplified):
```
LISTEN + SYN → SYN_RECV (send SYN-ACK)
SYN_RECV + ACK → ESTABLISHED (3-way handshake complete)
ESTABLISHED + data → Queue to receive buffer, send ACK
ESTABLISHED + FIN → FIN_WAIT, send ACK
```

### UDP: udp_rcv()

**Location**: `net/ipv4/udp.c`

```c
int udp_rcv(struct sk_buff *skb)
{
    struct udphdr *uh = udp_hdr(skb);

    // 1. Validate UDP header
    // 2. Checksum validation (optional for IPv4)

    // 3. SOCKET LOOKUP (2-tuple: dst_ip, dst_port)
    sk = __udp4_lib_lookup_skb(skb, uh->source, uh->dest, ...);

    if (sk) {
        // Socket found: deliver to it
        return udp_queue_rcv_skb(sk, skb);
    }

    // No socket listening: send ICMP port unreachable
    icmp_send(skb, ICMP_DEST_UNREACH, ICMP_PORT_UNREACH, 0);
    kfree_skb(skb);
    return 0;
}
```

---

## Stage 11: Socket Buffer

**Data queued to socket's receive buffer**:

```c
int udp_queue_rcv_skb(struct sock *sk, struct sk_buff *skb)
{
    // 1. Check receive buffer space
    if (sk->sk_rcvbuf - atomic_read(&sk->sk_rmem_alloc) < skb->truesize) {
        // Buffer full!
        UDP_INC_STATS(UDP_MIB_RCVBUFERRORS);
        kfree_skb(skb);
        return -ENOMEM;
    }

    // 2. Add to socket receive queue
    __skb_queue_tail(&sk->sk_receive_queue, skb);

    // 3. Update memory accounting
    sk_mem_charge(sk, skb->truesize);

    // 4. Wake up waiting process
    sk->sk_data_ready(sk);

    return 0;
}
```

---

## Stage 12: Application Receives

**System Call**: `recv()`, `recvfrom()`, `read()`, `recvmsg()`

```c
// Userspace
ssize_t recv(int sockfd, void *buf, size_t len, int flags);

// Kernel
SYSCALL_DEFINE4(recv, ...)
{
    // ... eventually calls:
    sock->ops->recvmsg(sock, &msg, size, flags);
}

// For UDP
int udp_recvmsg(struct sock *sk, struct msghdr *msg, ...)
{
    // 1. Wait for data (if blocking)
    skb = __skb_recv_datagram(sk, flags, ...);

    // 2. Copy data to userspace
    err = skb_copy_datagram_msg(skb, 0, msg, copied);

    // 3. Free sk_buff
    skb_free_datagram(sk, skb);

    return copied;
}
```

**The packet has reached the application!** 🎯

---

## Complete Function Call Chain (Summary)

```
[NIC Hardware]
    ↓ DMA
[Ring Buffer]
    ↓ Interrupt/NAPI
driver_poll()
    ↓
napi_gro_receive()  [may merge packets]
    ↓
netif_receive_skb()
    ↓
__netif_receive_skb()
    ↓
__netif_receive_skb_core()  [PROTOCOL DEMUX]
    ↓ (based on skb->protocol)
ip_rcv()  [net/ipv4/ip_input.c]
    ↓ (validate, netfilter hook)
NF_HOOK(PRE_ROUTING) → ip_rcv_finish()
    ↓
ip_route_input()  [routing decision]
    ↓
dst_input() → ip_local_deliver() OR ip_forward()
    ↓ (for local delivery)
NF_HOOK(INPUT) → ip_local_deliver_finish()
    ↓ (based on iph->protocol)
tcp_v4_rcv() OR udp_rcv()  [L4 DEMUX]
    ↓
__inet_lookup_skb()  [find socket]
    ↓
tcp_v4_do_rcv() OR udp_queue_rcv_skb()
    ↓
__skb_queue_tail(&sk->sk_receive_queue)
    ↓
sk_data_ready()  [wake app]
    ↓
[Application recv() system call]
```

---

## Key Takeaways

1. **No "L2 Stage"**: The Ethernet header is stripped by `eth_type_trans()` in the driver, not a separate stage

2. **Protocol Demultiplexing**: `__netif_receive_skb_core()` looks up the protocol handler (e.g., `ip_rcv`) based on `skb->protocol` field

3. **Netfilter Hooks**: PRE_ROUTING (before routing), INPUT (to local)

4. **Routing Decision**: `ip_route_input()` determines local delivery vs forwarding

5. **L4 Demux**: `ip_local_deliver_finish()` calls protocol handler based on IP protocol field

6. **Socket Lookup**: TCP uses 4-tuple, UDP uses destination IP+port

7. **Real File Locations**:
   - `net/core/dev.c` - `netif_receive_skb()`, `__netif_receive_skb_core()`
   - `net/ipv4/ip_input.c` - `ip_rcv()`, `ip_local_deliver()`
   - `net/ipv4/tcp_ipv4.c` - `tcp_v4_rcv()`
   - `net/ipv4/udp.c` - `udp_rcv()`
