# Kernel Duel - PvP Magic Combat System

> A competitive wizard duel game where the wand is a Linux kernel, magic is packets, and iptables configuration is your defense strategy.

## Core Concept

**Your Wand = Your Linux Kernel**

Players are wizards who cast magic (send packets) at each other. Each player's wand processes incoming magic using kernel-like rules. Configure your defenses wisely, manage your magic essence, and destroy your opponent's wand!

---

## Core Mechanics Mapping

### The Wand (Kernel)

```
┌────────────────────────────────────────┐
│         YOUR WAND (KERNEL)             │
├────────────────────────────────────────┤
│  Health: ████████░░ 80/100            │
│  (Kernel stability)                    │
├────────────────────────────────────────┤
│  Magic Essence Buffer: 7/10            │
│  [🔥][🔥][💧][⚡][💧][🌿][⚡][ ][ ][ ]  │
│  (Receive queue / sk_buff)             │
├────────────────────────────────────────┤
│  Defense Rules (iptables):             │
│  ✓ Block all 🔥 Fire magic            │
│  ✓ Accept 💧 Water magic              │
│  ✓ Redirect ⚡ Lightning → counter    │
│  ✗ No rule for 🌿 Nature              │
└────────────────────────────────────────┘
```

**Wand Components**:
- **Health (HP)**: Wand integrity (100 max)
- **Magic Essence Buffer**: Incoming magic queue (10 max)
- **Defense Configuration**: Your iptables rules
- **Processing Power**: CPU cycles for rule evaluation

### Magic Types = Packet Types

| Magic Element | Kernel Equivalent | Color |
|---------------|-------------------|-------|
| 🔥 **Fire** | Protocol type 0x01 (ICMP) | Red |
| 💧 **Water** | Protocol type 0x06 (TCP) | Blue |
| ⚡ **Lightning** | Protocol type 0x11 (UDP) | Yellow |
| 🌿 **Nature** | Protocol type 0x08 (Custom) | Green |
| 🧊 **Ice** | Protocol type 0x09 (Custom) | Cyan |
| 🌑 **Dark** | Protocol type 0x0A (Custom) | Purple |
| ✨ **Light** | Protocol type 0x0B (Custom) | White |

**Mixed Magic** (like your ice+fire example):
- Multi-protocol packets (like VLAN tagged, encapsulated)
- Requires more complex rules to handle
- Example: 🧊🔥 = Ice+Fire hybrid (harder to filter)

---

## The Netfilter Hook System in Gameplay

### Pre-Routing Hook (First Defense Layer)

**When**: Magic arrives at your wand, BEFORE you decide what to do with it

**In Kernel Terms**: `PREROUTING` hook in netfilter

**Game Mechanic**:
```
Enemy casts: 🔥🔥💧 (Fire, Fire, Water)
    ↓
Your PREROUTING Rules:
┌────────────────────────────────────┐
│ Rule 1: If 🔥 Fire → DROP          │  ✓ Matches!
│ Rule 2: If 💧 Water → ACCEPT       │
│ Rule 3: If ⚡ Lightning → REDIRECT │
└────────────────────────────────────┘
    ↓
Result:
- 🔥 DROPPED (blocked, no damage, no essence consumed)
- 🔥 DROPPED
- 💧 ACCEPTED → Goes to Magic Essence Buffer
```

**Strategy**: Configure PREROUTING to block harmful magic early
- **Pro**: Saves buffer space, prevents certain attacks
- **Con**: Uses processing power, can be bypassed with mixed magic

### Input Hook (Buffer Entry)

**When**: Magic passes PREROUTING and enters your Magic Essence Buffer

**In Kernel Terms**: `INPUT` hook

**Game Mechanic**:
```
Accepted Magic: 💧 Water
    ↓
INPUT Hook Check:
┌────────────────────────────────────┐
│ Buffer Status: 7/10 (space available) │
│ Rule: Rate limit Water to 3/turn     │
│ Current Water this turn: 2           │
└────────────────────────────────────┘
    ↓
ACCEPT → Add to buffer: [🔥][🔥][💧][⚡][💧][🌿][⚡][💧]←new
```

