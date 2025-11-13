"""CPU Architectures - different ways to manipulate magical data."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ArchitectureType(Enum):
    """CPU architecture types."""

    X86_CISC = "x86_cisc"  # Complex, powerful, expensive
    ARM_RISC = "arm_risc"  # Simple, efficient, flexible
    RISCV = "risc_v"  # Modular, extensible
    MIPS = "mips"  # Pipeline master
    SPARC = "sparc"  # Register windows


@dataclass
class Architecture:
    """Architecture configuration for spell processing."""

    arch_type: ArchitectureType
    name: str
    description: str

    # Performance characteristics
    power_multiplier: float  # Damage output multiplier
    mana_efficiency: float  # Mana cost multiplier (lower is better)
    cast_speed: int  # Base cast time modifier (turns added)
    flexibility: int  # Number of operations per cast (1-5)

    # Special abilities
    special_ability: str = ""

    def get_spell_cost(self, base_cost: int) -> int:
        """Calculate actual mana cost based on architecture."""
        return int(base_cost * self.mana_efficiency)

    def get_spell_power(self, base_power: int) -> int:
        """Calculate actual spell power based on architecture."""
        return int(base_power * self.power_multiplier)

    def get_cast_time(self, base_time: int) -> int:
        """Calculate actual cast time based on architecture."""
        return max(1, base_time + self.cast_speed)


# Architecture definitions
X86_CISC = Architecture(
    arch_type=ArchitectureType.X86_CISC,
    name="x86 CISC",
    description="Complex Instruction Set. Powerful single operations, high cost.",
    power_multiplier=1.5,  # 50% more damage
    mana_efficiency=1.5,  # 50% more mana cost
    cast_speed=1,  # +1 turn cast time
    flexibility=1,  # One powerful operation
    special_ability="COMPLEX_BLAST: Single devastating attack",
)

ARM_RISC = Architecture(
    arch_type=ArchitectureType.ARM_RISC,
    name="ARM RISC",
    description="Reduced Instruction Set. Simple, efficient, combinable operations.",
    power_multiplier=0.7,  # 30% less damage per operation
    mana_efficiency=0.6,  # 40% less mana cost
    cast_speed=0,  # No cast time penalty
    flexibility=3,  # Three simple operations
    special_ability="COMBO: Chain multiple simple operations together",
)

RISC_V = Architecture(
    arch_type=ArchitectureType.RISCV,
    name="RISC-V",
    description="Modular architecture with loadable extensions.",
    power_multiplier=1.0,  # Balanced damage
    mana_efficiency=0.8,  # Good efficiency
    cast_speed=0,  # No penalty
    flexibility=2,  # Base operations + extensions
    special_ability="EXTENSIONS: Load modules for special effects",
)

MIPS = Architecture(
    arch_type=ArchitectureType.MIPS,
    name="MIPS",
    description="Pipeline architecture. Multiple spells in flight simultaneously.",
    power_multiplier=0.9,  # Slightly less damage
    mana_efficiency=0.7,  # Very efficient
    cast_speed=-1,  # Faster casting
    flexibility=2,
    special_ability="PIPELINE: Cast while previous spells still traveling",
)

SPARC = Architecture(
    arch_type=ArchitectureType.SPARC,
    name="SPARC",
    description="Register windows for instant loadout switching.",
    power_multiplier=1.0,  # Balanced
    mana_efficiency=1.0,  # Balanced
    cast_speed=0,
    flexibility=2,
    special_ability="REGISTER_WINDOWS: 3 pre-configured loadouts, instant switch",
)

# Architecture registry
ARCHITECTURES = {
    ArchitectureType.X86_CISC: X86_CISC,
    ArchitectureType.ARM_RISC: ARM_RISC,
    ArchitectureType.RISCV: RISC_V,
    ArchitectureType.MIPS: MIPS,
    ArchitectureType.SPARC: SPARC,
}


def get_architecture(arch_type: ArchitectureType) -> Architecture:
    """Get architecture by type."""
    return ARCHITECTURES[arch_type]


@dataclass
class ArchitectureState:
    """Current architecture state for a player/entity."""

    active_architecture: Architecture
    available_architectures: List[Architecture]

    # RISC-V extensions
    loaded_extensions: List[str] = None

    # SPARC register windows (3 preset loadouts)
    register_windows: List[dict] = None  # Each window is a loadout config

    # MIPS pipeline (spells in flight)
    pipeline: List[dict] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.loaded_extensions is None:
            self.loaded_extensions = []
        if self.register_windows is None:
            self.register_windows = [{}, {}, {}]
        if self.pipeline is None:
            self.pipeline = []

    def switch_architecture(self, new_arch: Architecture) -> int:
        """Switch to new architecture. Returns mana cost."""
        if new_arch not in self.available_architectures:
            return -1  # Not available

        # Context switch cost
        mana_cost = 20

        self.active_architecture = new_arch
        return mana_cost
