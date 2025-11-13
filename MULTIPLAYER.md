# KernelMage - Multiplayer Co-op Guide

## Overview

KernelMage now supports **2-player cooperative gameplay**! Team up with a friend to battle enemies together using network magic.

### Multiplayer Features

✅ **Cooperative Combat** - Fight together against enemies
✅ **Real-time Synchronization** - See each other's actions
✅ **LAN Support** - Play on local network
✅ **Server Support** - Play over the internet
✅ **Turn Coordination** - Both players act each turn
✅ **Shared Rewards** - Split XP and loot

---

## How to Play Multiplayer

### Option 1: LAN Play (Direct Connection)

**Player 1 (Host):**
```bash
python3 main.py --multiplayer --host --port 8888
```

**Player 2 (Join):**
```bash
python3 main.py --multiplayer --join 192.168.1.100:8888
```

### Option 2: Internet Play (with Server)

**Set up Server:**
```bash
python3 -m kernelmage.multiplayer.server --host 0.0.0.0 --port 8888
```

**Both Players Connect:**
```bash
python3 main.py --multiplayer --server your-server.com:8888
```

---

## Architecture

### Network Protocol

KernelMage multiplayer uses a **client-server architecture**:

```
Player 1 (Client) ←→ Server ←→ Player 2 (Client)
```

**Message Types:**
- `CONNECT` / `DISCONNECT` - Connection management
- `PING` / `PONG` - Keep-alive
- `PLAYER_JOIN` / `PLAYER_UPDATE` - Player state sync
- `COMBAT_ACTION` - Combat actions
- `COMBAT_UPDATE` - Combat state sync
- `CHAT_MESSAGE` - Chat between players

### Data Flow

```
Turn Flow:
1. Both players see combat state
2. Each player selects action
3. Players submit actions to server
4. Server waits for both players
5. Server executes turn
6. Updated state sent to all players
7. Repeat
```

---

## Cooperative Combat System

### How It Works

**Traditional Combat:**
- 1 player vs enemies
- Player acts, then enemies act
- Single player controls everything

**Co-op Combat:**
- 2 players vs enemies
- Both players act simultaneously
- Coordinated attacks
- Shared victory/defeat

### Example Co-op Battle

```
╔═══ CO-OP COMBAT - Turn 3 ═══╗

┌─── Your Party ────┐   ┌─── Enemies ─────┐
│ Mage1 [YOU]       │   │ [1] Bandit       │
│  HP:   ████████   │   │     ██████       │
│  Mana: ███████    │   │                  │
│  x86 CISC         │   │ [2] Corrupted    │
│                   │   │     ████████     │
│ Mage2 [ALLY]      │   │                  │
│  HP:   ██████     │   └──────────────────┘
│  Mana: █████████  │
│  ARM RISC         │
└───────────────────┘

⏳ Waiting for players... (1/2 ready)

[Turn 1] Cooperative combat started!
[Turn 2] Mage1 attacks Bandit for 45 damage!
[Turn 2] Mage2 attacks Corrupted for 38 damage!
[Turn 3] Bandit attacks Mage2 for 12 damage!
```

---

## Technical Implementation

### Core Components

#### 1. Network Protocol (`kernelmage/multiplayer/protocol.py`)

Handles message serialization:

```python
from kernelmage.multiplayer.protocol import (
    NetworkMessage,
    MessageType,
    PlayerState,
    CombatAction
)

# Create player state
state = PlayerState(
    player_id="player1",
    name="Mage",
    level=5,
    hp=80,
    max_hp=100,
    mana=150,
    max_mana=150,
    location="village",
    architecture="x86_cisc"
)

# Send to server
msg = NetworkProtocol.create_player_update_message("player1", state)
client.send_message(msg)
```

#### 2. Game Server (`kernelmage/multiplayer/server.py`)

Manages connections and broadcasts:

```python
from kernelmage.multiplayer.server import GameServer

# Start server
server = GameServer(host="0.0.0.0", port=8888)
server.start()

# Server automatically:
# - Accepts connections
# - Forwards messages
# - Manages player list
```

#### 3. Game Client (`kernelmage/multiplayer/client.py`)

Connects to server:

```python
from kernelmage.multiplayer.client import GameClient

# Create client
client = GameClient("player1", "Mage")

# Connect
client.connect("192.168.1.100", 8888)

# Send player state
client.send_player_state(player_state)

# Receive messages
msg = client.get_message()
```

#### 4. Co-op Combat (`kernelmage/multiplayer/coop_combat.py`)

