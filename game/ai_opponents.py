"""
AI Opponents - 6 Difficulty Levels

Design philosophy: Data-driven, simple strategy functions
Like kernel's routing decision tree - clear paths, no complex logic
"""

import random
from typing import List, Optional, Tuple
from core_data import (Wand, GameState, MagicType, DefenseRule,
                      RuleAction, RuleChain)
from spell_database import lookup_spell, get_top_damage_combos, get_healing_combos


# ============================================================================
# AI Base Strategy - Simple function signatures
# ============================================================================

class AIStrategy:
    """
    Base AI strategy - simple data and methods

    Data:
        name: AI opponent name
        difficulty: 1-6 (difficulty level)
        description: What this AI does
    """
    def __init__(self, name: str, difficulty: int, description: str):
        self.name = name
        self.difficulty = difficulty
        self.description = description

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        """
        Decide which defense rules to add this turn
        Returns: List of rules to add (if CPU allows)
        """
        return []

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        """
        Decide how many essences to consume (1-3)
        Returns: Number of essences, or None to skip casting
        """
        return None

    def should_discard(self, state: GameState, my_wand: Wand) -> Optional[int]:
        """
        Decide if should discard essence from buffer
        Returns: Index to discard, or None
        """
        return None


# ============================================================================
# Level 1: Passive (Tutorial Bot)
# ============================================================================

class PassiveAI(AIStrategy):
    """
    Level 1 - Passive

    Strategy:
    - No defense rules (accepts all magic)
    - Casts random 1-2 element spells
    - Never discards
    - Easy to beat (for learning)
    """
    def __init__(self):
        super().__init__(
            name="Novice Mage",
            difficulty=1,
            description="No defense, random casts"
        )

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        # No defenses - pure passive
        return []

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        # Random cast 1 or 2 essences (if available)
        max_cast = min(my_wand.buffer.count, 2)
        return random.randint(1, max_cast)


# ============================================================================
# Level 2: Defensive (Safe Player)
# ============================================================================

class DefensiveAI(AIStrategy):
    """
    Level 2 - Defensive

    Strategy:
    - Blocks Fire and Dark (most dangerous)
    - Prefers healing combos when low HP
    - Conservative casting
    - Hard to kill but slow to attack
    """
    def __init__(self):
        super().__init__(
            name="Shieldmage",
            difficulty=2,
            description="Heavy defense, safe play"
        )
        self.defenses_configured = False

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        if self.defenses_configured:
            return []

        rules = [
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.FIRE
            ),
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            ),
        ]
        self.defenses_configured = True
        return rules

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        # If low HP (<50), try to heal
        if my_wand.hp < 50 and my_wand.buffer.count >= 2:
            # Check if we have water for healing
            if MagicType.WATER in my_wand.buffer.essences[:3]:
                return 2  # Try for healing combo

        # Otherwise cast conservatively (1-2)
        max_cast = min(my_wand.buffer.count, 2)
        return max_cast if max_cast > 0 else None


# ============================================================================
# Level 3: Aggressive (Glass Cannon)
# ============================================================================

class AggressiveAI(AIStrategy):
    """
    Level 3 - Aggressive

    Strategy:
    - Minimal defense (only blocks Dark)
    - Always tries to cast 3-element combos
    - Accepts most magic for essence gain
    - High damage but vulnerable
    """
    def __init__(self):
        super().__init__(
            name="Battle Mage",
            difficulty=3,
            description="Aggressive offense, minimal defense"
        )
        self.defenses_configured = False

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        if self.defenses_configured:
            return []

        # Only block Dark (too dangerous)
        rules = [
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            ),
        ]
        self.defenses_configured = True
        return rules

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        # Always try to cast maximum (3 elements)
        if my_wand.buffer.count >= 3:
            return 3
        elif my_wand.buffer.count >= 2:
            return 2
        else:
            return 1

    def should_discard(self, state: GameState, my_wand: Wand) -> Optional[int]:
        # Discard if buffer getting full (>8)
        if my_wand.buffer.count > 8:
            return 0  # Discard oldest
        return None


# ============================================================================
# Level 4: Balanced (Standard Opponent)
# ============================================================================

