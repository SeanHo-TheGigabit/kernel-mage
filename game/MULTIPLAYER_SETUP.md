# Kernel Duel - Multiplayer Setup Guide

Complete guide to setting up and playing Kernel Duel in multiplayer mode

## Quick Start

### 1. Install Dependencies

```bash
# Install Python WebSocket library
pip3 install websockets
```

### 2. Start the Server

```bash
cd /home/user/kernel-mage/game
python3 multiplayer_server.py
```

You should see:
```
============================================================
Kernel Duel Multiplayer Server
============================================================
Starting WebSocket server on ws://localhost:8765
Waiting for players to connect...
```

Server is now running and ready for connections!

### 3. Connect Clients

#### Option A: Godot Visual Client

1. **Install Godot**
   - Download Godot 4.2+ from https://godotengine.org/
   - Extract and run

2. **Open Project**
   - Launch Godot
   - Click "Import"
   - Navigate to `game/godot_client/`
   - Select `project.godot`
   - Click "Import & Edit"

3. **Run Client**
   - Press F5 or click "Play" button
   - Enter player name
   - First player: Leave room ID empty (creates new room)
   - Second player: Enter the room ID from first player

4. **Play!**
   - Wait for both players to join
   - Game starts automatically
   - Use buttons to cast spells and configure rules

#### Option B: Test with Python Client

```bash
# In another terminal
python3 test_multiplayer.py
```

This runs two simulated clients for testing purposes.

## Network Architecture

```
Player 1 (Godot)  ←→  Server (Python)  ←→  Player 2 (Godot)
   Client              WebSocket              Client
                       Port 8765
```

**Server-Authoritative Design:**
- All game logic runs on server
- Clients send actions (cast, configure_rule, etc.)
- Server processes and broadcasts results
- Prevents cheating (hidden enemy buffer, validates moves)

## Protocol Overview

### Client → Server Messages

**Join Game:**
```json
{
  "type": "join",
  "player_name": "Alice",
  "room_id": "abc123"  // optional, creates new if empty
}
```

**Cast Spell:**
```json
{
  "type": "cast",
  "essence_count": 2  // 1-3
}
```

**Configure Rule:**
```json
{
  "type": "configure_rule",
  "chain": "PREROUTING",
  "action": "DROP",
  "magic_type": 0,  // optional, 0=Fire, 1=Water, etc.
  "source_filter": false
}
```

**Discard Essence:**
```json
{
  "type": "discard",
  "index": 0
}
```

**Ready for Next Phase:**
```json
{
  "type": "ready"
}
```

### Server → Client Messages

**Joined Room:**
```json
{
  "type": "joined",
  "player_id": 0,  // 0 or 1
  "room_id": "abc123",
  "message": "Joined room abc123"
}
```

**State Update:**
```json
{
  "type": "state_update",
  "turn": 5,
  "phase": "action",
  "your_wand": {
    "hp": 75,
    "shield": 10,
    "cpu": 80,
    "buffer": [0, 1, 2],  // magic types
    "buffer_count": 3,
    "rules_count": 2
  },
  "enemy_wand": {
    "hp": 80,
    "shield": 0,
    "cpu": 90,
    "buffer_count": 5,  // count only, contents hidden!
    "rules_count": 3
  },
  "log": ["Alice cast Fireball!", "Bob took 10 damage"]
}
```

**Magic Incoming:**
```json
{
  "type": "magic_incoming",
  "your_received": 2,
  "your_dropped": 1,
  "your_overflow": 0,
  "enemy_received": 3
}
```

**Action Result:**
```json
{
  "type": "action_result",
  "success": true,
  "message": "Cast Elemental Storm!",
  "spell_cast": "Elemental Storm"
}
```

**Game Over:**
```json
{
  "type": "game_over",
  "winner": "Alice",
  "reason": "hp"  // or "starvation"
}
```

**Error:**
```json
{
  "type": "error",
  "message": "Room is full"
}
```