Manages cooperative battles:

```python
from kernelmage.multiplayer.coop_combat import create_coop_encounter

# Create encounter
players = [player1, player2]
enemies = [bandit, node]
encounter = create_coop_encounter(players, enemies)

# Submit actions
action1 = CombatAction(
    player_id="player1",
    action_type="attack",
    target_index=0,
    essence_type="fire",
    protocol_type="udp"
)
encounter.submit_player_action(player1, action1)

# Execute when both ready
if encounter.all_players_ready:
    encounter.execute_turn()
```

---

## Multiplayer Combat Flow

### Turn Sequence

**1. View Combat State**
```
Both players see:
- All party members (HP, mana, architecture)
- All enemies (HP, status)
- Combat log
- Ready status
```

**2. Select Actions**
```
Each player chooses:
- Attack → Select target, essence, protocol
- Ping → Scan enemy
- Switch Architecture
- (Wait for partner)
```

**3. Submit & Wait**
```
Turn Status:
⏳ Waiting for players... (1/2 ready)

When both ready:
✓ All players ready! Executing turn...
```

**4. Execute Turn**
```
Server processes:
1. Player 1's action → damage, effects
2. Player 2's action → damage, effects
3. All enemies attack
4. Check victory/defeat
```

**5. Update & Repeat**
```
New state broadcasted:
- Updated HP/mana
- Defeated enemies
- Combat log
- Next turn begins
```

---

## Network Protocols in Multiplayer

### TCP vs UDP (In-Game Spells)

These are **in-game spell protocols**, not network transport:

- **TCP Spell** - Reliable 3-turn cast
- **UDP Spell** - Fast 1-turn cast

### Network Transport

Multiplayer uses **TCP sockets** for reliability:

```python
# Real network layer (TCP)
socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# In-game magic layer (TCP/UDP spells)
SpellSystem.cast_spell(..., protocol_type=ProtocolType.TCP)
```

**Why TCP for networking?**
- Guaranteed delivery
- Ordered messages
- Critical for turn synchronization
- Prevents desyncs

---

## Running a Dedicated Server

### Server Setup

**1. Install on Server:**
```bash
# On your server machine
git clone <repo-url>
cd kernel-mage
pip3 install -r requirements.txt
```

**2. Start Server:**
```bash
python3 -m kernelmage.multiplayer.server \
    --host 0.0.0.0 \
    --port 8888
```

**3. Configure Firewall:**
```bash
# Allow port 8888
sudo ufw allow 8888/tcp
```

**4. Get Server IP:**
```bash
# Public IP
curl ifconfig.me

# Local IP
hostname -I
```

### Client Connection

**Connect to Server:**
```bash
python3 main.py \
    --multiplayer \
    --server YOUR_SERVER_IP:8888
```

---

## Synchronization Details

### Player State Sync

**What Gets Synchronized:**
- Player name
- Level
- HP/Max HP
- Mana/Max Mana
- Current location
- Active architecture

**When Synced:**
- On connect
- After combat actions
- On level up
- On location change

### Combat Sync

**Per Turn:**
```json
{
  "msg_type": "combat_action",
  "sender_id": "player1",
  "data": {
    "action": {
      "action_type": "attack",
      "target_index": 0,
      "essence_type": "fire",
      "protocol_type": "udp"
    }
  }
}
```

**State Update:**
```json
{
  "msg_type": "combat_update",
  "data": {
    "turn_number": 5,
    "players_hp": [80, 65],
    "enemies_hp": [30, 0],
    "combat_log": ["Turn 5...", "Mage1 attacks..."]
  }
}
```

---

## Latency & Performance

### Network Requirements

**Minimum:**
- 56 Kbps (dial-up) - Text-based, low bandwidth
- 100ms latency - Turn-based, latency-tolerant

**Recommended:**
- 1 Mbps+ broadband
- < 50ms latency for smooth experience

### Message Sizes

- Player state: ~200 bytes
- Combat action: ~150 bytes
- Chat message: ~100 bytes + text

**Bandwidth Usage:**
- Idle: ~0.1 KB/s (ping/pong)
- Combat: ~1-2 KB/s (action sync)
- Total: < 10 KB/minute

**Why So Low?**
- Turn-based (no real-time)
- JSON text (not binary)
- Only state changes sent
- No graphics/assets

---

## Security Considerations

### Current Implementation

**⚠ NOT PRODUCTION-READY**

