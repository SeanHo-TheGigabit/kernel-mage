# KernelMage Arena - Quick Guide

## What is Arena Mode?

Arena Mode is a **simplified, pure combat** version of KernelMage. No quests, no world map, no events - just you vs waves of enemies in a mage arena!

## How to Play

```bash
python3 main.py
```

## Game Flow

1. **Enter your mage name**
2. **Choose your starting architecture:**
   - **x86 CISC**: Powerful but slow (High damage, +1 turn cast time)
   - **ARM RISC**: Fast and efficient (Low mana cost, fast cast)
   - **RISC-V**: Balanced (Good all-around)

3. **Fight sequential rounds** of increasingly difficult enemies
4. **Rest between rounds** (restores 30% HP and 40% mana)
5. **Survive as long as you can!**

## Combat Basics

### Your Turn Actions

- **[A] Attack**: Cast a spell at an enemy
  - Choose target enemy
  - Choose essence type (Fire, Water, Lightning, etc.)
  - Choose protocol (TCP/UDP/ICMP)

- **[P] Ping**: Scan an enemy with ICMP ping
  - Shows enemy HP, IP, hostname, firewall status
  - Costs 1 turn but no mana

- **[S] Switch Architecture**: Change your CPU architecture
  - Costs 20 mana and 1 turn
  - Changes spell behavior

- **[I] Inventory**: View your essence supplies

- **[F] Flee**: Can't flee in arena mode!

### Magic System Simplified

**Essences** (Spell elements):
- Fire, Water, Earth, Lightning, Wind, Shadow, Light
- Each has different power ratings
- Use them to cast spells

**Protocols** (How spells are cast):
- **TCP**: Slow (3 turns) but 100% accurate, high mana cost
- **UDP**: Fast (1 turn) but 70% accuracy, low mana cost
- **ICMP Ping**: Information gathering only (1 turn, free)

**Architectures** (CPU processing style):
- **x86 CISC**: 1.5x power, 1.5x cost, +1 turn
- **ARM RISC**: 0.7x power, 0.6x cost, faster
- **RISC-V**: Balanced stats

## Round Progression

| Round | Enemies |
|-------|---------|
| 1 | 1 Bandit (Easy warm-up) |
| 2 | 2 Bandits |
| 3 | 1 Corrupted Node (Stronger) |
| 4 | 3 Swarm Minions |
| 5 | 1 Bandit + 1 Corrupted Node |
| 6 | 1 Illusionist |
| 7 | 2 Corrupted Nodes |
| 8 | 1 Gateway Boss (Tough!) |
| 9+ | Random hard encounters |

## Tips for Success

1. **Manage your mana**: Don't spam TCP spells or you'll run out of mana
2. **Use UDP for weak enemies**: Save mana for harder fights
3. **Ping before attacking**: Know enemy HP to plan your attacks
4. **Switch architecture strategically**: ARM for speed, x86 for power
5. **Rest is automatic**: You heal 30% between rounds
6. **Element weaknesses matter**: Fire beats Earth, Water beats Fire, etc.

## Scoring

Your score is: **Number of rounds survived**

Can you make it to Round 8 and defeat the Gateway Boss?
Can you survive beyond Round 9?

## Example Combat Turn

```
╔═══ Combat ═══╗
Player HP: 80/100  Mana: 90/150  Level: 2

Enemies:
[1] Network Bandit  HP: 50/50

[A] Attack  [P] Ping  [S] Switch Architecture  [I] Inventory  [F] Flee

> a
Select target: 1
Select essence: [1] Fire (30g)
Select protocol: [1] TCP  [2] UDP  [3] ICMP

> 2
> 1
> 2

Casting UDP Fire spell...
Damage: 45
Mana cost: 21
Cast time: 1 turn

Network Bandit takes 45 damage!
Network Bandit defeated!

Victory! Round 1 complete!
```

## Game Over

When you're defeated, you'll see:
- Final score (rounds survived)
- Final level
- Final architecture

Then you can play again and try to beat your high score!

---

**Good luck in the arena, mage!** 🧙‍♂️⚔️
