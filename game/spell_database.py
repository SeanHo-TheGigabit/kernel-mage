"""
Spell Database - All magic combinations

Data-driven design: Spells are data, not code
Like kernel's protocol handlers - registered in a table
"""

from typing import List, Dict, Tuple
from core_data import MagicType, Spell


# ============================================================================
# Spell Database - Static data table
# ============================================================================

# Format: (elements_tuple) -> (name, damage, special, shield)
# Damage: positive = damage enemy, negative = heal self
# Shield: amount of shield to add

SPELL_DATA: Dict[Tuple[MagicType, ...], Tuple[str, int, str, int]] = {
    # Single element (7 spells)
    (MagicType.FIRE,): ("Fireball", 10, "", 0),
    (MagicType.WATER,): ("Water Splash", -8, "heal", 0),
    (MagicType.LIGHTNING,): ("Lightning Bolt", 12, "", 0),
    (MagicType.NATURE,): ("Nature's Touch", -6, "heal", 0),
    (MagicType.ICE,): ("Ice Shard", 10, "", 0),
    (MagicType.DARK,): ("Dark Pulse", 15, "", 0),
    (MagicType.LIGHT,): ("Light Beam", 12, "", 0),

    # Fire combos (most common)
    (MagicType.FIRE, MagicType.FIRE): ("Inferno", 25, "", 0),
    (MagicType.FIRE, MagicType.WATER): ("Steam Blast", 20, "bypass fire resist", 0),
    (MagicType.FIRE, MagicType.LIGHTNING): ("Explosion", 24, "", 0),
    (MagicType.FIRE, MagicType.NATURE): ("Wildfire", 18, "DoT +2", 0),
    (MagicType.FIRE, MagicType.ICE): ("Thermal Shock", 22, "ignore shield", 0),
    (MagicType.FIRE, MagicType.DARK): ("Hellfire", 28, "", 0),
    (MagicType.FIRE, MagicType.LIGHT): ("Solar Flare", 20, "blind -20 CPU", 0),

    # Water combos
    (MagicType.WATER, MagicType.FIRE): ("Boiling Water", 18, "", 0),
    (MagicType.WATER, MagicType.WATER): ("Tsunami", 16, "clear buffer", 0),
    (MagicType.WATER, MagicType.LIGHTNING): ("Electrocution", 26, "", 0),
    (MagicType.WATER, MagicType.NATURE): ("Healing Spring", -15, "heal", 0),
    (MagicType.WATER, MagicType.ICE): ("Blizzard", 20, "slow", 0),
    (MagicType.WATER, MagicType.DARK): ("Dark Tide", 22, "drain essence", 0),
    (MagicType.WATER, MagicType.LIGHT): ("Holy Water", -12, "heal + cure", 0),

    # Lightning combos
    (MagicType.LIGHTNING, MagicType.FIRE): ("Lightning Fire", 23, "", 0),
    (MagicType.LIGHTNING, MagicType.WATER): ("Storm", 25, "", 0),
    (MagicType.LIGHTNING, MagicType.LIGHTNING): ("Chain Lightning", 20, "+5 if buffer>7", 0),
    (MagicType.LIGHTNING, MagicType.NATURE): ("Static Shock", 16, "paralyze 5%", 0),
    (MagicType.LIGHTNING, MagicType.ICE): ("Frozen Lightning", 24, "", 0),
    (MagicType.LIGHTNING, MagicType.DARK): ("Dark Storm", 26, "", 0),
    (MagicType.LIGHTNING, MagicType.LIGHT): ("Divine Thunder", 24, "", 0),

    # Nature combos
    (MagicType.NATURE, MagicType.FIRE): ("Burning Forest", 17, "DoT +3", 0),
    (MagicType.NATURE, MagicType.WATER): ("Growth", -10, "heal", 0),
    (MagicType.NATURE, MagicType.LIGHTNING): ("Nature's Wrath", 19, "", 0),
    (MagicType.NATURE, MagicType.NATURE): ("Entangle", 12, "slow", 0),
    (MagicType.NATURE, MagicType.ICE): ("Frost Vine", 18, "root", 0),
    (MagicType.NATURE, MagicType.DARK): ("Decay", 20, "DoT +4", 0),
    (MagicType.NATURE, MagicType.LIGHT): ("Rejuvenation", -18, "strong heal", 0),

    # Ice combos
    (MagicType.ICE, MagicType.FIRE): ("Melt", 15, "weak", 0),
    (MagicType.ICE, MagicType.WATER): ("Glacier", 22, "freeze essence", 0),
    (MagicType.ICE, MagicType.LIGHTNING): ("Ice Storm", 24, "", 0),
    (MagicType.ICE, MagicType.NATURE): ("Permafrost", 17, "slow", 0),
    (MagicType.ICE, MagicType.ICE): ("Ice Wall", 0, "shield", 20),
    (MagicType.ICE, MagicType.DARK): ("Frozen Void", 26, "", 0),
    (MagicType.ICE, MagicType.LIGHT): ("Diamond Dust", 22, "", 0),

    # Dark combos (powerful but rare)
    (MagicType.DARK, MagicType.FIRE): ("Shadowflame", 30, "", 0),
    (MagicType.DARK, MagicType.WATER): ("Dark Waters", 24, "drain essence", 0),
    (MagicType.DARK, MagicType.LIGHTNING): ("Void Lightning", 28, "", 0),
    (MagicType.DARK, MagicType.NATURE): ("Corruption", 22, "poison +5", 0),
    (MagicType.DARK, MagicType.ICE): ("Black Ice", 26, "freeze", 0),
    (MagicType.DARK, MagicType.DARK): ("Oblivion", 35, "massive", 0),
    (MagicType.DARK, MagicType.LIGHT): ("Eclipse", 20, "confuse", 0),

    # Light combos
    (MagicType.LIGHT, MagicType.FIRE): ("Searing Light", 25, "", 0),
    (MagicType.LIGHT, MagicType.WATER): ("Purification", -14, "heal + cure", 0),
    (MagicType.LIGHT, MagicType.LIGHTNING): ("Lightning Flash", 26, "", 0),
    (MagicType.LIGHT, MagicType.NATURE): ("Life Bloom", -16, "strong heal", 0),
    (MagicType.LIGHT, MagicType.ICE): ("Crystallize", 20, "shield", 10),
    (MagicType.LIGHT, MagicType.DARK): ("Balance", 18, "equalize", 0),
    (MagicType.LIGHT, MagicType.LIGHT): ("Divine Radiance", 28, "", 0),

    # Triple element combos (powerful!)
    (MagicType.FIRE, MagicType.WATER, MagicType.LIGHTNING): ("Elemental Storm", 35, "classic", 0),
    (MagicType.FIRE, MagicType.LIGHTNING, MagicType.WATER): ("Thunder Boil", 32, "", 0),
    (MagicType.WATER, MagicType.LIGHTNING, MagicType.FIRE): ("Storm Surge", 34, "clear buffer", 0),
    (MagicType.LIGHTNING, MagicType.FIRE, MagicType.WATER): ("Lightning Tempest", 33, "", 0),

    # Healing combos
    (MagicType.WATER, MagicType.WATER, MagicType.WATER): ("Ocean's Blessing", -25, "massive heal", 0),
    (MagicType.WATER, MagicType.NATURE, MagicType.WATER): ("Spring Rain", -22, "heal + cure", 0),
    (MagicType.NATURE, MagicType.WATER, MagicType.NATURE): ("Forest Sanctuary", -20, "heal", 10),
    (MagicType.LIGHT, MagicType.WATER, MagicType.LIGHT): ("Divine Fountain", -24, "massive heal", 0),

    # Offensive power combos
    (MagicType.FIRE, MagicType.FIRE, MagicType.FIRE): ("Inferno Storm", 40, "massive fire", 0),
    (MagicType.LIGHTNING, MagicType.LIGHTNING, MagicType.LIGHTNING): ("Lightning Cascade", 38, "chain", 0),
    (MagicType.DARK, MagicType.DARK, MagicType.DARK): ("Void Collapse", 45, "ultimate", 0),
    (MagicType.FIRE, MagicType.DARK, MagicType.FIRE): ("Dark Inferno", 42, "very high", 0),

    # Control combos
    (MagicType.ICE, MagicType.ICE, MagicType.ICE): ("Absolute Zero", 0, "freeze 2", 30),
    (MagicType.ICE, MagicType.WATER, MagicType.ICE): ("Permafrost Wall", 15, "shield", 25),
    (MagicType.NATURE, MagicType.NATURE, MagicType.NATURE): ("Nature's Binding", 18, "root + slow", 0),
}


