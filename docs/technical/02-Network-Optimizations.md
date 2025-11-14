# Linux Network Stack Optimizations

> Understanding NAPI, GRO, GSO, TSO, RSS, RPS, RFS, XPS and other performance features

## Overview

The Linux network stack has evolved many optimization techniques to handle high packet rates efficiently. These features reduce CPU overhead, improve throughput, and scale across multiple CPUs.

---

## Interrupt Handling

### Traditional Interrupt Model (Legacy)

```
Packet arrives → NIC generates IRQ → CPU handles interrupt
→ Process 1 packet → Return to work
→ Next packet → IRQ → CPU interrupt → Process → Return
→ Repeat...
```

**Problem**: **Interrupt Storm**
- High packet rate = thousands of interrupts/second
- Each interrupt has overhead (context switch, cache invalidation)
- CPU spends all time handling interrupts, not doing real work

### NAPI (New API) - Polling Under Load

**Key Insight**: When busy, polling is more efficient than interrupts

**How NAPI Works**:
```
[Low Traffic]
Packet → IRQ → Process → Re-enable IRQ

[High Traffic]
Packet → IRQ → Disable IRQ → Switch to POLLING mode
    ↓
  Poll loop: Process batch of packets
    ↓
  More packets? → Continue polling
    ↓
  No packets? → Re-enable IRQ, return to interrupt mode
```

**Code Flow**:
```c
// 1. Driver IRQ handler
static irqreturn_t nic_interrupt(int irq, void *data)
{
    struct nic_priv *priv = data;

    // Disable NIC interrupts at hardware level
    nic_disable_irq(priv);

    // Schedule NAPI poll (raises NET_RX_SOFTIRQ)
    napi_schedule(&priv->napi);

    return IRQ_HANDLED;
}

// 2. Driver poll function (runs in softirq context)
static int nic_poll(struct napi_struct *napi, int budget)
{
    struct nic_priv *priv = container_of(napi, struct nic_priv, napi);
    int work_done = 0;

    // Process up to 'budget' packets
    while (work_done < budget) {
        struct sk_buff *skb = nic_get_rx_packet(priv);
        if (!skb)
            break;  // No more packets

        napi_gro_receive(napi, skb);
        work_done++;
    }

    // If processed less than budget, we're done
    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        nic_enable_irq(priv);  // Re-enable interrupts
    }
    // else: still more packets, will be polled again

    return work_done;
}
```

**Benefits**:
- **Interrupt mitigation**: One interrupt triggers processing of many packets
- **Better cache utilization**: Process packets in batch
- **Automatic load adaptation**: Switches between interrupt and polling mode
- **Fair scheduling**: Budget prevents one device from monopolizing CPU

**Configuration**:
```bash
# NAPI budget (packets per poll)
sysctl net.core.netdev_budget  # default: 300

# NAPI weight (max packets per device per poll)
# Set during driver initialization: netif_napi_add(dev, napi, poll_func, weight)
```

---

## Receive-Side Optimizations

### GRO (Generic Receive Offload)

**Purpose**: Merge multiple small packets into one large packet before protocol processing

**Example**:
```
Without GRO:
  10 × 1500-byte TCP packets
  → 10 × ip_rcv() calls
  → 10 × tcp_v4_rcv() calls
  → 10 × socket processing
  = High per-packet overhead

With GRO:
  10 × 1500-byte TCP packets
  → Merged into 1 × 15000-byte packet
  → 1 × ip_rcv() call
  → 1 × tcp_v4_rcv() call
  → 1 × socket processing
  = 10× less overhead!
```

**How GRO Works**:
```c
void napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
{
    // 1. Try to merge with existing GRO flow
    skb = dev_gro_receive(napi, skb);
    if (!skb)
        return;  // Successfully merged, done

    // 2. Not merged: pass up the stack
    netif_receive_skb_internal(skb);
}

// GRO merge logic
static struct sk_buff *dev_gro_receive(struct napi_struct *napi,
                                       struct sk_buff *skb)
{
    struct list_head *head = &napi->gro_hash[hash].list;
    struct sk_buff *p;

    // Look for matching flow in GRO list
    list_for_each_entry(p, head, list) {
        // Can these packets merge?
        if (same_flow(p, skb) &&  // same TCP connection
            can_merge(p, skb)) {  // sequential, no gaps

            // Merge skb into p
            merge_packet_data(p, skb);
            update_headers(p);
            kfree_skb(skb);  // Free the merged packet
            return NULL;      // Merged successfully
        }
    }

    // No match found: add as new GRO flow
    list_add(&skb->list, head);
    return skb;
}
```