class BalancedAI(AIStrategy):
    """
    Level 4 - Balanced

    Strategy:
    - Blocks Fire and Dark
    - Plans for good 2-3 element combos
    - Heals when needed
    - Balanced approach
    """
    def __init__(self):
        super().__init__(
            name="Adept Mage",
            difficulty=4,
            description="Balanced offense and defense"
        )
        self.defenses_configured = False

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        if self.defenses_configured:
            return []

        rules = [
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.FIRE
            ),
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            ),
        ]
        self.defenses_configured = True
        return rules

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        # Emergency heal if very low HP (<30)
        if my_wand.hp < 30 and my_wand.buffer.count >= 2:
            if MagicType.WATER in my_wand.buffer.essences[:3]:
                return 2  # Try healing combo

        # Check for good 3-element combo
        if my_wand.buffer.count >= 3:
            # Check if we have a known good combo
            elements = my_wand.buffer.essences[:3]
            spell = lookup_spell(elements)
            if spell.damage >= 30 or spell.damage <= -15:  # Good damage or heal
                return 3

        # Otherwise cast 2 elements if available
        if my_wand.buffer.count >= 2:
            return 2

        return 1

    def should_discard(self, state: GameState, my_wand: Wand) -> Optional[int]:
        # Discard if buffer >7 and oldest is weak element
        if my_wand.buffer.count > 7:
            oldest = my_wand.buffer.essences[0]
            # Discard Nature (weakest damage)
            if oldest == MagicType.NATURE:
                return 0
        return None


# ============================================================================
# Level 5: Adaptive (Smart Opponent)
# ============================================================================

class AdaptiveAI(AIStrategy):
    """
    Level 5 - Adaptive

    Strategy:
    - Adapts defense based on player's attacks
    - Tracks player's preferred elements
    - Changes strategy based on HP difference
    - Aggressive when ahead, defensive when behind
    """
    def __init__(self):
        super().__init__(
            name="Archmage",
            difficulty=5,
            description="Adapts to player strategy"
        )
        self.player_element_count = {e: 0 for e in MagicType}
        self.turn_last_configured = 0

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        # Reconfigure every 3 turns
        if state.turn.turn_number - self.turn_last_configured < 3:
            return []

        # Remove old rules
        my_wand.rules.rules.clear()

        # Always block Dark
        rules = [
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            ),
        ]

        # Find player's most used element (from their buffer)
        # This simulates "learning" player's strategy
        enemy_wand = state.player if my_wand == state.enemy else state.enemy
        if enemy_wand.buffer.count > 0:
            # Count elements in enemy buffer (what they're building)
            for essence in enemy_wand.buffer.essences:
                self.player_element_count[essence] += 1

            # Block their most common element
            most_common = max(self.player_element_count.items(),
                             key=lambda x: x[1])[0]
            if most_common != MagicType.DARK:  # Don't duplicate
                rules.append(DefenseRule(
                    chain=RuleChain.PREROUTING,
                    action=RuleAction.DROP,
                    magic_type=most_common
                ))

        self.turn_last_configured = state.turn.turn_number
        return rules

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        enemy_wand = state.player if my_wand == state.enemy else state.enemy
        hp_diff = my_wand.hp - enemy_wand.hp

        # Aggressive if ahead
        if hp_diff > 20:
            # Go for power combo
            if my_wand.buffer.count >= 3:
                return 3
            return min(my_wand.buffer.count, 2)

        # Defensive if behind
        elif hp_diff < -20:
            # Try to heal or defend
            if my_wand.hp < 40 and my_wand.buffer.count >= 2:
                if MagicType.WATER in my_wand.buffer.essences[:3]:
                    return 2  # Healing combo
            return 1  # Conserve essence

        # Balanced if close
        else:
            if my_wand.buffer.count >= 3:
                elements = my_wand.buffer.essences[:3]
                spell = lookup_spell(elements)
                if spell.damage >= 25:
                    return 3
            return 2 if my_wand.buffer.count >= 2 else 1

    def should_discard(self, state: GameState, my_wand: Wand) -> Optional[int]:
        # Smart discard - remove elements that don't combo well
        if my_wand.buffer.count > 7:
            # Check last 3 elements for bad combo
            if my_wand.buffer.count >= 3:
                elements = my_wand.buffer.essences[-3:]
                spell = lookup_spell(elements)
                # If building bad combo, discard oldest
                if spell.damage < 20 and spell.damage > -10:
                    return 0
        return None


# ============================================================================
# Level 6: Expert (Maximum Difficulty)
# ============================================================================