**If buffer full** (overflow):
```
Buffer: [🔥][🔥][💧][⚡][💧][🌿][⚡][💧][🧊][⚡] (10/10 FULL!)
    ↓
New magic arrives: 💧
    ↓
BUFFER OVERFLOW!
    ↓
Options:
1. DROP new magic (packet drop)
2. Evict oldest (queue overflow behavior)
3. Take DAMAGE (buffer overflow attack)
```

### Output Hook (Your Attacks)

**When**: You cast magic at opponent

**In Kernel Terms**: `OUTPUT` hook

**Game Mechanic**:
```
You want to cast: 🔥🔥🔥 (Triple Fire combo)
    ↓
OUTPUT Hook:
┌────────────────────────────────────┐
│ Check: Do I have essence?           │
│ Cost: 3 essence to cast            │
│ Current essence: 7                 │
└────────────────────────────────────┘
    ↓
ALLOW → Cast magic at opponent
Your essence: 7 → 4
```

### Post-Routing Hook (Final Processing)

**When**: After routing decision, before magic leaves your wand

**In Kernel Terms**: `POSTROUTING` hook (used for NAT)

**Game Mechanic - Source Transformation**:
```
You cast: 💧💧 (Water)
    ↓
POSTROUTING Rule:
┌────────────────────────────────────┐
│ Transform: 💧💧 → 🧊 (Ice)         │
│ (Like SNAT - change source)        │
└────────────────────────────────────┘
    ↓
Opponent sees: 🧊 Ice instead of 💧💧 Water
(If they blocked Water, this bypasses it!)
```

---

## Defense Configuration (iptables-like)

### Basic Rules

Players configure defense rules similar to iptables:

```
┌─────────────────────────────────────────────┐
│  DEFENSE CONFIGURATION                      │
├─────────────────────────────────────────────┤
│  PREROUTING Chain:                          │
│  1. DROP all 🔥 Fire                        │
│  2. DROP all 🌑 Dark                        │
│  3. ACCEPT 💧 Water                         │
│  4. ACCEPT ⚡ Lightning                     │
│  5. Default: ACCEPT                         │
│                                             │
│  INPUT Chain:                               │
│  1. Rate limit: Max 3 of same type/turn    │
│  2. If buffer > 8/10: DROP lowest priority │
│  3. If combo detected: ALERT               │
│                                             │
│  POSTROUTING Chain (Your Attacks):          │
│  1. Transform: 💧💧 → 🧊                    │
│  2. Duplicate: 🔥 → 🔥🔥 (if power-up)     │
└─────────────────────────────────────────────┘
```

### Advanced Rules (Connection Tracking Equivalent)

**Combo Tracking** (like conntrack):

```
Enemy casting pattern:
Turn 1: 🔥
Turn 2: 💧
Turn 3: 🌿
Turn 4: 🔥 ← Combo detected! (Fire-Water-Nature-Fire)

Your defense:
┌────────────────────────────────────┐
│ Combo Detection (conntrack):       │
│ IF pattern matches "Meteor Storm"  │
│ THEN: Block next 🔥                │
│ STATE: COMBO_DETECTED              │
└────────────────────────────────────┘
```

This is like stateful firewall rules:
```bash
# Real iptables equivalent
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m recent --name COMBO --update --seconds 60 -j DROP
```

### Trade-off System

**Your key insight about mixed magic**:

```
Scenario: You configure "Block all 🔥 Fire"

Enemy sends: 🧊🔥 (Ice+Fire mixed)
    ↓
Your PREROUTING rule:
Rule 1: DROP if contains 🔥
    ↓
MATCH! But it also has 🧊 Ice...
    ↓
Options:
A) Strict mode: DROP entire packet
   - Pro: Safe, no fire damage
   - Con: Lost beneficial Ice essence

B) Strip mode: Remove 🔥, accept 🧊
   - Pro: Get Ice essence
   - Con: PROCESSING COST (like DPI - Deep Packet Inspection)
       → Take 5 damage to wand (processing overhead!)
       → Consume 1 essence to parse

C) Accept mode: Let it through
   - Pro: No processing cost
   - Con: Take Fire damage!
```

