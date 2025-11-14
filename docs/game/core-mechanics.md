# Kernel Duel - Core Mechanics

> Clear values and game rules for the PvP wizard duel game

## Win Condition

**Destroy opponent's Wand HP to 0**

---

## Core Resources

### Wand (Your Kernel)

| Property | Value | Notes |
|----------|-------|-------|
| **Max HP** | 100 | Wand health, 0 = defeat |
| **Starting HP** | 100 | Both players start equal |
| **HP Regeneration** | 0/turn | No passive regen |

### Essence Buffer (Receive Queue)

| Property | Value | Notes |
|----------|-------|-------|
| **Max Capacity** | 10 essence | Like sk_buff queue limit |
| **Starting Buffer** | 0 (empty) | Must collect essence to cast |
| **Overflow Damage** | 10 HP | If buffer full, take damage per overflow |

### Processing Power (CPU)

| Property | Value | Notes |
|----------|-------|-------|
| **Max CPU** | 100/turn | Available processing power |
| **Regeneration** | 100/turn | Full CPU refresh each turn |
| **Usage** | Varies by action | See actions below |

---

## Turn Structure (Real-time Incoming)

**KEY MECHANIC**: Magic essence arrives **constantly** at a fixed rate.

### Phase 1: Incoming (Automatic - 3 seconds)

**Enemy Magic Rate**: 3 essence/turn (automatic)
- Enemy sends 3 random magic types each turn
- You CANNOT prevent them from sending
- Your defenses only filter what enters YOUR buffer

**Example**:
```
Turn Start:
Enemy sends: 🔥 💧 ⚡ (automatic, 3 random types)
    ↓
Your PREROUTING rules apply
    ↓
Filtered magic enters your buffer
```

**Critical**: You cannot stop the incoming rate, only filter it!

### Phase 2: Processing (5 seconds - Player Action)

**Available Actions** (can do multiple if CPU allows):

| Action | CPU Cost | Effect |
|--------|----------|--------|
| **Configure 1 Rule** | 20 CPU | Add/edit/remove defense rule |
| **Cast Spell (consume essence)** | 0 CPU | Use buffered essence to attack |
| **Inspect Enemy** | 30 CPU | See opponent's last 5 casts |
| **Discard 1 Essence** | 5 CPU | Manually remove 1 from buffer |

**Example Turn**:
```
You have 100 CPU
- Configure rule: -20 CPU (80 remaining)
- Inspect enemy: -30 CPU (50 remaining)
- Configure another rule: -20 CPU (30 remaining)
- Cast spell: 0 CPU (30 remaining, unused)
```

### Phase 3: Resolution (Automatic - 1 second)

- Damage calculated
- HP updated
- Status effects applied
- Next turn begins

**Total Turn Time**: ~9 seconds/turn

---

## Magic Types

| Element | ID | Color | Damage (solo) |
|---------|------|-------|---------------|
| 🔥 Fire | 0x01 | Red | 10 |
| 💧 Water | 0x02 | Blue | 8 (heals if consume) |
| ⚡ Lightning | 0x03 | Yellow | 12 |
| 🌿 Nature | 0x04 | Green | 6 |
| 🧊 Ice | 0x05 | Cyan | 10 |
| 🌑 Dark | 0x06 | Purple | 15 |
| ✨ Light | 0x07 | White | 12 |

---

## Defense Rules (iptables-like)

### Rule Types

#### PREROUTING Rules (First Filter)

| Rule Type | CPU Cost/turn | Effect |
|-----------|---------------|--------|
| **DROP by type** | 5 CPU | Block specific magic type |
| **DROP by source** | 10 CPU | Block all from enemy IP |
| **ACCEPT by type** | 5 CPU | Explicitly allow type |
| **RATE LIMIT** | 15 CPU | Max N of type per turn |
| **STRIP (DPI)** | 30 CPU | Parse mixed magic, extract |

**Important**: Each active rule consumes CPU **every turn**!

#### INPUT Rules (Buffer Entry)

| Rule Type | CPU Cost/turn | Effect |
|-----------|---------------|--------|
| **Priority Queue** | 10 CPU | Sort by importance |
| **Drop Oldest** | 5 CPU | FIFO eviction |
| **Drop Lowest Priority** | 10 CPU | Smart eviction |

#### POSTROUTING Rules (Your Attacks)

| Rule Type | CPU Cost/turn | Effect |
|-----------|---------------|--------|
| **Transform** | 20 CPU | Change magic type before send |
| **Duplicate** | 25 CPU | Send 2× magic |

### Rule Limits

**Max Active Rules**: 10 total (across all chains)

