# KernelMage - Architecture & Developer Documentation

## Project Overview

KernelMage is a turn-based ASCII RPG implementing network communication concepts as a magic system. This document describes the code architecture and how to extend the game.

## Tech Stack

- **Python 3.11+**
- **Rich** - Terminal UI rendering
- **Dataclasses** - Clean data structures
- **Type Hints** - Better code clarity and IDE support

## Project Structure

```
kernel-mage/
├── main.py                          # Entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Game design document
├── GAMEPLAY.md                      # User guide
├── ARCHITECTURE.md                  # This file
├── EXTENDING.md                     # How to add content
│
└── kernelmage/                      # Main package
    ├── __init__.py
    │
    ├── core/                        # Core game engine
    │   ├── entity.py               # Base Entity class
    │   └── game.py                 # GameState, main loop
    │
    ├── entities/                    # Game entities
    │   ├── stats.py                # Stats, NetworkAddress
    │   ├── player.py               # Player character
    │   └── enemy.py                # Enemy types & factory functions
    │
    ├── magic/                       # Magic system
    │   ├── essences.py             # EssenceType, Essence data
    │   ├── architectures.py        # CPU architectures (x86, ARM, RISC-V)
    │   └── spells.py               # SpellSystem, casting logic
    │
    ├── network/                     # Network simulation
    │   ├── protocols.py            # TCP, UDP, ICMP, Multicast
    │   ├── dns.py                  # DNS/targeting system
    │   ├── routing.py              # Route calculation, hops
    │   └── packets.py              # MagicalPacket structure
    │
    ├── combat/                      # Combat system
    │   └── combat.py               # CombatEncounter, turn management
    │
    ├── ui/                          # User interface
    │   ├── display.py              # Display class (rich wrapper)
    │   └── combat_screen.py        # CombatScreen UI
    │
    ├── items/                       # Items (future)
    │   └── __init__.py
    │
    └── data/                        # Game data (future)
        └── __init__.py
```

## Core Systems

### Entity System
- `Entity` - Base class for all game entities
- `Stats` - HP, mana, network characteristics
- `NetworkAddress` - IP addressing and DNS cache
- `Player` - Player character with inventory
- `Enemy` - Enemy entities with AI and loot

### Magic System
- **Essences** - The DATA being processed (fire, water, etc.)
- **Architectures** - HOW data is processed (x86, ARM, RISC-V)
- **Spells** - Casting logic and damage calculation

### Network System
- **Protocols** - Casting behavior (TCP, UDP, ICMP)
- **DNS** - Targeting and reconnaissance
- **Routing** - Packet paths and hops
- **Packets** - Spell data structures

### Combat System
- Turn-based combat management
- Multi-turn spell casting
- Enemy AI
- Loot and XP system

### UI System
- Rich terminal interface
- Combat visualization
- Interactive menus

## Key Design Patterns

- **Factory Pattern** - Entity creation
- **Data Classes** - Clean data structures
- **Enums** - Type-safe categories
- **Static Methods** - Stateless systems

## Documentation Files

- `README.md` - Game design and lore (198KB!)
- `GAMEPLAY.md` - How to play guide
- `ARCHITECTURE.md` - This file - code architecture
- `EXTENDING.md` - How to add new content
