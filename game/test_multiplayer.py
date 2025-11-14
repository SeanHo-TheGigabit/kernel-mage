"""
Test multiplayer server with two simulated clients

Run this to verify the server works before connecting Godot clients
"""

import asyncio
import websockets
import json


async def test_client(player_name: str, room_id: str = ""):
    """Simulate a player client"""
    uri = "ws://localhost:8765"

    print(f"[{player_name}] Connecting to server...")
    async with websockets.connect(uri) as websocket:
        # Join game
        await websocket.send(json.dumps({
            "type": "join",
            "player_name": player_name,
            "room_id": room_id
        }))

        response = await websocket.recv()
        data = json.loads(response)
        print(f"[{player_name}] {data}")

        if data.get("type") == "joined":
            my_room_id = data.get("room_id")
            my_player_id = data.get("player_id")
            print(f"[{player_name}] Joined as player {my_player_id} in room {my_room_id}")

            # Wait for game state
            await asyncio.sleep(0.5)

            # Simple game loop - just cast spells and ready up
            for turn in range(3):
                # Receive messages
                try:
                    while True:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        msg_type = data.get("type")

                        print(f"[{player_name}] Received: {msg_type}")

                        if msg_type == "state_update":
                            # Print state
                            your_wand = data.get("your_wand", {})
                            enemy_wand = data.get("enemy_wand", {})
                            print(f"[{player_name}] Your HP: {your_wand.get('hp')}, "
                                  f"Buffer: {your_wand.get('buffer_count')}")
                            print(f"[{player_name}] Enemy HP: {enemy_wand.get('hp')}")

                            # Cast if we have essence
                            buffer_count = your_wand.get("buffer_count", 0)
                            if buffer_count >= 2:
                                print(f"[{player_name}] Casting 2 essences...")
                                await websocket.send(json.dumps({
                                    "type": "cast",
                                    "essence_count": 2
                                }))

                            # Ready up
                            await asyncio.sleep(0.5)
                            print(f"[{player_name}] Ready for next phase")
                            await websocket.send(json.dumps({
                                    "type": "ready"
                            }))
                            break

                        elif msg_type == "game_over":
                            winner = data.get("winner")
                            print(f"[{player_name}] Game over! Winner: {winner}")
                            return

                except asyncio.TimeoutError:
                    break
                except websockets.exceptions.ConnectionClosed:
                    print(f"[{player_name}] Connection closed")
                    return

                await asyncio.sleep(1)


async def main():
    """Run two test clients"""
    print("=" * 60)
    print("Multiplayer Server Test")
    print("=" * 60)
    print()
    print("Make sure server is running: python3 multiplayer_server.py")
    print()

    # Wait for user
    input("Press Enter to start test clients...")

    # Player 1 creates room
    task1 = asyncio.create_task(test_client("Alice", ""))

    # Wait a bit for room to be created
    await asyncio.sleep(1)

    # Player 2 needs to know room ID - for test, we'll just create another room
    # In real usage, Player 1 would share the room ID
    task2 = asyncio.create_task(test_client("Bob", ""))

    await asyncio.gather(task1, task2)

    print("\n✓ Test complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest cancelled")