**GRO Flush**:
- At end of NAPI poll: `napi_gro_flush()`
- Timeout: Old flows are flushed even if no new packets
- Results in `netif_receive_skb()` calls for merged packets

**GRO Matching Criteria** (for TCP):
1. Same protocol (TCP)
2. Same IP addresses (src + dst)
3. Same TCP ports (src + dst)
4. Sequential TCP sequence numbers
5. No TCP flags except ACK
6. Same TCP timestamp options

**View GRO Status**:
```bash
# Check if GRO is enabled
ethtool -k eth0 | grep generic-receive-offload

# Enable/disable GRO
ethtool -K eth0 gro on
ethtool -K eth0 gro off
```

### LRO (Large Receive Offload)

**Older, hardware-specific version of GRO**
- NIC hardware merges packets (not software)
- Less flexible than GRO
- GRO is preferred (works for forwarded packets too)

---

## Multi-Queue & CPU Distribution

### RSS (Receive Side Scaling) - Hardware

**Purpose**: Distribute incoming packets across multiple RX queues (NIC hardware)

**How It Works**:
```
Packet arrives at NIC
    ↓
NIC computes hash:
    hash = hash_function(src_ip, dst_ip, src_port, dst_port)
    ↓
queue_num = hash % num_rx_queues
    ↓
DMA packet to Ring Buffer of queue_num
    ↓
IRQ on CPU affined to queue_num
```

**Hash Function**: Toeplitz hash (standardized)

**Benefits**:
- Parallel packet processing across CPUs
- Each CPU has its own RX queue → no lock contention
- Same flow always goes to same CPU → good cache locality

**Configuration**:
```bash
# View RSS settings
ethtool -x eth0

# View number of RX queues
ethtool -l eth0
# Output:
# Combined:   4
# RX:         4
# TX:         4

# Set number of RX queues
ethtool -L eth0 rx 8

# View RSS hash key and indirection table
ethtool -x eth0

# Set custom indirection table
ethtool -X eth0 equal 4  # distribute equally across 4 queues
```

**Interrupt Affinity**:
```bash
# Check IRQ affinity
cat /proc/interrupts | grep eth0
# 50: eth0-rx-0
# 51: eth0-rx-1
# 52: eth0-rx-2
# 53: eth0-rx-3

# Set IRQ affinity (which CPUs handle which queue)
echo 1 > /proc/irq/50/smp_affinity  # CPU 0
echo 2 > /proc/irq/51/smp_affinity  # CPU 1
echo 4 > /proc/irq/52/smp_affinity  # CPU 2
echo 8 > /proc/irq/53/smp_affinity  # CPU 3
```

### RPS (Receive Packet Steering) - Software

**Purpose**: Software-based RSS for NICs that don't have multi-queue support

**How It Works**:
```
Packet received on single RX queue
    ↓
Driver calls netif_receive_skb()
    ↓
RPS: Compute hash (same as RSS)
    ↓
Enqueue to per-CPU backlog queue
    ↓
Raise NET_RX_SOFTIRQ on target CPU
    ↓
Target CPU processes packet
```

**Code Flow**:
```c
// In __netif_receive_skb_core()
if (rps_enabled) {
    int cpu = get_rps_cpu(skb->dev, skb, &rflow);

    if (cpu >= 0 && cpu != smp_processor_id()) {
        // Enqueue to remote CPU
        enqueue_to_backlog(skb, cpu, &rflow->last_qtail);
        return NET_RX_SUCCESS;
    }
}
// else: process on current CPU
```

**Configuration**:
```bash
# Enable RPS on eth0 RX queue 0
# Bitmask of CPUs to use (f = 1111 = CPUs 0-3)
echo f > /sys/class/net/eth0/queues/rx-0/rps_cpus

# View current RPS configuration
cat /sys/class/net/eth0/queues/rx-0/rps_cpus

# Increase flow table size (more concurrent flows)
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 2048 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

### RFS (Receive Flow Steering)

**Purpose**: Extend RPS to process packets on the CPU where application is running

**Why**: Better cache locality - if application on CPU 2 has socket, process packets on CPU 2

**How It Works**:
```
Application calls recv() on CPU 2
    ↓