**Game Balance**:
- Simple DROP rules: Fast, no cost, but inflexible
- DPI/Strip rules: Flexible, but expensive (damage + essence cost)
- Accept-all: No cost, but vulnerable

This mirrors real networking:
- Simple firewall rules: Fast
- Deep packet inspection: Slow, CPU intensive
- No firewall: Fast but vulnerable

---

## Magic Essence Buffer (Queue Management)

### The 10-Essence Limit

```
Magic Essence Buffer (like sk_buff receive queue):

┌─────────────────────────────────────────────┐
│ [🔥][🔥][💧][⚡][💧][🌿][⚡][ ][ ][ ]       │
│  1   2   3   4   5   6   7  8  9  10       │
│                                             │
│ Filled: 7/10                                │
│ Oldest: Position 1 (🔥 Fire)                │
│ Newest: Position 7 (⚡ Lightning)           │
└─────────────────────────────────────────────┘
```

### Queue Disciplines (qdisc) as Strategies

Different buffer management strategies:

#### 1. FIFO (First In, First Out) - Default
```
New magic arrives, buffer full → DROP new magic
- Simple
- Like pfifo qdisc
```

#### 2. Drop Oldest (Ring Buffer)
```
New magic arrives, buffer full → Evict position 1, shift left
- Always accepts new magic
- Loses oldest
```

#### 3. Priority Queue (pfifo_fast equivalent)
```
Magic has priority:
- High: ✨ Light, 🌑 Dark
- Medium: 🔥 Fire, 💧 Water
- Low: 🌿 Nature, ⚡ Lightning

Buffer full, new High priority magic arrives:
→ Evict lowest priority magic
```

#### 4. Random Early Drop (RED)
```
Buffer > 70% full: Start randomly dropping incoming magic
- Prevents full buffer
- Like RED qdisc (Random Early Detection)
```

**Configuration UI**:
```
┌─────────────────────────────────────────────┐
│  BUFFER STRATEGY                            │
├─────────────────────────────────────────────┤
│  [ ] FIFO (Simple, drop new when full)     │
│  [✓] Priority Queue (Keep important magic)  │
│  [ ] Drop Oldest (Always accept new)       │
│  [ ] RED (Prevent overflow)                │
└─────────────────────────────────────────────┘
```

---

## Casting System (Combo Magic)

### Consuming Essence in Sequence

You mentioned: "can decide to consume 1, 2, or 3 tgt and form different type of magic"

```
Your current buffer:
[🔥][💧][⚡][🌿][💧][🔥][⚡][ ][ ][ ]

Casting options (consume from LEFT to RIGHT):

1️⃣ Consume 1:
   [🔥] → Cast "Fireball"
   Remaining: [💧][⚡][🌿][💧][🔥][⚡][ ][ ][ ]

2️⃣ Consume 2:
   [🔥][💧] → Cast "Steam Blast" (Fire+Water combo)
   Remaining: [⚡][🌿][💧][🔥][⚡][ ][ ][ ][ ]

3️⃣ Consume 3:
   [🔥][💧][⚡] → Cast "Elemental Storm" (Fire+Water+Lightning)
   Remaining: [🌿][💧][🔥][⚡][ ][ ][ ][ ][ ]
```

### Combo Spell Table

| Sequence | Spell Name | Effect | Damage |
|----------|-----------|--------|---------|
| 🔥 | Fireball | Direct damage | 10 |
| 💧 | Water Splash | Heal 5 HP | -5 |
| 🔥🔥 | Inferno | Double damage | 25 |
| 💧💧 | Tsunami | AOE damage | 15 |
| 🔥💧 | Steam Blast | Bypass fire resistance | 20 |
| 💧🔥 | Boil | Different effect! | 18 |
| ⚡⚡⚡ | Lightning Storm | Multi-hit | 30 |
| 🔥💧⚡ | Elemental Chaos | Random effect | 15-40 |
| 🧊🧊 | Ice Wall | +Shield (block next) | 0 |
| 🌿🌿🌿 | Nature's Wrath | Poison DoT | 5/turn ×3 |

