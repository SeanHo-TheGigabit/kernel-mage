# Linux Kernel TX (Transmit) Path

> The journey of a packet from application to wire, with real function names and kernel code flow.

## Overview

```
Application (write/send system call)
    ↓
Socket Layer (sock_sendmsg)
    ↓
Protocol Layer - L4 (tcp_sendmsg / udp_sendmsg)
    ↓
IP Layer - L3 (ip_queue_xmit / ip_send_skb)
    ↓
Netfilter OUTPUT
    ↓
Routing (ip_route_output)
    ↓
Netfilter POSTROUTING
    ↓
Neighbor Discovery / ARP (neigh_output)
    ↓
L2 - Ethernet header (dev_hard_header)
    ↓
Traffic Control / QoS (tc qdiscs)
    ↓
Device Driver (dev->ndo_start_xmit)
    ↓
TX Ring Buffer (DMA descriptors)
    ↓
NIC Hardware
    ↓
Physical Wire
```

---

## Stage 1: Application - System Call

**System Calls**:
- `send()` / `sendto()` - For sockets
- `write()` - Generic file descriptor write
- `sendmsg()` - Advanced, with control messages
- `sendmmsg()` - Send multiple messages

**Example**:
```c
// TCP send
int sock = socket(AF_INET, SOCK_STREAM, 0);
connect(sock, ...);
send(sock, buffer, length, 0);

// UDP send
int sock = socket(AF_INET, SOCK_DGRAM, 0);
sendto(sock, buffer, length, 0, &dest_addr, sizeof(dest_addr));
```

**Kernel Entry**:
```c
SYSCALL_DEFINE4(send, int, fd, void __user *, buff,
                size_t, len, unsigned int, flags)
{
    return __sys_sendto(fd, buff, len, flags, NULL, 0);
}

SYSCALL_DEFINE6(sendto, int, fd, void __user *, buff, size_t, len,
                unsigned int, flags, struct sockaddr __user *, addr,
                int, addr_len)
{
    return __sys_sendto(fd, buff, len, flags, addr, addr_len);
}
```

---

## Stage 2: Socket Layer

**Function**: `sock_sendmsg()`

**Location**: `net/socket.c`

```c
int sock_sendmsg(struct socket *sock, struct msghdr *msg)
{
    int err = security_socket_sendmsg(sock, msg, msg_data_left(msg));
    if (err)
        return err;

    // Call protocol-specific send function
    return sock->ops->sendmsg(sock, msg, msg_data_left(msg));
}
```

**Socket Operations**: Different for each protocol family

```c
// For INET sockets (IPv4/IPv6)
const struct proto_ops inet_stream_ops = {  // TCP
    .sendmsg = inet_sendmsg,
    .recvmsg = inet_recvmsg,
    // ...
};

const struct proto_ops inet_dgram_ops = {   // UDP
    .sendmsg = inet_sendmsg,
    .recvmsg = inet_recvmsg,
    // ...
};

int inet_sendmsg(struct socket *sock, struct msghdr *msg, size_t size)
{
    struct sock *sk = sock->sk;

    // Call transport protocol send
    return sk->sk_prot->sendmsg(sk, msg, size);
}
```

**Flow Control Check**:
```c
// Check send buffer space
if (sk->sk_sndbuf - sk->sk_wmem_queued < size) {
    // Not enough space
    if (non_blocking)
        return -EAGAIN;
    else
        wait_for_space();  // Block until space available
}
```

---

## Stage 3: Transport Layer (L4)

### TCP: tcp_sendmsg()

**Location**: `net/ipv4/tcp.c`

```c
int tcp_sendmsg(struct sock *sk, struct msghdr *msg, size_t size)
{
    struct tcp_sock *tp = tcp_sk(sk);
    int flags = msg->msg_flags;

    // 1. Check socket state
    if (sk->sk_state != TCP_ESTABLISHED &&
        sk->sk_state != TCP_CLOSE_WAIT) {
        return -EPIPE;  // Not connected
    }

    // 2. MSG_FASTOPEN handling (TCP Fast Open)
    if (flags & MSG_FASTOPEN) {
        // ...
    }

    // 3. Copy data from userspace
    while (msg_data_left(msg) > 0) {
        int copy = min_t(int, msg_data_left(msg), tp->mss_cache);

        // Get or allocate sk_buff
        skb = tcp_write_queue_tail(sk);
        if (!skb || !tcp_skb_can_collapse_to(skb)) {
            skb = sk_stream_alloc_skb(sk, 0, sk->sk_allocation, ...);
            tcp_write_queue_tail(sk, skb);
        }

        // Copy from userspace to skb
        err = skb_copy_to_page_nocache(sk, &msg->msg_iter, skb, ...);

        // Update accounting
        sk->sk_wmem_queued += copy;
        tp->write_seq += copy;
    }

    // 4. Trigger transmission
    if (forced_push(tp)) {
        tcp_mark_push(tp, skb);
        __tcp_push_pending_frames(sk, tp->mss_cache, TCP_NAGLE_PUSH);
    }

    return size;
}
```

