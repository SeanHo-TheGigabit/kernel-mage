"""Player character class."""
from dataclasses import dataclass, field
from typing import Dict, Optional
from kernelmage.core.entity import Entity
from kernelmage.entities.stats import Stats, NetworkAddress
from kernelmage.magic.essences import Essence, EssenceType, create_starter_essences
from kernelmage.magic.architectures import (
    Architecture, ArchitectureState, ArchitectureType,
    get_architecture, X86_CISC, ARM_RISC, RISC_V
)


@dataclass
class Player(Entity):
    """Player character."""

    # Essence inventory (magical data)
    essences: Dict[EssenceType, Essence] = field(default_factory=dict)

    # Architecture system
    architecture_state: Optional[ArchitectureState] = None

    # DNS cache (known targets)
    dns_cache: Dict[str, NetworkAddress] = field(default_factory=dict)
    dns_cache_size: int = 5  # Max cached targets

    # Experience and progression
    level: int = 1
    experience: int = 0

    def __post_init__(self):
        """Initialize player with defaults."""
        # Set up starter essences if none provided
        if not self.essences:
            self.essences = create_starter_essences()

        # Set up architecture if none provided
        if self.architecture_state is None:
            available = [
                get_architecture(ArchitectureType.X86_CISC),
                get_architecture(ArchitectureType.ARM_RISC),
                get_architecture(ArchitectureType.RISCV),
            ]
            self.architecture_state = ArchitectureState(
                active_architecture=X86_CISC,
                available_architectures=available
            )

        # Set default network address if none
        if not self.network_address.ip:
            self.network_address = NetworkAddress.generate(
                subnet="192.168.1.0/24",
                host_id=42,
                hostname="player_mage"
            )

    @property
    def current_architecture(self) -> Architecture:
        """Get currently active architecture."""
        return self.architecture_state.active_architecture

    def has_essence(self, essence_type: EssenceType, amount: int = 1) -> bool:
        """Check if player has enough essence."""
        essence = self.essences.get(essence_type)
        return essence is not None and essence.quantity >= amount

    def consume_essence(self, essence_type: EssenceType, amount: int) -> bool:
        """Try to consume essence. Returns True if successful."""
        essence = self.essences.get(essence_type)
        if essence and essence.consume(amount):
            return True
        return False

    def add_essence(self, essence_type: EssenceType, amount: int, power: int = 50):
        """Add essence to inventory."""
        if essence_type in self.essences:
            self.essences[essence_type].quantity += amount
        else:
            self.essences[essence_type] = Essence(essence_type, amount, power)

    def cache_target(self, address: NetworkAddress):
        """Add target to DNS cache."""
        # Remove oldest if cache is full
        if len(self.dns_cache) >= self.dns_cache_size:
            # Remove first (oldest) entry
            first_key = next(iter(self.dns_cache))
            del self.dns_cache[first_key]

        # Add new target
        address.is_cached = True
        address.cache_ttl = 10  # Lasts 10 turns
        self.dns_cache[address.ip] = address

    def get_cached_target(self, ip: str) -> Optional[NetworkAddress]:
        """Get target from DNS cache."""
        return self.dns_cache.get(ip)

    def flush_dns_cache(self):
        """Clear all DNS cache entries."""
        self.dns_cache.clear()

    def switch_architecture(self, new_arch_type: ArchitectureType) -> bool:
        """Switch to a different architecture."""
        new_arch = get_architecture(new_arch_type)
        cost = self.architecture_state.switch_architecture(new_arch)

        if cost < 0:
            return False  # Architecture not available

        if self.stats.spend_mana(cost):
            return True  # Successfully switched
        return False  # Not enough mana

    def gain_experience(self, amount: int):
        """Gain experience points."""
        self.experience += amount
        # Simple leveling: 100 XP per level
        while self.experience >= self.level * 100:
            self.level_up()

    def level_up(self):
        """Level up the player."""
        self.level += 1
        # Stat increases
        self.stats.max_hp += 20
        self.stats.current_hp = self.stats.max_hp
        self.stats.max_mana += 30
        self.stats.current_mana = self.stats.max_mana
        self.stats.power += 2
        self.stats.defense += 1


def create_player(name: str = "Mage") -> Player:
    """Create a new player character."""
    stats = Stats(
        max_hp=100,
        current_hp=100,
        max_mana=150,
        current_mana=150,
        bandwidth=100,
        packet_loss=0.05,
        latency=1,
        power=10,
        defense=5,
    )

    return Player(
        name=name,
        stats=stats,
        symbol="@",
        description="A mage learning the secrets of network magic"
    )
