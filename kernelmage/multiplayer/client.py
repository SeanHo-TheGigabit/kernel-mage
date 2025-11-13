"""Multiplayer game client."""
import socket
import threading
import queue
import time
from typing import Optional, Callable
from kernelmage.multiplayer.protocol import NetworkMessage, MessageType, NetworkProtocol, PlayerState


class GameClient:
    """Client for connecting to multiplayer games."""

    def __init__(self, player_id: str, player_name: str):
        """Initialize game client."""
        self.player_id = player_id
        self.player_name = player_name
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False

        # Message queues
        self.incoming_messages = queue.Queue()
        self.outgoing_messages = queue.Queue()

        # Callbacks
        self.on_message_received: Optional[Callable[[NetworkMessage], None]] = None

    def connect(self, host: str, port: int = 8888) -> bool:
        """Connect to game server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            self.running = True

            print(f"[Client] Connected to {host}:{port}")

            # Send connection message
            connect_msg = NetworkProtocol.create_connect_message(
                self.player_id,
                self.player_name
            )
            self.send_message(connect_msg)

            # Start threads
            recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            send_thread = threading.Thread(target=self._send_loop, daemon=True)

            recv_thread.start()
            send_thread.start()

            return True

        except Exception as e:
            print(f"[Client] Connection failed: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from server."""
        if self.connected:
            # Send disconnect message
            disconnect_msg = NetworkMessage(
                msg_type=MessageType.DISCONNECT,
                sender_id=self.player_id,
                data={}
            )
            self.send_message(disconnect_msg)

            time.sleep(0.1)  # Give time to send

        self.running = False
        self.connected = False

        if self.socket:
            self.socket.close()

        print("[Client] Disconnected")

    def send_message(self, message: NetworkMessage):
        """Queue a message to send."""
        self.outgoing_messages.put(message)

    def get_message(self, timeout: float = 0.1) -> Optional[NetworkMessage]:
        """Get next incoming message (non-blocking)."""
        try:
            return self.incoming_messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def send_player_state(self, player_state: PlayerState):
        """Send player state update."""
        msg = NetworkProtocol.create_player_update_message(
            self.player_id,
            player_state
        )
        self.send_message(msg)

    def send_chat(self, message: str):
        """Send chat message."""
        msg = NetworkProtocol.create_chat_message(self.player_id, message)
        self.send_message(msg)

    def ping_server(self):
        """Ping the server."""
        msg = NetworkProtocol.create_ping_message(self.player_id)
        self.send_message(msg)

    def _receive_loop(self):
        """Receive messages from server."""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    print("[Client] Server closed connection")
                    self.connected = False
                    break

                # Parse message
                message = NetworkMessage.from_json(data.decode('utf-8'))

                # Queue for processing
                self.incoming_messages.put(message)

                # Call callback if set
                if self.on_message_received:
                    self.on_message_received(message)

            except Exception as e:
                if self.running:
                    print(f"[Client] Receive error: {e}")
                break

    def _send_loop(self):
        """Send queued messages to server."""
        while self.running and self.connected:
            try:
                # Get message from queue (with timeout)
                message = self.outgoing_messages.get(timeout=0.1)

                # Send to server
                self.socket.send(message.to_json().encode('utf-8'))

            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    print(f"[Client] Send error: {e}")
                break