**Key**: Order matters! 🔥💧 ≠ 💧🔥

This is like:
- Packet payload analysis
- Sequence matching (like regex in iptables)
- Application layer processing

---

## Fake Packets (Disruption Attacks)

### The Fake Packet Strategy

**Your idea**: "User can send some fake packet magic to disrupt opponent magic combo"

```
Scenario: Opponent is building combo

Opponent's buffer:
[🔥][🔥][💧][ ][ ][ ][ ][ ][ ][ ]

They want: 🔥🔥💧⚡ for "Meteor Storm" (powerful combo)

You send: 🌿🌿🌿 (Fake/Junk magic)
    ↓
Opponent's buffer becomes:
[🔥][🔥][💧][🌿][🌿][🌿][ ][ ][ ][ ]

Now they can't complete their combo!
- They must consume the junk first, or
- Wait for buffer to fill and overflow, or
- Manually discard (costs a turn)
```

**Real Networking Equivalent**:
- **SYN Flood**: Send many fake connection requests
- **UDP Flood**: Fill buffers with junk packets
- **Slowloris**: Keep connections alive but don't complete
- **Packet fragmentation attack**: Force reassembly overhead

### Fake Packet Types

```
1. Junk Magic (NULL packets):
   🌫️ Fog - Takes buffer space, no useful essence
   Cost: 1 essence to send
   Effect: Clogs opponent buffer

2. Poison Magic (Malformed packets):
   ☠️ Poison - Looks like Fire but damages if consumed
   Cost: 2 essence
   Effect: If opponent uses it in combo, take 10 damage

3. Decoy Magic (Spoofed):
   👻 Ghost Fire - Looks like 🔥 but is actually 💧
   Cost: 3 essence
   Effect: Bypasses Fire blocks, reveals as Water when consumed

4. Fragmented Magic (IP fragments):
   💥 Shattered - Sends incomplete sequence
   Cost: 2 essence
   Effect: Opponent must wait for complete sequence or discard
```

---

## tcpdump Equivalent (Magic Inspection)

### The Inspect Mechanic

**In real networking**: `tcpdump` captures and displays packets

**In your game**: "Inspect" ability to see opponent's casting pattern

```
┌─────────────────────────────────────────────┐
│  MAGIC VISION (tcpdump)                     │
├─────────────────────────────────────────────┤
│  Cost: 1 essence per use                    │
│  Duration: 3 turns                          │
│                                             │
│  Opponent's last 5 casts:                   │
│  Turn 5: 🔥🔥   → Inferno                   │
│  Turn 6: 💧    → Water Splash              │
│  Turn 7: 🌿🌿  → Nature's Call             │
│  Turn 8: 🔥💧  → Steam Blast                │
│  Turn 9: ⚡⚡⚡ → Lightning Storm            │
│                                             │
│  Pattern detected: Prefers Lightning!       │
│  Recommendation: Add ⚡ Lightning block      │
└─────────────────────────────────────────────┘
```

**Advanced Inspection** (like Wireshark filters):
```
Filter options:
- Show only 🔥 Fire casts
- Show only combo casts (2+ elements)
- Show casts that damaged you
- Show failed casts (blocked by your rules)
```

**Stealth Mode** (Anti-detection):
```
Opponent can enable "Stealth Casting":
- Cost: 2× essence cost
- Effect: Your Magic Vision can't see their casts
- Like: Encrypted packets, VPN, Tor
```

---

## Connection Tracking (Combo State Memory)

### Tracking Opponent Combos

**In kernel**: conntrack remembers connection state (NEW, ESTABLISHED, RELATED)

**In your game**: Track opponent's combo building

```
Opponent's casting history:

Turn 1: 🔥 (State: BUILDING)
Turn 2: 🔥 (State: BUILDING, pattern: 🔥🔥)
Turn 3: 💧 (State: BUILDING, pattern: 🔥🔥💧)
Turn 4: ⚡ (State: COMPLETE, Combo: "Elemental Storm")
    ↓
Your defense triggers:
┌────────────────────────────────────┐
│ Combo State: ESTABLISHED           │
│ Next cast will be: Elemental Storm │
│ Action: Enable shield (auto)       │
└────────────────────────────────────┘
```

