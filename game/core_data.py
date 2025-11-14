"""
Kernel Duel - Core Data Structures

Linux kernel style: Data first, simple relationships, clear ownership
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional
import time


# ============================================================================
# Magic Types - Like protocol types in kernel
# ============================================================================

class MagicType(IntEnum):
    """Magic element types - like IP protocol numbers"""
    FIRE = 0x01      # Red, aggressive
    WATER = 0x02     # Blue, healing
    LIGHTNING = 0x03 # Yellow, high damage
    NATURE = 0x04    # Green, support
    ICE = 0x05       # Cyan, control
    DARK = 0x06      # Purple, powerful
    LIGHT = 0x07     # White, balanced

    @property
    def symbol(self) -> str:
        """Visual representation"""
        symbols = {
            self.FIRE: "🔥",
            self.WATER: "💧",
            self.LIGHTNING: "⚡",
            self.NATURE: "🌿",
            self.ICE: "🧊",
            self.DARK: "🌑",
            self.LIGHT: "✨",
        }
        return symbols[self]

    @property
    def name_str(self) -> str:
        """Element name"""
        return self.name.capitalize()


# ============================================================================
# Essence Buffer - Like sk_buff queue in kernel
# ============================================================================

@dataclass
class EssenceBuffer:
    """
    Circular buffer for magic essence - like ring buffer in NIC driver

    Data:
        essences: List of magic types (max 10)
        capacity: Max buffer size (10)
        overflow_count: How many overflowed this turn
    """
    capacity: int = 10
    essences: List[MagicType] = field(default_factory=list)
    overflow_count: int = 0

    def add(self, magic: MagicType) -> bool:
        """
        Add essence to buffer
        Returns: True if added, False if overflow
        """
        if len(self.essences) < self.capacity:
            self.essences.append(magic)
            return True
        else:
            self.overflow_count += 1
            return False

    def consume(self, count: int) -> List[MagicType]:
        """
        Consume N essences from front (FIFO)
        Returns: List of consumed essences
        """
        if count > len(self.essences):
            count = len(self.essences)

        consumed = self.essences[:count]
        self.essences = self.essences[count:]
        return consumed

    def discard(self, index: int) -> bool:
        """Remove essence at index"""
        if 0 <= index < len(self.essences):
            self.essences.pop(index)
            return True
        return False

    @property
    def count(self) -> int:
        """Current essence count"""
        return len(self.essences)

    @property
    def is_full(self) -> bool:
        """Check if buffer full"""
        return len(self.essences) >= self.capacity

    def reset_overflow(self):
        """Reset overflow counter (called each turn)"""
        self.overflow_count = 0


# ============================================================================
# Defense Rules - Like iptables rules
# ============================================================================

class RuleAction(IntEnum):
    """Rule actions - like netfilter verdicts"""
    DROP = 0      # Block magic
    ACCEPT = 1    # Allow magic
    STRIP = 2     # DPI - extract from mixed


class RuleChain(IntEnum):
    """Rule chains - like netfilter hooks"""
    PREROUTING = 0   # First filter
    INPUT = 1        # Buffer entry
    POSTROUTING = 2  # Outgoing transform


@dataclass
class DefenseRule:
    """
    Single iptables-like rule

    Data:
        chain: Which hook point (PREROUTING/INPUT/POSTROUTING)
        action: What to do (DROP/ACCEPT/STRIP)
        magic_type: Which element to match (None = all)
        source_filter: Filter by enemy IP (True = only enemy)
        cpu_cost: Cost per turn
    """
    chain: RuleChain
    action: RuleAction
    magic_type: Optional[MagicType] = None
    source_filter: bool = False  # True = from enemy IP only
    cpu_cost: int = 0

    def __post_init__(self):
        """Calculate CPU cost - like processing overhead"""
        if self.source_filter and self.magic_type:
            # Compound rule: enemy + type = expensive
            self.cpu_cost = 25
        elif self.source_filter:
            # Source filtering
            self.cpu_cost = 10
        elif self.action == RuleAction.STRIP:
            # DPI is expensive
            self.cpu_cost = 30
        else:
            # Simple type filter
            self.cpu_cost = 5

    def matches(self, magic: MagicType, from_enemy: bool) -> bool:
        """Check if rule matches this magic"""
        type_match = (self.magic_type is None or
                     self.magic_type == magic)
        source_match = (not self.source_filter or
                       from_enemy)
        return type_match and source_match


@dataclass
class RuleSet:
    """
    Collection of rules - like iptables ruleset

    Data:
        rules: List of active rules
        max_rules: Maximum allowed (10)
    """
    rules: List[DefenseRule] = field(default_factory=list)
    max_rules: int = 10

    def add_rule(self, rule: DefenseRule) -> bool:
        """Add rule if space available"""
        if len(self.rules) < self.max_rules:
            self.rules.append(rule)
            return True
        return False

    def remove_rule(self, index: int) -> bool:
        """Remove rule at index"""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            return True
        return False

    def total_cpu_cost(self) -> int:
        """Calculate total CPU cost per turn"""
        return sum(rule.cpu_cost for rule in self.rules)

    def process_magic(self, magic: MagicType, from_enemy: bool,
                     chain: RuleChain) -> RuleAction:
        """
        Process magic through rules in this chain
        Returns: Action to take (default ACCEPT)
        """
        for rule in self.rules:
            if rule.chain == chain and rule.matches(magic, from_enemy):
                return rule.action
        return RuleAction.ACCEPT


# ============================================================================
# Wand - The player's kernel
# ============================================================================

@dataclass
class Wand:
    """
    Player's wand (kernel)

    Data:
        hp: Health (100 max)
        max_hp: Maximum health
        cpu: Available CPU this turn
        max_cpu: CPU per turn (100)
        buffer: Essence buffer (sk_buff queue)
        rules: Defense rules (iptables)
        owner: Player name
    """
    owner: str
    hp: int = 100
    max_hp: int = 100
    cpu: int = 100
    max_cpu: int = 100
    buffer: EssenceBuffer = field(default_factory=EssenceBuffer)
    rules: RuleSet = field(default_factory=RuleSet)

    # Status effects
    shield: int = 0  # Temporary HP
    frozen_essences: int = 0  # How many essences frozen

    def refresh_cpu(self):
        """Refresh CPU at start of turn"""
        self.cpu = self.max_cpu

    def spend_cpu(self, amount: int) -> bool:
        """Spend CPU, return True if successful"""
        if self.cpu >= amount:
            self.cpu -= amount
            return True
        return False

    def take_damage(self, amount: int):
        """
        Take damage - shield absorbs first
        Like: Packet filtering, shield = firewall
        """
        if self.shield > 0:
            if amount <= self.shield:
                self.shield -= amount
                return
            else:
                amount -= self.shield
                self.shield = 0

        self.hp -= amount
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount: int):
        """Heal HP (cannot exceed max)"""
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def add_shield(self, amount: int):
        """Add temporary shield"""
        self.shield += amount

    @property
    def is_alive(self) -> bool:
        """Check if wand still functional"""
        return self.hp > 0

    @property
    def passive_cpu_cost(self) -> int:
        """CPU cost from active rules"""
        return self.rules.total_cpu_cost()


# ============================================================================
# Magic Spell - The result of consuming essence
# ============================================================================

@dataclass
class Spell:
    """
    Spell cast from essence combination

    Data:
        name: Spell name
        elements: Essences consumed
        damage: Damage dealt (negative = heal)
        special: Special effect description
    """
    name: str
    elements: List[MagicType]
    damage: int
    special: str = ""
    shield: int = 0

    @property
    def element_count(self) -> int:
        """How many essences used"""
        return len(self.elements)

    def __str__(self) -> str:
        """String representation"""
        elem_str = "".join(e.symbol for e in self.elements)
        return f"{elem_str} {self.name} ({self.damage} dmg)"


# ============================================================================
# Turn State - Current game state
# ============================================================================

@dataclass
class TurnState:
    """
    Current turn information

    Data:
        turn_number: Current turn (starts at 1)
        phase: Current phase (incoming/action/resolution)
        start_time: When turn started (for real-time)
        phase_duration: How long each phase lasts (seconds)
    """
    turn_number: int = 1
    phase: str = "incoming"  # incoming, action, resolution
    start_time: float = field(default_factory=time.time)

    # Phase durations (seconds)
    incoming_duration: float = 3.0
    action_duration: float = 5.0
    resolution_duration: float = 1.0

    def elapsed(self) -> float:
        """Time since phase started"""
        return time.time() - self.start_time

    def phase_complete(self) -> bool:
        """Check if current phase time is up"""
        durations = {
            "incoming": self.incoming_duration,
            "action": self.action_duration,
            "resolution": self.resolution_duration,
        }
        return self.elapsed() >= durations.get(self.phase, 0)

    def next_phase(self):
        """Advance to next phase"""
        phases = ["incoming", "action", "resolution"]
        current_idx = phases.index(self.phase)

        if current_idx < len(phases) - 1:
            self.phase = phases[current_idx + 1]
        else:
            # New turn
            self.phase = "incoming"
            self.turn_number += 1

        self.start_time = time.time()


# ============================================================================
# Game State - Everything
# ============================================================================

@dataclass
class GameState:
    """
    Complete game state - like kernel's network stack state

    Data:
        player: Player's wand
        enemy: Enemy's wand
        turn: Turn state
        log: Event log
        winner: Who won (None if ongoing)
    """
    player: Wand
    enemy: Wand
    turn: TurnState = field(default_factory=TurnState)
    log: List[str] = field(default_factory=list)
    winner: Optional[str] = None

    # Starvation tracking
    player_no_cast_turns: int = 0
    enemy_no_cast_turns: int = 0

    def add_log(self, message: str):
        """Add message to log"""
        self.log.append(f"Turn {self.turn.turn_number}: {message}")
        # Keep last 50 messages
        if len(self.log) > 50:
            self.log = self.log[-50:]

    def check_victory(self) -> Optional[str]:
        """
        Check win conditions
        Returns: Winner name or None
        """
        # HP-based victory
        if not self.player.is_alive:
            self.winner = self.enemy.owner
            return self.winner
        if not self.enemy.is_alive:
            self.winner = self.player.owner
            return self.winner

        # Starvation-based victory (5 turns no cast)
        if self.player_no_cast_turns >= 5:
            self.winner = self.enemy.owner
            self.add_log(f"{self.player.owner} starved! (5 turns no cast)")
            return self.winner
        if self.enemy_no_cast_turns >= 5:
            self.winner = self.player.owner
            self.add_log(f"{self.enemy.owner} starved! (5 turns no cast)")
            return self.winner

        return None


if __name__ == "__main__":
    # Test data structures
    print("=== Kernel Duel - Data Structure Test ===\n")

    # Create a wand
    wand = Wand(owner="Player")
    print(f"Created wand for {wand.owner}")
    print(f"  HP: {wand.hp}/{wand.max_hp}")
    print(f"  CPU: {wand.cpu}/{wand.max_cpu}")
    print(f"  Buffer: {wand.buffer.count}/{wand.buffer.capacity}\n")

    # Add some essence
    print("Adding essence to buffer:")
    wand.buffer.add(MagicType.FIRE)
    wand.buffer.add(MagicType.WATER)
    wand.buffer.add(MagicType.LIGHTNING)
    for i, essence in enumerate(wand.buffer.essences):
        print(f"  [{i}] {essence.symbol} {essence.name_str}")
    print()

    # Create a rule
    print("Adding defense rule:")
    rule = DefenseRule(
        chain=RuleChain.PREROUTING,
        action=RuleAction.DROP,
        magic_type=MagicType.DARK
    )
    wand.rules.add_rule(rule)
    print(f"  DROP Dark magic (cost: {rule.cpu_cost} CPU)")
    print(f"  Total rule cost: {wand.passive_cpu_cost} CPU/turn\n")

    # Test damage
    print("Testing damage system:")
    print(f"  Before: HP={wand.hp}, Shield={wand.shield}")
    wand.add_shield(20)
    print(f"  Added 20 shield: HP={wand.hp}, Shield={wand.shield}")
    wand.take_damage(15)
    print(f"  Took 15 damage: HP={wand.hp}, Shield={wand.shield}")
    wand.take_damage(10)
    print(f"  Took 10 damage: HP={wand.hp}, Shield={wand.shield}")

    print("\n✓ Data structures working correctly!")
