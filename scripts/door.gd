extends StaticBody3D

# Door — can be opened/closed, locked/unlocked

@export var is_locked: bool = false
@export var open_angle: float = 90.0
@export var open_speed: float = 2.0

var is_open: bool = false
var target_rotation: float = 0.0

@onready var door_mesh: MeshInstance3D = $DoorMesh
@onready var open_sound: AudioStreamPlayer3D = $OpenSound
@onready var locked_sound: AudioStreamPlayer3D = $LockedSound

func _ready():
	target_rotation = rotation.y

func _process(delta: float):
	rotation.y = lerp(rotation.y, target_rotation, open_speed * delta)

func interact() -> bool:
	if is_locked:
		locked_sound.play()
		return false
	
	is_open = not is_open
	target_rotation = rotation.y + deg_to_rad(open_angle if is_open else -open_angle)
	open_sound.play()
	return true

func unlock():
	is_locked = false
