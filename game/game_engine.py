"""
Game Engine - Pure logic, no UI dependencies

Design: All game logic here, UI just displays and sends commands
This makes networking easy - UI is just another client
"""

import random
from typing import List, Optional, Tuple
from core_data import (GameState, Wand, MagicType, DefenseRule,
                      RuleAction, RuleChain, TurnState)
from spell_database import lookup_spell
from ai_opponents import AIStrategy


# ============================================================================
# Magic Generation - Incoming essence system
# ============================================================================

def generate_incoming_magic(count: int = 3) -> List[Tuple[MagicType, bool]]:
    """
    Generate incoming magic essences

    Args:
        count: How many to generate (default 3)

    Returns:
        List of (magic_type, from_enemy) tuples
        from_enemy: True = direct from enemy, False = ally route
    """
    magic_list = []

    for _ in range(count):
        # Random magic type
        magic = random.choice(list(MagicType))

        # 70% from enemy direct, 30% from routes
        # Of routes: 2/3 enemy route, 1/3 ally route
        roll = random.random()
        if roll < 0.70:
            from_enemy = True  # Direct attack
        elif roll < 0.90:
            from_enemy = True  # Via enemy route
        else:
            from_enemy = False  # Via ally route

        magic_list.append((magic, from_enemy))

    return magic_list


# ============================================================================
# Rules Engine - Process magic through filters
# ============================================================================

def process_prerouting(magic: MagicType, from_enemy: bool,
                       wand: Wand) -> Tuple[bool, int]:
    """
    Process magic through PREROUTING rules

    Args:
        magic: Magic type
        from_enemy: Whether from enemy IP
        wand: Target wand

    Returns:
        (accepted, cpu_cost) - True if magic passes, CPU cost incurred
    """
    cpu_cost = 0

    # Check each rule
    for rule in wand.rules.rules:
        if rule.chain != RuleChain.PREROUTING:
            continue

        if rule.matches(magic, from_enemy):
            # Rule matches!
            if rule.action == RuleAction.DROP:
                return (False, 0)  # Blocked, no processing cost
            elif rule.action == RuleAction.ACCEPT:
                return (True, 0)  # Explicitly accepted
            elif rule.action == RuleAction.STRIP:
                # DPI - expensive operation
                # For now, just accept the magic
                # TODO: Handle mixed magic parsing
                cpu_cost += 30
                return (True, cpu_cost)

    # Default: ACCEPT if no rule matched
    return (True, 0)


def apply_incoming_magic(wand: Wand, magic_list: List[Tuple[MagicType, bool]]) -> dict:
    """
    Apply incoming magic to wand's buffer through all filters

    Args:
        wand: Target wand
        magic_list: List of (magic, from_enemy) tuples

    Returns:
        Dict with statistics (accepted, dropped, overflow)
    """
    stats = {
        'total': len(magic_list),
        'accepted': 0,
        'dropped': 0,
        'overflow': 0,
        'cpu_used': 0
    }

    wand.buffer.reset_overflow()

    for magic, from_enemy in magic_list:
        # PREROUTING filter
        accepted, cpu_cost = process_prerouting(magic, from_enemy, wand)
        stats['cpu_used'] += cpu_cost

        if not accepted:
            stats['dropped'] += 1
            continue

        # Try to add to buffer
        if wand.buffer.add(magic):
            stats['accepted'] += 1
        else:
            # Buffer full - overflow damage!
            stats['overflow'] += 1
            wand.take_damage(10)  # 10 HP per overflow

    return stats


# ============================================================================
# Turn Processing - Main game loop logic
# ============================================================================

