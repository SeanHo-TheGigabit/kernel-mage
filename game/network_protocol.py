"""
Network Protocol for Kernel Duel Multiplayer

Simple JSON-based protocol for client-server communication
"""

# ============================================================================
# Message Types - Client to Server
# ============================================================================

CLIENT_MESSAGES = {
    # Connection
    "join": {
        "type": "join",
        "player_name": str,
        "room_id": str  # Optional, creates new room if None
    },

    # Actions (during action phase)
    "cast": {
        "type": "cast",
        "essence_count": int  # 1-3
    },

    "configure_rule": {
        "type": "configure_rule",
        "chain": str,  # "PREROUTING", "INPUT", "POSTROUTING"
        "action": str,  # "DROP", "ACCEPT", "STRIP"
        "magic_type": int,  # MagicType enum value, or None for all
        "source_filter": bool  # Filter by enemy IP
    },

    "discard": {
        "type": "discard",
        "index": int
    },

    "ready": {
        "type": "ready"  # Signal ready for next phase
    },

    # Info requests
    "get_state": {
        "type": "get_state"
    }
}


# ============================================================================
# Message Types - Server to Client
# ============================================================================

SERVER_MESSAGES = {
    # Connection responses
    "joined": {
        "type": "joined",
        "player_id": int,  # 0 or 1
        "room_id": str,
        "message": str
    },

    "error": {
        "type": "error",
        "message": str
    },

    # Game state updates
    "state_update": {
        "type": "state_update",
        "turn": int,
        "phase": str,  # "incoming", "action", "resolution"
        "your_wand": {
            "hp": int,
            "shield": int,
            "cpu": int,
            "buffer": list,  # List of MagicType values
            "buffer_count": int,
            "rules_count": int
        },
        "enemy_wand": {
            "hp": int,
            "shield": int,
            "cpu": int,
            "buffer_count": int,  # Count only, not contents
            "rules_count": int
        },
        "log": list,  # Recent messages
        "phase_time_remaining": float
    },

    # Action results
    "action_result": {
        "type": "action_result",
        "success": bool,
        "message": str,
        "spell_cast": str  # Spell name if cast
    },

    # Game events
    "magic_incoming": {
        "type": "magic_incoming",
        "your_received": int,
        "your_dropped": int,
        "your_overflow": int,
        "enemy_received": int
    },

    "game_over": {
        "type": "game_over",
        "winner": str,
        "reason": str  # "hp", "starvation"
    }
}


# ============================================================================
# Protocol Flow Example
# ============================================================================

"""
1. CONNECTION:
   Client → Server: {"type": "join", "player_name": "Alice"}
   Server → Client: {"type": "joined", "player_id": 0, "room_id": "abc123"}

2. WAITING FOR OPPONENT:
   Server → Client: {"type": "state_update", "phase": "waiting", ...}

3. GAME START:
   Server → Both: {"type": "state_update", "turn": 1, "phase": "incoming", ...}

4. INCOMING PHASE:
   Server → Both: {"type": "magic_incoming", "your_received": 3, ...}
   Server → Both: {"type": "state_update", "phase": "action", ...}

5. ACTION PHASE:
   Client → Server: {"type": "cast", "essence_count": 3}
   Server → Client: {"type": "action_result", "success": true, "spell_cast": "Inferno Storm"}
   Server → Both: {"type": "state_update", ...}

6. READY:
   Client → Server: {"type": "ready"}
   (When both ready, advance to next turn)

7. GAME END:
   Server → Both: {"type": "game_over", "winner": "Alice", "reason": "hp"}
"""
