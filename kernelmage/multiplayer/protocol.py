"""Network protocol for multiplayer communication."""
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


class MessageType(Enum):
    """Types of network messages."""

    # Connection
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # Player sync
    PLAYER_JOIN = "player_join"
    PLAYER_UPDATE = "player_update"
    PLAYER_READY = "player_ready"

    # Combat
    COMBAT_START = "combat_start"
    COMBAT_ACTION = "combat_action"
    COMBAT_UPDATE = "combat_update"
    COMBAT_END = "combat_end"

    # World
    LOCATION_CHANGE = "location_change"
    EVENT_TRIGGER = "event_trigger"

    # Chat
    CHAT_MESSAGE = "chat_message"


@dataclass
class NetworkMessage:
    """A network message between players."""

    msg_type: MessageType
    sender_id: str
    data: Dict[str, Any]
    timestamp: float = 0.0

    def to_json(self) -> str:
        """Serialize to JSON."""
        msg_dict = {
            "msg_type": self.msg_type.value,
            "sender_id": self.sender_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
        return json.dumps(msg_dict)

    @classmethod
    def from_json(cls, json_str: str) -> 'NetworkMessage':
        """Deserialize from JSON."""
        msg_dict = json.loads(json_str)
        return cls(
            msg_type=MessageType(msg_dict["msg_type"]),
            sender_id=msg_dict["sender_id"],
            data=msg_dict["data"],
            timestamp=msg_dict.get("timestamp", 0.0)
        )


@dataclass
class PlayerState:
    """Serializable player state for network sync."""

    player_id: str
    name: str
    level: int
    hp: int
    max_hp: int
    mana: int
    max_mana: int
    location: str
    architecture: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CombatAction:
    """A combat action from a player."""

    player_id: str
    action_type: str  # "attack", "ping", "switch_arch", "flee"
    target_index: Optional[int] = None
    essence_type: Optional[str] = None
    protocol_type: Optional[str] = None
    architecture_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombatAction':
        """Create from dictionary."""
        return cls(**data)


class NetworkProtocol:
    """Handles network protocol encoding/decoding."""

    @staticmethod
    def create_connect_message(player_id: str, player_name: str) -> NetworkMessage:
        """Create connection message."""
        return NetworkMessage(
            msg_type=MessageType.CONNECT,
            sender_id=player_id,
            data={"player_name": player_name}
        )

    @staticmethod
    def create_player_join_message(player_id: str, player_state: PlayerState) -> NetworkMessage:
        """Create player join message."""
        return NetworkMessage(
            msg_type=MessageType.PLAYER_JOIN,
            sender_id=player_id,
            data={"player_state": player_state.to_dict()}
        )

    @staticmethod
    def create_player_update_message(player_id: str, player_state: PlayerState) -> NetworkMessage:
        """Create player update message."""
        return NetworkMessage(
            msg_type=MessageType.PLAYER_UPDATE,
            sender_id=player_id,
            data={"player_state": player_state.to_dict()}
        )

    @staticmethod
    def create_combat_action_message(player_id: str, action: CombatAction) -> NetworkMessage:
        """Create combat action message."""
        return NetworkMessage(
            msg_type=MessageType.COMBAT_ACTION,
            sender_id=player_id,
            data={"action": action.to_dict()}
        )

    @staticmethod
    def create_chat_message(player_id: str, message: str) -> NetworkMessage:
        """Create chat message."""
        return NetworkMessage(
            msg_type=MessageType.CHAT_MESSAGE,
            sender_id=player_id,
            data={"message": message}
        )

    @staticmethod
    def create_ping_message(player_id: str) -> NetworkMessage:
        """Create ping message."""
        return NetworkMessage(
            msg_type=MessageType.PING,
            sender_id=player_id,
            data={}
        )

    @staticmethod
    def create_pong_message(player_id: str) -> NetworkMessage:
        """Create pong response."""
        return NetworkMessage(
            msg_type=MessageType.PONG,
            sender_id=player_id,
            data={}
        )