**Key TCP Concepts**:

**MSS (Maximum Segment Size)**:
```
MSS = MTU - IP header - TCP header
MSS = 1500 - 20 - 20 = 1460 bytes (typical)
```

**Nagle's Algorithm**: Reduce small packets
```
if (pending_data < MSS && no_unacked_data) {
    wait();  // Buffer data
} else {
    send();
}
```

**TCP Segmentation**:
```c
// tcp_write_xmit() - Segment data into MSS-sized chunks
while (tcp_send_head(sk)) {
    skb = tcp_send_head(sk);

    // Check congestion window
    if (!tcp_cwnd_test(tp, skb))
        break;

    // Transmit segment
    tcp_transmit_skb(sk, skb, 1, GFP_ATOMIC);
}
```

### UDP: udp_sendmsg()

**Location**: `net/ipv4/udp.c`

```c
int udp_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    struct inet_sock *inet = inet_sk(sk);
    struct sk_buff *skb;
    struct udphdr *uh;

    // 1. Get destination address
    if (msg->msg_name) {
        // Provided in sendto()
        daddr = msg_name->sin_addr.s_addr;
        dport = msg_name->sin_port;
    } else if (sk->sk_state == TCP_ESTABLISHED) {
        // Connected UDP socket
        daddr = inet->inet_daddr;
        dport = inet->inet_dport;
    } else {
        return -EDESTADDRREACH;
    }

    // 2. Routing lookup
    rt = ip_route_output_ports(..., daddr, saddr, dport, sport, ...);

    // 3. Allocate sk_buff
    skb = sock_alloc_send_skb(sk, len + header_len, ...);

    // 4. Reserve space for headers
    skb_reserve(skb, header_len);

    // 5. Copy data from userspace
    err = skb_copy_datagram_from_iter(skb, 0, &msg->msg_iter, len);

    // 6. Add UDP header
    skb_push(skb, sizeof(struct udphdr));
    uh = udp_hdr(skb);
    uh->source = inet->inet_sport;
    uh->dest = dport;
    uh->len = htons(len + sizeof(struct udphdr));
    uh->check = 0;  // Will be calculated later

    // 7. Pass to IP layer
    return ip_send_skb(skb);
}
```

**UDP vs TCP**:
- **No connection state**: Each packet independent
- **No segmentation**: Application responsible for sizing
- **No retransmission**: Fire and forget
- **Simpler, faster**: Less overhead

---

## Stage 4: IP Layer (L3)

### For TCP: ip_queue_xmit()

**Location**: `net/ipv4/ip_output.c`

```c
int ip_queue_xmit(struct sock *sk, struct sk_buff *skb, struct flowi *fl)
{
    struct inet_sock *inet = inet_sk(sk);
    struct ip_options_rcu *inet_opt;
    struct rtable *rt;
    struct iphdr *iph;

    // 1. Check if we have route cached
    rt = (struct rtable *)__sk_dst_check(sk, 0);
    if (!rt) {
        // No cached route: lookup
        rt = ip_route_output_ports(...);
        sk_dst_set(sk, &rt->dst);
    }

    // 2. Reserve space for IP header
    skb_push(skb, sizeof(struct iphdr) + opt_len);

    // 3. Build IP header
    iph = ip_hdr(skb);
    iph->version = 4;
    iph->ihl = 5 + (opt_len / 4);
    iph->tos = inet->tos;
    iph->tot_len = htons(skb->len);
    iph->id = htons(atomic_inc_return(&ip_ident));
    iph->frag_off = htons(IP_DF);  // Don't Fragment
    iph->ttl = ip_select_ttl(inet, &rt->dst);
    iph->protocol = sk->sk_protocol;  // IPPROTO_TCP or IPPROTO_UDP
    iph->saddr = fl4->saddr;
    iph->daddr = fl4->daddr;

    // IP options (if any)
    ip_options_build(skb, opt, inet->inet_daddr, rt, 0);

    // 4. Calculate IP checksum
    ip_send_check(iph);

    // 5. Set skb fields
    skb->priority = sk->sk_priority;
    skb->mark = sk->sk_mark;

    // 6. Pass to ip_local_out (netfilter OUTPUT hook)
    return ip_local_out(skb);
}
```

