# KernelMage - Quick Start Guide

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
# Run all tests
python3 tests/run_all_tests.py

# Run individual test suites
python3 tests/test_entities.py
python3 tests/test_magic.py
python3 tests/test_network.py
python3 tests/test_combat.py
```

## Quick Game Overview

**KernelMage** is a turn-based ASCII RPG where **magic is network communication**:

- 🔥 **Essences** = Data types (fire, water, lightning, etc.)
- 🖥️ **Architectures** = CPU instruction sets (x86, ARM, RISC-V)
- 📡 **Protocols** = Casting methods (TCP, UDP, ICMP)
- 🎯 **DNS** = Targeting system
- 📦 **Packets** = Spells traveling through the network

### Combat Example

```
1. Explore → Enter Combat
2. Select target (enemy #1)
3. Choose essence (Fire)
4. Choose protocol:
   - TCP: Slow (3 turns), guaranteed hit, expensive
   - UDP: Fast (1 turn), might miss, cheap
5. Spell resolves, deal damage!
```

### Architecture Strategy

- **x86 CISC**: High damage, high cost → Use for bosses
- **ARM RISC**: Low cost, efficient → Use for swarms
- **RISC-V**: Balanced, modular → Use for flexibility

## Documentation

- **README.md** - Complete game design (198KB!)
- **GAMEPLAY.md** - How to play guide
- **ARCHITECTURE.md** - Code structure
- **EXTENDING.md** - How to add content
- **QUICKSTART.md** - This file

## Project Stats

- **Python 3.11+**
- **2,400+ lines of code**
- **33 passing tests**
- **28 game files**
- **Fully playable!**

## Key Files

```
main.py                  # Run this to play!
kernelmage/
  ├── core/game.py      # Main game loop
  ├── entities/         # Player and enemies
  ├── magic/            # Spells and architectures
  ├── network/          # DNS, routing, packets
  ├── combat/           # Combat system
  └── ui/               # Terminal interface
```

## Extending the Game

See **EXTENDING.md** for detailed guides on adding:
- New enemies
- Story events
- Quests
- Locations/dungeons
- Items/equipment

Example - Add a new enemy:

```python
# In kernelmage/entities/enemy.py
def create_my_enemy() -> Enemy:
    stats = Stats(max_hp=100, power=10, defense=5)
    return Enemy(
        name="My Enemy",
        stats=stats,
        symbol="M",
        essence_drop=EssenceType.FIRE,
        xp_reward=50
    )
```

Then use it in encounters!

## Quick Commands

```bash
# Play game
python3 main.py

# Run tests
python3 tests/run_all_tests.py

# Check imports
python3 -c "from kernelmage.core.game import run_game; print('OK')"
```

## Game Controls

**Main Menu:**
- `e` - Explore/Combat
- `i` - Inventory
- `a` - Architecture info
- `s` - Switch architecture
- `q` - Quit

**Combat:**
- `a` - Attack (cast spell)
- `p` - Ping (reveal enemy stats)
- `s` - Switch architecture
- `f` - Flee

## Tips

1. **Use Ping** to see enemy stats before attacking
2. **UDP is great** for weak enemies (fast, cheap)
3. **TCP for bosses** when you can't afford to miss
4. **Switch to ARM** when low on mana
5. **Switch to x86** for maximum damage

Enjoy the game! 🎮✨
