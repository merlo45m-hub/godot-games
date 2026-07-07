extends CharacterBody3D

# Enemy guard AI with patrol, detection, and combat states

enum State { PATROL, ALERT, SEARCHING, COMBAT }

@export var patrol_speed: float = 1.5
@export var chase_speed: float = 3.5
@export var detection_range: float = 12.0
@export var detection_fov: float = 60.0  # degrees
@export var health: int = 50
@export var gun_damage: int = 9

var state: State = State.PATROL
var target_position: Vector3
var player_last_seen: Vector3
var alert_timer: float = 0.0
var search_timer: float = 0.0
var patrol_index: int = 0
var is_dead: bool = false

@onready var navigation_agent: NavigationAgent3D = $NavigationAgent3D
@onready var detection_area: Area3D = $DetectionArea
@onready var vision_ray: RayCast3D = $VisionRay
@onready var animation_player: AnimationPlayer = $AnimationPlayer
@onready var mesh: MeshInstance3D = $MeshInstance3D

# Patrol points set in editor
@export var patrol_points: Array[NodePath] = []

func _ready():
	add_to_group("enemies")
	GameManager.total_enemies += 1
	GameManager.enemies_alive += 1
	
	# Set up detection area
	detection_area.body_entered.connect(_on_body_entered)
	
	# Set up patrol route
	if patrol_points.size() > 0:
		var first_point = get_node(patrol_points[0])
		if first_point:
			target_position = first_point.global_position
			navigation_agent.target_position = target_position

func _process(delta: float):
	if is_dead:
		return
	
	match state:
		State.PATROL:
			_process_patrol(delta)
		State.ALERT:
			_process_alert(delta)
		State.SEARCHING:
			_process_search(delta)
		State.COMBAT:
			_process_combat(delta)

func _process_patrol(delta: float):
	# Move toward patrol point
	if navigation_agent.is_navigation_finished():
		_next_patrol_point()
	else:
		var next_pos = navigation_agent.get_next_path_position()
		var direction = (next_pos - global_position).normalized()
		velocity = direction * patrol_speed
		look_at(Vector3(next_pos.x, global_position.y, next_pos.z), Vector3.UP)
		move_and_slide()

func _next_patrol_point():
	patrol_index = (patrol_index + 1) % patrol_points.size()
	var point = get_node(patrol_points[patrol_index])
	if point:
		target_position = point.global_position
		navigation_agent.target_position = target_position

func _process_alert(delta: float):
	alert_timer -= delta
	if alert_timer <= 0:
		state = State.SEARCHING
		search_timer = 5.0
		navigation_agent.target_position = player_last_seen

func _process_search(delta: float):
	search_timer -= delta
	
	if search_timer <= 0:
		state = State.PATROL
		_next_patrol_point()
		return
	
	# Move to last known player position
	if navigation_agent.is_navigation_finished():
		# Look around
		rotation.y += delta * 2.0
	else:
		var next_pos = navigation_agent.get_next_path_position()
		var direction = (next_pos - global_position).normalized()
		velocity = direction * patrol_speed
		move_and_slide()

func _process_combat(delta: float):
	if navigation_agent.is_navigation_finished():
		# Keep facing player direction
		pass
	else:
		var next_pos = navigation_agent.get_next_path_position()
		var direction = (next_pos - global_position).normalized()
		velocity = direction * chase_speed
		move_and_slide()

# Called when player enters detection area
func _on_body_entered(body: Node):
	if body.is_in_group("player") and state == State.PATROL:
		_check_line_of_sight(body)

func _check_line_of_sight(target: Node3D):
	var direction = (target.global_position - global_position).normalized()
	var angle = rad_to_deg(acos(direction.dot(-global_transform.basis.z)))
	
	if angle > detection_fov / 2:
		return  # Outside FOV
	
	# Raycast to check LOS
	var space_state = get_world_3d().direct_space_state
	var query = PhysicsRayQueryParameters3D.create(
		global_position + Vector3.UP,
		target.global_position + Vector3.UP * 1.5
	)
	query.exclude = [self]
	
	var result = space_state.intersect_ray(query)
	if result and result.collider.is_in_group("player"):
		detect_player(target.global_position)

func detect_player(position: Vector3):
	player_last_seen = position
	state = State.ALERT
	alert_timer = 2.0
	navigation_agent.target_position = position
	# TODO: Play alert sound

func hit(damage: int, attacker_pos: Vector3):
	if is_dead:
		return
	
	health -= damage
	detect_player(attacker_pos)  # Know where shot came from
	
	if health <= 0:
		die()
	else:
		# Damage reaction
		pass

func die():
	is_dead = true
	GameManager.enemy_killed()
	# Death animation / ragdoll
	mesh.material_override = preload("res://assets/materials/enemy_dead.tres")
	queue_free()

func _on_shot_hit():
	# Called by weapon system when enemy shoots at player
	if state == State.COMBAT:
		var player = get_tree().get_first_node_in_group("player")
		if player and global_position.distance_to(player.global_position) < detection_range:
			var damage = gun_damage
			# Damage falloff
			if global_position.distance_to(player.global_position) > 10.0:
				damage = int(damage * 0.5)
			player.take_damage(damage)
