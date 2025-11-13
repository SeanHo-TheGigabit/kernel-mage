"""Combat system and management."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from kernelmage.entities.player import Player
from kernelmage.entities.enemy import Enemy
from kernelmage.core.entity import Entity
from kernelmage.magic.spells import SpellSystem, SpellCastResult
from kernelmage.magic.essences import EssenceType
from kernelmage.network.protocols import ProtocolType
from kernelmage.network.packets import MagicalPacket
import random


class CombatState(Enum):
    """Combat state."""

    ACTIVE = "active"
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLED = "fled"


@dataclass
class PendingSpell:
    """A spell that's being cast over multiple turns."""

    packet: MagicalPacket
    caster: Entity
    target: Entity
    protocol: ProtocolType
    turns_remaining: int
    total_turns: int

    @property
    def is_ready(self) -> bool:
        """Check if spell is ready to resolve."""
        return self.turns_remaining <= 0


@dataclass
class CombatEncounter:
    """A combat encounter between player and enemies."""

    player: Player
    enemies: List[Enemy]

    state: CombatState = CombatState.ACTIVE
    turn_number: int = 0

    # Pending spells (multi-turn casts)
    pending_player_spells: List[PendingSpell] = field(default_factory=list)
    pending_enemy_spells: List[PendingSpell] = field(default_factory=list)

    # Combat log
    combat_log: List[str] = field(default_factory=list)

    def log(self, message: str):
        """Add message to combat log."""
        self.combat_log.append(f"[Turn {self.turn_number}] {message}")

    @property
    def active_enemies(self) -> List[Enemy]:
        """Get list of living enemies."""
        return [e for e in self.enemies if e.is_alive]

    @property
    def is_over(self) -> bool:
        """Check if combat is over."""
        return self.state != CombatState.ACTIVE

    def check_victory_conditions(self):
        """Check and update combat state based on victory conditions."""
        if not self.player.is_alive:
            self.state = CombatState.DEFEAT
            self.log("Player defeated!")
        elif len(self.active_enemies) == 0:
            self.state = CombatState.VICTORY
            self.log("Victory! All enemies defeated!")

            # Award XP and loot
            self.award_loot()

    def award_loot(self):
        """Award experience and loot to player."""
        total_xp = 0
        loot = {}

        for enemy in self.enemies:
            total_xp += enemy.xp_reward

            essence_type, amount = enemy.get_loot()
            if essence_type:
                loot[essence_type] = loot.get(essence_type, 0) + amount

        self.player.gain_experience(total_xp)
        self.log(f"Gained {total_xp} experience!")

        for essence_type, amount in loot.items():
            self.player.add_essence(essence_type, amount)
            self.log(f"Looted {amount}g of {essence_type.value} essence!")

    def player_cast_spell(
        self,
        target: Enemy,
        essence_type: EssenceType,
        protocol_type: ProtocolType
    ) -> SpellCastResult:
        """Player casts a spell at target."""
        result = SpellSystem.cast_spell(
            self.player,
            target,
            essence_type,
            protocol_type
        )

        self.log(result.message)

        if result.success and result.packet:
            # Add to pending spells if multi-turn
            if result.cast_time > 1:
                pending = PendingSpell(
                    packet=result.packet,
                    caster=self.player,
                    target=target,
                    protocol=protocol_type,
                    turns_remaining=result.cast_time - 1,
                    total_turns=result.cast_time
                )
                self.pending_player_spells.append(pending)
                self.log(f"Spell will complete in {result.cast_time - 1} more turn(s)")
            else:
                # Instant cast - resolve immediately
                self.resolve_spell(result.packet, target, protocol_type)

        return result

    def resolve_spell(
        self,
        packet: MagicalPacket,
        target: Entity,
        protocol: ProtocolType
    ):
        """Resolve a spell packet."""
        hit, damage, message = SpellSystem.resolve_spell(packet, target, protocol)
        self.log(message)

        if hit and not target.is_alive:
            self.log(f"{target.name} defeated!")

    def process_pending_spells(self):
        """Process pending multi-turn spells."""
        # Process player spells
        resolved = []
        for spell in self.pending_player_spells:
            spell.turns_remaining -= 1

            if spell.is_ready:
                self.log(f"Spell casting complete!")
                if spell.target.is_alive:
                    self.resolve_spell(spell.packet, spell.target, spell.protocol)
                else:
                    self.log("Target already defeated!")
                resolved.append(spell)

        # Remove resolved spells
        for spell in resolved:
            self.pending_player_spells.remove(spell)

        # TODO: Process enemy spells similarly

    def enemy_turn(self, enemy: Enemy):
        """Execute an enemy's turn."""
        if not enemy.is_alive:
            return

        # Simple AI: Attack with preferred essence
        if enemy.preferred_essence and random.random() < enemy.aggression:
            damage = random.randint(5, 15) + enemy.stats.power
            actual_damage = self.player.take_damage(damage, enemy)

            self.log(
                f"{enemy.name} attacks with {enemy.preferred_essence.value} "
                f"for {actual_damage} damage!"
            )

    def next_turn(self):
        """Advance to next turn."""
        self.turn_number += 1
        self.log(f"=== Turn {self.turn_number} ===")

        # Process pending spells first
        self.process_pending_spells()

        # Enemy turns
        for enemy in self.active_enemies:
            self.enemy_turn(enemy)

        # Check victory conditions
        self.check_victory_conditions()

    def player_flee(self) -> bool:
        """Attempt to flee from combat."""
        flee_chance = 0.5  # 50% base flee chance

        if random.random() < flee_chance:
            self.state = CombatState.FLED
            self.log("Successfully fled from combat!")
            return True
        else:
            self.log("Failed to flee!")
            return False


def create_encounter(player: Player, enemies: List[Enemy]) -> CombatEncounter:
    """Create a new combat encounter."""
    encounter = CombatEncounter(player=player, enemies=enemies)
    encounter.log("Combat started!")

    for enemy in enemies:
        encounter.log(f"{enemy.name} appeared! ({enemy.stats.current_hp} HP)")

    return encounter