### For UDP: ip_send_skb()

```c
int ip_send_skb(struct sk_buff *skb)
{
    return ip_local_out(skb);
}
```

---

## Stage 5: Netfilter OUTPUT Hook

**Function**: `ip_local_out()`

```c
int ip_local_out(struct sk_buff *skb)
{
    // Netfilter OUTPUT hook
    return NF_HOOK(NFPROTO_IPV4, NF_INET_LOCAL_OUT,
                   dev_net(skb->dev), skb->sk, skb, NULL,
                   skb_dst(skb)->dev,
                   ip_output);  // callback after netfilter
}
```

**iptables Rules Applied**:
```bash
iptables -t raw -A OUTPUT ...     # Connection tracking bypass
iptables -t mangle -A OUTPUT ...  # Packet modification
iptables -t nat -A OUTPUT ...     # DNAT (rare for OUTPUT)
iptables -t filter -A OUTPUT ...  # Filtering (ACCEPT/DROP)
```

**Possible Verdicts**:
- `NF_ACCEPT` → Continue to `ip_output()`
- `NF_DROP` → Drop packet
- `NF_QUEUE` → Send to userspace (nfqueue)

---

## Stage 6: Routing & Fragmentation

### ip_output()

```c
int ip_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct net_device *dev = skb_dst(skb)->dev;

    skb->dev = dev;
    skb->protocol = htons(ETH_P_IP);

    // Netfilter POSTROUTING hook
    return NF_HOOK(NFPROTO_IPV4, NF_INET_POST_ROUTING,
                   net, sk, skb, NULL, dev,
                   ip_finish_output);
}
```

### Netfilter POSTROUTING Hook

**iptables Rules**:
```bash
iptables -t mangle -A POSTROUTING ...  # Packet modification
iptables -t nat -A POSTROUTING ...     # SNAT/MASQUERADE
```

**This is where NAT happens!**

**SNAT Example**:
```
Before SNAT:
src=192.168.1.100:5000 → dst=8.8.8.8:53

After SNAT:
src=203.0.113.10:12345 → dst=8.8.8.8:53

Connection tracking entry created:
ORIGINAL: 192.168.1.100:5000 → 8.8.8.8:53
REPLY:    8.8.8.8:53 → 203.0.113.10:12345
```

### ip_finish_output()

```c
static int ip_finish_output(struct net *net, struct sock *sk,
                            struct sk_buff *skb)
{
    unsigned int mtu = dst_mtu(skb_dst(skb));

    // Check if fragmentation needed
    if (skb->len > mtu && !skb_is_gso(skb)) {
        return ip_fragment(net, sk, skb, mtu, ip_finish_output2);
    }

    return ip_finish_output2(net, sk, skb);
}
```

**Fragmentation**:
```c
int ip_fragment(struct net *net, struct sock *sk, struct sk_buff *skb,
                unsigned int mtu, int (*output)(...))
{
    struct iphdr *iph = ip_hdr(skb);
    int offset = 0;

    // Calculate how many fragments needed
    int fragment_size = (mtu - hlen) & ~7;  // Must be 8-byte aligned

    while (offset < skb->len) {
        struct sk_buff *skb2 = alloc_skb(...);

        // Copy fragment data
        skb_copy_bits(skb, offset, skb2->data, fragment_size);

        // Build IP header for fragment
        iph = ip_hdr(skb2);
        iph->frag_off = htons(offset / 8);  // Offset in 8-byte units
        if (offset + fragment_size < skb->len)
            iph->frag_off |= htons(IP_MF);  // More Fragments flag

        // Send fragment
        ip_finish_output2(net, sk, skb2);

        offset += fragment_size;
    }
}
```

---

## Stage 7: Neighbor Discovery & L2 Header

### ip_finish_output2() - ARP Resolution

```c
static int ip_finish_output2(struct net *net, struct sock *sk,
                             struct sk_buff *skb)
{
    struct dst_entry *dst = skb_dst(skb);
    struct rtable *rt = (struct rtable *)dst;
    struct net_device *dev = dst->dev;
    struct neighbour *neigh;

    // Get next hop IP
    nexthop = (__force u32)rt_nexthop(rt, ip_hdr(skb)->daddr);

    // Neighbor lookup (ARP cache)
    neigh = __ipv4_neigh_lookup_noref(dev, nexthop);
    if (unlikely(!neigh))
        neigh = __neigh_create(&arp_tbl, &nexthop, dev, false);

    if (neigh) {
        // Send via neighbor
        return neigh_output(neigh, skb, false);
    }

    return -EINVAL;
}
```