**Connection Tracking Table**:
```
┌──────────────────────────────────────────────────┐
│  COMBO TRACKING TABLE                            │
├──────────────────────────────────────────────────┤
│  Entry 1:                                        │
│    Pattern: 🔥🔥💧                               │
│    State: BUILDING                               │
│    Age: 2 turns                                  │
│    Prediction: Next is ⚡ (for Meteor Storm)    │
│    Auto-defense: READY (block ⚡ if completed)  │
│                                                  │
│  Entry 2:                                        │
│    Pattern: 🌿🌿                                 │
│    State: INCOMPLETE                             │
│    Age: 5 turns (TIMEOUT)                        │
│    Action: FLUSH (remove from memory)           │
└──────────────────────────────────────────────────┘
```

**Connection Tracking Limits**:
- Max 5 combo patterns tracked simultaneously
- Each entry uses 1 essence overhead
- Timeout: 5 turns of inactivity → flush entry
- Just like: `net.netfilter.nf_conntrack_max`

---

## Implementing the Game Mechanics

### Turn Structure

```
┌────────────── TURN PHASES ──────────────┐
│                                         │
│  1. RECEIVE PHASE                       │
│     - Opponent's magic arrives          │
│     - PREROUTING rules applied          │
│     - Magic enters buffer (if accepted) │
│     - INPUT rules applied               │
│                                         │
│  2. DECISION PHASE                      │
│     - View your buffer                  │
│     - Inspect opponent (optional)       │
│     - Configure defense rules           │
│                                         │
│  3. CASTING PHASE                       │
│     - Choose essence to consume (1-3)   │
│     - OUTPUT rules applied              │
│     - POSTROUTING transformation        │
│     - Cast at opponent                  │
│                                         │
│  4. RESOLUTION PHASE                    │
│     - Damage calculated                 │
│     - Status effects applied            │
│     - Buffer cleaned up                 │
│     - Turn counter ++                   │
│                                         │
└─────────────────────────────────────────┘
```

### UI Layout

```
┌────────────────────────────────────────────────────────────┐
│                    KERNEL DUEL                             │
├──────────────────────────┬─────────────────────────────────┤
│  OPPONENT                │  YOU                            │
│  Wand HP: ████░░ 40/100  │  Wand HP: ██████░░ 70/100      │
│  Buffer: ???(hidden)     │  Buffer: [🔥][💧][⚡][🌿][💧]   │
│  Last cast: ⚡⚡⚡        │          [ ][ ][ ][ ][ ]        │
├──────────────────────────┴─────────────────────────────────┤
│  BATTLE LOG                                                │
│  Turn 8: Opponent cast "Lightning Storm" - You took 30 dmg│
│  Turn 7: You cast "Steam Blast" - Opponent took 20 dmg    │
│  Turn 6: Magic Vision activated - 3 turns remaining       │
├────────────────────────────────────────────────────────────┤
│  YOUR ACTIONS                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ CAST MAGIC   │  │ CONFIGURE    │  │ INSPECT      │    │
│  │              │  │ DEFENSES     │  │ (Cost: 1)    │    │
│  │ Consume 1-3  │  │ (iptables)   │  │              │    │
│  │ essence      │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
├────────────────────────────────────────────────────────────┤
│  DEFENSE RULES (PREROUTING)                               │
│  [✓] DROP all 🔥 Fire                                     │
│  [✓] DROP all 🌑 Dark                                     │
│  [ ] Rate limit ⚡ Lightning (max 2/turn)                 │
│  [ ] REDIRECT 💧 Water → heal                            │
│  [Edit Rules]                                             │
└────────────────────────────────────────────────────────────┘
```

### Cast Magic UI