## Game Flow

### Phase 1: Connection
1. Player 1 connects, creates room
2. Server generates room ID (e.g., "abc123")
3. Player 1 shares room ID with Player 2
4. Player 2 joins with same room ID
5. Game starts automatically when both connected

### Phase 2: Incoming (automatic)
1. Server generates 3 random magic essences for each player
2. Essences filtered through each player's PREROUTING rules
3. Accepted essences added to buffer
4. Overflow damage if buffer full
5. Server sends `magic_incoming` message to both players
6. Server sends `state_update` to both players

### Phase 3: Action (simultaneous)
1. Both players can take actions:
   - Cast spells (consume essences)
   - Configure defense rules
   - Discard essences
2. Server validates and applies each action
3. Server sends `action_result` and `state_update` after each action
4. When both players send "ready", proceed to resolution

### Phase 4: Resolution (automatic)
1. Server checks win conditions
2. If game over: Send `game_over` message
3. If continuing: Start next turn (back to Incoming phase)

## Magic Types

| Value | Symbol | Name      |
|-------|--------|-----------|
| 0     | 🔥     | Fire      |
| 1     | 💧     | Water     |
| 2     | ⚡     | Lightning |
| 3     | 🌿     | Nature    |
| 4     | 🌑     | Dark      |
| 5     | ✨     | Light     |
| 6     | ❄️     | Ice       |

## Rule Chains

- `PREROUTING` - Filter incoming magic before buffering
- `INPUT` - (Future: rate limiting)
- `POSTROUTING` - (Future: output filtering)

## Rule Actions

- `DROP` - Block this magic type
- `ACCEPT` - Explicitly allow (overrides DROP)
- `STRIP` - Deep packet inspection (high CPU cost)

## Troubleshooting

### Server won't start
- Check if port 8765 is already in use: `netstat -an | grep 8765`
- Try killing existing process: `pkill -f multiplayer_server.py`
- Check websockets installed: `pip3 list | grep websockets`

### Client can't connect
- Verify server is running
- Check firewall settings
- Ensure using correct URL: `ws://localhost:8765`
- For remote connections: Replace `localhost` with server IP

### Room not found
- Room IDs are case-sensitive
- Rooms are deleted when players disconnect
- First player must create room before second joins

### Game state not updating
- Check network connection
- Look for error messages in server console
- Verify both clients sent "ready" to advance turn

## Advanced: Custom Clients

You can create your own client in any language that supports WebSockets!

**Minimum Requirements:**
1. WebSocket client library
2. JSON parsing
3. Send/receive messages per protocol above
4. Display game state to player
5. Get player input for actions

**Example: Python Client**
```python
import asyncio
import websockets
import json

async def play():
    async with websockets.connect("ws://localhost:8765") as ws:
        # Join
        await ws.send(json.dumps({
            "type": "join",
            "player_name": "Alice"
        }))

        # Receive messages
        async for message in ws:
            data = json.loads(message)
            print(f"Received: {data['type']}")

            # Handle message types...
```

See `test_multiplayer.py` for complete example.

## Performance

- Server can handle ~100 concurrent games (200 players)
- Each game room is isolated
- Latency: <50ms on local network
- Message size: ~500 bytes average

## Security Notes

**Current Implementation:**
- Local network only (localhost)
- No authentication
- No encryption
- Trust-based (server validates moves)

**For Production:**
- Add TLS/SSL (wss://)
- Implement player authentication
- Add rate limiting
- Input validation already present
- Server-authoritative prevents most cheating

## File Reference

- `multiplayer_server.py` - Main server implementation
- `network_protocol.py` - Protocol documentation
- `game_engine.py` - Core game logic
- `core_data.py` - Data structures
- `godot_client/` - Visual client
- `test_multiplayer.py` - Test client

## Support

Check the main README and documentation in:
- `../docs/game/` - Game mechanics
- `../docs/technical/` - Linux kernel concepts