# ============================================================================
# Spell Lookup Functions
# ============================================================================

def lookup_spell(essences: List[MagicType]) -> Spell:
    """
    Look up spell from essence combination
    Like: Protocol handler lookup in kernel

    Args:
        essences: List of 1-3 magic types

    Returns:
        Spell object with damage and effects
    """
    # Convert to tuple for dictionary lookup
    key = tuple(essences)

    if key in SPELL_DATA:
        name, damage, special, shield = SPELL_DATA[key]
        return Spell(
            name=name,
            elements=essences,
            damage=damage,
            special=special,
            shield=shield
        )
    else:
        # Unknown combo - generic weak spell
        elem_str = "+".join(e.name_str for e in essences)
        return Spell(
            name=f"Wild {elem_str}",
            elements=essences,
            damage=5 * len(essences),  # 5 dmg per element
            special="unoptimized"
        )


def get_spell_info(essences: List[MagicType]) -> str:
    """Get spell description for UI"""
    spell = lookup_spell(essences)

    parts = [f"{spell.name} ({spell.damage} dmg)"]

    if spell.shield > 0:
        parts.append(f"+{spell.shield} shield")
    if spell.special:
        parts.append(f"[{spell.special}]")

    return " ".join(parts)


def get_top_damage_combos() -> List[Tuple[List[MagicType], str, int]]:
    """
    Get highest damage combos for AI planning
    Returns: List of (elements, name, damage) sorted by damage
    """
    combos = []
    for elements, (name, damage, special, shield) in SPELL_DATA.items():
        if damage > 0:  # Only offensive spells
            combos.append((list(elements), name, damage))

    # Sort by damage descending
    combos.sort(key=lambda x: x[2], reverse=True)
    return combos[:20]  # Top 20


