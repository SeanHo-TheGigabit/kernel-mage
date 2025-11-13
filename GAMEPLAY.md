# KernelMage - Gameplay Guide

## How to Play

### Starting the Game

```bash
python3 main.py
```

### Game Concept

**KernelMage** is a turn-based ASCII RPG where magic is actually network communication!

- **Magic = Network packets** between souls
- **Spells = TCP/UDP/ICMP packets** with different characteristics
- **Architectures = CPU instruction sets** (x86, ARM, RISC-V) that modify how you cast
- **Essences = Data types** (fire, water, lightning, etc.) that you manipulate

### Controls

#### Main Menu
- `e` - Enter Combat (random encounter)
- `i` - View Inventory (essences)
- `a` - View Architecture info
- `s` - Switch Architecture
- `q` - Quit Game

#### Combat Menu
- `a` - Attack (cast spell)
- `p` - Ping (ICMP scan to reveal enemy stats)
- `s` - Switch Architecture (costs a turn + 20 mana)
- `i` - View Inventory
- `f` - Flee (50% chance)

### Combat Flow

1. **Select Action** - Choose what to do on your turn
2. **Select Target** - Pick which enemy to attack
3. **Select Essence** - Choose magical data type (fire, water, etc.)
4. **Select Protocol** - Choose network protocol:
   - **TCP**: Guaranteed hit, slow (3 turns), expensive (2x mana)
   - **UDP**: Fast (1 turn), cheap (0.7x mana), but can miss (70% accuracy)
   - **Multicast**: Area effect, hits multiple targets (2 turns, 2.5x mana)
5. **Spell Resolves** - Damage is calculated and applied

### Architectures

#### x86 CISC (Complex)
- **High damage** (1.5x multiplier)
- **High mana cost** (1.5x)
- **Slow** (+1 turn cast time)
- **Best for**: Boss fights, maximum damage

#### ARM RISC (Efficient)
- **Lower damage** (0.7x multiplier)
- **Very efficient** (0.6x mana cost)
- **Fast** (no cast time penalty)
- **Best for**: Swarms, sustained combat, low mana

#### RISC-V (Modular)
- **Balanced** (1.0x damage, 0.8x mana)
- **Extensible** (can load modules)
- **Best for**: Flexibility, experimentation

### Essences

Each essence has:
- **Quantity** (in grams) - consumed when casting
- **Power Rating** (0-100) - base damage
- **Element type** - determines effectiveness against enemies

### Tips

1. **Use Ping** to reveal enemy stats before attacking
2. **Switch architectures** based on situation (x86 for bosses, ARM for swarms)
3. **Manage mana** - TCP is powerful but expensive
4. **Watch essence quantity** - you can run out!
5. **UDP is great** for weak enemies (fast, cheap, usually hits)
6. **TCP is reliable** when you can't afford to miss

### Progression

- **Defeat enemies** to gain XP
- **Level up** to increase HP, mana, and stats
- **Loot essences** from defeated enemies
- **Learn new architectures** (coming soon!)

### Example Combat

```
Turn 1: Ping enemy to see stats (10 mana)
Turn 2: Switch to ARM architecture for efficiency (20 mana)
Turn 3-5: Cast UDP fire spells (cheap, fast) to clear minions
Turn 6: Switch to x86 for boss (20 mana)
Turn 7-9: Cast TCP lightning spell (slow but powerful, guaranteed hit)
Turn 10: Victory!
```

## Technical Details

### Spell Damage Calculation

```
Base Damage = Essence Power + Player Power
× Protocol Multiplier (TCP=1.0, UDP=0.8)
× Architecture Multiplier (x86=1.5, ARM=0.7, RISC-V=1.0)
× Route Multiplier (based on hops)
- Enemy Defense
```

### Mana Cost Calculation

```
Base Cost = 30
× Protocol Multiplier (TCP=2.0, UDP=0.7)
× Architecture Multiplier (x86=1.5, ARM=0.6, RISC-V=0.8)
```

### Network Concepts

- **Direct routing** (1 hop): Fast, full damage
- **Indirect routing** (2-4 hops): Slower, damage decreases per hop
- **Packet loss**: Chance for spell to miss based on enemy stats
- **DNS cache**: Remember targeted enemies (coming soon!)

## Future Features

- More architectures (MIPS, SPARC)
- RISC-V extensions system
- Dungeon exploration
- Network topology maps
- Equipment system (wands as NICs, robes as firewalls)
- Story mode with lore
- More enemy types
- Status effects (burn, freeze, stun)

Enjoy the game!