Kernel records: This flow should be processed on CPU 2
    ↓
Packet arrives for this flow
    ↓
RFS: Lookup flow, find CPU 2
    ↓
Steer packet to CPU 2
```

**Benefits**:
- Data is processed on same CPU where application runs
- Better cache hit rate
- Reduced cache line bouncing

**Configuration**:
```bash
# Enable RFS (requires RPS)
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 2048 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

### aRFS (Accelerated RFS)

**Hardware-assisted RFS** - NIC programs hardware filters based on RFS decisions

---

## Transmit-Side Optimizations

### GSO (Generic Segmentation Offload)

**Purpose**: Delay packet segmentation until just before transmission

**Example**:
```
Without GSO:
  Application sends 15000 bytes
  → TCP segments into 10 × 1500-byte packets
  → 10 × ip_output() calls
  → 10 × driver transmit calls

With GSO:
  Application sends 15000 bytes
  → Keep as single 15000-byte "super-packet"
  → 1 × ip_output() call
  → Driver segments into 10 × 1500-byte packets just before TX
```

**Benefits**:
- Reduce per-packet processing overhead
- Better CPU cache utilization
- Protocol processing happens once for large packet

**Code Location**: Segmentation done in `dev_hard_start_xmit()` or `__dev_queue_xmit()`

### TSO (TCP Segmentation Offload)

**Purpose**: NIC hardware does TCP segmentation

**Example**:
```
Software creates 15000-byte TCP "super-segment"
    ↓
Pass to NIC driver
    ↓
NIC segments into 10 × 1500-byte packets
    ↓
NIC updates TCP headers (seq numbers)
    ↓
NIC calculates checksums
    ↓
Transmit on wire
```

**Benefits**:
- Offload CPU work to NIC hardware
- Even better performance than GSO

**Configuration**:
```bash
# Check TSO status
ethtool -k eth0 | grep tcp-segmentation-offload

# Enable/disable TSO
ethtool -K eth0 tso on
ethtool -K eth0 tso off
```

### UFO (UDP Fragmentation Offload)

**Similar to TSO but for UDP**
- Less common, deprecated in newer kernels

### XPS (Transmit Packet Steering)

**Purpose**: Select TX queue based on CPU

**How It Works**:
```
Application on CPU 2 sends packet
    ↓
XPS: Use TX queue associated with CPU 2
    ↓
Reduces lock contention
    ↓
Better cache locality
```

**Configuration**:
```bash
# Set XPS for TX queue 0 to use CPU 0
echo 1 > /sys/class/net/eth0/queues/tx-0/xps_cpus

# Set XPS for TX queue 1 to use CPU 1
echo 2 > /sys/class/net/eth0/queues/tx-1/xps_cpus
```

---

## Checksum Offloading

### RX Checksum Offload

**Purpose**: NIC validates checksums, not CPU

```
Packet arrives
    ↓
NIC validates:
  - Ethernet FCS (always)
  - IP header checksum
  - TCP/UDP checksum
    ↓
Sets skb->ip_summed = CHECKSUM_UNNECESSARY
    ↓
Kernel skips checksum validation
```

### TX Checksum Offload

**Purpose**: NIC calculates checksums

```
Kernel builds packet
    ↓
Leaves checksum fields empty
    ↓
Sets skb->ip_summed = CHECKSUM_PARTIAL
    ↓
NIC calculates and fills checksums
```

**Configuration**:
```bash
# View checksum offload status
ethtool -k eth0 | grep checksum

# Enable/disable
ethtool -K eth0 rx-checksum on
ethtool -K eth0 tx-checksum-ipv4 on
```

---

## Zero-Copy Techniques

### sendfile() System Call

**Purpose**: Transfer data from file to socket without copying to userspace

```
Traditional send():
  Disk → Kernel buffer → Userspace buffer → Kernel socket buffer → NIC

sendfile():
  Disk → Kernel buffer → Kernel socket buffer → NIC
  (No userspace copy!)
```

**Usage**:
```c
// Send file to socket
sendfile(socket_fd, file_fd, NULL, file_size);
```

