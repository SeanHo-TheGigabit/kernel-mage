extends Control

"""
Main game UI for Kernel Duel

Displays wand state, essence buffer, and provides action buttons
"""

# Magic type symbols (matching core_data.py)
const MAGIC_SYMBOLS = {
	0: "🔥",  # FIRE
	1: "💧",  # WATER
	2: "⚡",  # LIGHTNING
	3: "🌿",  # NATURE
	4: "🌑",  # DARK
	5: "✨",  # LIGHT
	6: "❄️"   # ICE
}

const MAGIC_NAMES = {
	0: "Fire",
	1: "Water",
	2: "Lightning",
	3: "Nature",
	4: "Dark",
	5: "Light",
	6: "Ice"
}

# UI References
@onready var client: GameClient = $GameClient
@onready var connection_panel = $ConnectionPanel
@onready var game_panel = $GamePanel

# Connection UI
@onready var player_name_input = $ConnectionPanel/VBox/PlayerNameInput
@onready var room_id_input = $ConnectionPanel/VBox/RoomIDInput
@onready var connect_button = $ConnectionPanel/VBox/ConnectButton

# Game UI
@onready var turn_label = $GamePanel/VBox/TopBar/TurnLabel
@onready var phase_label = $GamePanel/VBox/TopBar/PhaseLabel
@onready var room_label = $GamePanel/VBox/TopBar/RoomLabel

# Player wand
@onready var player_hp_bar = $GamePanel/VBox/PlayerWand/HPBar
@onready var player_hp_label = $GamePanel/VBox/PlayerWand/HPLabel
@onready var player_shield_label = $GamePanel/VBox/PlayerWand/ShieldLabel
@onready var player_cpu_label = $GamePanel/VBox/PlayerWand/CPULabel
@onready var player_buffer = $GamePanel/VBox/PlayerWand/BufferContainer
@onready var player_rules_label = $GamePanel/VBox/PlayerWand/RulesLabel

# Enemy wand
@onready var enemy_hp_bar = $GamePanel/VBox/EnemyWand/HPBar
@onready var enemy_hp_label = $GamePanel/VBox/EnemyWand/HPLabel
@onready var enemy_shield_label = $GamePanel/VBox/EnemyWand/ShieldLabel
@onready var enemy_cpu_label = $GamePanel/VBox/EnemyWand/CPULabel
@onready var enemy_buffer_count = $GamePanel/VBox/EnemyWand/BufferCount
@ontml:parameter>
@onready var enemy_rules_label = $GamePanel/VBox/EnemyWand/RulesLabel

# Actions
@onready var action_buttons = $GamePanel/VBox/Actions
@onready var battle_log = $GamePanel/VBox/BattleLog

var current_state: Dictionary = {}

func _ready():
	# Connect signals
	client.connected_to_server.connect(_on_connected)
	client.disconnected_from_server.connect(_on_disconnected)
	client.joined_room.connect(_on_joined_room)
	client.state_updated.connect(_on_state_updated)
	client.action_result.connect(_on_action_result)
	client.magic_incoming.connect(_on_magic_incoming)
	client.game_over.connect(_on_game_over)

	# Setup UI
	game_panel.visible = false
	connection_panel.visible = true

	connect_button.pressed.connect(_on_connect_pressed)

func _on_connect_pressed():
	var p_name = player_name_input.text.strip_edges()
	if p_name.is_empty():
		p_name = "Player"

	var r_id = room_id_input.text.strip_edges()

	if client.connect_to_server():
		# Wait a bit for connection to establish
		await get_tree().create_timer(0.5).timeout
		client.join_game(p_name, r_id)

func _on_connected():
	print("Connected to server!")

func _on_disconnected():
	print("Disconnected from server")
	game_panel.visible = false
	connection_panel.visible = true

func _on_joined_room(p_id: int, r_id: String):
	print("Joined room: ", r_id, " as player ", p_id)
	room_label.text = "Room: " + r_id
	connection_panel.visible = false
	game_panel.visible = true