This is a **prototype** for LAN/trusted play:
- No authentication
- No encryption
- No anti-cheat
- Trust-based

### For Public Servers

**TODO (Future):**
- [ ] Player authentication
- [ ] TLS/SSL encryption
- [ ] Rate limiting
- [ ] Anti-cheat validation
- [ ] Replay detection

---

## Troubleshooting

### Connection Issues

**Problem: "Connection refused"**
```
Solution:
1. Check server is running
2. Verify IP address
3. Check firewall rules
4. Try localhost first
```

**Problem: "Timeout"**
```
Solution:
1. Ping server first
2. Check network connectivity
3. Verify port is open
4. Try different port
```

### Desync Issues

**Problem: "Players out of sync"**
```
Solution:
1. Both restart clients
2. Restart server
3. Check network stability
4. Reduce latency
```

### Performance Issues

**Problem: "Slow turns"**
```
Solution:
1. Check network latency
2. Reduce message frequency
3. Use LAN instead of internet
4. Close other network apps
```

---

## Testing

### Run Multiplayer Tests

```bash
# All multiplayer tests
python3 tests/test_multiplayer.py

# Includes:
✓ Protocol serialization
✓ Server-client connection
✓ Cooperative combat
✓ State synchronization
```

### Manual Testing

**Test 1: Localhost**
```bash
# Terminal 1 (Server)
python3 -c "from kernelmage.multiplayer.server import *; server = GameServer('127.0.0.1', 8888); server.start(); import time; time.sleep(60)"

# Terminal 2 (Player 1)
python3 main.py --multiplayer --join 127.0.0.1:8888

# Terminal 3 (Player 2)
python3 main.py --multiplayer --join 127.0.0.1:8888
```

**Test 2: LAN**
```bash
# Find your IP
hostname -I  # e.g., 192.168.1.100

# Terminal 1 (Server on 192.168.1.100)
python3 -m kernelmage.multiplayer.server

# Terminal 2 (Player on another computer)
python3 main.py --multiplayer --join 192.168.1.100:8888
```

---

## Future Enhancements

### Planned Features

- [ ] **3-4 Player Support** - Bigger parties
- [ ] **PvP Mode** - Player vs player combat
- [ ] **Lobby System** - Matchmaking
- [ ] **Chat System** - Text chat during combat
- [ ] **Spectator Mode** - Watch others play
- [ ] **Replay System** - Save and replay matches
- [ ] **Leaderboards** - Track victories
- [ ] **WebSocket Support** - Browser-based play
- [ ] **Mobile Support** - Play on phone

### Technical TODOs

- [ ] **Reconnection** - Handle disconnects gracefully
- [ ] **State Recovery** - Resume after disconnect
- [ ] **Compression** - Reduce bandwidth
- [ ] **Delta Sync** - Only send changes
- [ ] **UDP Transport** - Lower latency option
- [ ] **P2P Mode** - Direct peer-to-peer

---

## API Reference

### Server API

```python
from kernelmage.multiplayer.server import GameServer

server = GameServer(host="0.0.0.0", port=8888)
server.start()        # Start accepting connections
server.stop()         # Stop server
server.clients        # Dict of connected clients
```

### Client API

```python
from kernelmage.multiplayer.client import GameClient

client = GameClient("player_id", "PlayerName")
client.connect(host, port)              # Connect to server
client.disconnect()                     # Disconnect
client.send_message(msg)                # Send message
client.get_message(timeout=0.1)         # Receive message
client.send_player_state(state)         # Sync player state
client.send_chat(message)               # Send chat
```

### Co-op Combat API

```python
from kernelmage.multiplayer.coop_combat import create_coop_encounter

encounter = create_coop_encounter(players, enemies)
encounter.submit_player_action(player, action)
encounter.all_players_ready            # Check if ready
encounter.execute_turn()               # Execute turn
```

---

## Summary

KernelMage multiplayer lets you:

✅ **Team up** with a friend
✅ **Fight together** in co-op combat
✅ **Share rewards** (XP and loot)
✅ **Play anywhere** (LAN or internet)
✅ **Real-time sync** - see each other's actions

**Network magic, now with friends!** 🎮✨

---

## Quick Start

```bash
# Server
python3 -m kernelmage.multiplayer.server

# Player 1
python3 main.py --multiplayer --join localhost:8888

# Player 2 (in another terminal)
python3 main.py --multiplayer --join localhost:8888

# Fight together!
```

**Enjoy cooperative network magic!** 🧙‍♂️🧙‍♀️📡
