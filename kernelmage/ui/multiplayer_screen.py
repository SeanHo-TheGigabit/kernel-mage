"""Multiplayer UI screens."""
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from typing import List
from kernelmage.ui.display import Display
from kernelmage.multiplayer.coop_combat import CoopCombatEncounter
from kernelmage.entities.player import Player
from kernelmage.entities.enemy import Enemy


class MultiplayerScreen:
    """UI for multiplayer gameplay."""

    def __init__(self, display: Display):
        """Initialize multiplayer screen."""
        self.display = display

    def show_connection_menu(self) -> tuple[str, str, int]:
        """
        Show multiplayer connection menu.

        Returns:
            (mode, host, port) where mode is "host" or "join"
        """
        self.display.clear()

        self.display.console.print("\n[bold cyan]╔═══ Multiplayer Mode ═══╗[/bold cyan]\n")

        options = [
            ("h", "Host Game (LAN)"),
            ("j", "Join Game (LAN)"),
            ("s", "Connect to Server"),
            ("b", "Back to Single Player"),
        ]

        choice = self.display.show_menu("Multiplayer Options", options)

        if choice == "h":
            # Host game
            port = self.display.prompt_input("Port (default 8888):") or "8888"
            return ("host", "0.0.0.0", int(port))

        elif choice == "j":
            # Join game
            host = self.display.prompt_input("Host IP:") or "localhost"
            port = self.display.prompt_input("Port (default 8888):") or "8888"
            return ("join", host, int(port))

        elif choice == "s":
            # Connect to remote server
            host = self.display.prompt_input("Server address:") or "localhost"
            port = self.display.prompt_input("Port (default 8888):") or "8888"
            return ("join", host, int(port))

        else:
            return ("back", "", 0)

    def show_waiting_for_players(self, player_count: int, max_players: int = 2):
        """Show waiting screen."""
        self.display.clear()

        self.display.console.print("\n[bold cyan]Waiting for Players...[/bold cyan]\n")
        self.display.console.print(f"Players connected: {player_count}/{max_players}\n")
        self.display.console.print("[dim]Press Ctrl+C to cancel[/dim]\n")

    def show_coop_combat_state(self, encounter: CoopCombatEncounter, local_player: Player):
        """Display cooperative combat state."""
        self.display.console.clear()

        # Title
        self.display.console.print(
            f"\n[bold red]⚔ CO-OP COMBAT - Turn {encounter.turn_number} ⚔[/bold red]\n"
        )

        # Players panel
        players_panel = self._create_coop_players_panel(encounter, local_player)

        # Enemies panel
        enemies_panel = self._create_coop_enemies_panel(encounter)

        # Show panels side by side
        panels = Columns([players_panel, enemies_panel], equal=True)
        self.display.console.print(panels)

        # Ready status
        ready_text = self._create_ready_status(encounter)
        if ready_text:
            self.display.console.print(ready_text)

        # Combat log (last 5 messages)
        self.display.show_combat_log(encounter.combat_log, last_n=5)

        self.display.console.print()

    def _create_coop_players_panel(self, encounter: CoopCombatEncounter, local_player: Player) -> Panel:
        """Create players panel for coop combat."""
        content = ""

        for player in encounter.players:
            is_local = (player == local_player)
            marker = "[YOU]" if is_local else "[ALLY]"

            hp_bar = self.display.show_hp_bar(
                player.stats.current_hp,
                player.stats.max_hp,
                width=20
            )

            mana_bar = self.display.show_hp_bar(
                player.stats.current_mana,
                player.stats.max_mana,
                width=20
            )

            alive_status = "" if player.is_alive else " [red](DEFEATED)[/red]"

            content += (
                f"[bold cyan]{player.name}[/bold cyan] {marker}{alive_status}\n"
                f"  HP:   {hp_bar}\n"
                f"  Mana: {mana_bar}\n"
                f"  Arch: [yellow]{player.current_architecture.name}[/yellow]\n\n"
            )

        return Panel(content.strip(), title="[bold]Your Party[/bold]", border_style="cyan")

    def _create_coop_enemies_panel(self, encounter: CoopCombatEncounter) -> Panel:
        """Create enemies panel for coop combat."""
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

    def _create_ready_status(self, encounter: CoopCombatEncounter) -> str:
        """Create ready status text."""
        if encounter.all_players_ready:
            return "[green]✓ All players ready! Executing turn...[/green]"

        ready_count = len(encounter.players_ready)
        total_count = len(encounter.active_players)

        if ready_count > 0:
            return f"[yellow]⏳ Waiting for players... ({ready_count}/{total_count} ready)[/yellow]"

        return ""

    def show_player_list(self, players: List[str]):
        """Show list of connected players."""
        self.display.clear()

        self.display.console.print("\n[bold]Connected Players:[/bold]\n")

        for i, player_name in enumerate(players, 1):
            self.display.console.print(f"  {i}. {player_name}")

        self.display.console.print()

    def show_chat_message(self, player_name: str, message: str):
        """Show a chat message."""
        self.display.console.print(f"[cyan]{player_name}:[/cyan] {message}")

    def prompt_chat_message(self) -> Optional[str]:
        """Prompt for chat message (non-blocking)."""
        # In real implementation, this would be non-blocking
        # For now, simple prompt
        return None  # Disabled for turn-based gameplay
