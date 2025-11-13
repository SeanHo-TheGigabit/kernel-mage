"""Magical essences (data types) system."""
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class EssenceType(Enum):
    """Types of magical essences (data)."""

    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    LIGHTNING = "lightning"
    WIND = "wind"
    SHADOW = "shadow"
    LIGHT = "light"


@dataclass
class Essence:
    """A magical essence (the actual data being processed)."""

    essence_type: EssenceType
    quantity: int  # In grams
    power_rating: int  # Base power (0-100)

    # Visual properties
    COLOR_MAP = {
        EssenceType.FIRE: "red",
        EssenceType.WATER: "blue",
        EssenceType.EARTH: "green",
        EssenceType.LIGHTNING: "yellow",
        EssenceType.WIND: "cyan",
        EssenceType.SHADOW: "magenta",
        EssenceType.LIGHT: "white",
    }

    # Element interactions (weakness/resistance)
    EFFECTIVENESS = {
        EssenceType.FIRE: {EssenceType.WATER: 0.5, EssenceType.EARTH: 1.5},
        EssenceType.WATER: {EssenceType.LIGHTNING: 0.5, EssenceType.FIRE: 1.5},
        EssenceType.EARTH: {EssenceType.WIND: 0.5, EssenceType.LIGHTNING: 1.5},
        EssenceType.LIGHTNING: {EssenceType.EARTH: 0.5, EssenceType.WATER: 1.5},
        EssenceType.WIND: {EssenceType.EARTH: 1.5, EssenceType.FIRE: 0.5},
        EssenceType.SHADOW: {EssenceType.LIGHT: 0.5},
        EssenceType.LIGHT: {EssenceType.SHADOW: 1.5},
    }

    @property
    def color(self) -> str:
        """Get the display color for this essence."""
        return self.COLOR_MAP.get(self.essence_type, "white")

    def get_effectiveness(self, target_type: EssenceType) -> float:
        """Get damage multiplier against target essence type."""
        return self.EFFECTIVENESS.get(self.essence_type, {}).get(target_type, 1.0)

    def consume(self, amount: int) -> bool:
        """Try to consume essence. Returns True if successful."""
        if self.quantity >= amount:
            self.quantity -= amount
            return True
        return False

    def __str__(self) -> str:
        """String representation."""
        return f"{self.essence_type.value.title()} Essence ({self.quantity}g, {self.power_rating} power)"


# Default essence inventory for new players
def create_starter_essences() -> Dict[EssenceType, Essence]:
    """Create starter essence inventory."""
    return {
        EssenceType.FIRE: Essence(EssenceType.FIRE, quantity=50, power_rating=80),
        EssenceType.WATER: Essence(EssenceType.WATER, quantity=30, power_rating=65),
        EssenceType.LIGHTNING: Essence(EssenceType.LIGHTNING, quantity=10, power_rating=100),
        EssenceType.EARTH: Essence(EssenceType.EARTH, quantity=100, power_rating=50),
        EssenceType.WIND: Essence(EssenceType.WIND, quantity=40, power_rating=70),
        EssenceType.SHADOW: Essence(EssenceType.SHADOW, quantity=20, power_rating=75),
        EssenceType.LIGHT: Essence(EssenceType.LIGHT, quantity=15, power_rating=85),
    }