If you have 10 rules consuming 10 CPU each = 100 CPU/turn used
→ **No CPU left to configure new rules or inspect!**

---

## The Balance Problem & Solution

### Problem 1: "Immune Everything" Configuration

**User's Concern**: "If I DROP all enemy magic types, I'm immune!"

**Example Broken Config**:
```
PREROUTING:
☑ DROP 🔥 Fire (-5 CPU)
☑ DROP 💧 Water (-5 CPU)
☑ DROP ⚡ Lightning (-5 CPU)
☑ DROP 🌿 Nature (-5 CPU)
☑ DROP 🧊 Ice (-5 CPU)
☑ DROP 🌑 Dark (-5 CPU)
☑ DROP ✨ Light (-5 CPU)

Total: -35 CPU/turn

Result: All enemy magic blocked!
But: No essence enters buffer → Cannot attack!
```

**Solution 1: Essence Starvation Win**

**New Rule**: If you cannot cast for **5 consecutive turns**, opponent wins!

- Blocking everything = no essence = cannot attack
- Opponent wins by timeout
- Forces players to accept SOME magic

**Solution 2: Source Blocking Trade-off**

**User's Concern**: "Can block enemy IP but recovery magic routes through enemy"

**Mechanic**: Some beneficial magic comes "through" enemy route

```
DROP by source (enemy IP): -10 CPU
Effect:
- Blocks ALL enemy direct attacks ✓
- Also blocks RECOVERY magic routing through enemy network ✗
- Recovery rate: 0 HP/turn instead of 5 HP/turn

Trade-off: Safety vs sustainability
```

**Solution 3: Mixed Magic Bypass**

Enemy can send **mixed/hybrid magic**:
```
Normal: 🔥 Fire (you can DROP)
Hybrid: 🔥💧 Fire+Water mixed

If you DROP Fire:
- Normal 🔥 → Blocked
- Hybrid 🔥💧 → Gets through! (contains Water)

To block hybrid: Need STRIP rule (-30 CPU each turn!)
```

**Solution 4: CPU Exhaustion**

**Total CPU Economy**:
```
You have 100 CPU/turn

Ideal defense (block all 7 types):
- DROP Fire: -5
- DROP Water: -5
- DROP Lightning: -5
- DROP Nature: -5
- DROP Ice: -5
- DROP Dark: -5
- DROP Light: -5
Total: -35 CPU/turn

Remaining: 65 CPU

But to attack effectively, you need essence!
- Must ACCEPT at least some magic
- Must manage buffer
- May need to Inspect opponent (30 CPU)
- May need to configure counters (20 CPU/action)

If you block everything:
→ No essence
→ Cannot attack
→ Lose by starvation (5 turn rule)
```

### Problem 2: "Filter Enemy + Type = Immune but Expensive"

**User's Insight**: Filtering both enemy AND type should be costly

**Mechanic**: Compound Rules Cost More

| Rule | CPU Cost |
|------|----------|
| DROP Fire | -5 CPU |
| DROP from Enemy IP | -10 CPU |
| DROP Fire **from Enemy IP** | -25 CPU (compound!) |

**Example**:
```
User wants to block only enemy Fire:
☑ DROP Fire from Enemy IP (-25 CPU)

Result:
- Enemy Fire blocked
- Ally Fire (recovery routing through ally) still accepted
- Expensive! Only 4 such rules possible (100 CPU)
```

### Problem 3: "Too Strong Defense = No Offense Power"

**Solution**: Processing power is shared!

**Scenario**:
```
Player A: Heavy defense
- 7 DROP rules (-35 CPU)
- 1 Priority Queue (-10 CPU)
- 1 Transform (-20 CPU)
Total: -65 CPU/turn

Remaining: 35 CPU
→ Can only configure 1 rule/turn (20 CPU)
→ Cannot Inspect (need 30 CPU, only have 35)
→ Slow to adapt!

Player B: Balanced
- 2 DROP rules (-10 CPU)
- 1 ACCEPT Water (recovery) (-5 CPU)
Total: -15 CPU/turn

Remaining: 85 CPU
→ Can Inspect (30 CPU) AND configure (20 CPU) each turn
→ Fast adaptation
→ More essence (accepts more types)
→ More attack options
```

**Balance Enforced**: Defense costs offense capability!

---

## Mandatory Mechanics (Force Interaction)

### 1. Recovery Magic Routing

**Mechanic**: 30% of magic arrives via "enemy network route"

