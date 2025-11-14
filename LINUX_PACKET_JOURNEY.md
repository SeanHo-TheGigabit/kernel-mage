# Linux Kernel Networking Documentation

> Technical reference for understanding Linux network stack packet flow - foundation for educational game development

## Documentation Structure

### 📚 Technical Reference (Kernel Internals)

Located in `docs/technical/`:

- **[RX Path](docs/technical/01-RX-Path.md)** - Complete packet receive flow
- **[Network Optimizations](docs/technical/02-Network-Optimizations.md)** - NAPI, GRO, RSS, RPS, TSO
- **[TX Path](docs/technical/03-TX-Path.md)** - Complete packet transmit flow
- **[Netfilter & Routing](docs/technical/04-Netfilter-and-Routing.md)** - Different packet paths, NAT, connection tracking

### 🎮 Game Design (Kernel Duel)

Located in `docs/game/`:

- **[Core Mechanics](docs/game/core-mechanics.md)** ⭐ **START HERE**
  - Clear values and rules
  - Resource management (HP, Essence, CPU)
  - Turn structure (real-time incoming essence)
  - Defense rules (iptables-like configuration)
  - Balance mechanisms

- **[Magic Combos](docs/game/magic-combos.md)** - Complete spell reference
  - All 76 spell combinations
  - Damage values and special effects
  - Combo building strategies
  - Tier list and meta analysis

- **[Balance Analysis](docs/game/balance-analysis.md)** - Strategy deep-dive
  - 10 attack/defense strategies analyzed
  - Mathematical proof: No perfect build exists
  - Counter-strategy matrix
  - Skill expression mechanics

### 📝 Drafts & Discussions

Located in `docs/drafts/`:

- **kernel-mage-adventure.md** - Single-player adventure game concept (alternative design)
- **kernel-duel-initial-design.md** - Initial PvP design (superseded by docs/game/)

---

## Quick Start - Game Design

### Core Concept

**Kernel Duel** - PvP wizard combat where:
- Your wand = Linux kernel (you configure iptables-like rules)
- Magic = Network packets (7 types: fire🔥, water💧, lightning⚡, nature🌿, ice🧊, dark🌑, light✨)
- Essence buffer = Socket buffer (10 max capacity)
- Win condition = Destroy opponent's wand (reduce HP to 0)

### Key Mechanics

**Real-time Pressure**:
- 3 magic essence arrive per turn (automatic)
- Buffer capacity: 10 max
- Must cast spells or take overflow damage (10 HP per overflow)

**Defense Configuration (iptables)**:
- PREROUTING: Filter incoming magic
- INPUT: Buffer management strategy
- POSTROUTING: Transform outgoing attacks
- Each rule costs CPU per turn

**Resource Triangle**:
```
     Defense (CPU cost)
        /    \
       /      \
      /        \
Essence Gain ←→ Attack Power
```

**Balance**: Perfect defense → No essence → Cannot attack → Lose by starvation (5 turns)

### Read in Order

1. **[Core Mechanics](docs/game/core-mechanics.md)** - Understand the rules
2. **[Magic Combos](docs/game/magic-combos.md)** - Learn the spells
3. **[Balance Analysis](docs/game/balance-analysis.md)** - Study strategies

---

## Technical Reference - Packet Flow

### Receive Path (Simplified)

```
Physical Wire
    ↓
NIC Hardware (DMA to ring buffer)
    ↓
Driver (NAPI, GRO)
    ↓
__netif_receive_skb_core() [Protocol demultiplexing]
    ↓
ip_rcv() [IP validation]
    ↓
Netfilter PREROUTING [DNAT, marking]
    ↓
Routing Decision
    ↓
    ├─→ ip_local_deliver() → INPUT → TCP/UDP → Socket → App
    └─→ ip_forward() → FORWARD → POSTROUTING → TX
```

### Transmit Path (Simplified)

```
Application
    ↓
Socket → TCP/UDP
    ↓
IP layer (build headers)
    ↓
Netfilter OUTPUT [Filtering]
    ↓
Routing (find output interface)
    ↓
Netfilter POSTROUTING [SNAT/MASQUERADE]
    ↓
ARP resolution → L2 header
    ↓
Traffic Control (QoS)
    ↓
Driver → NIC → Wire
```

### Key Insights