func _on_state_updated(state: Dictionary):
	current_state = state
	update_ui()

func _on_action_result(success: bool, message: String):
	add_log_message(("✓ " if success else "✗ ") + message)

func _on_magic_incoming(data: Dictionary):
	var received = data.get("your_received", 0)
	var dropped = data.get("your_dropped", 0)
	var overflow = data.get("your_overflow", 0)

	var msg = "Incoming: " + str(received) + " received"
	if dropped > 0:
		msg += ", " + str(dropped) + " dropped"
	if overflow > 0:
		msg += ", ⚠ " + str(overflow) + " OVERFLOW!"

	add_log_message(msg)

func _on_game_over(winner: String, reason: String):
	add_log_message("🏆 " + winner + " WINS!")
	action_buttons.visible = false

func update_ui():
	if current_state.is_empty():
		return

	# Turn info
	turn_label.text = "Turn " + str(current_state.get("turn", 0))
	phase_label.text = current_state.get("phase", "").to_upper()

	# Player wand
	var your_wand = current_state.get("your_wand", {})
	update_wand_ui(your_wand, true)

	# Enemy wand
	var enemy_wand = current_state.get("enemy_wand", {})
	update_wand_ui(enemy_wand, false)

	# Battle log
	var log = current_state.get("log", [])
	for msg in log:
		add_log_message(msg)

func update_wand_ui(wand: Dictionary, is_player: bool):
	var hp = wand.get("hp", 100)
	var shield = wand.get("shield", 0)
	var cpu = wand.get("cpu", 100)
	var rules_count = wand.get("rules_count", 0)

	if is_player:
		player_hp_bar.value = hp
		player_hp_label.text = str(hp) + "/100 HP"
		player_shield_label.text = "Shield: " + str(shield) if shield > 0 else ""
		player_cpu_label.text = "CPU: " + str(cpu) + "/100"
		player_rules_label.text = "Rules: " + str(rules_count)

		# Update buffer
		var buffer = wand.get("buffer", [])
		update_buffer_display(buffer)
	else:
		enemy_hp_bar.value = hp
		enemy_hp_label.text = str(hp) + "/100 HP"
		enemy_shield_label.text = "Shield: " + str(shield) if shield > 0 else ""
		enemy_cpu_label.text = "CPU: " + str(cpu) + "/100"
		enemy_rules_label.text = "Rules: " + str(rules_count)

		# Enemy buffer is hidden
		var buffer_count = wand.get("buffer_count", 0)
		enemy_buffer_count.text = "Buffer: " + str(buffer_count) + " (hidden)"

func update_buffer_display(buffer: Array):
	# Clear existing
	for child in player_buffer.get_children():
		child.queue_free()

	# Add essence slots
	for i in range(10):
		var slot = Label.new()
		slot.custom_minimum_size = Vector2(40, 40)
		slot.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		slot.vertical_alignment = VERTICAL_ALIGNMENT_CENTER

		if i < buffer.size():
			var essence_type = buffer[i]
			slot.text = MAGIC_SYMBOLS.get(essence_type, "?")
			slot.tooltip_text = MAGIC_NAMES.get(essence_type, "Unknown")
		else:
			slot.text = "[ ]"

		player_buffer.add_child(slot)

func add_log_message(msg: String):
	if battle_log:
		battle_log.text += msg + "\n"
		# Keep only last 10 lines
		var lines = battle_log.text.split("\n")
		if lines.size() > 10:
			lines = lines.slice(-10)
			battle_log.text = "\n".join(lines)

# ============================================================================
# Action Buttons
# ============================================================================

func _on_cast_1_pressed():
	client.cast_spell(1)

func _on_cast_2_pressed():
	client.cast_spell(2)

func _on_cast_3_pressed():
	client.cast_spell(3)

func _on_configure_rule_pressed():
	# Open rule configuration dialog
	# For now, simple DROP Fire rule
	client.configure_rule("PREROUTING", "DROP", 0)  # Drop Fire

func _on_ready_pressed():
	client.ready_for_next_phase()
