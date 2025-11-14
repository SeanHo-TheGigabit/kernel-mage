# Kernel Duel - Game Implementation

PvP wizard combat where your wand is a Linux kernel!

**→ Want to play immediately?** See **[QUICKSTART.md](QUICKSTART.md)** (30 seconds to start!)

---

## Architecture

```
┌─────────────────────────────────────┐
│  Game Engine (game_engine.py)      │  ← Pure logic, no UI
│  - Turn processing                  │
│  - Rules engine (iptables-like)     │
│  - Magic generation & filtering     │
│  - AI opponent logic                │
└──────────┬──────────────────────────┘
           │ (Simple method calls)
           │
┌──────────▼──────────────────────────┐
│  Terminal UI (terminal_ui.py)       │  ← Display only
│  - Shows game state                 │
│  - Gets player input                │
│  - Calls engine methods             │
└─────────────────────────────────────┘
```

**Network-ready**: Engine is separate from UI, making multiplayer easy to add later!

## Files

### Core Engine
- `core_data.py` - Data structures (kernel-style with dataclasses)
- `spell_database.py` - All 76 magic combos
- `ai_opponents.py` - 6 AI difficulty levels
- `game_engine.py` - Game logic (pure, no UI)

### Single Player
- `terminal_ui.py` - Terminal interface with AI opponents

### Multiplayer
- `multiplayer_server.py` - WebSocket server for PvP matches
- `network_protocol.py` - Protocol specification
- `godot_client/` - Godot visual client (GDScript)

## How to Play

### Single Player (vs AI)

```bash
python3 terminal_ui.py
```

Choose AI difficulty (1-6) and battle against computer opponents!

### Multiplayer (PvP)

**Option 1: Godot Visual Client (recommended)**

1. Start server:
   ```bash
   python3 multiplayer_server.py
   ```

2. Open Godot client (see `godot_client/README.md`)

3. Connect two players to the same room

**Option 2: Terminal (coming soon)**
- Terminal multiplayer client in development

### Controls

**Action Phase Menu**:
- `[1]` Cast spell - Consume 1-3 essences for combo attack
- `[2]` Configure defense - Add iptables-like filter rule
- `[3]` Discard essence - Remove unwanted essence (costs 5 CPU)
- `[4]` View buffer - See possible spell combinations
- `[5]` Skip - End your turn
- `[Q]` Quit game

### Game Flow

1. **Incoming Phase** (automatic)
   - 3 magic essences arrive per turn
   - Filtered through your PREROUTING rules
   - Accepted magic enters your buffer (max 10)
   - Buffer overflow = 10 HP damage per overflow

2. **Action Phase** (your turn)
   - Configure defense rules (costs 20 CPU)
   - Cast spells (consume 1-3 essences)
   - Discard unwanted essences (costs 5 CPU)
   - AI opponent also acts

3. **Resolution** (automatic)
   - Damage applied
   - Victory check (HP reaches 0 or starvation)

## AI Opponents

1. **Novice Mage** - Tutorial bot, no defense, random casts
2. **Shieldmage** - Heavy defense, conservative play
3. **Battle Mage** - Aggressive, minimal defense, spam attacks
4. **Adept Mage** - Balanced offense and defense
5. **Archmage** - Adapts to your strategy, learns patterns
6. **Grand Archmage** - Expert planning, optimal combos

## Win Conditions

- **HP Victory**: Reduce opponent's HP to 0
- **Starvation**: Cannot cast for 5 turns (blocked all magic = no essence)

## Tips

- **Balance defense vs resources**: Block too much = no essence = can't attack
- **Watch buffer overflow**: Must cast regularly or take damage
- **CPU management**: Rules cost CPU every turn, limits actions
- **Combo planning**: Save good elements for 3-element power combos
- **Heal when needed**: Water combos heal HP

## Example Turn

```
Turn 5 - INCOMING
→ 3 magic arrive: 🔥💧⚡
→ Your rule: DROP Fire
→ Accepted: 💧⚡ (2 added to buffer)

Turn 5 - ACTION
Your buffer: [🔥][💧][⚡][🌿][💧]
Your HP: 75/100, CPU: 85/100

Actions:
[1] Cast 3 essences: 🔥💧⚡ → Elemental Storm (35 dmg)
[2] Configure defense
[5] Skip

> 1
✓ Cast Elemental Storm → 35 damage to enemy!
```

## Multiplayer Architecture

```
┌─────────────────────────────────────┐
│  Godot Client (Player 1)            │
│  - Visual UI                         │
│  - WebSocket connection              │
└──────────┬──────────────────────────┘
           │ JSON messages
           │
┌──────────▼──────────────────────────┐
│  Multiplayer Server (Python)        │  ← Manages game rooms
│  - WebSocket server (port 8765)     │
│  - Room matchmaking                  │
│  - State synchronization             │
└──────────┬──────────────────────────┘
           │ method calls
           │
┌──────────▼──────────────────────────┐
│  Game Engine (Pure Logic)           │  ← Server-authoritative
│  - Turn processing                   │
│  - Rules engine                      │
│  - Prevents cheating                 │
└─────────────────────────────────────┘
           │ method calls
           │
┌──────────▼──────────────────────────┐
│  Godot Client (Player 2)            │
│  - Visual UI                         │
│  - WebSocket connection              │
└─────────────────────────────────────┘
```

**Key Features:**
- Server-authoritative (all game logic on server)
- Real-time WebSocket communication
- JSON protocol for easy client development
- Hidden information (enemy buffer contents)
- Room-based matchmaking

See `network_protocol.py` for full message specification.
