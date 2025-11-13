"""Cooperative combat system for multiplayer."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from kernelmage.entities.player import Player
from kernelmage.entities.enemy import Enemy
from kernelmage.combat.combat import CombatEncounter, CombatState
from kernelmage.multiplayer.protocol import PlayerState, CombatAction
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType
import time


@dataclass
class CoopCombatEncounter:
    """Cooperative combat encounter with multiple players."""

    players: List[Player]
    enemies: List[Enemy]

    state: CombatState = CombatState.ACTIVE
    turn_number: int = 0

    # Player actions this turn
    pending_actions: Dict[str, Optional[CombatAction]] = field(default_factory=dict)
    players_ready: set = field(default_factory=set)

    # Combat log
    combat_log: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize player tracking."""
        for player in self.players:
            player_id = id(player)  # Use object id as player_id
            self.pending_actions[str(player_id)] = None

    def log(self, message: str):
        """Add message to combat log."""
        timestamp = time.time()
        self.combat_log.append(f"[Turn {self.turn_number}] {message}")

    @property
    def active_enemies(self) -> List[Enemy]:
        """Get list of living enemies."""
        return [e for e in self.enemies if e.is_alive]

    @property
    def active_players(self) -> List[Player]:
        """Get list of living players."""
        return [p for p in self.players if p.is_alive]

    @property
    def is_over(self) -> bool:
        """Check if combat is over."""
        return self.state != CombatState.ACTIVE

    @property
    def all_players_ready(self) -> bool:
        """Check if all players have submitted actions."""
        active_player_ids = {str(id(p)) for p in self.active_players}
        return active_player_ids <= self.players_ready

    def submit_player_action(self, player: Player, action: Optional[CombatAction]):
        """Submit a player's action for this turn."""
        player_id = str(id(player))
        self.pending_actions[player_id] = action
        self.players_ready.add(player_id)

        self.log(f"{player.name} ready!")

    def execute_turn(self):
        """Execute all player actions for this turn."""
        if not self.all_players_ready:
            return  # Not all players ready

        self.turn_number += 1
        self.log(f"=== Turn {self.turn_number} ===")

        # Execute player actions
        for player in self.active_players:
            player_id = str(id(player))
            action = self.pending_actions.get(player_id)

            if action:
                self._execute_action(player, action)

        # Enemy turns
        for enemy in self.active_enemies:
            self._enemy_turn(enemy)

        # Clear actions for next turn
        self.pending_actions = {pid: None for pid in self.pending_actions.keys()}
        self.players_ready.clear()

        # Check victory
        self.check_victory_conditions()

    def _execute_action(self, player: Player, action: CombatAction):
        """Execute a single player action."""
        if action.action_type == "attack":
            # Get target
            if action.target_index is not None and 0 <= action.target_index < len(self.enemies):
                target = self.enemies[action.target_index]

                if target.is_alive and action.essence_type and action.protocol_type:
                    # Import here to avoid circular import
                    from kernelmage.magic.spells import SpellSystem

                    # Cast spell
                    essence_type = EssenceType(action.essence_type)
                    protocol_type = ProtocolType(action.protocol_type)

                    result = SpellSystem.cast_spell(
                        player, target, essence_type, protocol_type
                    )

                    if result.success and result.packet:
                        # Resolve immediately for multiplayer
                        hit, damage, message = SpellSystem.resolve_spell(
                            result.packet, target, protocol_type
                        )

                        self.log(f"{player.name}: {message}")

                        if not target.is_alive:
                            self.log(f"{target.name} defeated!")

        elif action.action_type == "ping":
            # ICMP ping
            if action.target_index is not None and 0 <= action.target_index < len(self.enemies):
                target = self.enemies[action.target_index]
                from kernelmage.network.dns import DNSSystem

                info = DNSSystem.ping(player, target)
                self.log(f"{player.name} pinged {target.name} ({info['hp']}/{info['max_hp']} HP)")

    def _enemy_turn(self, enemy: Enemy):
        """Execute enemy turn (attacks random player)."""
        import random

        if not self.active_players:
            return

        # Attack random player
        target = random.choice(self.active_players)

        damage = random.randint(5, 15) + enemy.stats.power
        actual_damage = target.take_damage(damage, enemy)

        self.log(f"{enemy.name} attacks {target.name} for {actual_damage} damage!")

    def check_victory_conditions(self):
        """Check and update combat state."""
        if not any(p.is_alive for p in self.players):
            self.state = CombatState.DEFEAT
            self.log("All players defeated!")

        elif len(self.active_enemies) == 0:
            self.state = CombatState.VICTORY
            self.log("Victory! All enemies defeated!")
            self.award_loot()

    def award_loot(self):
        """Award XP and loot to all players."""
        total_xp = sum(enemy.xp_reward for enemy in self.enemies)

        # Split XP among living players
        if self.active_players:
            xp_per_player = total_xp // len(self.active_players)

            for player in self.active_players:
                player.gain_experience(xp_per_player)
                self.log(f"{player.name} gained {xp_per_player} XP!")

                # Award essence drops
                for enemy in self.enemies:
                    essence_type, amount = enemy.get_loot()
                    if essence_type:
                        # Split loot
                        amount_per_player = amount // len(self.active_players)
                        if amount_per_player > 0:
                            player.add_essence(essence_type, amount_per_player)


def create_coop_encounter(players: List[Player], enemies: List[Enemy]) -> CoopCombatEncounter:
    """Create a cooperative combat encounter."""
    encounter = CoopCombatEncounter(players=players, enemies=enemies)
    encounter.log(f"Cooperative combat started! {len(players)} players vs {len(enemies)} enemies")

    for enemy in enemies:
        encounter.log(f"{enemy.name} appeared! ({enemy.stats.current_hp} HP)")

    return encounter