```
┌────────────────────────────────────────┐
│  CAST MAGIC                            │
├────────────────────────────────────────┤
│  Your buffer:                          │
│  [🔥][💧][⚡][🌿][💧][ ][ ][ ][ ][ ]  │
│   1   2   3   4   5  6  7  8  9  10   │
│                                        │
│  Select essence to consume:            │
│  ( ) Consume 1: [🔥]                   │
│      → Fireball (10 dmg)              │
│                                        │
│  ( ) Consume 2: [🔥][💧]               │
│      → Steam Blast (20 dmg)           │
│                                        │
│  (•) Consume 3: [🔥][💧][⚡]            │
│      → Elemental Storm (35 dmg!)      │
│                                        │
│  Remaining: [🌿][💧][ ][ ][ ][ ][ ]   │
│                                        │
│  [CAST!]  [Cancel]                    │
└────────────────────────────────────────┘
```

### Defense Configuration UI

```
┌────────────────────────────────────────────────────┐
│  DEFENSE CONFIGURATION (iptables)                  │
├────────────────────────────────────────────────────┤
│  PREROUTING Chain (First defense):                │
│  ┌──────────────────────────────────────────────┐ │
│  │ 1. IF magic is 🔥 Fire THEN DROP             │ │
│  │ 2. IF magic is 🌑 Dark THEN DROP             │ │
│  │ 3. IF magic contains 🔥 THEN STRIP (cost:5hp)│ │
│  │ 4. DEFAULT: ACCEPT                           │ │
│  └──────────────────────────────────────────────┘ │
│  [Add Rule] [Edit] [Delete]                       │
│                                                    │
│  INPUT Chain (Buffer management):                 │
│  ┌──────────────────────────────────────────────┐ │
│  │ 1. Rate limit same type: Max 3/turn          │ │
│  │ 2. Priority: ✨ > 🌑 > 🔥 > 💧 > 🌿 > ⚡      │ │
│  │ 3. Buffer > 8/10: DROP lowest priority       │ │
│  └──────────────────────────────────────────────┘ │
│  [Configure Buffer Strategy]                      │
│                                                    │
│  POSTROUTING Chain (Your attacks):                │
│  ┌──────────────────────────────────────────────┐ │
│  │ 1. Transform 💧💧 → 🧊 Ice                   │ │
│  │ 2. Duplicate 🔥 → 🔥🔥 (if power-up active)  │ │
│  └──────────────────────────────────────────────┘ │
│  [Add Transformation]                             │
│                                                    │
│  Connection Tracking:                             │
│  [✓] Track opponent combos (uses 1 essence)      │
│  [✓] Auto-shield on detected Storm combo         │
│  [ ] Log all incoming magic                       │
│                                                    │
│  [SAVE CONFIGURATION]  [Reset to Default]        │
└────────────────────────────────────────────────────┘
```

---

## Advanced Mechanics

### 1. Mixed Magic Parsing (DPI)

```
Opponent sends: 🧊🔥 (Ice+Fire mixed)

Your PREROUTING rule: "DROP if contains 🔥"

Options menu:
┌────────────────────────────────────────┐
│ Mixed magic detected!                  │
│                                        │
│ ( ) DROP entire packet                │
│     Safe, no damage                   │
│     Lost potential Ice essence        │
│                                        │
│ (•) STRIP Fire, keep Ice              │
│     Cost: 5 HP (processing)           │
│     Cost: 1 essence (parsing)         │
│     Gain: 🧊 Ice essence              │
│                                        │
│ ( ) ACCEPT both                       │
│     Gain: 🧊🔥 mixed essence          │
│     Risk: Fire damage if consumed     │
│                                        │
│ [Choose]                              │
└────────────────────────────────────────┘
```

**Game balance**:
- Simple rules: Fast, cheap, but rigid
- DPI/Strip: Flexible, but expensive
- Accept-all: Risky but no overhead

### 2. Rate Limiting (Prevent Spam)

```
PREROUTING Rule: "Limit Fire to 2 per turn"

Turn 5:
Opponent sends: 🔥🔥🔥🔥🔥 (5× Fire)

Your defense:
Turn 5: Accept 🔥🔥 (first 2)
        DROP 🔥🔥🔥 (exceeded limit)

Buffer: [🔥][🔥] (only 2 accepted)
```

