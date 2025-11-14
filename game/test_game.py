"""
Self-test: Play a complete game to verify everything works
"""

from game_engine import GameEngine
from ai_opponents import create_ai
from core_data import DefenseRule, RuleAction, RuleChain, MagicType

def test_complete_game():
    """Run a complete game simulation"""
    print("=== Kernel Duel Self-Test ===\n")

    # Create game with AI
    ai = create_ai(3)  # Battle Mage (aggressive)
    engine = GameEngine(player_name="TestPlayer", ai=ai)

    print(f"Game: {engine.state.player.owner} vs {engine.state.enemy.owner}")
    print(f"AI Strategy: {ai.description}\n")

    turn_limit = 20  # Prevent infinite games
    turn = 0

    while turn < turn_limit:
        turn += 1
        print(f"--- Turn {turn} ---")

        # Incoming phase
        print("Incoming phase...")
        p_stats, e_stats = engine.start_incoming_phase()
        print(f"  Player: {p_stats['accepted']} essence, {p_stats['overflow']} overflow")
        print(f"  Enemy: {e_stats['accepted']} essence, {e_stats['overflow']} overflow")

        # Action phase
        print("Action phase...")
        engine.start_action_phase()

        # Player configures defense on turn 1
        if turn == 1:
            rule = DefenseRule(
                chain=RuleChain.PREROUTING,
                action=RuleAction.DROP,
                magic_type=MagicType.DARK
            )
            if engine.player_configure_rule(rule):
                print("  Player configured: DROP Dark")

        # Player casts if has enough essence
        if engine.state.player.buffer.count >= 3:
            if engine.player_cast(3):
                print(f"  Player cast 3-element spell!")
        elif engine.state.player.buffer.count >= 2:
            if engine.player_cast(2):
                print(f"  Player cast 2-element spell!")
        elif engine.state.player.buffer.count >= 1:
            if engine.player_cast(1):
                print(f"  Player cast 1-element spell!")

        # AI turn
        engine.process_ai_turn()

        # Show state
        state = engine.get_state_snapshot()
        p = state['player']
        e = state['enemy']
        print(f"\nState:")
        print(f"  Player: {p['hp']} HP, {p['cpu']} CPU, {p['buffer_count']} essence")
        print(f"  Enemy:  {e['hp']} HP, {e['cpu']} CPU, {e['buffer_count']} essence")

        # Check victory
        winner = engine.end_turn()
        if winner:
            print(f"\n{'='*50}")
            print(f"🏆 {winner} WINS! 🏆")
            print(f"{'='*50}")
            print(f"\nFinal Score:")
            print(f"  {engine.state.player.owner}: {engine.state.player.hp} HP")
            print(f"  {engine.state.enemy.owner}: {engine.state.enemy.hp} HP")
            return True

        print()

    print("Game reached turn limit (draw)")
    return False


def test_spell_database():
    """Test spell lookups"""
    from spell_database import lookup_spell, get_top_damage_combos

    print("\n=== Spell Database Test ===\n")

    # Test some combos
    test_combos = [
        [MagicType.FIRE],
        [MagicType.FIRE, MagicType.WATER],
        [MagicType.FIRE, MagicType.WATER, MagicType.LIGHTNING],
    ]

    for elements in test_combos:
        spell = lookup_spell(elements)
        elem_str = "".join(e.symbol for e in elements)
        print(f"{elem_str} → {spell.name} ({spell.damage} dmg)")

    # Top damage
    print("\nTop 3 damage spells:")
    for i, (elements, name, damage) in enumerate(get_top_damage_combos()[:3], 1):
        elem_str = "".join(e.symbol for e in elements)
        print(f"  {i}. {elem_str} {name} - {damage} dmg")


def test_ai_levels():
    """Test all AI difficulty levels"""
    print("\n=== AI Levels Test ===\n")

    for level in range(1, 7):
        ai = create_ai(level)
        print(f"Level {level}: {ai.name} - {ai.description}")


if __name__ == "__main__":
    # Run all tests
    test_spell_database()
    test_ai_levels()

    print("\n" + "="*50)
    print("Starting game simulation...")
    print("="*50 + "\n")

    success = test_complete_game()

    if success:
        print("\n✅ All tests passed! Game is working!")
    else:
        print("\n⚠️  Game ended in draw (turn limit reached)")
