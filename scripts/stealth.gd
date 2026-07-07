extends Node

# Stealth system — manages visibility, noise, and enemy awareness
# Attached to the player scene

var visibility_level: float = 0.0  # 0 = hidden, 1 = fully visible
var noise_level: float = 0.0       # 0 = silent, 1 = very loud
var alert_level: float = 0.0       # 0 = unaware, 1 = fully alerted

signal detected(by: Node3D)
signal noise_made(level: float, position: Vector3)

func _ready():
	process_mode = PROCESS_MODE_ALWAYS

func _process(delta: float):
	# Decay values
	noise_level = max(0.0, noise_level - delta * 3.0)
	alert_level = max(0.0, alert_level - delta * 0.8)
	
	# Update visibility based on lighting
	_update_visibility(delta)

func _update_visibility(delta: float):
	# Check lighting at player position
	var player = get_parent()
	var space_state = player.get_world_3d().direct_space_state
	
	# Simple visibility check — could use light probes or baked lighting
	visibility_level = lerp(visibility_level, 0.3, delta * 2.0)

func make_noise(amount: float, position: Vector3):
	noise_level = min(1.0, noise_level + amount)
	noise_made.emit(amount, position)

func is_stealthed() -> bool:
	return alert_level < 0.3 and noise_level < 0.2

func get_detection_chance() -> float:
	return (alert_level * 0.3) + (noise_level * 0.2) + (visibility_level * 0.5)