### Neighbor Output - neigh_output()

```c
int neigh_output(struct neighbour *neigh, struct sk_buff *skb, bool skip_cache)
{
    // Check neighbor state
    if (neigh->nud_state & NUD_CONNECTED) {
        // We have MAC address!
        return neigh_hh_output(neigh->ha, skb);
    }

    // Need to resolve MAC address
    return neigh_resolve_output(neigh, skb);
}
```

**ARP Resolution**:
```c
int neigh_resolve_output(struct neighbour *neigh, struct sk_buff *skb)
{
    // Queue packet
    __skb_queue_tail(&neigh->arp_queue, skb);

    // Send ARP request
    neigh_probe(neigh);

    // Packet will be sent when ARP reply arrives
    return 0;
}
```

**ARP Cache**:
```bash
# View ARP cache
ip neigh show

# Example:
# 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
```

### Add Ethernet Header - dev_hard_header()

```c
int dev_hard_header(struct sk_buff *skb, struct net_device *dev,
                    unsigned short type, const void *daddr,
                    const void *saddr, unsigned int len)
{
    // Call device's header_ops->create
    // For Ethernet: eth_header()
    return dev->header_ops->create(skb, dev, type, daddr, saddr, len);
}

int eth_header(struct sk_buff *skb, struct net_device *dev,
               unsigned short type, const void *daddr,
               const void *saddr, unsigned int len)
{
    struct ethhdr *eth;

    // Add Ethernet header
    skb_push(skb, ETH_HLEN);
    eth = (struct ethhdr *)skb->data;

    // Fill Ethernet header
    memcpy(eth->h_dest, daddr, ETH_ALEN);       // Destination MAC (6 bytes)
    memcpy(eth->h_source, saddr, ETH_ALEN);     // Source MAC (6 bytes)
    eth->h_proto = htons(type);                  // EtherType (2 bytes): 0x0800 for IPv4

    return ETH_HLEN;
}
```

**Packet Structure Now**:
```
┌──────────────────────────────────────────────────┐
│ Ethernet Header (14 bytes)                       │
│  ├─ Dest MAC (6)                                 │
│  ├─ Src MAC (6)                                  │
│  └─ EtherType (2): 0x0800                        │
├──────────────────────────────────────────────────┤
│ IP Header (20+ bytes)                            │
├──────────────────────────────────────────────────┤
│ TCP/UDP Header (20/8 bytes)                      │
├──────────────────────────────────────────────────┤
│ Application Data                                 │
└──────────────────────────────────────────────────┘
```

---

## Stage 8: Traffic Control (QoS)

### dev_queue_xmit() - Entry to QoS

**Location**: `net/core/dev.c`

```c
int dev_queue_xmit(struct sk_buff *skb)
{
    struct net_device *dev = skb->dev;
    struct Qdisc *q;

    // Select TX queue
    txq = netdev_pick_tx(dev, skb, NULL);
    q = rcu_dereference_bh(txq->qdisc);

    if (q->enqueue) {
        // Has qdisc: enqueue packet
        return __dev_xmit_skb(skb, q, dev, txq);
    } else {
        // No qdisc: direct transmit
        return dev_hard_start_xmit(skb, dev, txq, NULL);
    }
}
```

### Queue Disciplines (qdiscs)

**Default qdisc**: `pfifo_fast`

```
pfifo_fast (3 bands):
┌─────────────────┐
│  Band 0 (High)  │  ← TOS: Interactive (Telnet, SSH)
├─────────────────┤
│  Band 1 (Medium)│  ← TOS: Bulk (FTP)
├─────────────────┤
│  Band 2 (Low)   │  ← TOS: Best effort
└─────────────────┘
```

**Hierarchical qdiscs** (e.g., HTB - Hierarchical Token Bucket):

```
                Root qdisc (HTB)
                      |
        ┌─────────────┼─────────────┐
        │             │             │
    Class 1:1     Class 1:2     Class 1:3
    (50 Mbps)     (30 Mbps)     (20 Mbps)
        |             |             |
    SFQ qdisc     SFQ qdisc     SFQ qdisc
```

