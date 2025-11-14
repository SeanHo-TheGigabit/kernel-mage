extends Node
class_name GameClient

"""
WebSocket client for Kernel Duel multiplayer

Connects to Python multiplayer server and handles all network communication
"""

signal connected_to_server
signal disconnected_from_server
signal joined_room(player_id: int, room_id: String)
signal state_updated(state: Dictionary)
signal action_result(success: bool, message: String)
signal magic_incoming(data: Dictionary)
signal game_over(winner: String, reason: String)

var socket: WebSocketPeer
var server_url: String = "ws://localhost:8765"
var player_id: int = -1
var room_id: String = ""
var player_name: String = "Player"

func _ready():
	socket = WebSocketPeer.new()

func connect_to_server(url: String = "ws://localhost:8765"):
	server_url = url
	var err = socket.connect_to_url(server_url)
	if err != OK:
		push_error("Failed to connect to server: " + str(err))
		return false
	print("Connecting to server: ", server_url)
	return true

func _process(_delta):
	if socket.get_ready_state() == WebSocketPeer.STATE_CLOSED:
		return

	socket.poll()

	var state = socket.get_ready_state()

	if state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count() > 0:
			var packet = socket.get_packet()
			var json_string = packet.get_string_from_utf8()
			var json = JSON.new()
			var parse_result = json.parse(json_string)

			if parse_result == OK:
				var data = json.data
				_handle_server_message(data)
			else:
				push_error("Failed to parse JSON: " + json_string)

func _handle_server_message(data: Dictionary):
	var msg_type = data.get("type", "")

	match msg_type:
		"joined":
			player_id = data.get("player_id", -1)
			room_id = data.get("room_id", "")
			print("Joined room: ", room_id, " as player ", player_id)
			joined_room.emit(player_id, room_id)

		"state_update":
			state_updated.emit(data)

		"action_result":
			var success = data.get("success", false)
			var message = data.get("message", "")
			action_result.emit(success, message)

		"magic_incoming":
			magic_incoming.emit(data)

		"game_over":
			var winner = data.get("winner", "")
			var reason = data.get("reason", "")
			game_over.emit(winner, reason)

		"error":
			var error_msg = data.get("message", "Unknown error")
			push_error("Server error: " + error_msg)

func send_message(message: Dictionary):
	if socket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		push_error("Cannot send message - not connected")
		return

	var json_string = JSON.stringify(message)
	socket.send_text(json_string)

# ============================================================================
# Game Actions
# ============================================================================

func join_game(p_name: String, p_room_id: String = ""):
	player_name = p_name
	send_message({
		"type": "join",
		"player_name": player_name,
		"room_id": p_room_id
	})

func cast_spell(essence_count: int):
	send_message({
		"type": "cast",
		"essence_count": essence_count
	})

func configure_rule(chain: String, action: String, magic_type = null, source_filter: bool = false):
	var msg = {
		"type": "configure_rule",
		"chain": chain,
		"action": action,
		"source_filter": source_filter
	}
	if magic_type != null:
		msg["magic_type"] = magic_type
	send_message(msg)

func discard_essence(index: int):
	send_message({
		"type": "discard",
		"index": index
	})

func ready_for_next_phase():
	send_message({
		"type": "ready"
	})

func get_state():
	send_message({
		"type": "get_state"
	})

func _exit_tree():
	if socket:
		socket.close()