```
3 magic/turn arrive:
- 2 direct (70%)
- 1 via enemy route (30%)

If you DROP enemy IP:
→ Lose 30% of ALL incoming magic
→ Including beneficial Water (recovery)

Example:
Turn 5: Incoming 💧💧🔥
- 💧 (direct) → buffer
- 💧 (via enemy route) → blocked by enemy IP DROP
- 🔥 (direct) → blocked by Fire DROP

Result: Only 1 Water in buffer instead of 2!
```

**Trade-off**: Blocking enemy IP reduces your resource gain!

### 2. Essence Starvation Rule

**If buffer empty for 5 turns → AUTO LOSE**

Forces you to accept some magic types.

### 3. Mixed Magic Escalation

**Turns 1-5**: Enemy sends simple magic (🔥 💧 ⚡)
**Turns 6-10**: 30% chance of mixed magic (🔥💧)
**Turns 11+**: 60% chance of mixed magic

Simple DROP rules become less effective over time!

### 4. Buffer Pressure

**Incoming Rate > Buffer Capacity**

- 3 essence/turn incoming
- Buffer capacity: 10
- Must consume (cast spells) regularly or overflow

**Overflow Damage**: 10 HP per overflowed essence

**Example**:
```
Buffer: [🔥][💧][⚡][🌿][🧊][🌑][✨][🔥][💧][⚡] (10/10 FULL)

Turn 10: 3 new magic arrive (all pass your filters)
→ 3 essence overflow
→ Take 30 HP damage!

Solution: Must cast spells to free buffer space!
```

---

## Resource Management Loop

```
Turn Start: Enemy sends 3 magic (automatic)
    ↓
Your PREROUTING filters
    ↓
Accepted magic → Buffer
    ↓
If buffer full → Overflow damage!
    ↓
Your turn: Must cast to free space
    ↓
But: Need CPU to configure defenses
    ↓
Trade-off: Attack vs Defense vs Adapt
    ↓
Repeat
```

**Key Tension**:
1. Accept too much → Buffer overflow → HP damage
2. Block too much → No essence → Cannot attack → Starvation loss
3. Complex rules → High CPU cost → Cannot adapt

**Optimal Strategy**: Balance!

---

## Counter-Strategy Matrix

| Enemy Strategy | Counter | CPU Cost | Trade-off |
|----------------|---------|----------|-----------|
| Spam Fire 🔥🔥🔥 | DROP Fire | -5 CPU | Miss recovery magic if any |
| Mixed Fire+Water 🔥💧 | STRIP Fire | -30 CPU | Expensive, limits adaptation |
| Block enemy IP | Use Transform (bypass) | -20 CPU | Moderate cost |
| Heavy defense (no attack) | Ignore, wait 5 turns | 0 CPU | They auto-lose (starvation) |
| Buffer overflow spam | Priority Queue + Discard | -10 CPU + 5/discard | Must manage actively |

---

## Example Turn Breakdown

**Turn 3**:

**Phase 1: Incoming (automatic)**
```
Enemy sends: 🔥 💧 ⚡

Your PREROUTING rules:
- DROP Fire (-5 CPU)
- ACCEPT Water (-5 CPU)
- (Lightning has no rule, defaults ACCEPT)

Result:
- 🔥 blocked
- 💧 enters buffer
- ⚡ enters buffer

Your buffer: [💧][⚡][🌿][🔥][💧] (was 3, now 5)
```

**Phase 2: Your actions**
```
CPU available: 100
Passive costs: -10 (your 2 rules)
Remaining: 90 CPU

Actions:
1. Configure new rule: "DROP Dark" (-20 CPU)
2. Cast spell: Consume [💧][⚡] → "Storm Splash" (15 dmg)

CPU used: 20
CPU remaining: 70 (unused, wasted)

Your buffer: [🌿][🔥][💧] (was 5, now 3 after casting)
Opponent HP: 100 → 85
```

**Phase 3: Resolution**
```
Opponent takes 15 damage
Your HP: unchanged
Turn ends
```

---

## Summary: The Balance Mechanisms

1. **CPU Economy**: Rules cost CPU every turn → limits defense complexity
2. **Essence Starvation**: Block all → cannot attack → auto-lose after 5 turns
3. **Recovery Routing**: 30% magic via enemy route → blocking enemy IP = less resources
4. **Mixed Magic**: Hybrid types bypass simple rules → need expensive STRIP
5. **Buffer Pressure**: 3/turn incoming, 10 max → must cast or overflow
6. **Compound Rule Cost**: Filtering enemy + type = 5× more expensive
7. **Action CPU Cost**: Inspecting/configuring uses CPU → less defense possible

**Result**: Players must balance defense, resource gain, and offense!

No "perfect immune" build exists.
