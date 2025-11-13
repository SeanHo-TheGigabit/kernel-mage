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
from kernelmage.world.world_map import WorldMap, LocationId
from kernelmage.world.events import EventManager
import random


class GameState:
    """Main game state."""

    def __init__(self):
        """Initialize game state."""
        self.player: Optional[Player] = None
        self.current_encounter: Optional[CombatEncounter] = None
        self.display = Display()
        self.combat_screen = CombatScreen(self.display)

        # World and events
        self.world_map = WorldMap()
        self.event_manager = EventManager()

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

        # Show current location
        current_loc = self.world_map.current_location
        self.display.console.print(
            f"📍 Location: [cyan]{current_loc.name}[/cyan] ({current_loc.subnet})\n"
        )

        options = [
            ("e", f"Explore {current_loc.name}"),
            ("m", "View Map"),
            ("t", "Travel"),
            ("v", "View Events"),
            ("i", "View Inventory"),
            ("a", "View Architecture"),
            ("s", "Switch Architecture"),
            ("q", "Quit Game"),
        ]

        return self.display.show_menu("Main Menu", options)

    def handle_main_menu(self):
        """Handle main menu interaction."""
        while self.running:
            # Check for story events
            event = self.event_manager.check_events(
                self.player.level,
                self.encounters_won,
                self.world_map.current_location_id.value
            )
            if event:
                self.show_story_event(event)

            choice = self.show_main_menu()

            if choice == "e":
                self.explore_current_location()
            elif choice == "m":
                self.show_map()
            elif choice == "t":
                self.travel_menu()
            elif choice == "v":
                self.show_events()
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

    def show_map(self):
        """Show the world map."""
        self.display.clear()

        # Show ASCII map
        map_ascii = self.world_map.get_map_ascii(self.player.level)
        self.display.console.print(map_ascii)
        self.display.console.print()

        # Show current location info
        current_loc = self.world_map.current_location
        info = self.world_map.get_location_info(current_loc.location_id)
        self.display.console.print(info)

        self.display.pause()

    def travel_menu(self):
        """Show travel menu."""
        self.display.clear()

        current_loc = self.world_map.current_location
        connected = self.world_map.get_connected_locations()

        if not connected:
            self.display.show_message("No connected locations!", style="yellow")
            self.display.pause()
            return

        self.display.console.print(f"\n[bold]Travel from {current_loc.name}[/bold]\n")

        for i, loc in enumerate(connected, 1):
            # Check if accessible
            accessible = loc.can_access(self.player.level)
            discovered = self.world_map.is_discovered(loc.location_id)

            if discovered:
                status = ""
                if not accessible:
                    status = f" [red](Level {loc.required_level} required)[/red]"
                elif loc.is_safe_zone:
                    status = " [green](Safe)[/green]"
                elif loc.is_dungeon:
                    status = f" [red](Dungeon - Danger {loc.danger_level})[/red]"

                self.display.console.print(
                    f"[{i}] {loc.name}{status}\n"
                    f"    {loc.description}\n"
                )
            else:
                self.display.console.print(
                    f"[{i}] ??? (Undiscovered)\n"
                )

        choice = self.display.prompt_input("\nSelect destination (or 'c' to cancel):")

        if choice.lower() == 'c':
            return

        try:
            idx = int(choice) - 1
            destination = connected[idx]

            success, message = self.world_map.travel_to(
                destination.location_id,
                self.player.level
            )

            self.display.show_message(message, style="green" if success else "red")
        except (ValueError, IndexError):
            self.display.show_message("Invalid choice!", style="red")

        self.display.pause()

    def show_events(self):
        """Show event status and available events."""
        self.display.clear()

        self.display.console.print("\n[bold cyan]Story Events[/bold cyan]\n")

        # Show event status
        status = self.event_manager.get_event_status()
        self.display.console.print(status)
        self.display.console.print()

        # Show available events
        available = self.event_manager.get_available_events_summary(
            self.player.level,
            self.encounters_won,
            self.world_map.current_location_id.value
        )
        self.display.console.print(available)

        self.display.pause()

    def show_story_event(self, event):
        """Display a story event."""
        self.display.clear()

        self.display.print_panel(
            event.description,
            title=f"[bold yellow]{event.title}[/bold yellow]",
            style="cyan"
        )

        if event.choices:
            self.display.console.print()
            choice = self.display.show_menu("What do you do?", event.choices)
            # Handle choice (basic for now)
            self.handle_event_choice(event, choice)

        event.trigger()
        self.display.pause()

    def handle_event_choice(self, event, choice: str):
        """Handle player choice in event."""
        # Basic handling - can be expanded
        if event.event_id == "welcome" and choice == "y":
            self.display.show_message("Quest accepted! May the packets be with you.", style="green")
        elif event.event_id == "welcome" and choice == "n":
            self.display.show_message("Prepare well, young mage.", style="yellow")

        # Mark event as completed
        event.complete()

    def explore_current_location(self):
        """Explore current location (trigger encounter)."""
        location = self.world_map.current_location

        if location.is_safe_zone:
            self.display.show_message(
                "This is a safe zone. No enemies here.\nRest and prepare for your journey.",
                style="green"
            )
            self.display.pause()
            return

        # Generate encounter based on location
        self.start_location_encounter(location)

    def start_location_encounter(self, location):
        """Start an encounter based on location."""
        if not location.enemy_types:
            self.display.show_message("No encounters in this area.", style="yellow")
            self.display.pause()
            return

        # Determine number of enemies
        num_enemies = random.randint(location.min_enemies, location.max_enemies)

        # Create enemies based on location
        enemies = []
        enemy_factories = {
            "bandit": create_bandit,
            "swarm_minion": create_swarm_minion,
            "corrupted_node": create_corrupted_node,
            "illusionist": create_illusionist,
            "gateway_boss": create_gateway_boss,
        }

        for _ in range(num_enemies):
            enemy_type = random.choice(location.enemy_types)
            factory = enemy_factories.get(enemy_type)
            if factory:
                enemies.append(factory())

        if enemies:
            self.current_encounter = create_encounter(self.player, enemies)
            self.run_combat()


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
