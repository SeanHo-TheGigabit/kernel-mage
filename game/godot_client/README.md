# Kernel Duel - Godot Client

Visual multiplayer client for Kernel Duel

## Setup

1. **Install Godot 4.2+**
   - Download from https://godotengine.org/
   - Use Godot 4.2 or later

2. **Open Project**
   - Open Godot Editor
   - Click "Import"
   - Navigate to `godot_client/` folder
   - Select `project.godot`
   - Click "Import & Edit"

3. **Start Multiplayer Server**
   ```bash
   # In game/ directory
   python3 multiplayer_server.py
   ```
   Server starts on `ws://localhost:8765`

4. **Run Client**
   - Press F5 in Godot Editor
   - Or click "Play" button

## How to Play

### Connecting

1. Enter your player name
2. (Optional) Enter room ID to join existing room
   - Leave empty to create new room
3. Click "Connect"
4. Wait for opponent to join

### Controls

**During Action Phase:**
- `Cast 1/2/3` - Cast spell using 1-3 essences from buffer
- `Configure Rule` - Add iptables-like defense rule
- `Ready` - End your turn

### Game Flow

1. **Incoming Phase** (automatic)
   - 3 magic essences arrive
   - Filtered through your PREROUTING rules
   - Accepted magic enters buffer (max 10)
   - Overflow = 10 HP damage per essence

2. **Action Phase** (your turn)
   - Configure defense rules (costs 20 CPU)
   - Cast spells (consume essences)
   - Both players act, then click Ready

3. **Resolution** (automatic)
   - Damage applied
   - Next turn begins

## UI Elements

**Your Wand:**
- HP bar and value
- Shield (if active)
- CPU (action points)
- Essence buffer (shows all 10 slots with magic symbols)
- Active rules count

**Enemy Wand:**
- HP bar and value
- Shield (if active)
- CPU
- Buffer count (contents hidden!)
- Active rules count

**Battle Log:**
- Shows recent actions and events
- Incoming magic results
- Spell casts
- Damage dealt

## Magic Symbols

- 🔥 Fire
- 💧 Water
- ⚡ Lightning
- 🌿 Nature
- 🌑 Dark
- ✨ Light
- ❄️ Ice

## Network Protocol

Client communicates with Python server via WebSocket JSON messages.

See `../network_protocol.py` for full protocol specification.

## Architecture

```
Godot Client (GDScript)
    ↓ WebSocket (JSON)
Python Multiplayer Server
    ↓ method calls
Game Engine (Pure Logic)
```

The client is just a visual layer - all game logic runs on the server to prevent cheating!
