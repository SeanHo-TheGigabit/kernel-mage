# KernelMage Arena - Quick Start Guide

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd kernel-mage

# Install dependencies
pip3 install -r requirements.txt
```

## Running the Game

```bash
python3 main.py
```

## Testing

```bash
# Run arena tests
python3 tests/test_arena.py

# Run all tests
python3 tests/run_all_tests.py
```

## Quick Game Overview

**KernelMage Arena** is a **simplified pure combat** game - fight sequential waves of enemies in a mage arena!

**No world map. No quests. Just pure combat!**

### Core Mechanics

- 🔥 **Essences** = Spell elements (Fire, Water, Lightning, etc.)
- 🖥️ **Architectures** = CPU instruction sets (x86, ARM, RISC-V)
- 📡 **Protocols** = Casting methods (TCP, UDP, ICMP)
- ⚔️ **Arena Rounds** = Sequential combat encounters

### How to Play

1. **Start** → Enter your mage name
2. **Choose Architecture** → x86, ARM, or RISC-V
3. **Fight Rounds** → Defeat waves of enemies
4. **Rest** → Heal 30% HP/Mana between rounds
5. **Survive** → How many rounds can you beat?

### Combat Flow

```
Round 1: 1 Bandit (Easy)
Round 2: 2 Bandits
Round 3: 1 Corrupted Node (Stronger)
Round 4: 3 Swarm Minions
Round 5: Mixed enemies
Round 6: Illusionist
Round 7: 2 Corrupted Nodes
Round 8: Gateway Boss (Very Hard!)
Round 9+: Random hard encounters
```

### Combat Actions

- **[A] Attack**: Cast spell (choose target, essence, protocol)
- **[P] Ping**: Scan enemy (shows HP, stats, weaknesses)
- **[S] Switch Architecture**: Change CPU (costs 20 mana, 1 turn)
- **[I] Inventory**: View essences
- **[F] Flee**: Can't flee from arena!

### Protocol Strategy

- **TCP**: Slow (3 turns) but 100% accurate → Use for bosses
- **UDP**: Fast (1 turn) but 70% accuracy → Use for weak enemies
- **ICMP Ping**: Free scan, no damage → Use for info

### Architecture Strategy

- **x86 CISC**: 1.5x power, +1 turn → Maximum damage for bosses
- **ARM RISC**: 0.6x cost, fast → Save mana, quick casts
- **RISC-V**: Balanced → Good all-around

## Documentation

- **ARENA_GUIDE.md** - Complete arena guide
- **QUICKSTART.md** - This file
- **ARCHITECTURE.md** - Code structure
- **EXTENDING.md** - How to add content

## Project Stats

- **Python 3.11+**
- **Simplified pure combat**
- **Progressive difficulty**
- **Score: Rounds survived**

## Key Files

```
main.py                  # Run this to play!
kernelmage/
  ├── core/arena.py     # Arena game loop
  ├── entities/         # Player and enemies
  ├── magic/            # Spells and architectures
  ├── network/          # DNS, routing, packets
  ├── combat/           # Combat system
  └── ui/               # Terminal interface
```

## Quick Commands

```bash
# Play arena
python3 main.py

# Run arena tests
python3 tests/test_arena.py

# Check imports
python3 -c "from kernelmage.core.arena import run_arena; print('OK')"
```

## Tips for Success

1. **Ping before attacking** - Know enemy HP and weaknesses
2. **Manage mana** - Don't spam TCP or you'll run dry
3. **UDP for weak enemies** - Save mana for harder rounds
4. **TCP for bosses** - Can't afford to miss
5. **Switch to ARM when low** - Conserve mana
6. **Switch to x86 for power** - Maximize damage on tough enemies
7. **Element weaknesses** - Fire beats Earth, Water beats Fire, etc.

## Scoring

**Your score = Rounds survived**

- Round 1-4: Beginner
- Round 5-7: Intermediate
- Round 8: Boss fight!
- Round 9+: Expert mode

Can you beat the Gateway Boss in Round 8?

Enjoy the arena! ⚔️🧙‍♂️
