"""
Terminal UI - Display layer only, no game logic

Completely separate from engine - just displays state and sends commands
This makes it easy to replace with network client or different UI later
"""

import os
import sys
from typing import Optional
from core_data import MagicType, DefenseRule, RuleAction, RuleChain
from game_engine import GameEngine
from ai_opponents import create_ai


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_hp_bar(current: int, maximum: int, width: int = 20) -> str:
    """Draw HP bar"""
    filled = int((current / maximum) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{maximum}"


def draw_buffer(essences: list, capacity: int = 10) -> str:
    """Draw essence buffer"""
    symbols = []
    for i in range(capacity):
        if i < len(essences):
            magic = MagicType(essences[i])
            symbols.append(magic.symbol)
        else:
            symbols.append("[ ]")

    return " ".join(symbols)


def display_game_state(engine: GameEngine):
    """Display current game state"""
    state = engine.get_state_snapshot()

    print("=" * 70)
    print(f"KERNEL DUEL - Turn {state['turn']} ({state['phase'].upper()} phase)")
    print("=" * 70)
    print()

    # Player side
    p = state['player']
    print(f"┌─ {p['name']} " + "─" * (60 - len(p['name'])))
    print(f"│ HP:     {draw_hp_bar(p['hp'], 100)}")
    if p['shield'] > 0:
        print(f"│ Shield: {p['shield']}")
    print(f"│ CPU:    {p['cpu']}/100")
    print(f"│ Buffer: {draw_buffer(p['buffer'], 10)}")
    print(f"│         ({p['buffer_count']}/10 essences)")
    print(f"│ Rules:  {p['rules_count']} active")
    print()

    # Enemy side
    e = state['enemy']
    print(f"┌─ {e['name']} (AI) " + "─" * (55 - len(e['name'])))
    print(f"│ HP:     {draw_hp_bar(e['hp'], 100)}")
    if e['shield'] > 0:
        print(f"│ Shield: {e['shield']}")
    print(f"│ CPU:    {e['cpu']}/100")
    print(f"│ Buffer: ???  (hidden)")
    print(f"│ Rules:  {e['rules_count']} active")
    print()

    # Battle log
    if state['log']:
        print("┌─ Battle Log " + "─" * 55)
        for msg in state['log']:
            print(f"│ {msg}")
        print()

    print("─" * 70)


def show_action_menu():
    """Display available actions"""
    print("\nActions:")
    print("  [1] Cast spell (consume essence)")
    print("  [2] Configure defense rule")
    print("  [3] Discard essence")
    print("  [4] View buffer details")
    print("  [5] Skip / Wait")
    print("  [Q] Quit game")
    print()


def get_player_cast_choice(engine: GameEngine) -> Optional[int]:
    """Get how many essences player wants to cast"""
    buffer_count = engine.state.player.buffer.count

    if buffer_count == 0:
        print("  Buffer empty! Cannot cast.")
        input("  Press Enter to continue...")
        return None

    print(f"\n  Your buffer ({buffer_count} essences):")
    for i, essence in enumerate(engine.state.player.buffer.essences):
        magic = MagicType(essence)
        print(f"    [{i}] {magic.symbol} {magic.name_str}")

    print(f"\n  Cast how many essences? (1-{min(buffer_count, 3)}, or 0 to cancel)")
    choice = input("  > ").strip()

    if choice == "0":
        return None

    try:
        count = int(choice)
        if 1 <= count <= min(buffer_count, 3):
            # Preview spell
            from spell_database import get_spell_info
            essences = engine.state.player.buffer.essences[:count]
            spell_info = get_spell_info(essences)
            print(f"\n  Spell: {spell_info}")
            confirm = input("  Cast this spell? (y/n) > ").strip().lower()
            if confirm == 'y':
                return count
    except ValueError:
        pass

    print("  Invalid choice!")
    input("  Press Enter to continue...")
    return None


def get_defense_rule_choice(engine: GameEngine) -> Optional[DefenseRule]:
    """Get defense rule configuration from player"""
    print("\n  Configure Defense Rule")
    print("  Current CPU:", engine.state.player.cpu)
    print("  Cost: 20 CPU per rule")
    print()

    if engine.state.player.cpu < 20:
        print("  Not enough CPU!")
        input("  Press Enter to continue...")
        return None

    # Choose action
    print("  Action:")
    print("    [1] DROP (block magic)")
    print("    [2] ACCEPT (allow magic)")
    print("    [0] Cancel")
    action_choice = input("  > ").strip()

    if action_choice == "0":
        return None

    action_map = {"1": RuleAction.DROP, "2": RuleAction.ACCEPT}
    if action_choice not in action_map:
        print("  Invalid choice!")
        input("  Press Enter to continue...")
        return None

    action = action_map[action_choice]

    # Choose magic type
    print("\n  Block which element?")
    magic_types = list(MagicType)
    for i, magic in enumerate(magic_types, 1):
        print(f"    [{i}] {magic.symbol} {magic.name_str}")
    print("    [0] All types")

    type_choice = input("  > ").strip()

    magic_type = None
    if type_choice != "0":
        try:
            idx = int(type_choice) - 1
            if 0 <= idx < len(magic_types):
                magic_type = magic_types[idx]
        except ValueError:
            pass

    # Create rule
    rule = DefenseRule(
        chain=RuleChain.PREROUTING,
        action=action,
        magic_type=magic_type
    )

    print(f"\n  Rule: {action.name} {magic_type.name_str if magic_type else 'ALL'}")
    print(f"  Cost: {rule.cpu_cost} CPU/turn")
    confirm = input("  Add this rule? (y/n) > ").strip().lower()

    if confirm == 'y':
        return rule

    return None


def get_discard_choice(engine: GameEngine) -> Optional[int]:
    """Get which essence to discard"""
    buffer_count = engine.state.player.buffer.count

    if buffer_count == 0:
        print("  Buffer empty! Nothing to discard.")
        input("  Press Enter to continue...")
        return None

    if engine.state.player.cpu < 5:
        print("  Not enough CPU! (costs 5 CPU)")
        input("  Press Enter to continue...")
        return None

    print(f"\n  Your buffer ({buffer_count} essences):")
    for i, essence in enumerate(engine.state.player.buffer.essences):
        magic = MagicType(essence)
        print(f"    [{i}] {magic.symbol} {magic.name_str}")

    print("\n  Discard which essence? (0 to cancel)")
    choice = input("  > ").strip()

    try:
        idx = int(choice)
        if idx == 0:
            return None
        if 0 <= idx - 1 < buffer_count:
            return idx - 1
    except ValueError:
        pass

    print("  Invalid choice!")
    input("  Press Enter to continue...")
    return None


def run_action_phase(engine: GameEngine) -> bool:
    """
    Run action phase - player makes decisions

    Returns:
        False if player wants to quit
    """
    while True:
        clear_screen()
        display_game_state(engine)
        show_action_menu()

        choice = input("Choose action > ").strip().lower()

        if choice == 'q':
            return False

        elif choice == '1':
            # Cast spell
            count = get_player_cast_choice(engine)
            if count:
                if engine.player_cast(count):
                    print("\n✓ Spell cast!")
                else:
                    print("\n✗ Cast failed!")
                input("  Press Enter to continue...")

        elif choice == '2':
            # Configure rule
            rule = get_defense_rule_choice(engine)
            if rule:
                if engine.player_configure_rule(rule):
                    print("\n✓ Rule added!")
                else:
                    print("\n✗ Failed to add rule!")
                input("  Press Enter to continue...")

        elif choice == '3':
            # Discard essence
            idx = get_discard_choice(engine)
            if idx is not None:
                if engine.player_discard(idx):
                    print("\n✓ Essence discarded!")
                else:
                    print("\n✗ Failed to discard!")
                input("  Press Enter to continue...")

        elif choice == '4':
            # View buffer details
            from spell_database import lookup_spell
            print("\n  Buffer Analysis:")
            for count in range(1, min(engine.state.player.buffer.count, 3) + 1):
                essences = engine.state.player.buffer.essences[:count]
                from spell_database import get_spell_info
                info = get_spell_info(essences)
                print(f"    {count} essence(s): {info}")
            input("\n  Press Enter to continue...")

        elif choice == '5':
            # Skip / end action phase
            break

        else:
            print("  Invalid choice!")
            input("  Press Enter to continue...")

    return True


def main():
    """Main game loop"""
    print("=" * 70)
    print("KERNEL DUEL - PvP Wizard Combat")
    print("=" * 70)
    print()
    print("Choose AI difficulty:")
    print("  [1] Novice Mage (Tutorial)")
    print("  [2] Shieldmage (Defensive)")
    print("  [3] Battle Mage (Aggressive)")
    print("  [4] Adept Mage (Balanced)")
    print("  [5] Archmage (Adaptive)")
    print("  [6] Grand Archmage (Expert)")
    print()

    difficulty = input("Select difficulty (1-6) > ").strip()
    try:
        level = int(difficulty)
        if level < 1 or level > 6:
            level = 4
    except ValueError:
        level = 4

    # Create game
    ai = create_ai(level)
    player_name = input("Enter your name > ").strip() or "Player"
    engine = GameEngine(player_name=player_name, ai=ai)

    print(f"\nStarting game: {player_name} vs {ai.name}!")
    input("Press Enter to begin...")

    # Main game loop
    while True:
        # Incoming phase
        clear_screen()
        print("=== INCOMING PHASE ===\n")
        print("Magic essence arriving...\n")
        p_stats, e_stats = engine.start_incoming_phase()
        print(f"You received: {p_stats['accepted']} essence")
        if p_stats['overflow'] > 0:
            print(f"⚠ OVERFLOW! Took {p_stats['overflow'] * 10} damage!")
        print(f"\n{ai.name} received: {e_stats['accepted']} essence")
        if e_stats['overflow'] > 0:
            print(f"⚠ Enemy overflow! {e_stats['overflow'] * 10} damage!")

        input("\nPress Enter to continue...")

        # Action phase
        engine.start_action_phase()

        # AI acts first
        engine.process_ai_turn()

        # Player's turn
        if not run_action_phase(engine):
            print("\nThanks for playing!")
            break

        # End turn
        winner = engine.end_turn()

        if winner:
            clear_screen()
            display_game_state(engine)
            print("\n" + "=" * 70)
            print(f"🏆 {winner} WINS! 🏆")
            print("=" * 70)
            break


if __name__ == "__main__":
    main()
