# Extending KernelMage - Content Creation Guide

This guide shows you how to easily extend KernelMage with new content: enemies, quests, story events, dungeons, and more.

## Table of Contents

1. [Adding New Enemies](#adding-new-enemies)
2. [Adding Story Events](#adding-story-events)
3. [Adding Quests](#adding-quests)
4. [Adding Locations/Dungeons](#adding-locationsdungeons)
5. [Adding Items/Equipment](#adding-itemsequipment)
6. [Adding Essences](#adding-essences)
7. [Adding Architectures](#adding-architectures)
8. [Adding Protocols](#adding-protocols)

---

## Adding New Enemies

**File**: `kernelmage/entities/enemy.py`

Enemies are created using factory functions. Here's how to add a new one:

```python
def create_my_custom_enemy() -> Enemy:
    """Create my custom enemy."""
    stats = Stats(
        max_hp=75,              # Hit points
        current_hp=75,
        max_mana=60,            # Bandwidth
        current_mana=60,
        bandwidth=80,           # Affects spell power
        packet_loss=0.12,       # 12% miss chance
        latency=1,              # Turns delay
        power=8,                # Attack power
        defense=4,              # Firewall strength
    )

    return Enemy(
        name="Custom Enemy",
        stats=stats,
        symbol="C",             # Single character for map display
        description="A dangerous custom enemy",
        essence_drop=EssenceType.SHADOW,    # What they drop
        essence_drop_amount=20,             # How much
        xp_reward=45,                       # Experience points
        aggression=0.75,                    # 75% chance to attack
        preferred_essence=EssenceType.SHADOW,  # What they cast
    )
```

**Then use it in encounters:**

```python
# In core/game.py, add to start_random_encounter():
elif encounter_type == 5:
    enemies = [create_my_custom_enemy()]
```

---

## Adding Story Events

**Step 1**: Create a story module

Create `kernelmage/story/events.py`:

```python
"""Story events and narrative."""
from dataclasses import dataclass
from typing import Callable, Optional
from kernelmage.entities.player import Player


@dataclass
class StoryEvent:
    """A story event that can trigger."""

    event_id: str                    # Unique identifier
    title: str                       # Event title
    description: str                 # What happens
    choices: list[tuple[str, str]]   # (key, description) choices

    # Conditions
    required_level: int = 1
    required_victories: int = 0
    required_items: list[str] = None

    # Flags
    triggered: bool = False
    completed: bool = False

    def can_trigger(self, player: Player, game_state) -> bool:
        """Check if event can trigger."""
        if self.triggered:
            return False

        if player.level < self.required_level:
            return False

        if game_state.encounters_won < self.required_victories:
            return False

        return True

    def trigger(self):
        """Mark event as triggered."""
        self.triggered = True


# Define story events
INTRO_EVENT = StoryEvent(
    event_id="intro",
    title="The Network Awakens",
    description="""
You stand in the village square, your wand (a custom NIC) humming with power.
The village elder approaches you.

"Young mage," she says, "You've learned that magic is network communication.
But dark forces corrupt the spiritual network. Will you help us?"
    """,
    choices=[
        ("y", "Accept the quest"),
        ("n", "Decline for now"),
    ],
    required_level=1,
)

FIRST_VICTORY_EVENT = StoryEvent(
    event_id="first_victory",
    title="Your First Victory",
    description="""
You stand over the defeated bandit, his soul node flickering and going dark.
You feel the essence flowing into your inventory.

"Well done," a voice says. A mysterious mage appears.
"You're learning. But there's much more to discover about the network..."
    """,
    choices=[
        ("c", "Continue"),
    ],
    required_victories=1,
)

ARCHITECTURE_DISCOVERY_EVENT = StoryEvent(
    event_id="arch_discovery",
    title="The Architecture Library",
    description="""
You discover an ancient library filled with scrolls about different
processing architectures. Each one teaches a different way to manipulate
magical data.

x86 CISC: Powerful but expensive
ARM RISC: Efficient and flexible
RISC-V: Modular and extensible

Which path calls to you?
    """,
    choices=[
        ("x", "Study x86 CISC"),
        ("a", "Study ARM RISC"),
        ("r", "Study RISC-V"),
    ],
    required_level=2,
)

# Event registry
ALL_EVENTS = {
    "intro": INTRO_EVENT,
    "first_victory": FIRST_VICTORY_EVENT,
    "arch_discovery": ARCHITECTURE_DISCOVERY_EVENT,
}


class EventManager:
    """Manages story events."""

    def __init__(self):
        self.events = ALL_EVENTS.copy()
        self.event_queue = []

    def check_events(self, player: Player, game_state) -> Optional[StoryEvent]:
        """Check if any events should trigger."""
        for event in self.events.values():
            if event.can_trigger(player, game_state):
                return event
        return None

    def complete_event(self, event_id: str):
        """Mark event as completed."""
        if event_id in self.events:
            self.events[event_id].completed = True
```

**Step 2**: Integrate into game loop

In `kernelmage/core/game.py`:

```python
from kernelmage.story.events import EventManager

class GameState:
    def __init__(self):
        # ... existing ...
        self.event_manager = EventManager()

    def handle_main_menu(self):
        """Handle main menu interaction."""
        while self.running:
            # Check for story events
            event = self.event_manager.check_events(self.player, self)
            if event:
                self.show_story_event(event)

            choice = self.show_main_menu()
            # ... rest of code ...

    def show_story_event(self, event: StoryEvent):
        """Display a story event."""
        self.display.clear()
        self.display.print_panel(event.description, title=event.title, style="cyan")

        if event.choices:
            choice = self.display.show_menu("What do you do?", event.choices)
            # Handle choice
            self.handle_event_choice(event, choice)

        event.trigger()
        self.display.pause()

    def handle_event_choice(self, event: StoryEvent, choice: str):
        """Handle player choice in event."""
        # Implement consequences based on event_id and choice
        if event.event_id == "intro" and choice == "y":
            self.display.show_message("Quest accepted!", style="green")
        elif event.event_id == "arch_discovery":
            # Could unlock new architectures, etc.
            pass
```

---

## Adding Quests

**Step 1**: Create quest system

Create `kernelmage/story/quests.py`:

```python
"""Quest system."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class QuestStatus(Enum):
    """Quest status."""
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Quest:
    """A quest with objectives."""

    quest_id: str
    title: str
    description: str

    # Objectives
    objectives: Dict[str, Any] = field(default_factory=dict)
    # Example: {"defeat_bandits": 5, "collect_fire_essence": 100}

    progress: Dict[str, int] = field(default_factory=dict)

    # Rewards
    xp_reward: int = 0
    essence_rewards: Dict[str, int] = field(default_factory=dict)

    status: QuestStatus = QuestStatus.AVAILABLE

    def accept(self):
        """Accept the quest."""
        self.status = QuestStatus.ACTIVE
        self.progress = {key: 0 for key in self.objectives.keys()}

    def update_progress(self, objective: str, amount: int = 1):
        """Update quest progress."""
        if objective in self.progress:
            self.progress[objective] = min(
                self.progress[objective] + amount,
                self.objectives[objective]
            )

            # Check completion
            if self.is_completed():
                self.status = QuestStatus.COMPLETED

    def is_completed(self) -> bool:
        """Check if quest is completed."""
        for objective, target in self.objectives.items():
            if self.progress.get(objective, 0) < target:
                return False
        return True

    def get_progress_text(self) -> str:
        """Get progress as text."""
        lines = []
        for objective, target in self.objectives.items():
            current = self.progress.get(objective, 0)
            lines.append(f"  - {objective}: {current}/{target}")
        return "\n".join(lines)


# Define quests
BANDIT_QUEST = Quest(
    quest_id="clear_bandits",
    title="Clear the Highway",
    description="Bandits are terrorizing the highway. Defeat 5 bandits.",
    objectives={"defeat_bandits": 5},
    xp_reward=150,
    essence_rewards={"fire": 50, "lightning": 25},
)

ESSENCE_COLLECTION_QUEST = Quest(
    quest_id="collect_essences",
    title="Essence Collection",
    description="Collect various essences for the village mage.",
    objectives={
        "fire_essence": 100,
        "water_essence": 50,
        "lightning_essence": 25,
    },
    xp_reward=200,
)

ARCHITECTURE_MASTERY_QUEST = Quest(
    quest_id="master_architectures",
    title="Architecture Mastery",
    description="Win battles using each different architecture.",
    objectives={
        "x86_victories": 3,
        "arm_victories": 3,
        "riscv_victories": 3,
    },
    xp_reward=300,
)


class QuestManager:
    """Manages quests."""

    def __init__(self):
        self.quests: Dict[str, Quest] = {
            "clear_bandits": BANDIT_QUEST,
            "collect_essences": ESSENCE_COLLECTION_QUEST,
            "master_architectures": ARCHITECTURE_MASTERY_QUEST,
        }

    def get_active_quests(self) -> list[Quest]:
        """Get all active quests."""
        return [q for q in self.quests.values() if q.status == QuestStatus.ACTIVE]

    def get_available_quests(self) -> list[Quest]:
        """Get available quests."""
        return [q for q in self.quests.values() if q.status == QuestStatus.AVAILABLE]

    def update_quest(self, quest_id: str, objective: str, amount: int = 1):
        """Update quest progress."""
        if quest_id in self.quests:
            self.quests[quest_id].update_progress(objective, amount)
```

**Step 2**: Integrate quest tracking

In `kernelmage/core/game.py`:

```python
from kernelmage.story.quests import QuestManager

class GameState:
    def __init__(self):
        # ... existing ...
        self.quest_manager = QuestManager()

    def run_combat(self):
        """Run combat encounter."""
        # ... existing combat code ...

        if encounter.state == CombatState.VICTORY:
            # Update quest progress
            for enemy in encounter.enemies:
                if enemy.name == "Bandit":
                    self.quest_manager.update_quest("clear_bandits", "defeat_bandits", 1)

            # Check architecture used
            arch_name = self.player.current_architecture.arch_type.value
            self.quest_manager.update_quest(
                "master_architectures",
                f"{arch_name}_victories",
                1
            )
```

---

## Adding Locations/Dungeons

**Step 1**: Create location system

Create `kernelmage/world/locations.py`:

```python
"""Locations and dungeons."""
from dataclasses import dataclass, field
from typing import List, Optional
from kernelmage.entities.enemy import Enemy


@dataclass
class Location:
    """A location in the game world."""

    location_id: str
    name: str
    description: str
    subnet: str                     # Network subnet (e.g., "192.168.1.0/24")

    # Encounters
    enemy_types: List[str] = field(default_factory=list)  # Enemy factory names
    min_enemies: int = 1
    max_enemies: int = 3

    # Properties
    danger_level: int = 1
    is_safe_zone: bool = False
    is_dungeon: bool = False

    # Network properties
    base_latency: int = 1
    packet_loss_modifier: float = 0.0    # Added to base packet loss
    congestion: float = 0.0              # Network congestion (0.0-1.0)


# Define locations
VILLAGE = Location(
    location_id="village",
    name="Peaceful Village",
    description="A safe village protected by firewalls. Network: 192.168.1.0/24",
    subnet="192.168.1.0/24",
    is_safe_zone=True,
    enemy_types=[],
)

HIGHWAY = Location(
    location_id="highway",
    name="Highway Network",
    description="Wide area network with bandit activity. Network: 10.0.0.0/8",
    subnet="10.0.0.0/8",
    enemy_types=["bandit", "swarm_minion"],
    min_enemies=1,
    max_enemies=3,
    danger_level=1,
    base_latency=2,
    packet_loss_modifier=0.05,
)

CORRUPTED_DUNGEON = Location(
    location_id="corrupted_dungeon",
    name="Corrupted Data Center",
    description="Isolated hostile network. Network: 10.66.6.0/24",
    subnet="10.66.6.0/24",
    enemy_types=["corrupted_node", "illusionist", "swarm_minion"],
    min_enemies=2,
    max_enemies=4,
    danger_level=3,
    is_dungeon=True,
    base_latency=3,
    packet_loss_modifier=0.15,
    congestion=0.6,
)

BOSS_LAIR = Location(
    location_id="gateway_lair",
    name="Gateway Boss Lair",
    description="Subnet gateway controlled by powerful boss. Network: 10.99.99.0/24",
    subnet="10.99.99.0/24",
    enemy_types=["gateway_boss", "corrupted_node"],
    min_enemies=1,
    max_enemies=2,
    danger_level=5,
    is_dungeon=True,
    base_latency=1,
    congestion=0.3,
)

# Location registry
LOCATIONS = {
    "village": VILLAGE,
    "highway": HIGHWAY,
    "corrupted_dungeon": CORRUPTED_DUNGEON,
    "gateway_lair": BOSS_LAIR,
}


class WorldManager:
    """Manages world locations."""

    def __init__(self):
        self.locations = LOCATIONS
        self.current_location_id = "village"

    @property
    def current_location(self) -> Location:
        """Get current location."""
        return self.locations[self.current_location_id]

    def travel_to(self, location_id: str) -> bool:
        """Travel to a location."""
        if location_id in self.locations:
            self.current_location_id = location_id
            return True
        return False

    def get_available_locations(self) -> List[Location]:
        """Get locations player can travel to."""
        # Could add logic for unlocking locations
        return list(self.locations.values())
```

**Step 2**: Add travel menu

In `kernelmage/core/game.py`:

```python
from kernelmage.world.locations import WorldManager

class GameState:
    def __init__(self):
        # ... existing ...
        self.world_manager = WorldManager()

    def show_main_menu(self) -> str:
        """Show main menu."""
        # ... existing ...

        options = [
            ("e", f"Explore {self.world_manager.current_location.name}"),
            ("t", "Travel"),
            ("i", "View Inventory"),
            # ... rest ...
        ]

        return self.display.show_menu("Main Menu", options)

    def handle_main_menu(self):
        """Handle main menu interaction."""
        while self.running:
            choice = self.show_main_menu()

            if choice == "e":
                self.explore_location()
            elif choice == "t":
                self.travel_menu()
            # ... rest ...

    def travel_menu(self):
        """Show travel menu."""
        self.display.clear()
        self.display.console.print("\n[bold]Travel to:[/bold]\n")

        locations = self.world_manager.get_available_locations()
        for i, loc in enumerate(locations, 1):
            current = " [HERE]" if loc.location_id == self.world_manager.current_location_id else ""
            danger = f"⚠ Danger: {loc.danger_level}"

            self.display.console.print(
                f"[{i}] {loc.name}{current}\n"
                f"    {loc.description}\n"
                f"    {danger}\n"
            )

        choice = self.display.prompt_input("Select location (or 'c' to cancel):")

        if choice.lower() == 'c':
            return

        try:
            idx = int(choice) - 1
            location = locations[idx]

            if self.world_manager.travel_to(location.location_id):
                self.display.show_message(
                    f"Traveled to {location.name}!\n{location.description}",
                    style="green"
                )
        except (ValueError, IndexError):
            self.display.show_message("Invalid choice!", style="red")

        self.display.pause()

    def explore_location(self):
        """Explore current location (trigger encounter)."""
        location = self.world_manager.current_location

        if location.is_safe_zone:
            self.display.show_message("This is a safe zone. No encounters here.", style="cyan")
            self.display.pause()
            return

        # Generate encounter based on location
        self.start_location_encounter(location)
```

---

## Adding Items/Equipment

Create `kernelmage/items/equipment.py`:

```python
"""Equipment system."""
from dataclasses import dataclass
from enum import Enum


class EquipmentSlot(Enum):
    """Equipment slots."""
    WAND = "wand"          # NIC
    ROBE = "robe"          # Firewall
    AMULET = "amulet"      # Router
    RING = "ring"          # DNS cache
    BOOTS = "boots"        # Subnet hopper


@dataclass
class Equipment:
    """An equipment item."""

    item_id: str
    name: str
    description: str
    slot: EquipmentSlot

    # Stat bonuses
    bandwidth_bonus: int = 0
    power_bonus: int = 0
    defense_bonus: int = 0
    mana_bonus: int = 0
    packet_loss_reduction: float = 0.0

    # Special effects
    special_effect: str = ""


# Define equipment
BASIC_WAND = Equipment(
    item_id="basic_wand",
    name="Basic Wand",
    description="A simple NIC. 100 Mbps bandwidth.",
    slot=EquipmentSlot.WAND,
    bandwidth_bonus=0,
    power_bonus=0,
)

GIGABIT_WAND = Equipment(
    item_id="gigabit_wand",
    name="Gigabit Wand",
    description="High-performance NIC. 1000 Mbps bandwidth!",
    slot=EquipmentSlot.WAND,
    bandwidth_bonus=50,
    power_bonus=5,
    packet_loss_reduction=0.05,
)

FIREWALL_ROBE = Equipment(
    item_id="firewall_robe",
    name="Firewall Robes",
    description="Enchanted robes that block incoming packets.",
    slot=EquipmentSlot.ROBE,
    defense_bonus=5,
)

ROUTER_AMULET = Equipment(
    item_id="router_amulet",
    name="Router Amulet",
    description="Optimizes spell routing.",
    slot=EquipmentSlot.AMULET,
    special_effect="Reduces routing hops by 1",
)
```

---

## Quick Reference

### Adding Content Checklist

**New Enemy**:
1. Create factory function in `entities/enemy.py`
2. Add to encounter generation in `core/game.py`

**New Story Event**:
1. Define `StoryEvent` in `story/events.py`
2. Add trigger conditions
3. Handle in `GameState.show_story_event()`

**New Quest**:
1. Define `Quest` in `story/quests.py`
2. Add to `QuestManager`
3. Update progress in relevant game actions

**New Location**:
1. Define `Location` in `world/locations.py`
2. Add to `LOCATIONS` registry
3. Add to travel menu

**New Item**:
1. Define `Equipment` in `items/equipment.py`
2. Add equip/unequip logic
3. Apply stat bonuses

---

## Summary

KernelMage is designed to be **easily extensible**:

- ✅ **Data-driven** - Add content by creating data structures
- ✅ **Factory pattern** - Easy entity creation
- ✅ **Registry pattern** - Central repositories for content
- ✅ **Modular** - Systems are independent and composable
- ✅ **Type-safe** - Enums and type hints prevent errors

You can add new enemies, quests, locations, and events **without modifying core game logic**!