**Packet Classification**:
```c
// tc filter rules determine which class
if (dst_port == 80)
    class = 1:1;  // HTTP → high priority
else if (dst_port == 22)
    class = 1:2;  // SSH → medium priority
else
    class = 1:3;  // default → low priority
```

**Qdisc Operations**:
```c
struct Qdisc_ops {
    int (*enqueue)(struct sk_buff *skb, struct Qdisc *sch, ...);
    struct sk_buff *(*dequeue)(struct Qdisc *sch);
    struct sk_buff *(*peek)(struct Qdisc *sch);
    int (*init)(struct Qdisc *sch, struct nlattr *arg);
    void (*destroy)(struct Qdisc *sch);
};
```

**Example qdiscs**:
- **pfifo_fast**: Default, 3-band priority queue
- **HTB**: Hierarchical rate limiting
- **SFQ**: Stochastic Fair Queuing (fairness per flow)
- **TBF**: Token Bucket Filter (rate shaping)
- **FQ_CODEL**: Fair Queue with Controlled Delay (modern, reduces bufferbloat)
- **Cake**: Comprehensive qdisc with built-in shaping and fairness

---

## Stage 9: Device Driver - dev_hard_start_xmit()

### Transmit Function

```c
int dev_hard_start_xmit(struct sk_buff *skb, struct net_device *dev,
                        struct netdev_queue *txq, int *ret)
{
    // Call driver's ndo_start_xmit
    rc = dev->netdev_ops->ndo_start_xmit(skb, dev);

    if (rc == NETDEV_TX_OK) {
        // Success
    } else if (rc == NETDEV_TX_BUSY) {
        // Queue full, retry later
    }

    return rc;
}
```

### Driver Transmit Function

**Example**: Intel e1000e driver

```c
static netdev_tx_t e1000_xmit_frame(struct sk_buff *skb,
                                    struct net_device *netdev)
{
    struct e1000_adapter *adapter = netdev_priv(netdev);
    struct e1000_ring *tx_ring = adapter->tx_ring;

    // 1. Check if TX ring has space
    if (e1000_maybe_stop_tx(tx_ring, skb_shinfo(skb)->nr_frags + 2))
        return NETDEV_TX_BUSY;

    // 2. Handle TSO (TCP Segmentation Offload)
    if (skb_is_gso(skb)) {
        if (e1000_tso(tx_ring, skb))
            goto out_drop;
    }

    // 3. Handle checksum offload
    if (e1000_tx_csum(tx_ring, skb))
        goto out_drop;

    // 4. Map skb to DMA addresses
    count = e1000_tx_map(tx_ring, skb, first, max_per_txd, nr_frags);

    // 5. Setup TX descriptors
    e1000_tx_queue(tx_ring, count);

    // 6. Ring doorbell (tell NIC about new descriptors)
    writel(tx_ring->next_to_use, adapter->hw.hw_addr + tx_ring->tail);

    return NETDEV_TX_OK;

out_drop:
    dev_kfree_skb_any(skb);
    return NETDEV_TX_OK;
}
```

### TX Descriptor Setup

**TX Descriptor** (simplified):
```c
struct e1000_tx_desc {
    __le64 buffer_addr;   // Physical address of packet data
    union {
        __le32 data;
        struct {
            __le16 length;     // Packet length
            __u8 cso;          // Checksum offset
            __u8 cmd;          // Command flags
        } flags;
    } lower;
    union {
        __le32 data;
        struct {
            __u8 status;       // Descriptor status
            __u8 css;          // Checksum start
            __le16 special;
        } fields;
    } upper;
};
```

**TX Ring Buffer**:
```
┌──────────────────────────────────────┐
│  TX Descriptor Ring                  │
│  ┌────┬────┬────┬────┬────┬────┐   │
│  │ D0 │ D1 │ D2 │ D3 │ D4 │ D5 │   │
│  └─│──┴─│──┴─│──┴─│──┴─│──┴─│──┘   │
│    │    │    │    │    │    │       │
│    ↓    ↓    ↓    ↓    ↓    ↓       │
│  [pkt][pkt][   ][   ][   ][   ]     │
│                                      │
│  Head (HW) ──┘         Tail (SW) ─┘  │
└──────────────────────────────────────┘

Head: Next descriptor for NIC to transmit
Tail: Next descriptor for software to write
```

---

## Stage 10: NIC Hardware Transmission

### NIC Processing

1. **Read TX Descriptor** via DMA
   - NIC reads descriptor from ring buffer
   - Gets physical address of packet buffer
   - Gets packet length and flags