**Real kernel equivalent**:
```bash
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

### 3. Combo Detection & Auto-Shield

```
Opponent's pattern:
Turn 5: 🔥
Turn 6: 🔥
Turn 7: 💧
Turn 8: ⚡ ← COMBO COMPLETE! "Elemental Storm"

Your conntrack system:
┌────────────────────────────────────┐
│ ALERT: Elemental Storm detected!  │
│ Auto-activating Ice Shield...     │
│ Cost: 1 essence                   │
│ Effect: Block next attack         │
└────────────────────────────────────┘

Result: Opponent's attack BLOCKED!
```

### 4. Stealth Casting (Encryption)

```
Your option: Enable "Stealth Mode"
- Cost: 2× essence for all casts
- Effect: Opponent's Inspect can't see your casts
- Duration: Until disabled

Like: VPN, encrypted packets, Tor
```

### 5. Reflection / Redirection (DNAT)

```
PREROUTING Rule: "REDIRECT ⚡ Lightning → reflect back"

Opponent casts: ⚡⚡⚡ Lightning Storm (30 dmg)
    ↓
Your REDIRECT rule triggers:
    ↓
Opponent takes: 30 dmg (their own attack!)
Your HP: No change
Cost: 2 essence (redirect processing)
```

**Real kernel equivalent**:
```bash
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
```

---

## Win Conditions

### Destroy Opponent's Wand

**Wand HP reaches 0**:
- Direct damage from spells
- Buffer overflow damage
- Processing overhead damage (DPI)
- Connection tracking overflow

### Alternate Victory Conditions

1. **Wand Corruption** (like kernel panic):
   - Opponent's buffer overflows 3 times in a row
   - System becomes unstable
   - Automatic loss

2. **Essence Starvation**:
   - Cannot cast for 5 consecutive turns (no essence)
   - Cannot defend effectively
   - Automatic loss

3. **Timeout**:
   - After 20 turns, higher HP wins
   - Like: Network timeout

---

## Progression & Unlockables

### Wand Upgrades (Kernel Patches)

```
Level 1: Basic Wand
- Buffer: 10 essence max
- Rules: 5 max
- No combo tracking

Level 5: Enhanced Wand
- Buffer: 15 essence max
- Rules: 10 max
- Basic combo tracking (3 patterns)

Level 10: Master Wand
- Buffer: 20 essence max
- Rules: 20 max
- Advanced combo tracking (10 patterns)
- DPI enabled
- NAPI mode (faster processing)
```

### Unlockable Rules

```
Starter rules:
- Simple DROP
- Simple ACCEPT

Unlock at Level 3:
- Rate limiting
- Priority queue

Unlock at Level 5:
- REDIRECT (reflect)
- STRIP (DPI)
- Combo tracking

Unlock at Level 10:
- Custom transformations
- Auto-shield
- Stealth mode
```

### Magic Types Unlock

```
Starter: 🔥 Fire, 💧 Water, ⚡ Lightning
Level 5: 🌿 Nature, 🧊 Ice
Level 10: 🌑 Dark, ✨ Light
Level 15: 👻 Ghost (stealth), ☠️ Poison (fake)
```

---

## Example Battle Scenario

```
Turn 1:
YOU: Configure "DROP 🔥", "ACCEPT 💧"
OPPONENT: Cast 🔥 → Your rule blocks (no dmg)
Your buffer: [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]

Turn 2:
OPPONENT: Cast 💧💧 → Accepted
Your buffer: [💧][💧][ ][ ][ ][ ][ ][ ][ ][ ]
YOU: Not enough essence to cast (need at least 1)

Turn 3:
OPPONENT: Cast ⚡🌿 → Both accepted
Your buffer: [💧][💧][⚡][🌿][ ][ ][ ][ ][ ][ ]
YOU: Cast 💧💧 "Tsunami" (15 dmg to opponent)
Your buffer: [⚡][🌿][ ][ ][ ][ ][ ][ ][ ][ ]
Opponent HP: 100 → 85

