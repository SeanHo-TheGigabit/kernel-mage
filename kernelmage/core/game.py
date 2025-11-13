"""Core game engine and loop."""
from typing import Optional
from kernelmage.entities.player import Player, create_player
from kernelmage.entities.enemy import (
    Enemy, create_bandit, create_corrupted_node,
    create_gateway_boss, create_illusionist, create_swarm_minion
)
from kernelmage.combat.combat import CombatEncounter, CombatState, create_encounter
from kernelmage.ui.display import Display
from kernelmage.ui.combat_screen import CombatScreen
from kernelmage.magic.spells import SpellSystem
from kernelmage.magic.architectures import ArchitectureType, get_architecture
import random


class GameState:
    """Main game state."""

    def __init__(self):
        """Initialize game state."""
        self.player: Optional[Player] = None
        self.current_encounter: Optional[CombatEncounter] = None
        self.display = Display()
        self.combat_screen = CombatScreen(self.display)

        self.encounters_won = 0
        self.running = True

    def start_new_game(self):
        """Start a new game."""
        self.display.clear()
        self.display.show_title()
        self.display.console.print()

        # Get player name
        name = self.display.prompt_input("Enter your mage's name:") or "Mage"
        self.player = create_player(name)

        self.display.show_message(
            f"Welcome, {self.player.name}!\n\n"
            "You are a mage learning the secrets of network magic.\n"
            "Magic is network communication between souls.\n"
            "Spells are packets. Targeting is DNS. Wands are NICs.\n\n"
            "Good luck on your journey!",
            style="cyan"
        )

        self.display.pause()

    def show_main_menu(self) -> str:
        """Show main menu."""
        self.display.clear()

        self.display.console.print(f"\n[bold cyan]╔═══ {self.player.name} ═══╗[/bold cyan]\n")
        self.display.show_player_stats(self.player)
        self.display.console.print()

        options = [
            ("e", "Enter Combat (Test Encounter)"),
            ("i", "View Inventory"),
            ("a", "View Architecture"),
            ("s", "Switch Architecture"),
            ("q", "Quit Game"),
        ]

        return self.display.show_menu("Main Menu", options)

    def handle_main_menu(self):
        """Handle main menu interaction."""
        while self.running:
            choice = self.show_main_menu()

            if choice == "e":
                self.start_random_encounter()
            elif choice == "i":
                self.show_inventory()
            elif choice == "a":
                self.show_architecture()
            elif choice == "s":
                self.architecture_menu()
            elif choice == "q":
                self.running = False
                self.display.show_message("Thanks for playing!", style="bold cyan")

    def show_inventory(self):
        """Show inventory screen."""
        self.display.clear()
        self.display.console.print("\n[bold]Inventory[/bold]\n")
        self.display.show_essence_inventory(self.player)
        self.display.pause()

    def show_architecture(self):
        """Show current architecture."""
        self.display.clear()
        self.display.show_architecture_info(self.player.current_architecture)
        self.display.pause()

    def architecture_menu(self):
        """Show architecture switching menu."""
        self.display.clear()

        self.display.console.print("\n[bold]Available Architectures[/bold]\n")

        for i, arch in enumerate(self.player.architecture_state.available_architectures, 1):
            current = " [CURRENT]" if arch == self.player.current_architecture else ""
            self.display.console.print(
                f"[{i}] [cyan]{arch.name}[/cyan]{current}\n"
                f"    {arch.description}\n"
            )

        choice = self.display.prompt_input("\nSelect architecture (or 'c' to cancel):")

        if choice.lower() == 'c':
            return

        try:
            idx = int(choice) - 1
            arch = self.player.architecture_state.available_architectures[idx]

            if arch == self.player.current_architecture:
                self.display.show_message("Already using that architecture!", style="yellow")
            else:
                if self.player.switch_architecture(arch.arch_type):
                    self.display.show_message(
                        f"Switched to {arch.name}! (Cost: 20 mana)",
                        style="green"
                    )
                else:
                    self.display.show_message("Not enough mana!", style="red")

            self.display.pause()
        except (ValueError, IndexError):
            self.display.show_message("Invalid choice!", style="red")
            self.display.pause()

    def start_random_encounter(self):
        """Start a random combat encounter."""
        encounter_type = random.choice([1, 2, 3, 4])

        if encounter_type == 1:
            # Single bandit
            enemies = [create_bandit()]
        elif encounter_type == 2:
            # Two bandits
            enemies = [create_bandit(), create_bandit()]
        elif encounter_type == 3:
            # Corrupted node
            enemies = [create_corrupted_node()]
        else:
            # Swarm of minions
            enemies = [create_swarm_minion() for _ in range(3)]

        self.current_encounter = create_encounter(self.player, enemies)
        self.run_combat()

    def run_combat(self):
        """Run combat encounter."""
        encounter = self.current_encounter

        while not encounter.is_over:
            # Show combat state
            self.combat_screen.show_combat_state(encounter)

            # Player's turn
            action = self.combat_screen.show_combat_menu()

            if action == "a":
                self.handle_attack(encounter)
            elif action == "p":
                self.handle_ping(encounter)
            elif action == "s":
                self.handle_architecture_switch(encounter)
            elif action == "i":
                self.show_inventory()
            elif action == "f":
                if encounter.player_flee():
                    break
                else:
                    # Failed to flee, enemies get a turn
                    encounter.next_turn()

        # Combat ended
        if encounter.state == CombatState.VICTORY:
            self.combat_screen.show_victory(encounter)
            self.encounters_won += 1
        elif encounter.state == CombatState.DEFEAT:
            self.combat_screen.show_defeat()
            self.running = False  # Game over

    def handle_attack(self, encounter: CombatEncounter):
        """Handle player attack action."""
        # Select target
        target_idx = self.combat_screen.select_target(encounter.enemies)
        if target_idx < 0:
            return

        target = encounter.enemies[target_idx]

        # Select essence
        essence_type = self.combat_screen.select_essence(self.player)
        if not essence_type:
            self.display.show_message("No essence available!", style="red")
            self.display.pause()
            return

        # Select protocol
        protocol_type = self.combat_screen.select_protocol()

        # Cast spell
        result = encounter.player_cast_spell(target, essence_type, protocol_type)

        if not result.success:
            self.display.show_message(result.message, style="red")
            self.display.pause()
            return

        # Show result
        self.display.show_message(result.message, style="green")
        self.display.pause()

        # Advance turn
        encounter.next_turn()

    def handle_ping(self, encounter: CombatEncounter):
        """Handle ICMP ping action."""
        # Select target
        target_idx = self.combat_screen.select_target(encounter.enemies)
        if target_idx < 0:
            return

        target = encounter.enemies[target_idx]

        # Cast ping
        result = SpellSystem.cast_ping(self.player, target)

        if result["success"]:
            info = result["info"]
            message = (
                f"Pinged {info['name']}:\n"
                f"  IP: {info['ip']}\n"
                f"  Hostname: {info['hostname']}\n"
                f"  HP: {info['hp']}/{info['max_hp']}\n"
                f"  Latency: {info['latency']} turns\n"
                f"  Packet Loss: {info['packet_loss'] * 100:.1f}%\n"
                f"  Firewall: {info['firewall']}\n"
            )
            self.display.show_message(message, style="cyan")
            encounter.log(result["message"])
        else:
            self.display.show_message(result["message"], style="red")

        self.display.pause()

        # Ping costs a turn
        encounter.next_turn()

    def handle_architecture_switch(self, encounter: CombatEncounter):
        """Handle architecture switching in combat."""
        self.architecture_menu()
        # Switching costs a turn
        encounter.next_turn()


def run_game():
    """Main game entry point."""
    game = GameState()

    try:
        game.start_new_game()
        game.handle_main_menu()
    except KeyboardInterrupt:
        game.display.console.print("\n\n[yellow]Game interrupted![/yellow]\n")
    except Exception as e:
        game.display.console.print(f"\n\n[red]Error: {e}[/red]\n")
        raise

    game.display.console.print("\n[cyan]Goodbye![/cyan]\n")