### MSG_ZEROCOPY

**Purpose**: Avoid copying userspace buffer to kernel

```c
// Send with zero-copy
send(sock, buffer, size, MSG_ZEROCOPY);
```

**How**: Uses get_user_pages() to pin userspace memory, NIC DMAs directly from it

**Caveat**: Application must wait for TX completion before modifying buffer

---

## Busy Polling

### Kernel Busy Poll

**Purpose**: Application polls for packets instead of blocking

**Use Case**: Ultra-low latency applications

```c
// Set socket to busy-poll mode
int busy_poll = 50;  // microseconds
setsockopt(sock, SOL_SOCKET, SO_BUSY_POLL, &busy_poll, sizeof(busy_poll));
```

**How**: When application calls `recv()`, kernel polls NIC for packets instead of sleeping

**Trade-off**: Lower latency but higher CPU usage

---

## Feature Interactions

### RX Path With All Features

```
Packet arrives at NIC
    ↓
[RSS] NIC selects RX queue based on hash → DMA to ring buffer
    ↓
[IRQ + NAPI] IRQ on affined CPU → Switch to polling
    ↓
[GRO] Driver polls packets → Merge into larger packets
    ↓
[RX Checksum] NIC validated checksums → skip software validation
    ↓
[RPS/RFS] Steer to CPU where application runs
    ↓
Protocol processing → Socket → Application
```

### TX Path With All Features

```
Application sends data
    ↓
[GSO] Kernel keeps as large "super-packet"
    ↓
[XPS] Select TX queue based on CPU
    ↓
[TSO] NIC segments into MTU-sized packets
    ↓
[TX Checksum] NIC calculates checksums
    ↓
Transmit on wire
```

---

## Performance Tuning Summary

### For High Throughput

```bash
# Enable all offloads
ethtool -K eth0 gro on
ethtool -K eth0 tso on
ethtool -K eth0 gso on
ethtool -K eth0 rx-checksum on
ethtool -K eth0 tx-checksum-ipv4 on

# Increase ring buffer size
ethtool -G eth0 rx 4096 tx 4096

# Use multiple queues
ethtool -L eth0 combined 8

# Configure RSS
ethtool -X eth0 equal 8

# Increase socket buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
```

### For Low Latency

```bash
# Disable some batching
ethtool -C eth0 rx-usecs 0  # reduce interrupt coalescing

# Enable busy polling
sysctl -w net.core.busy_poll=50
sysctl -w net.core.busy_read=50

# Pin interrupts to specific CPUs
# Use CPU isolation (isolcpus kernel parameter)
```

### View Current Settings

```bash
# All offload features
ethtool -k eth0

# Ring buffer sizes
ethtool -g eth0

# Interrupt coalescing
ethtool -c eth0

# Queue configuration
ethtool -l eth0

# Statistics
ethtool -S eth0
```

---

## Glossary

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **NAPI** | New API | Interrupt mitigation via polling |
| **GRO** | Generic Receive Offload | Software packet merging (RX) |
| **LRO** | Large Receive Offload | Hardware packet merging (RX) |
| **GSO** | Generic Segmentation Offload | Software packet segmentation (TX) |
| **TSO** | TCP Segmentation Offload | Hardware TCP segmentation (TX) |
| **UFO** | UDP Fragmentation Offload | Hardware UDP fragmentation (TX) |
| **RSS** | Receive Side Scaling | Hardware multi-queue distribution |
| **RPS** | Receive Packet Steering | Software multi-CPU distribution |
| **RFS** | Receive Flow Steering | CPU-aware packet steering |
| **aRFS** | Accelerated RFS | Hardware-assisted RFS |
| **XPS** | Transmit Packet Steering | TX queue selection by CPU |

---

## Summary

These optimizations work together to:
1. **Reduce per-packet overhead** (GRO, GSO, TSO)
2. **Distribute work across CPUs** (RSS, RPS, RFS, XPS)
3. **Offload work to hardware** (TSO, checksum offload)
4. **Reduce interrupts** (NAPI, interrupt coalescing)
5. **Avoid memory copies** (zero-copy techniques)

Understanding these features is critical for:
- High-performance networking
- Network troubleshooting
- Game design (showing optimizations as "power-ups"!)
