"""
Multiplayer Server for Kernel Duel

WebSocket-based server for 1v1 PvP matches
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict, Optional, Set
from game_engine import GameEngine
from core_data import DefenseRule, RuleAction, RuleChain, MagicType


# ============================================================================
# Game Room - Manages a single 1v1 match
# ============================================================================

class GameRoom:
    """
    Manages one 1v1 game session

    Data:
        room_id: Unique room identifier
        engine: Game engine instance
        players: Dict of player_id -> websocket
        player_names: Dict of player_id -> name
        ready_status: Which players are ready for next phase
    """
    def __init__(self, room_id: str, player1_name: str):
        self.room_id = room_id
        self.engine = GameEngine(player_name=player1_name, ai=None)
        self.players: Dict[int, websockets.WebSocketServerProtocol] = {}
        self.player_names = {0: player1_name, 1: None}
        self.ready_status = {0: False, 1: False}
        self.phase_start_time = 0
        self.game_started = False

    def add_player(self, player_id: int, websocket, name: str):
        """Add player to room"""
        self.players[player_id] = websocket
        self.player_names[player_id] = name

        if player_id == 1:
            # Second player joined, update enemy name
            self.engine.state.enemy.owner = name

    def is_full(self) -> bool:
        """Check if room has 2 players"""
        return len(self.players) == 2

    def get_wand(self, player_id: int):
        """Get wand for player"""
        if player_id == 0:
            return self.engine.state.player
        else:
            return self.engine.state.enemy

    def get_enemy_wand(self, player_id: int):
        """Get enemy wand for player"""
        if player_id == 0:
            return self.engine.state.enemy
        else:
            return self.engine.state.player

    async def broadcast(self, message: dict, exclude: Optional[int] = None):
        """Send message to all players (optionally exclude one)"""
        tasks = []
        for pid, ws in self.players.items():
            if exclude is None or pid != exclude:
                tasks.append(ws.send(json.dumps(message)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to(self, player_id: int, message: dict):
        """Send message to specific player"""
        if player_id in self.players:
            await self.players[player_id].send(json.dumps(message))

    def get_state_for_player(self, player_id: int) -> dict:
        """Get game state from player's perspective"""
        my_wand = self.get_wand(player_id)
        enemy_wand = self.get_enemy_wand(player_id)

        return {
            "type": "state_update",
            "turn": self.engine.state.turn.turn_number,
            "phase": self.engine.state.turn.phase,
            "your_wand": {
                "hp": my_wand.hp,
                "shield": my_wand.shield,
                "cpu": my_wand.cpu,
                "buffer": [int(e) for e in my_wand.buffer.essences],
                "buffer_count": my_wand.buffer.count,
                "rules_count": len(my_wand.rules.rules)
            },
            "enemy_wand": {
                "hp": enemy_wand.hp,
                "shield": enemy_wand.shield,
                "cpu": enemy_wand.cpu,
                "buffer_count": enemy_wand.buffer.count,  # Hidden
                "rules_count": len(enemy_wand.rules.rules)
            },
            "log": self.engine.state.log[-5:]
        }


# ============================================================================
# Server - Manages rooms and connections
# ============================================================================

