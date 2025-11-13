"""World map and location connections."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class LocationId(Enum):
    """Location identifiers."""
    VILLAGE = "village"
    HIGHWAY = "highway"
    FOREST = "forest"
    CORRUPTED_DUNGEON = "corrupted_dungeon"
    MAGE_TOWER = "mage_tower"
    GATEWAY_LAIR = "gateway_lair"


@dataclass
class Location:
    """A location in the game world."""

    location_id: LocationId
    name: str
    description: str
    subnet: str                     # Network subnet

    # Connections to other locations
    connected_to: List[LocationId] = field(default_factory=list)

    # Encounters
    enemy_types: List[str] = field(default_factory=list)
    min_enemies: int = 1
    max_enemies: int = 3

    # Properties
    danger_level: int = 1
    is_safe_zone: bool = False
    is_dungeon: bool = False
    required_level: int = 1          # Level required to enter

    # Network properties
    base_latency: int = 1
    packet_loss_modifier: float = 0.0
    congestion: float = 0.0

    # Map position (for visual display)
    map_x: int = 0
    map_y: int = 0

    def can_access(self, player_level: int) -> bool:
        """Check if player can access this location."""
        return player_level >= self.required_level


# Define all locations
VILLAGE = Location(
    location_id=LocationId.VILLAGE,
    name="Peaceful Village",
    description="A safe village protected by firewalls. Your home base.",
    subnet="192.168.1.0/24",
    connected_to=[LocationId.HIGHWAY, LocationId.FOREST],
    is_safe_zone=True,
    enemy_types=[],
    map_x=2,
    map_y=2,
)

HIGHWAY = Location(
    location_id=LocationId.HIGHWAY,
    name="Highway Network",
    description="Wide area network with bandit activity.",
    subnet="10.0.0.0/8",
    connected_to=[LocationId.VILLAGE, LocationId.MAGE_TOWER, LocationId.CORRUPTED_DUNGEON],
    enemy_types=["bandit", "swarm_minion"],
    min_enemies=1,
    max_enemies=3,
    danger_level=1,
    base_latency=2,
    packet_loss_modifier=0.05,
    map_x=4,
    map_y=2,
)

FOREST = Location(
    location_id=LocationId.FOREST,
    name="Network Forest",
    description="Tangled mesh network with wild packets.",
    subnet="10.10.0.0/16",
    connected_to=[LocationId.VILLAGE, LocationId.MAGE_TOWER],
    enemy_types=["swarm_minion", "corrupted_node"],
    min_enemies=2,
    max_enemies=4,
    danger_level=2,
    base_latency=2,
    packet_loss_modifier=0.10,
    map_x=2,
    map_y=0,
)

MAGE_TOWER = Location(
    location_id=LocationId.MAGE_TOWER,
    name="Mage Tower Relay",
    description="Network relay station. Safe haven for mages.",
    subnet="172.16.0.0/12",
    connected_to=[LocationId.HIGHWAY, LocationId.FOREST, LocationId.GATEWAY_LAIR],
    is_safe_zone=True,
    enemy_types=[],
    required_level=3,
    map_x=4,
    map_y=0,
)

CORRUPTED_DUNGEON = Location(
    location_id=LocationId.CORRUPTED_DUNGEON,
    name="Corrupted Data Center",
    description="Isolated hostile network. Dangerous!",
    subnet="10.66.6.0/24",
    connected_to=[LocationId.HIGHWAY],
    enemy_types=["corrupted_node", "illusionist", "swarm_minion"],
    min_enemies=2,
    max_enemies=4,
    danger_level=3,
    is_dungeon=True,
    required_level=4,
    base_latency=3,
    packet_loss_modifier=0.15,
    congestion=0.6,
    map_x=6,
    map_y=2,
)

GATEWAY_LAIR = Location(
    location_id=LocationId.GATEWAY_LAIR,
    name="Gateway Boss Lair",
    description="Subnet gateway controlled by powerful boss.",
    subnet="10.99.99.0/24",
    connected_to=[LocationId.MAGE_TOWER],
    enemy_types=["gateway_boss", "corrupted_node"],
    min_enemies=1,
    max_enemies=2,
    danger_level=5,
    is_dungeon=True,
    required_level=6,
    base_latency=1,
    congestion=0.3,
    map_x=6,
    map_y=0,
)

# Location registry
LOCATIONS: Dict[LocationId, Location] = {
    LocationId.VILLAGE: VILLAGE,
    LocationId.HIGHWAY: HIGHWAY,
    LocationId.FOREST: FOREST,
    LocationId.MAGE_TOWER: MAGE_TOWER,
    LocationId.CORRUPTED_DUNGEON: CORRUPTED_DUNGEON,
    LocationId.GATEWAY_LAIR: GATEWAY_LAIR,
}


class WorldMap:
    """Manages the world map and locations."""

    def __init__(self):
        self.locations = LOCATIONS
        self.current_location_id = LocationId.VILLAGE
        self.discovered_locations = {LocationId.VILLAGE}  # Start with village discovered

    @property
    def current_location(self) -> Location:
        """Get current location."""
        return self.locations[self.current_location_id]

    def travel_to(self, location_id: LocationId, player_level: int) -> tuple[bool, str]:
        """
        Travel to a location.

        Returns:
            (success: bool, message: str)
        """
        if location_id not in self.locations:
            return (False, "Unknown location!")

        destination = self.locations[location_id]

        # Check if connected
        if location_id not in self.current_location.connected_to:
            return (False, f"Cannot reach {destination.name} from here!")

        # Check level requirement
        if not destination.can_access(player_level):
            return (False, f"Level {destination.required_level} required!")

        # Travel successful
        self.current_location_id = location_id
        self.discovered_locations.add(location_id)

        return (True, f"Traveled to {destination.name}!")

    def get_connected_locations(self) -> List[Location]:
        """Get locations connected to current location."""
        current = self.current_location
        return [self.locations[loc_id] for loc_id in current.connected_to]

    def get_discovered_locations(self) -> List[Location]:
        """Get all discovered locations."""
        return [self.locations[loc_id] for loc_id in self.discovered_locations]

    def is_discovered(self, location_id: LocationId) -> bool:
        """Check if location has been discovered."""
        return location_id in self.discovered_locations

    def get_map_ascii(self, player_level: int) -> str:
        """
        Generate ASCII map of the world.

        Shows discovered locations, current position, and connections.
        """
        # Create 7x3 grid
        grid = [[" " for _ in range(7)] for _ in range(3)]

        # Place locations on grid
        for loc_id, loc in self.locations.items():
            if self.is_discovered(loc_id):
                # Show location symbol
                if loc_id == self.current_location_id:
                    symbol = "@"  # Current location
                elif loc.is_safe_zone:
                    symbol = "H"  # Home/Haven
                elif loc.is_dungeon:
                    symbol = "D"  # Dungeon
                else:
                    symbol = "."  # Normal area

                # Check if accessible
                if not loc.can_access(player_level):
                    symbol = "?"  # Locked

                grid[loc.map_y][loc.map_x] = symbol
            else:
                # Undiscovered
                grid[loc.map_y][loc.map_x] = "?"

        # Build ASCII map
        lines = []
        lines.append("╔═════════════════════════════╗")
        lines.append("║     WORLD MAP               ║")
        lines.append("╠═════════════════════════════╣")

        for row in grid:
            line = "║  " + "   ".join(row) + "  ║"
            lines.append(line)

        lines.append("╠═════════════════════════════╣")
        lines.append("║ @ = You   H = Safe          ║")
        lines.append("║ . = Area  D = Dungeon       ║")
        lines.append("║ ? = Locked/Unknown          ║")
        lines.append("╚═════════════════════════════╝")

        return "\n".join(lines)

    def get_location_info(self, location_id: LocationId) -> str:
        """Get detailed info about a location."""
        if not self.is_discovered(location_id):
            return "??? - Undiscovered"

        loc = self.locations[location_id]

        info = f"[bold]{loc.name}[/bold]\n"
        info += f"{loc.description}\n\n"
        info += f"Network: {loc.subnet}\n"
        info += f"Danger Level: {'⚠' * loc.danger_level}\n"

        if loc.required_level > 1:
            info += f"Required Level: {loc.required_level}\n"

        if loc.is_safe_zone:
            info += "✓ Safe Zone\n"
        elif loc.is_dungeon:
            info += "⚔ Dungeon\n"

        # Show connections
        if loc.connected_to:
            info += f"\nConnected to: "
            names = [self.locations[lid].name for lid in loc.connected_to
                     if self.is_discovered(lid)]
            info += ", ".join(names)

        return info
