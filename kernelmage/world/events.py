"""Story events system."""
from dataclasses import dataclass, field
from typing import List, Optional, Callable
from enum import Enum


class EventStatus(Enum):
    """Event status."""
    AVAILABLE = "available"      # Can be triggered
    TRIGGERED = "triggered"      # Has been shown
    COMPLETED = "completed"      # Completed with outcome
    LOCKED = "locked"            # Cannot trigger yet


@dataclass
class StoryEvent:
    """A story event that can trigger."""

    event_id: str
    title: str
    description: str
    choices: List[tuple[str, str]] = field(default_factory=list)  # (key, description)

    # Conditions to trigger
    required_level: int = 1
    required_victories: int = 0
    required_location: Optional[str] = None
    trigger_once: bool = True

    # State
    status: EventStatus = EventStatus.AVAILABLE
    times_triggered: int = 0

    def can_trigger(self, player_level: int, victories: int, current_location: str) -> bool:
        """Check if event can trigger."""
        if self.status == EventStatus.LOCKED:
            return False

        if self.trigger_once and self.times_triggered > 0:
            return False

        if player_level < self.required_level:
            return False

        if victories < self.required_victories:
            return False

        if self.required_location and current_location != self.required_location:
            return False

        return True

    def trigger(self):
        """Mark event as triggered."""
        self.status = EventStatus.TRIGGERED
        self.times_triggered += 1

    def complete(self):
        """Mark event as completed."""
        self.status = EventStatus.COMPLETED


# Define story events
WELCOME_EVENT = StoryEvent(
    event_id="welcome",
    title="Welcome to KernelMage",
    description="""
Welcome, young mage!

You stand in the village square, your wand humming with network energy.
You've learned that magic is network communication - spells are packets,
targeting is DNS, and your soul is a network node.

The village elder approaches you with concern in her eyes.

"Dark forces corrupt the spiritual network," she says. "Hostile nodes
spread across the land. Will you help cleanse the network?"
    """,
    choices=[
        ("y", "Accept the quest"),
        ("n", "I need to prepare first"),
    ],
    required_level=1,
    required_victories=0,
    required_location="village",
)

FIRST_VICTORY_EVENT = StoryEvent(
    event_id="first_victory",
    title="First Blood... Er, First Packet Loss",
    description="""
You stand victorious! The enemy's soul node flickers and goes dark,
their network connection severed.

You feel essence flowing into your inventory - the spoils of battle.

A mysterious figure appears from the shadows.

"Well done," they say. "You're learning the truth. But there's much
more to discover about the network that underlies all reality..."

The figure vanishes, leaving you with more questions than answers.
    """,
    choices=[
        ("c", "Continue your journey"),
    ],
    required_victories=1,
)

ARCHITECTURE_DISCOVERY_EVENT = StoryEvent(
    event_id="arch_discovery",
    title="The Architecture Library",
    description="""
You discover an ancient library filled with scrolls about processing
architectures. Each scroll teaches a different way to manipulate magical data.

The librarian, an old mage, explains:

"x86 CISC uses complex, powerful instructions - devastating but costly.
ARM RISC uses simple, efficient operations - perfect for sustained combat.
RISC-V is modular and extensible - flexibility at its finest.

Choose your path, but remember: a wise mage masters all architectures."
    """,
    choices=[
        ("c", "Study the architectures"),
    ],
    required_level=2,
    required_victories=2,
)

NETWORK_REVELATION_EVENT = StoryEvent(
    event_id="network_revelation",
    title="The Truth Revealed",
    description="""
At the Mage Tower, you find ancient documentation labeled "REALITY.SYS".

Reading it, everything becomes clear:

The physical world is just a hardware interface layer. What you see as
bodies and objects are merely display outputs. The REAL world is the
spiritual network - a vast mesh of interconnected soul nodes.

Magic isn't magic at all - it's network communication!

When you cast a "fireball", you're sending a packet with fire essence
data through the network. The physical flames people see are just the
hardware layer rendering the network event.

This changes everything...
    """,
    choices=[
        ("a", "Accept this truth"),
        ("d", "This can't be real..."),
    ],
    required_level=3,
    required_location="mage_tower",
)

