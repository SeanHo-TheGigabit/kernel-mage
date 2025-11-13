"""Display system using rich library."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from typing import List, Optional
from kernelmage.entities.player import Player
from kernelmage.entities.enemy import Enemy
from kernelmage.magic.essences import EssenceType, Essence
from kernelmage.magic.architectures import Architecture
from kernelmage.network.protocols import ProtocolType


class Display:
    """Main display system."""

    def __init__(self):
        """Initialize display."""
        self.console = Console()

    def clear(self):
        """Clear the screen."""
        self.console.clear()

    def print(self, text: str, style: str = ""):
        """Print text to console."""
        self.console.print(text, style=style)

    def print_panel(self, content: str, title: str = "", style: str = ""):
        """Print a panel with content."""
        panel = Panel(content, title=title, border_style=style)
        self.console.print(panel)

    def show_title(self):
        """Show game title screen."""
        title = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗  ██╗███████╗██████╗ ███╗   ██╗███████╗██╗          ║
║   ██║ ██╔╝██╔════╝██╔══██╗████╗  ██║██╔════╝██║          ║
║   █████╔╝ █████╗  ██████╔╝██╔██╗ ██║█████╗  ██║          ║
║   ██╔═██╗ ██╔══╝  ██╔══██╗██║╚██╗██║██╔══╝  ██║          ║
║   ██║  ██╗███████╗██║  ██║██║ ╚████║███████╗███████╗     ║
║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝     ║
║                                                           ║
║   ███╗   ███╗ █████╗  ██████╗ ███████╗                   ║
║   ████╗ ████║██╔══██╗██╔════╝ ██╔════╝                   ║
║   ██╔████╔██║███████║██║  ███╗█████╗                     ║
║   ██║╚██╔╝██║██╔══██║██║   ██║██╔══╝                     ║
║   ██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗                   ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                   ║
║                                                           ║
║        Where Magic is Network Communication               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(title, style="bold cyan")

    def show_player_stats(self, player: Player):
        """Display player stats."""
        table = Table(title=f"{player.name} - Level {player.level}", show_header=False)

        table.add_row(
            "HP:",
            f"[red]{player.stats.current_hp}/{player.stats.max_hp}[/red]"
        )
        table.add_row(
            "Mana:",
            f"[blue]{player.stats.current_mana}/{player.stats.max_mana}[/blue]"
        )
        table.add_row(
            "XP:",
            f"[yellow]{player.experience}/{player.level * 100}[/yellow]"
        )
        table.add_row(
            "Architecture:",
            f"[cyan]{player.current_architecture.name}[/cyan]"
        )
        table.add_row(
            "Network:",
            f"[green]{player.network_address}[/green]"
        )

        self.console.print(table)

    def show_essence_inventory(self, player: Player):
        """Display essence inventory."""
        table = Table(title="Essence Inventory")

        table.add_column("Essence", style="bold")
        table.add_column("Quantity", justify="right")
        table.add_column("Power", justify="right")

        for essence_type, essence in player.essences.items():
            if essence.quantity > 0:
                color = essence.color
                table.add_row(
                    f"[{color}]{essence_type.value.title()}[/{color}]",
                    f"{essence.quantity}g",
                    f"{essence.power_rating}"
                )

        self.console.print(table)

    def show_architecture_info(self, architecture: Architecture):
        """Display architecture information."""
        info = (
            f"[bold]{architecture.name}[/bold]\n\n"
            f"{architecture.description}\n\n"
            f"Power Multiplier: [red]{architecture.power_multiplier}x[/red]\n"
            f"Mana Efficiency: [blue]{architecture.mana_efficiency}x[/blue]\n"
            f"Cast Speed: [yellow]{architecture.cast_speed:+d}[/yellow]\n"
            f"Flexibility: [green]{architecture.flexibility}[/green]\n\n"
            f"[cyan]{architecture.special_ability}[/cyan]"
        )

        self.print_panel(info, title="Architecture Info")

    def show_menu(self, title: str, options: List[tuple[str, str]]) -> str:
        """
        Show a menu and return selected option key.

        Args:
            title: Menu title
            options: List of (key, description) tuples

        Returns:
            Selected option key
        """
        table = Table(title=title, show_header=False)

        for key, description in options:
            table.add_row(f"[cyan]{key}[/cyan]", description)

        self.console.print(table)
        self.console.print()

        while True:
            choice = self.console.input("[bold yellow]Choose:[/bold yellow] ").strip().lower()
            if any(key == choice for key, _ in options):
                return choice
            self.console.print("[red]Invalid choice![/red]")

    def show_hp_bar(self, current: int, maximum: int, width: int = 20) -> str:
        """Create a text HP bar."""
        percentage = current / maximum if maximum > 0 else 0
        filled = int(width * percentage)
        empty = width - filled

        bar = "█" * filled + "░" * empty
        color = "green" if percentage > 0.5 else "yellow" if percentage > 0.25 else "red"

        return f"[{color}]{bar}[/{color}] {current}/{maximum}"

    def show_combat_log(self, messages: List[str], last_n: int = 10):
        """Display recent combat log messages."""
        recent = messages[-last_n:] if len(messages) > last_n else messages

        if recent:
            log_text = "\n".join(recent)
            self.print_panel(log_text, title="Combat Log", style="dim")

    def prompt_input(self, prompt: str = "") -> str:
        """Get input from user."""
        return self.console.input(f"[bold yellow]{prompt}[/bold yellow] ").strip()

    def show_message(self, message: str, style: str = ""):
        """Show a message."""
        self.console.print(f"\n{message}\n", style=style)

    def pause(self):
        """Wait for user to press enter."""
        self.console.input("\n[dim]Press Enter to continue...[/dim]")