Turn 4:
OPPONENT: Inspects your buffer (sees [⚡][🌿])
OPPONENT: Configures "DROP ⚡" (predicting your next cast)
OPPONENT: Cast 🔥🔥🔥🔥 (4× Fire spam!)
Your buffer: [⚡][🌿][ ][ ][ ][ ][ ][ ][ ][ ] (all Fire blocked!)

YOU: Cast ⚡🌿 "Nature's Shock" (18 dmg)
    ↓
OPPONENT's rule blocks ⚡!
Cast FAILED
You lose your turn!

Turn 5:
YOU: Change strategy - add "Transform 🌿 → 💧"
OPPONENT: Cast 🧊🔥 (mixed Ice+Fire)
Your "DROP 🔥" rule:
  Option: STRIP Fire (cost 5 HP)
  Result: [⚡][🌿][🧊][ ][ ][ ][ ][ ][ ][ ]
  Your HP: 100 → 95 (processing cost)

YOU: Configure POSTROUTING "Transform 🌿 → 💧"
YOU: Cast 🌿 → Transforms to 💧 → Opponent takes 10 dmg
    (Bypassed their Lightning block!)
Opponent HP: 85 → 75

... battle continues!
```

---

## Implementation Roadmap

### Phase 1: Core Mechanics (MVP)
- [x] Basic wand (HP, buffer)
- [x] 3 magic types (Fire, Water, Lightning)
- [x] Simple PREROUTING rules (DROP/ACCEPT)
- [x] 1-2-3 casting system
- [x] Turn-based combat
- [x] Basic UI

### Phase 2: Defense System
- [ ] All netfilter hooks (PREROUTING, INPUT, OUTPUT, POSTROUTING)
- [ ] Rate limiting
- [ ] Priority queue
- [ ] Buffer strategies (FIFO, Priority, RED)

### Phase 3: Advanced Features
- [ ] Mixed magic (DPI, STRIP)
- [ ] Combo tracking (conntrack)
- [ ] Inspect (tcpdump)
- [ ] Transformations (NAT)
- [ ] Fake packets (junk, poison, decoy)

### Phase 4: Progression
- [ ] Wand upgrades
- [ ] Unlock system
- [ ] New magic types
- [ ] Advanced rules

### Phase 5: Multiplayer
- [ ] PvP matchmaking
- [ ] Ranked mode
- [ ] Spectator mode
- [ ] Replay system

---

## Summary: Game ↔ Kernel Mapping

| Game Concept | Kernel Equivalent | Mechanic |
|--------------|-------------------|----------|
| Wand | Linux kernel | Your processing system |
| Wand HP | System stability | 0 HP = kernel panic |
| Magic | Network packets | Data being transmitted |
| Magic type | Protocol type | IPv4, TCP, UDP, etc. |
| Essence buffer | sk_buff queue | Receive queue (10 max) |
| PREROUTING rules | iptables PREROUTING | First defense layer |
| INPUT rules | iptables INPUT | Buffer entry control |
| OUTPUT rules | iptables OUTPUT | Cast validation |
| POSTROUTING rules | iptables POSTROUTING | Transform/NAT |
| Combo tracking | conntrack | Connection state memory |
| Inspect | tcpdump | Packet inspection |
| Mixed magic | Multi-protocol packets | Requires DPI |
| DPI/Strip | Deep packet inspection | Expensive but flexible |
| Rate limiting | iptables limit | Prevent spam |
| Buffer overflow | Queue overflow | Take damage |
| Fake packets | SYN flood, junk | Disrupt combos |
| Reflection | REDIRECT/DNAT | Bounce attacks back |
| Stealth | Encryption/VPN | Hide your casts |
| Priority queue | pfifo_fast qdisc | Sort by importance |

---

This game teaches real networking concepts through engaging PvP combat! Players learn:
- How firewalls work (iptables)
- Buffer management (queues)
- Protocol handling
- NAT and transformations
- DoS attacks and defense
- Network inspection (tcpdump)
- Performance trade-offs (DPI cost)

**You've created a brilliant educational game concept!** 🎮✨🔥💧⚡