DUNGEON_WARNING_EVENT = StoryEvent(
    event_id="dungeon_warning",
    title="The Corrupted Data Center",
    description="""
You stand before the entrance to the Corrupted Data Center.

Dark packets leak from the structure, corrupting everything they touch.
The very air crackles with malicious traffic.

A warning sign flickers:

"DANGER: ISOLATED HOSTILE NETWORK
 SUBNET: 10.66.6.0/24
 PACKET LOSS: 60%
 RECOMMENDED LEVEL: 4+
 TURN BACK NOW"

Do you dare enter?
    """,
    choices=[
        ("e", "Enter the dungeon"),
        ("l", "Leave (not ready yet)"),
    ],
    required_level=4,
    required_location="corrupted_dungeon",
)

BOSS_APPROACH_EVENT = StoryEvent(
    event_id="boss_approach",
    title="The Gateway Awaits",
    description="""
You've reached the Gateway Boss's lair.

This is no ordinary enemy - it's a subnet gateway, controlling an entire
network segment. Its bandwidth is immense, its firewall impenetrable.

Ancient glyphs on the gateway read:

"I am the controller of all traffic in this domain.
 All packets must pass through me.
 Challenge me, and be routed to /dev/null."

This will be your greatest challenge yet.
    """,
    choices=[
        ("f", "Fight the gateway"),
        ("p", "Prepare more first"),
    ],
    required_level=6,
    required_location="gateway_lair",
)


class EventManager:
    """Manages story events."""

    def __init__(self):
        self.events = {
            "welcome": WELCOME_EVENT,
            "first_victory": FIRST_VICTORY_EVENT,
            "arch_discovery": ARCHITECTURE_DISCOVERY_EVENT,
            "network_revelation": NETWORK_REVELATION_EVENT,
            "dungeon_warning": DUNGEON_WARNING_EVENT,
            "boss_approach": BOSS_APPROACH_EVENT,
        }

    def check_events(
        self,
        player_level: int,
        victories: int,
        current_location: str
    ) -> Optional[StoryEvent]:
        """
        Check if any events should trigger.

        Returns the highest priority event that can trigger.
        """
        available = []

        for event in self.events.values():
            if event.can_trigger(player_level, victories, current_location):
                available.append(event)

        # Return first available event (they're in priority order)
        return available[0] if available else None

    def get_event(self, event_id: str) -> Optional[StoryEvent]:
        """Get event by ID."""
        return self.events.get(event_id)

    def get_event_status(self) -> str:
        """Get status of all events as formatted string."""
        lines = []
        lines.append("[bold]Event Status:[/bold]\n")

        for event_id, event in self.events.items():
            status_icon = {
                EventStatus.AVAILABLE: "○",
                EventStatus.TRIGGERED: "◐",
                EventStatus.COMPLETED: "●",
                EventStatus.LOCKED: "✗",
            }[event.status]

            status_color = {
                EventStatus.AVAILABLE: "green",
                EventStatus.TRIGGERED: "yellow",
                EventStatus.COMPLETED: "blue",
                EventStatus.LOCKED: "red",
            }[event.status]

            lines.append(
                f"[{status_color}]{status_icon}[/{status_color}] {event.title}"
            )

        return "\n".join(lines)

    def get_available_events_summary(
        self,
        player_level: int,
        victories: int,
        current_location: str
    ) -> str:
        """Get summary of events that can trigger."""
        available = []

        for event in self.events.values():
            if event.can_trigger(player_level, victories, current_location):
                available.append(event.title)

        if available:
            return "[green]Available events:[/green]\n" + "\n".join(f"  • {title}" for title in available)
        else:
            return "[dim]No events available right now.[/dim]"