2. **DMA Packet Data**
   - NIC DMAs packet data from RAM
   - No CPU involvement

3. **Apply Hardware Offloads**:
   - **TSO (TCP Segmentation Offload)**: Segment large packet
   - **Checksum Calculation**: IP, TCP, UDP checksums
   - **VLAN Tag Insertion**: Add 802.1Q tag

4. **Add FCS (Frame Check Sequence)**
   - Calculate CRC32 over entire frame
   - Append 4-byte FCS

5. **Physical Transmission**
   - Convert packet to electrical/optical signals
   - Transmit on wire
   - Handle collisions (if half-duplex)

### TX Completion

**Interrupt/Polling**:
```c
// TX completion handler
static irqreturn_t e1000_msix_tx(int irq, void *data)
{
    struct e1000_ring *tx_ring = data;

    // Schedule NAPI to clean TX ring
    napi_schedule(&tx_ring->napi);

    return IRQ_HANDLED;
}

// Clean TX ring (free transmitted packets)
static bool e1000_clean_tx_irq(struct e1000_ring *tx_ring)
{
    while (tx_ring->next_to_clean != tx_ring->next_to_use) {
        struct e1000_tx_desc *tx_desc = E1000_TX_DESC(*tx_ring, i);

        // Check if transmitted
        if (!(tx_desc->upper.fields.status & E1000_TXD_STAT_DD))
            break;  // Not done yet

        // Get skb
        struct sk_buff *skb = tx_ring->buffer_info[i].skb;

        // Unmap DMA
        dma_unmap_single(dev, buffer_info->dma, ...);

        // Free skb
        dev_kfree_skb_any(skb);

        // Move to next descriptor
        i++;
        cleaned++;
    }

    tx_ring->next_to_clean = i;

    // Wake queue if it was stopped
    if (cleaned && netif_queue_stopped(netdev))
        netif_wake_queue(netdev);

    return cleaned < budget;
}
```

---

## Complete TX Function Call Chain

```
[Application]
    ↓
send() / write() system call
    ↓
sock_sendmsg()  [net/socket.c]
    ↓
inet_sendmsg()  [net/ipv4/af_inet.c]
    ↓
tcp_sendmsg() OR udp_sendmsg()  [net/ipv4/tcp.c, net/ipv4/udp.c]
    ↓
ip_queue_xmit() OR ip_send_skb()  [net/ipv4/ip_output.c]
    ↓
ip_local_out()  [Netfilter OUTPUT hook]
    ↓
ip_output()
    ↓
NF_HOOK(POSTROUTING)  [Netfilter, NAT happens here]
    ↓
ip_finish_output()
    ↓
ip_finish_output2()  [ARP resolution, add L2 header]
    ↓
neigh_output()  [net/core/neighbour.c]
    ↓
dev_queue_xmit()  [net/core/dev.c]
    ↓
__dev_xmit_skb()  [Traffic control / QoS]
    ↓
qdisc->enqueue()  [Queue packet if qdisc exists]
    ↓
qdisc->dequeue()  [Dequeue when ready to transmit]
    ↓
dev_hard_start_xmit()
    ↓
ndo_start_xmit()  [Driver transmit function]
    ↓
[Setup TX descriptors]
    ↓
[Ring doorbell - write to MMIO register]
    ↓
[NIC DMA, hardware offloads, transmit]
    ↓
[Physical Wire]
```

---

## Key Takeaways

1. **Socket Layer**: Entry point, flow control

2. **L4 Processing**:
   - TCP: Connection state, segmentation, reliability
   - UDP: Connectionless, simple header

3. **L3 Processing**: IP header, routing, fragmentation

4. **Netfilter Hooks**:
   - OUTPUT: Filtering for locally-generated packets
   - POSTROUTING: NAT (SNAT/MASQUERADE)

5. **ARP Resolution**: MAC address lookup for next hop

6. **Traffic Control**: QoS, rate limiting, prioritization

7. **Driver**: DMA setup, hardware offloads (TSO, checksum)

8. **Hardware**: DMA read, apply offloads, transmit on wire

9. **TX Completion**: Free transmitted packets, wake queue

10. **File Locations**:
    - `net/socket.c` - Socket layer
    - `net/ipv4/tcp.c` - TCP
    - `net/ipv4/udp.c` - UDP
    - `net/ipv4/ip_output.c` - IP output
    - `net/core/dev.c` - Core device, qdisc
    - `drivers/net/ethernet/` - NIC drivers
