"""Simplified Arena Mode - Pure Combat Sequence"""
from typing import Optional
from kernelmage.entities.player import Player, create_player
from kernelmage.entities.enemy import (
    create_bandit, create_corrupted_node,
    create_gateway_boss, create_illusionist, create_swarm_minion
)
from kernelmage.combat.combat import CombatEncounter, CombatState, create_encounter
from kernelmage.ui.display import Display
from kernelmage.ui.combat_screen import CombatScreen
from kernelmage.magic.spells import SpellSystem
from kernelmage.magic.architectures import ArchitectureType
import random


class ArenaGame:
    """Simplified arena-style combat game."""

    def __init__(self):
        """Initialize arena game."""
        self.player: Optional[Player] = None
        self.current_encounter: Optional[CombatEncounter] = None
        self.display = Display()
        self.combat_screen = CombatScreen(self.display)

        self.round_number = 0
        self.running = True

    def start(self):
        """Start the arena game."""
        self.display.clear()
        self.display.show_title()
        self.display.console.print()

        # Welcome message
        self.display.show_message(
            "WELCOME TO THE MAGE ARENA\n\n"
            "Fight waves of enemies using network magic.\n"
            "How long can you survive?\n\n"
            "Magic is network communication:\n"
            "• Spells are packets\n"
            "• TCP = Slow but accurate\n"
            "• UDP = Fast but risky\n"
            "• Pick your architecture wisely!",
            style="cyan bold"
        )
        self.display.pause()

        # Get player name
        self.display.clear()
        name = self.display.prompt_input("Enter your mage's name:") or "Mage"
        self.player = create_player(name)

        # Choose starting architecture
        self.choose_starting_architecture()

        # Give starting essences
        from kernelmage.magic.essences import EssenceType
        self.player.add_essence(EssenceType.FIRE, 30)
        self.player.add_essence(EssenceType.WATER, 30)
        self.player.add_essence(EssenceType.LIGHTNING, 20)

        self.display.show_message(
            f"\n{self.player.name}, you enter the arena!\n"
            f"Architecture: {self.player.current_architecture.name}\n"
            f"Starting Essences: 30 Fire, 30 Water, 20 Lightning\n\n"
            "Good luck!",
            style="green bold"
        )
        self.display.pause()

        # Start arena loop
        self.arena_loop()

    def choose_starting_architecture(self):
        """Let player choose starting architecture."""
        self.display.clear()

        self.display.console.print("\n[bold cyan]Choose Your Architecture[/bold cyan]\n")

        architectures = [
            (ArchitectureType.X86_CISC, "Powerful but slow (High damage, +1 turn cast)"),
            (ArchitectureType.ARM_RISC, "Fast and efficient (Low cost, fast cast)"),
            (ArchitectureType.RISC_V, "Balanced (Good all-around)"),
        ]

        for i, (arch_type, desc) in enumerate(architectures, 1):
            self.display.console.print(f"[{i}] {arch_type.value}\n    {desc}\n")

        while True:
            choice = self.display.prompt_input("Choose (1-3):")
            try:
                idx = int(choice) - 1
                if 0 <= idx < 3:
                    arch_type, _ = architectures[idx]
                    self.player.switch_architecture(arch_type)
                    break
            except ValueError:
                pass
            self.display.show_message("Invalid choice! Pick 1, 2, or 3", style="red")

    def arena_loop(self):
        """Main arena combat loop."""
        while self.running:
            self.round_number += 1

            # Show round start
            self.display.clear()
            self.display.console.print(
                f"\n[bold yellow]═══ ROUND {self.round_number} ═══[/bold yellow]\n"
            )

            # Rest between rounds (partial healing)
            if self.round_number > 1:
                self.rest_between_rounds()

            self.display.show_player_stats(self.player)
            self.display.console.print()
            self.display.show_message("Enemies approaching...", style="red")
            self.display.pause()

            # Generate enemies for this round
            enemies = self.generate_round_enemies(self.round_number)

            # Start combat
            self.current_encounter = create_encounter(self.player, enemies)
            self.run_combat()

            # Check if player lost
            if not self.player.is_alive:
                self.show_game_over()
                break

            # Victory - continue to next round
            self.show_round_victory()

    def generate_round_enemies(self, round_num: int):
        """Generate enemies based on round number (progressive difficulty)."""
        enemies = []

        if round_num == 1:
            # Round 1: Single bandit
            enemies = [create_bandit()]

        elif round_num == 2:
            # Round 2: Two bandits
            enemies = [create_bandit(), create_bandit()]

        elif round_num == 3:
            # Round 3: Corrupted node
            enemies = [create_corrupted_node()]

        elif round_num == 4:
            # Round 4: Swarm of minions
            enemies = [create_swarm_minion() for _ in range(3)]

        elif round_num == 5:
            # Round 5: Mixed group
            enemies = [create_bandit(), create_corrupted_node()]

        elif round_num == 6:
            # Round 6: Illusionist
            enemies = [create_illusionist()]

        elif round_num == 7:
            # Round 7: Multiple corrupted nodes
            enemies = [create_corrupted_node(), create_corrupted_node()]

        elif round_num == 8:
            # Round 8: Boss
            enemies = [create_gateway_boss()]

        else:
            # Round 9+: Random hard encounters
            encounter_type = random.choice([1, 2, 3, 4])
            if encounter_type == 1:
                enemies = [create_illusionist(), create_corrupted_node()]
            elif encounter_type == 2:
                enemies = [create_corrupted_node() for _ in range(3)]
            elif encounter_type == 3:
                enemies = [create_gateway_boss()]
            else:
                enemies = [create_bandit(), create_swarm_minion(), create_swarm_minion()]

        return enemies

    def rest_between_rounds(self):
        """Restore some HP and mana between rounds."""
        heal_amount = int(self.player.stats.max_hp * 0.3)
        mana_amount = int(self.player.stats.max_mana * 0.4)

        old_hp = self.player.stats.current_hp
        old_mana = self.player.stats.current_mana

        self.player.stats.current_hp = min(
            self.player.stats.max_hp,
            self.player.stats.current_hp + heal_amount
        )
        self.player.stats.current_mana = min(
            self.player.stats.max_mana,
            self.player.stats.current_mana + mana_amount
        )

        healed = self.player.stats.current_hp - old_hp
        restored = self.player.stats.current_mana - old_mana

        self.display.show_message(
            f"You rest between rounds...\n"
            f"HP restored: +{healed}\n"
            f"Mana restored: +{restored}",
            style="green"
        )
        self.display.console.print()

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
                # No fleeing in arena!
                self.display.show_message(
                    "There is no escape from the arena!",
                    style="red bold"
                )
                self.display.pause()

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
        self.display.clear()

        self.display.console.print("\n[bold]Switch Architecture[/bold]\n")

        architectures = [
            (ArchitectureType.X86_CISC, "Powerful but slow"),
            (ArchitectureType.ARM_RISC, "Fast and efficient"),
            (ArchitectureType.RISC_V, "Balanced"),
        ]

        for i, (arch_type, desc) in enumerate(architectures, 1):
            current = " [CURRENT]" if arch_type == self.player.current_architecture.arch_type else ""
            self.display.console.print(f"[{i}] {arch_type.value}{current}\n    {desc}\n")

        choice = self.display.prompt_input("Choose (1-3 or 'c' to cancel):")

        if choice.lower() == 'c':
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < 3:
                arch_type, _ = architectures[idx]
                if self.player.switch_architecture(arch_type):
                    self.display.show_message(
                        f"Switched to {arch_type.value}! (Cost: 20 mana)",
                        style="green"
                    )
                    # Switching costs a turn
                    encounter.next_turn()
                else:
                    self.display.show_message("Not enough mana!", style="red")
                    self.display.pause()
        except (ValueError, IndexError):
            self.display.show_message("Invalid choice!", style="red")
            self.display.pause()

    def show_inventory(self):
        """Show inventory screen."""
        self.display.clear()
        self.display.console.print("\n[bold]Essence Inventory[/bold]\n")
        self.display.show_essence_inventory(self.player)
        self.display.pause()

    def show_round_victory(self):
        """Show victory for this round."""
        self.display.clear()

        self.display.console.print(
            f"\n[bold green]✓ ROUND {self.round_number} COMPLETE[/bold green]\n"
        )

        self.display.show_message(
            f"Enemies defeated!\n"
            f"Level: {self.player.level}\n"
            f"HP: {self.player.stats.current_hp}/{self.player.stats.max_hp}\n"
            f"Mana: {self.player.stats.current_mana}/{self.player.stats.max_mana}",
            style="cyan"
        )

        self.display.pause()

    def show_game_over(self):
        """Show game over screen."""
        self.display.clear()

        self.display.console.print(
            "\n[bold red]╔═══════════════════════════════╗[/bold red]\n"
            "[bold red]║       DEFEATED                ║[/bold red]\n"
            "[bold red]╚═══════════════════════════════╝[/bold red]\n"
        )

        self.display.show_message(
            f"\n{self.player.name} has fallen in combat...\n\n"
            f"FINAL SCORE\n"
            f"═══════════\n"
            f"Rounds Survived: {self.round_number}\n"
            f"Final Level: {self.player.level}\n"
            f"Architecture: {self.player.current_architecture.name}",
            style="yellow"
        )

        self.display.pause()
        self.running = False


def run_arena():
    """Main arena entry point."""
    arena = ArenaGame()

    try:
        arena.start()
    except KeyboardInterrupt:
        arena.display.console.print("\n\n[yellow]Arena interrupted![/yellow]\n")
    except Exception as e:
        arena.display.console.print(f"\n\n[red]Error: {e}[/red]\n")
        raise

    arena.display.console.print("\n[cyan]Thanks for playing![/cyan]\n")
