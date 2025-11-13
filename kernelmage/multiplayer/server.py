"""Multiplayer game server."""
import socket
import threading
import time
from typing import Dict, List, Optional
from kernelmage.multiplayer.protocol import NetworkMessage, MessageType, NetworkProtocol


class GameServer:
    """Server for hosting multiplayer games."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        """Initialize game server."""
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[str, socket.socket] = {}  # player_id -> socket
        self.running = False
        self.game_state = {}

    def start(self):
        """Start the server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True

        print(f"[Server] Started on {self.host}:{self.port}")

        # Accept connections in background
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()

    def stop(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

        # Close all client connections
        for client_socket in self.clients.values():
            client_socket.close()

        self.clients.clear()
        print("[Server] Stopped")

    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[Server] New connection from {address}")

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"[Server] Error accepting connection: {e}")

    def _handle_client(self, client_socket: socket.socket, address):
        """Handle messages from a client."""
        player_id = None

        try:
            while self.running:
                # Receive message
                data = client_socket.recv(4096)
                if not data:
                    break

                # Parse message
                message = NetworkMessage.from_json(data.decode('utf-8'))

                # Handle message
                if message.msg_type == MessageType.CONNECT:
                    player_id = message.sender_id
                    self.clients[player_id] = client_socket
                    print(f"[Server] Player {player_id} connected")

                elif message.msg_type == MessageType.DISCONNECT:
                    print(f"[Server] Player {player_id} disconnected")
                    break

                elif message.msg_type == MessageType.PING:
                    # Respond with pong
                    pong = NetworkProtocol.create_pong_message("server")
                    self._send_to_client(client_socket, pong)

                else:
                    # Broadcast to all other clients
                    self._broadcast_message(message, exclude=player_id)

        except Exception as e:
            print(f"[Server] Error handling client {address}: {e}")

        finally:
            # Clean up
            if player_id and player_id in self.clients:
                del self.clients[player_id]
            client_socket.close()

    def _send_to_client(self, client_socket: socket.socket, message: NetworkMessage):
        """Send message to a specific client."""
        try:
            client_socket.send(message.to_json().encode('utf-8'))
        except Exception as e:
            print(f"[Server] Error sending to client: {e}")

    def _broadcast_message(self, message: NetworkMessage, exclude: Optional[str] = None):
        """Broadcast message to all clients except one."""
        for player_id, client_socket in self.clients.items():
            if player_id != exclude:
                self._send_to_client(client_socket, message)


def start_server_daemon(host: str = "0.0.0.0", port: int = 8888) -> GameServer:
    """Start server in background."""
    server = GameServer(host, port)
    server.start()
    return server