def get_healing_combos() -> List[Tuple[List[MagicType], str, int]]:
    """
    Get healing combos for AI planning
    Returns: List of (elements, name, heal_amount) sorted by healing
    """
    combos = []
    for elements, (name, damage, special, shield) in SPELL_DATA.items():
        if damage < 0:  # Healing spells
            combos.append((list(elements), name, abs(damage)))

    combos.sort(key=lambda x: x[2], reverse=True)
    return combos


if __name__ == "__main__":
    # Test spell database
    print("=== Spell Database Test ===\n")

    # Test single element
    print("Single element spell:")
    spell = lookup_spell([MagicType.FIRE])
    print(f"  {spell}\n")

    # Test double element
    print("Double element spell:")
    spell = lookup_spell([MagicType.FIRE, MagicType.WATER])
    print(f"  {spell}\n")

    # Test triple element
    print("Triple element spell:")
    spell = lookup_spell([MagicType.FIRE, MagicType.WATER, MagicType.LIGHTNING])
    print(f"  {spell}\n")

    # Test unknown combo
    print("Unknown combo:")
    spell = lookup_spell([MagicType.FIRE, MagicType.FIRE, MagicType.NATURE])
    print(f"  {spell}\n")

    # Show top damage
    print("Top 5 damage combos:")
    for i, (elements, name, dmg) in enumerate(get_top_damage_combos()[:5], 1):
        elem_str = "".join(e.symbol for e in elements)
        print(f"  {i}. {elem_str} {name} - {dmg} dmg")

    print("\n✓ Spell database working!")