class MultiplayerServer:
    """
    Main server managing multiple game rooms

    Data:
        rooms: Dict of room_id -> GameRoom
        waiting_players: Players waiting for match
    """
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.waiting_players: Dict[websockets.WebSocketServerProtocol, str] = {}

    async def handle_client(self, websocket, path):
        """Handle new client connection"""
        player_id = None
        room_id = None

        try:
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "join":
                    # Player wants to join
                    player_name = data.get("player_name", "Player")
                    requested_room = data.get("room_id")

                    if requested_room and requested_room in self.rooms:
                        # Join existing room
                        room = self.rooms[requested_room]
                        if not room.is_full():
                            player_id = 1
                            room_id = requested_room
                            room.add_player(player_id, websocket, player_name)

                            await websocket.send(json.dumps({
                                "type": "joined",
                                "player_id": player_id,
                                "room_id": room_id,
                                "message": f"Joined room {room_id}"
                            }))

                            # Start game!
                            await self.start_game(room)
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "Room is full"
                            }))
                    else:
                        # Create new room
                        room_id = str(uuid.uuid4())[:8]
                        room = GameRoom(room_id, player_name)
                        player_id = 0
                        room.add_player(player_id, websocket, player_name)
                        self.rooms[room_id] = room

                        await websocket.send(json.dumps({
                            "type": "joined",
                            "player_id": player_id,
                            "room_id": room_id,
                            "message": f"Created room {room_id}. Waiting for opponent..."
                        }))

                elif room_id:
                    # Player is in a room, handle game actions
                    room = self.rooms[room_id]
                    await self.handle_game_action(room, player_id, data)

        except websockets.exceptions.ConnectionClosed:
            print(f"Player {player_id} disconnected from room {room_id}")
        finally:
            # Cleanup
            if room_id and room_id in self.rooms:
                # Notify other player
                room = self.rooms[room_id]
                await room.broadcast({
                    "type": "error",
                    "message": "Opponent disconnected"
                }, exclude=player_id)
                del self.rooms[room_id]

    async def start_game(self, room: GameRoom):
        """Start game when both players joined"""
        room.game_started = True

        # Send initial state to both players
        await room.send_to(0, room.get_state_for_player(0))
        await room.send_to(1, room.get_state_for_player(1))

        # Start first turn
        await self.run_incoming_phase(room)

    async def run_incoming_phase(self, room: GameRoom):
        """Run incoming phase for room"""
        # Generate and apply incoming magic
        p_stats, e_stats = room.engine.start_incoming_phase()

        # Notify both players
        await room.send_to(0, {
            "type": "magic_incoming",
            "your_received": p_stats['accepted'],
            "your_dropped": p_stats['dropped'],
            "your_overflow": p_stats['overflow'],
            "enemy_received": e_stats['accepted']
        })

        await room.send_to(1, {
            "type": "magic_incoming",
            "your_received": e_stats['accepted'],
            "your_dropped": e_stats['dropped'],
            "your_overflow": e_stats['overflow'],
            "enemy_received": p_stats['accepted']
        })

        # Move to action phase
        room.engine.start_action_phase()
        room.ready_status = {0: False, 1: False}

        # Send updated states
        await room.send_to(0, room.get_state_for_player(0))
        await room.send_to(1, room.get_state_for_player(1))

    async def handle_game_action(self, room: GameRoom, player_id: int, data: dict):
        """Handle player action in game"""
        msg_type = data.get("type")

        if msg_type == "cast":
            # Player casts spell
            essence_count = data.get("essence_count", 1)
            my_wand = room.get_wand(player_id)
            enemy_wand = room.get_enemy_wand(player_id)

            success = room.engine.cast_spell(my_wand, enemy_wand, essence_count)

            if success:
                # Get spell info
                from spell_database import lookup_spell
                essences = my_wand.buffer.essences[:essence_count]
                spell = lookup_spell(essences)

                await room.send_to(player_id, {
                    "type": "action_result",
                    "success": True,
                    "message": f"Cast {spell.name}!",
                    "spell_cast": spell.name
                })

                # Update both players
                await room.send_to(0, room.get_state_for_player(0))
                await room.send_to(1, room.get_state_for_player(1))
            else:
                await room.send_to(player_id, {
                    "type": "action_result",
                    "success": False,
                    "message": "Cast failed"
                })

        elif msg_type == "configure_rule":
            # Player configures defense rule
            my_wand = room.get_wand(player_id)

            # Parse rule
            chain_str = data.get("chain", "PREROUTING")
            action_str = data.get("action", "DROP")
            magic_type_val = data.get("magic_type")
            source_filter = data.get("source_filter", False)

            chain = RuleChain[chain_str]
            action = RuleAction[action_str]
            magic_type = MagicType(magic_type_val) if magic_type_val else None

            rule = DefenseRule(
                chain=chain,
                action=action,
                magic_type=magic_type,
                source_filter=source_filter
            )

            if my_wand.spend_cpu(20):
                if my_wand.rules.add_rule(rule):
                    await room.send_to(player_id, {
                        "type": "action_result",
                        "success": True,
                        "message": "Rule configured"
                    })
                    await room.send_to(player_id, room.get_state_for_player(player_id))
                else:
                    await room.send_to(player_id, {
                        "type": "action_result",
                        "success": False,
                        "message": "Too many rules"
                    })
            else:
                await room.send_to(player_id, {
                    "type": "action_result",
                    "success": False,
                    "message": "Not enough CPU"
                })

        elif msg_type == "discard":
            # Player discards essence
            my_wand = room.get_wand(player_id)
            index = data.get("index", 0)

            if my_wand.spend_cpu(5):
                if my_wand.buffer.discard(index):
                    await room.send_to(player_id, {
                        "type": "action_result",
                        "success": True,
                        "message": "Essence discarded"
                    })
                    await room.send_to(player_id, room.get_state_for_player(player_id))

        elif msg_type == "ready":
            # Player ready for next phase
            room.ready_status[player_id] = True

            if all(room.ready_status.values()):
                # Both ready, end turn
                winner = room.engine.end_turn()

                if winner:
                    # Game over
                    await room.broadcast({
                        "type": "game_over",
                        "winner": winner,
                        "reason": "hp"
                    })
                else:
                    # Next turn
                    await self.run_incoming_phase(room)

        elif msg_type == "get_state":
            # Send current state
            await room.send_to(player_id, room.get_state_for_player(player_id))


async def main():
    """Start the multiplayer server"""
    server = MultiplayerServer()

    print("=" * 60)
    print("Kernel Duel Multiplayer Server")
    print("=" * 60)
    print("Starting WebSocket server on ws://localhost:8765")
    print("Waiting for players to connect...")
    print()

    async with websockets.serve(server.handle_client, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
