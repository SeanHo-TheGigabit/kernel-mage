# Kernel Duel - Quickstart

Get playing in 30 seconds!

## Single Player (vs AI)

```bash
cd /home/user/kernel-mage/game
python3 terminal_ui.py
```

1. Choose AI difficulty (1-6)
2. Press `[1]` to cast spells
3. Destroy enemy HP before yours hits zero!

**That's it!** You're playing.

---

## Multiplayer (vs Friend)

### Step 1: Install dependency
```bash
pip3 install websockets
```

### Step 2: Start server
```bash
cd /home/user/kernel-mage/game
python3 multiplayer_server.py
```
Leave this running.

### Step 3: Connect players

**Option A: Godot (Visual)**
1. Install Godot 4.2+ from https://godotengine.org/
2. Open Godot → Import → Select `game/godot_client/project.godot`
3. Press F5 to run
4. **Player 1**: Enter name, leave room empty, click Connect
5. **Player 2**: Enter name, enter Player 1's room ID, click Connect
6. Battle begins!

**Option B: Terminal (Coming Soon)**
- Terminal multiplayer client in development

---

## Quick Controls

**Single Player:**
- `[1]` Cast spell (use 1-3 magic essences)
- `[2]` Configure defense rule (block magic types)
- `[3]` Discard essence (remove unwanted magic)
- `[5]` Skip turn
- `[Q]` Quit

**Multiplayer (Godot):**
- Click "Cast 1/2/3" buttons
- Click "Configure Rule" for defense
- Click "Ready" to end turn

---

## How It Works (5 second version)

1. **Magic flows in constantly** (3/turn) → Goes to your essence buffer
2. **Cast spells** by combining 1-3 essences (bigger combos = more damage)
3. **Configure defense rules** to block unwanted magic (iptables-style)
4. **Win condition**: Reduce enemy HP to 0

**Key mechanic:** Buffer holds max 10 essences. Overflow = 10 HP damage per extra essence!

---

## Example Turn

```
Turn 5 - Incoming Phase:
→ Magic arrives: 🔥💧⚡
→ Your rules: DROP Fire
→ Accepted: 💧⚡ (added to buffer)

Turn 5 - Action Phase:
Your buffer: [🔥][💧][⚡][🌿][💧]
Your HP: 75/100

Actions:
[1] Cast 3: 🔥💧⚡ → Elemental Storm (35 dmg!)
[2] Configure defense
[5] Skip

> 1
✓ Cast Elemental Storm → 35 damage to enemy!
Enemy HP: 65/100
```

---

## Magic Types

🔥 Fire | 💧 Water | ⚡ Lightning | 🌿 Nature | 🌑 Dark | ✨ Light | ❄️ Ice

Mix them for 76 different spell combos!

---

## AI Difficulty Levels

1. **Novice Mage** - Tutorial bot
2. **Shieldmage** - Heavy defense
3. **Battle Mage** - Aggressive attacker
4. **Adept Mage** - Balanced strategy
5. **Archmage** - Adapts to you
6. **Grand Archmage** - Expert (good luck!)

---

## Need More Info?

- **Game mechanics**: See `README.md`
- **Multiplayer setup**: See `MULTIPLAYER_SETUP.md`
- **Full overview**: See `IMPLEMENTATION_SUMMARY.md`
- **Godot client**: See `godot_client/README.md`

---

## Troubleshooting

**"ModuleNotFoundError: websockets"**
```bash
pip3 install websockets
```

**"Can't connect to server"**
- Make sure `multiplayer_server.py` is running
- Check you're using the right room ID

**"Game too hard!"**
- Start with AI difficulty 1 or 2
- Block Fire/Dark magic first (most common attacks)
- Use 3-essence combos for maximum damage

---

**Now go play!** 🎮✨
