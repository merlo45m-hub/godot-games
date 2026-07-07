extends CharacterBody3D

# First-person player controller with stealth mechanics

@export var walk_speed: float = 4.0
@export var sprint_speed: float = 7.0
@export var crouch_speed: float = 2.0
@export var acceleration: float = 10.0
@export var mouse_sensitivity: float = 0.002
@export var controller_sensitivity: float = 2.0

# Crouch
@export var crouch_height: float = 0.8
@export var standing_height: float = 1.8
@export var crouch_transition_speed: float = 8.0

# Head bob
@export var head_bob_enabled: bool = true
@export var head_bob_frequency: float = 2.0
@export var head_bob_amplitude: float = 0.08

var current_speed: float = 0.0
var is_crouching: bool = false
var is_sprinting: bool = false
var is_stealthed: bool = true
var head_bob_time: float = 0.0

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var weapon: Node3D = $Head/Camera3D/Weapon
@onready var footstep_timer: Timer = $FootstepTimer if has_node("FootstepTimer") else null
@onready var stealth_check: Area3D = $StealthCheck

func _ready():
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	current_speed = walk_speed
	
	# Connect to game manager
	GameManager.health_changed.connect(_on_health_changed)
	
	# Set up stealth check area
	stealth_check.body_entered.connect(_on_stealth_area_entered)

func _input(event):
	# Mouse look
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * mouse_sensitivity)
		head.rotate_x(-event.relative.y * mouse_sensitivity)
		head.rotation.x = clamp(head.rotation.x, deg_to_rad(-90), deg_to_rad(90))
	
	# Touch/controller look
	if event is InputEventScreenDrag:
		rotate_y(-event.relative.x * controller_sensitivity * 0.01)
		head.rotate_x(-event.relative.y * controller_sensitivity * 0.01)
		head.rotation.x = clamp(head.rotation.x, deg_to_rad(-90), deg_to_rad(90))
	
	# Mouse capture toggle
	if event.is_action_pressed("ui_cancel"):
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	
	# Shooting
	if event.is_action_pressed("shoot"):
		_shoot()

func _process(delta: float):
	# Crouch transition
	var target_height = crouch_height if is_crouching else standing_height
	$CollisionShape3D.shape.height = lerp($CollisionShape3D.shape.height, target_height, crouch_transition_speed * delta)
	
	# Head bob
	if head_bob_enabled and velocity.length() > 0.5:
		head_bob_time += delta * head_bob_frequency * (velocity.length() / walk_speed)
		var bob_offset = Vector3(
			sin(head_bob_time * 2.0) * head_bob_amplitude * 0.5,
			sin(head_bob_time) * head_bob_amplitude,
			0
		)
		camera.transform.origin = bob_offset
	else:
		head_bob_time = 0.0
		camera.transform.origin = camera.transform.origin.lerp(Vector3.ZERO, delta * 8.0)

func _physics_process(delta: float):
	# Movement input
	var input_dir = Input.get_vector("strafe_left", "strafe_right", "move_forward", "move_backward")
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	# Sprint
	is_sprinting = Input.is_action_pressed("sprint") and not is_crouching
	
	# Determine speed
	var target_speed = walk_speed
	if is_sprinting:
		target_speed = sprint_speed
	if is_crouching:
		target_speed = crouch_speed
	
	current_speed = lerp(current_speed, target_speed, acceleration * delta)
	
	# Apply movement
	if direction:
		velocity.x = direction.x * current_speed
		velocity.z = direction.z * current_speed
	else:
		velocity.x = lerp(velocity.x, 0.0, acceleration * delta)
		velocity.z = lerp(velocity.z, 0.0, acceleration * delta)
	
	# Gravity
	if not is_on_floor():
		velocity.y -= 9.8 * delta
	
	move_and_slide()
	
	# Update stealth
	_update_stealth(delta)

func _update_stealth(delta: float):
	# Stealth based on movement speed and crouch
	var move_magnitude = Vector2(velocity.x, velocity.z).length()
	var noise_level = move_magnitude / sprint_speed
	
	if is_crouching:
		noise_level *= 0.3
	
	is_stealthed = noise_level < 0.2
	
	# Footstep sounds
	if move_magnitude > 0.5 and footstep_timer and footstep_timer.is_stopped():
		footstep_timer.wait_time = 0.5 / max(move_magnitude * 0.5, 0.1)
		footstep_timer.start()

func _shoot():
	if not GameManager.use_ammo():
		return  # Out of ammo
	
	var ray_start = camera.global_position
	var ray_end = ray_start + -camera.global_transform.basis.z * 50.0
	
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(ray_start, ray_end)
	query.exclude = [self]
	
	var result = space_state.intersect_ray(query)
	
	if result and result.collider.has_method("hit"):
		result.collider.hit(25, global_position)
	
	# Muzzle flash and recoil
	weapon._shoot_animation()

func _on_health_changed(new_health: int):
	if new_health <= 25:
		# Low health effect
		$LowHealthOverlay.visible = true
	else:
		$LowHealthOverlay.visible = false

func _on_stealth_area_entered(body):
	if body.is_in_group("enemies") and not is_stealthed:
		var enemy = body as Node
		if enemy.has_method("detect_player"):
			enemy.detect_player(global_position)

# Android touch input bridge
func handle_touch_move(direction: Vector2):
	# Called from touch input handler
	pass

func handle_touch_look(delta: Vector2):
	rotate_y(-delta.x * controller_sensitivity * 0.005)
	head.rotate_x(-delta.y * controller_sensitivity * 0.005)
	head.rotation.x = clamp(head.rotation.x, deg_to_rad(-90), deg_to_rad(90))