1. **No separate "L2/L3 stages"** - Protocol demultiplexing happens directly
2. **5 Netfilter hooks** - PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING
3. **Routing decides path** - Local delivery vs forwarding
4. **Connection tracking** - Enables stateful firewall and NAT
5. **Optimizations everywhere** - NAPI, GRO, RSS, TSO, etc.

---

## Game ↔ Kernel Mapping

| Game Concept | Kernel Equivalent | Purpose |
|--------------|-------------------|---------|
| Wand HP | System stability | Win condition |
| Essence buffer (10 max) | sk_buff receive queue | Resource management |
| Magic types | Protocol types | Different characteristics |
| PREROUTING rules | iptables PREROUTING | First defense layer |
| INPUT rules | Buffer management | Queue discipline |
| POSTROUTING rules | iptables POSTROUTING | NAT/transformation |
| CPU resource | Processing power | Action limits |
| Combo casting (1-3) | Packet sequence | Skill expression |
| Mixed magic | Multi-protocol packets | Complexity |
| Inspect | tcpdump | Information gathering |
| Overflow damage | Buffer overflow | Pressure mechanic |
| Starvation loss | Resource exhaustion | Anti-turtle |

---

## Why This Design Works

### Educational Value

Players learn real networking concepts:
- ✅ **iptables configuration** - Defense rules
- ✅ **Buffer management** - Queue overflow
- ✅ **NAT/transformation** - POSTROUTING magic changes
- ✅ **Connection tracking** - Combo detection
- ✅ **DoS defense** - Overflow attacks
- ✅ **Resource trade-offs** - CPU vs defense vs offense

### Competitive Balance

No dominant strategy:
- Perfect defense → Starvation loss (no essence)
- Perfect offense → Takes too much damage
- CPU limits → Cannot do everything
- Real-time pressure → Must make decisions
- Skill expression → Adaptation and combos matter

### Game Design Principles

1. **Clear values** - All numbers specified
2. **Trade-offs** - Every choice has a cost
3. **Counterplay** - Every strategy has counters
4. **Skill ceiling** - Mastery through adaptation
5. **Time pressure** - Real-time incoming essence
6. **Resource management** - HP, Essence, CPU triangle

---

## Implementation Status

### ✅ Complete & Playable!

**Game is fully implemented in Python!** See `game/` directory.

#### Phase 1 - Core Systems
- ✅ Data structures (kernel-style with dataclasses)
- ✅ Spell database (all 76 combos)
- ✅ 6 AI opponents (Novice → Grand Archmage)

#### Phase 2 - Game Engine & UI
- ✅ Game engine (pure logic, no UI dependencies)
- ✅ Rules engine (PREROUTING/INPUT/POSTROUTING filtering)
- ✅ Magic generation (3/turn automatic)
- ✅ Buffer management with overflow damage
- ✅ Terminal UI (completely separate from engine)
- ✅ Interactive spell casting and rule configuration

**How to play:**
```bash
cd game
python3 terminal_ui.py
```

### 🎯 Next Steps (Optional Enhancements)

1. **Multiplayer** - Network protocol (engine is ready!)
2. **Godot Client** - Visual UI connecting to Python server
3. **Balance Tweaks** - Based on playtesting
4. **More AI** - Tournament mode, different strategies
5. **Replay System** - Save/watch battles

---

## Tools & Resources

### For Understanding Linux Networking

```bash
# Packet capture
tcpdump -i eth0 -nn -vv

# Network stats
ip -s link show eth0

# Routing tables
ip route show

# Netfilter rules
iptables -L -v -n

# Connection tracking
conntrack -L

# NIC features
ethtool -k eth0
```

### Kernel Source Locations

- `net/core/dev.c` - Core networking, `netif_receive_skb()`
- `net/ipv4/ip_input.c` - IP receive, `ip_rcv()`
- `net/ipv4/ip_output.c` - IP transmit
- `net/netfilter/` - Netfilter framework
- `net/sched/` - Traffic control (QoS)

---

## Contributing

This documentation is designed to be:
- **Accurate** - Based on actual kernel source code
- **Educational** - Clear explanations with examples
- **Practical** - Useful for game development

Found errors or have suggestions? Feedback welcome!

---

## License

Documentation created for educational purposes. Linux kernel is GPL-2.0.

---

**Game Design**: Competitive wizard duels teaching real networking! ⚔️🔥💧⚡