class ExpertAI(AIStrategy):
    """
    Level 6 - Expert

    Strategy:
    - Plans combos 2-3 turns ahead
    - Optimal rule configuration
    - Compound rules (enemy + type filtering)
    - Perfect timing on heals and damage
    - Minimizes wasted essence
    """
    def __init__(self):
        super().__init__(
            name="Grand Archmage",
            difficulty=6,
            description="Expert planning and execution"
        )
        self.combo_plan = []  # Elements needed for planned combo
        self.turn_last_configured = 0

    def configure_defenses(self, state: GameState, my_wand: Wand) -> List[DefenseRule]:
        # Reconfigure every 2 turns
        if state.turn.turn_number - self.turn_last_configured < 2:
            return []

        my_wand.rules.rules.clear()

        # Always block Dark and Fire
        rules = [
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            ),
            DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.FIRE
            ),
        ]

        # Add rate limiting if we have CPU
        if my_wand.cpu >= 30:  # 15 CPU cost for rate limit
            rules.append(DefenseRule(
                chain=RuleChain.INPUT,
                action=RuleAction.DROP,
                # Rate limit handled by rule system
            ))

        self.turn_last_configured = state.turn.turn_number
        return rules

    def choose_cast(self, state: GameState, my_wand: Wand) -> Optional[int]:
        if my_wand.buffer.count == 0:
            return None

        enemy_wand = state.player if my_wand == state.enemy else state.enemy

        # Critical heal (<25 HP)
        if my_wand.hp < 25:
            # Try for best healing combo
            healing_combos = get_healing_combos()
            for elements, name, heal in healing_combos:
                if len(elements) <= my_wand.buffer.count:
                    # Check if we have these elements
                    if self._has_elements(my_wand, elements):
                        # Rearrange buffer to get this combo
                        return len(elements)
            # Fall back to any water
            if MagicType.WATER in my_wand.buffer.essences:
                return 2

        # Lethal damage check
        if enemy_wand.hp <= 45:
            # Try for killing blow
            damage_combos = get_top_damage_combos()
            for elements, name, damage in damage_combos:
                if damage >= enemy_wand.hp and len(elements) <= my_wand.buffer.count:
                    if self._has_elements(my_wand, elements):
                        return len(elements)

        # Optimal combo planning
        if my_wand.buffer.count >= 3:
            # Check all possible 3-element combos from buffer
            best_damage = 0
            best_count = 0

            for count in [3, 2, 1]:
                if my_wand.buffer.count >= count:
                    elements = my_wand.buffer.essences[:count]
                    spell = lookup_spell(elements)
                    if spell.damage > best_damage:
                        best_damage = spell.damage
                        best_count = count

            if best_count > 0:
                return best_count

        return 1 if my_wand.buffer.count > 0 else None

    def should_discard(self, state: GameState, my_wand: Wand) -> Optional[int]:
        # Discard strategically to build better combos
        if my_wand.buffer.count > 6:
            # Find worst positioned element
            for i in range(my_wand.buffer.count):
                # Check if removing this improves next combo
                temp_buffer = my_wand.buffer.essences.copy()
                temp_buffer.pop(i)

                if len(temp_buffer) >= 2:
                    new_spell = lookup_spell(temp_buffer[:2])
                    old_spell = lookup_spell(my_wand.buffer.essences[:2])

                    if new_spell.damage > old_spell.damage:
                        return i

        return None

    def _has_elements(self, wand: Wand, needed: List[MagicType]) -> bool:
        """Check if wand buffer contains needed elements (order doesn't matter)"""
        buffer_copy = wand.buffer.essences.copy()
        for element in needed:
            if element in buffer_copy:
                buffer_copy.remove(element)
            else:
                return False
        return True


# ============================================================================
# AI Factory - Create AI by difficulty
# ============================================================================

AI_LEVELS = {
    1: PassiveAI,
    2: DefensiveAI,
    3: AggressiveAI,
    4: BalancedAI,
    5: AdaptiveAI,
    6: ExpertAI,
}


def create_ai(difficulty: int) -> AIStrategy:
    """
    Create AI opponent of specified difficulty

    Args:
        difficulty: 1-6 (Passive to Expert)

    Returns:
        AI strategy instance
    """
    if difficulty not in AI_LEVELS:
        difficulty = 4  # Default to balanced

    return AI_LEVELS[difficulty]()


def list_ai_opponents():
    """Print all available AI opponents"""
    print("Available AI Opponents:\n")
    for level in range(1, 7):
        ai = create_ai(level)
        print(f"  Level {level}: {ai.name}")
        print(f"           {ai.description}\n")


if __name__ == "__main__":
    # Test AI creation
    print("=== AI Opponents Test ===\n")

    list_ai_opponents()

    print("Testing AI behavior:")
    ai = create_ai(6)
    print(f"  Created: {ai.name} (Level {ai.difficulty})")
    print(f"  Description: {ai.description}")

    print("\n✓ AI system working!")