class GameEngine:
    """
    Main game engine - processes turns, applies rules

    Data:
        state: Current game state
        ai: AI opponent (None if PvP)
    """
    def __init__(self, player_name: str = "Player", ai: Optional[AIStrategy] = None):
        self.state = GameState(
            player=Wand(owner=player_name),
            enemy=Wand(owner=ai.name if ai else "Opponent")
        )
        self.ai = ai

    def start_incoming_phase(self):
        """Start incoming phase - magic arrives for both players"""
        # Generate magic for player
        player_magic = generate_incoming_magic(3)
        player_stats = apply_incoming_magic(self.state.player, player_magic)

        self.state.add_log(f"{self.state.player.owner} incoming: "
                          f"{player_stats['accepted']} accepted, "
                          f"{player_stats['dropped']} dropped, "
                          f"{player_stats['overflow']} overflow")

        # Generate magic for enemy
        enemy_magic = generate_incoming_magic(3)
        enemy_stats = apply_incoming_magic(self.state.enemy, enemy_magic)

        self.state.add_log(f"{self.state.enemy.owner} incoming: "
                          f"{enemy_stats['accepted']} accepted, "
                          f"{enemy_stats['dropped']} dropped, "
                          f"{enemy_stats['overflow']} overflow")

        return player_stats, enemy_stats

    def start_action_phase(self):
        """Start action phase - players can configure and cast"""
        # Refresh CPU for both
        self.state.player.refresh_cpu()
        self.state.enemy.refresh_cpu()

        # Subtract passive costs
        self.state.player.spend_cpu(self.state.player.passive_cpu_cost)
        self.state.enemy.spend_cpu(self.state.enemy.passive_cpu_cost)

    def process_ai_turn(self):
        """Let AI make its decisions"""
        if not self.ai:
            return

        # AI configures defenses
        new_rules = self.ai.configure_defenses(self.state, self.state.enemy)
        for rule in new_rules:
            if self.state.enemy.spend_cpu(20):  # Cost to configure
                self.state.enemy.rules.add_rule(rule)
                self.state.add_log(f"{self.state.enemy.owner} configured rule")

        # AI decides to cast
        cast_count = self.ai.choose_cast(self.state, self.state.enemy)
        if cast_count:
            self.cast_spell(self.state.enemy, self.state.player, cast_count)
            self.state.enemy_no_cast_turns = 0
        else:
            self.state.enemy_no_cast_turns += 1

        # AI decides to discard
        discard_idx = self.ai.should_discard(self.state, self.state.enemy)
        if discard_idx is not None:
            if self.state.enemy.spend_cpu(5):
                self.state.enemy.buffer.discard(discard_idx)

    def cast_spell(self, caster: Wand, target: Wand, essence_count: int) -> bool:
        """
        Cast spell by consuming essences

        Args:
            caster: Who is casting
            target: Who to target
            essence_count: How many essences to consume (1-3)

        Returns:
            True if cast successful
        """
        if essence_count < 1 or essence_count > 3:
            return False

        if caster.buffer.count < essence_count:
            return False

        # Consume essences
        essences = caster.buffer.consume(essence_count)

        # Lookup spell
        spell = lookup_spell(essences)

        # Apply effects
        if spell.damage > 0:
            # Damage spell
            target.take_damage(spell.damage)
            self.state.add_log(f"{caster.owner} cast {spell.name} → "
                             f"{spell.damage} dmg to {target.owner}")
        elif spell.damage < 0:
            # Healing spell
            caster.heal(abs(spell.damage))
            self.state.add_log(f"{caster.owner} cast {spell.name} → "
                             f"healed {abs(spell.damage)} HP")

        if spell.shield > 0:
            caster.add_shield(spell.shield)
            self.state.add_log(f"{caster.owner} gained {spell.shield} shield")

        return True

    def player_cast(self, essence_count: int) -> bool:
        """Player casts spell"""
        result = self.cast_spell(self.state.player, self.state.enemy, essence_count)
        if result:
            self.state.player_no_cast_turns = 0
        return result

    def player_configure_rule(self, rule: DefenseRule) -> bool:
        """Player adds defense rule"""
        if self.state.player.spend_cpu(20):
            if self.state.player.rules.add_rule(rule):
                self.state.add_log(f"{self.state.player.owner} configured rule")
                return True
        return False

    def player_discard(self, index: int) -> bool:
        """Player discards essence"""
        if self.state.player.spend_cpu(5):
            if self.state.player.buffer.discard(index):
                self.state.add_log(f"{self.state.player.owner} discarded essence")
                return True
        return False

    def end_turn(self):
        """End current turn, check victory"""
        # Check victory conditions
        winner = self.state.check_victory()

        if not winner:
            # Advance to next turn
            self.state.turn.turn_number += 1
            self.state.turn.phase = "incoming"

        return winner

    def get_state_snapshot(self) -> dict:
        """Get current game state as dict (for UI or network)"""
        return {
            'turn': self.state.turn.turn_number,
            'phase': self.state.turn.phase,
            'player': {
                'name': self.state.player.owner,
                'hp': self.state.player.hp,
                'shield': self.state.player.shield,
                'cpu': self.state.player.cpu,
                'buffer': [e.value for e in self.state.player.buffer.essences],
                'buffer_count': self.state.player.buffer.count,
                'rules_count': len(self.state.player.rules.rules),
            },
            'enemy': {
                'name': self.state.enemy.owner,
                'hp': self.state.enemy.hp,
                'shield': self.state.enemy.shield,
                'cpu': self.state.enemy.cpu,
                'buffer_count': self.state.enemy.buffer.count,  # Hidden in real game
                'rules_count': len(self.state.enemy.rules.rules),
            },
            'log': self.state.log[-5:],  # Last 5 messages
            'winner': self.state.winner,
        }


if __name__ == "__main__":
    # Test game engine
    from ai_opponents import create_ai

    print("=== Game Engine Test ===\n")

    # Create engine with AI opponent
    ai = create_ai(3)  # Battle Mage
    engine = GameEngine(player_name="TestPlayer", ai=ai)

    print(f"Game started: {engine.state.player.owner} vs {engine.state.enemy.owner}\n")

    # Simulate a few turns
    for turn in range(3):
        print(f"--- Turn {turn + 1} ---")

        # Incoming phase
        print("Incoming phase...")
        p_stats, e_stats = engine.start_incoming_phase()
        print(f"  Player: {p_stats['accepted']} magic accepted")
        print(f"  Enemy: {e_stats['accepted']} magic accepted")

        # Action phase
        print("\nAction phase...")
        engine.start_action_phase()

        # Player casts if possible
        if engine.state.player.buffer.count >= 2:
            engine.player_cast(2)

        # AI acts
        engine.process_ai_turn()

        # Show state
        state = engine.get_state_snapshot()
        print(f"\nState:")
        print(f"  Player: {state['player']['hp']} HP, "
              f"{state['player']['buffer_count']} essence")
        print(f"  Enemy: {state['enemy']['hp']} HP, "
              f"{state['enemy']['buffer_count']} essence")

        # End turn
        winner = engine.end_turn()
        if winner:
            print(f"\n{winner} wins!")
            break

        print()

    print("\n✓ Game engine working!")
