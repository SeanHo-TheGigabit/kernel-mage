"""Combat screen UI."""
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from typing import List
from kernelmage.ui.display import Display
from kernelmage.combat.combat import CombatEncounter, CombatState
from kernelmage.entities.enemy import Enemy
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType


class CombatScreen:
    """Combat screen display."""

    def __init__(self, display: Display):
        """Initialize combat screen."""
        self.display = display

    def show_combat_state(self, encounter: CombatEncounter):
        """Display current combat state."""
        self.display.console.clear()

        # Title
        self.display.console.print(
            f"\n[bold red]⚔ COMBAT - Turn {encounter.turn_number} ⚔[/bold red]\n"
        )

        # Player stats panel
        player_stats = self._create_player_panel(encounter)

        # Enemies panel
        enemies_panel = self._create_enemies_panel(encounter)

        # Show panels side by side
        panels = Columns([player_stats, enemies_panel], equal=True)
        self.display.console.print(panels)

        # Pending spells
        if encounter.pending_player_spells:
            pending_text = ""
            for spell in encounter.pending_player_spells:
                pending_text += (
                    f"⏳ {spell.packet.payload.essence_type.value.title()} spell "
                    f"via {spell.protocol.value.upper()} - "
                    f"{spell.turns_remaining} turn(s) remaining\n"
                )
            self.display.print_panel(pending_text.strip(), title="Pending Spells", style="yellow")

        # Combat log (last 5 messages)
        self.display.show_combat_log(encounter.combat_log, last_n=5)

        self.display.console.print()

    def _create_player_panel(self, encounter: CombatEncounter) -> Panel:
        """Create player stats panel."""
        player = encounter.player

        hp_bar = self.display.show_hp_bar(
            player.stats.current_hp,
            player.stats.max_hp,
            width=30
        )

        mana_bar = self.display.show_hp_bar(
            player.stats.current_mana,
            player.stats.max_mana,
            width=30
        )

        content = (
            f"[bold cyan]{player.name}[/bold cyan] (Lvl {player.level})\n"
            f"[green]{player.network_address}[/green]\n\n"
            f"HP:   {hp_bar}\n"
            f"Mana: {mana_bar}\n\n"
            f"Architecture: [yellow]{player.current_architecture.name}[/yellow]\n"
            f"Power: {player.stats.power} | Defense: {player.stats.defense}"
        )

        return Panel(content, title="[bold]You[/bold]", border_style="cyan")

    def _create_enemies_panel(self, encounter: CombatEncounter) -> Panel:
        """Create enemies panel."""
        content = ""

        for i, enemy in enumerate(encounter.enemies, 1):
            if enemy.is_alive:
                hp_bar = self.display.show_hp_bar(
                    enemy.stats.current_hp,
                    enemy.stats.max_hp,
                    width=20
                )

                content += (
                    f"[{i}] [bold red]{enemy.name}[/bold red] ({enemy.symbol})\n"
                    f"    {hp_bar}\n"
                    f"    [dim]{enemy.network_address}[/dim]\n\n"
                )
            else:
                content += f"[{i}] [dim strikethrough]{enemy.name} (Defeated)[/dim strikethrough]\n\n"

        if not encounter.active_enemies:
            content = "[green]All enemies defeated![/green]"

        return Panel(content.strip(), title="[bold]Enemies[/bold]", border_style="red")

    def show_combat_menu(self) -> str:
        """Show combat action menu."""
        options = [
            ("a", "Attack (cast spell)"),
            ("p", "Ping (ICMP scan target)"),
            ("s", "Switch Architecture"),
            ("i", "Inventory"),
            ("f", "Flee"),
        ]

        return self.display.show_menu("Choose Action", options)

    def select_target(self, enemies: List[Enemy]) -> int:
        """Select a target from alive enemies."""
        alive_enemies = [(i, e) for i, e in enumerate(enemies) if e.is_alive]

        if not alive_enemies:
            return -1

        self.display.console.print("\n[bold]Select Target:[/bold]")
        for i, enemy in alive_enemies:
            hp_percent = enemy.stats.hp_percentage
            self.display.console.print(
                f"  [{i + 1}] {enemy.name} "
                f"({enemy.stats.current_hp}/{enemy.stats.max_hp} HP)"
            )

        while True:
            try:
                choice = self.display.prompt_input("Target number:")
                target_idx = int(choice) - 1

                if 0 <= target_idx < len(enemies) and enemies[target_idx].is_alive:
                    return target_idx
                else:
                    self.display.console.print("[red]Invalid target![/red]")
            except ValueError:
                self.display.console.print("[red]Please enter a number![/red]")

    def select_essence(self, player) -> EssenceType:
        """Select essence to use."""
        available = [(e_type, essence) for e_type, essence in player.essences.items()
                     if essence.quantity > 0]

        if not available:
            return None

        self.display.console.print("\n[bold]Select Essence:[/bold]")
        for i, (e_type, essence) in enumerate(available, 1):
            color = essence.color
            self.display.console.print(
                f"  [{i}] [{color}]{e_type.value.title()}[/{color}] "
                f"({essence.quantity}g, {essence.power_rating} power)"
            )

        while True:
            try:
                choice = self.display.prompt_input("Essence number:")
                idx = int(choice) - 1

                if 0 <= idx < len(available):
                    return available[idx][0]
                else:
                    self.display.console.print("[red]Invalid choice![/red]")
            except ValueError:
                self.display.console.print("[red]Please enter a number![/red]")

    def select_protocol(self) -> ProtocolType:
        """Select network protocol."""
        protocols = [
            (ProtocolType.TCP, "TCP - Reliable, slow, guaranteed hit (3 turns, 2x mana)"),
            (ProtocolType.UDP, "UDP - Fast, unreliable (1 turn, 0.7x mana, 70% accuracy)"),
            (ProtocolType.MULTICAST, "Multicast - Area effect (2 turns, 2.5x mana)"),
        ]

        self.display.console.print("\n[bold]Select Protocol:[/bold]")
        for i, (p_type, desc) in enumerate(protocols, 1):
            self.display.console.print(f"  [{i}] {desc}")

        while True:
            try:
                choice = self.display.prompt_input("Protocol number:")
                idx = int(choice) - 1

                if 0 <= idx < len(protocols):
                    return protocols[idx][0]
                else:
                    self.display.console.print("[red]Invalid choice![/red]")
            except ValueError:
                self.display.console.print("[red]Please enter a number![/red]")

    def show_victory(self, encounter: CombatEncounter):
        """Show victory screen."""
        self.display.console.print("\n[bold green]═══ VICTORY! ═══[/bold green]\n")

        # Show rewards
        self.display.console.print(f"Level: {encounter.player.level}")
        self.display.console.print(f"XP: {encounter.player.experience}\n")

        self.display.pause()

    def show_defeat(self):
        """Show defeat screen."""
        self.display.console.print("\n[bold red]═══ DEFEAT ═══[/bold red]\n")
        self.display.console.print("You have been defeated...\n")

        self.display.pause()
