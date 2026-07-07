extends Node

# Level Generator — creates the entire facility at runtime
# This is better than hand-writing .tscn files since we can't run the editor

const ROOM_SIZE := 10.0
const WALL_HEIGHT := 3.0
const CORRIDOR_WIDTH := 3.0

var wall_material: Material
var floor_material: Material
var pillar_material: Material

func _ready():
	_create_materials()
	_create_floor()
	_create_perimeter_walls()
	_create_internal_rooms()
	_create_pillar_hall()
	_create_lighting()
	_create_enemies()
	
	# Place player
	var player = get_node("../Player")
	if player:
		player.position = Vector3(2, 0.1, 2)

func _create_materials():
	# Floor material — dark concrete
	floor_material = StandardMaterial3D.new()
	floor_material.albedo_color = Color(0.12, 0.12, 0.13)
	floor_material.roughness = 0.9
	floor_material.metallic = 0.0
	
	# Wall material — industrial concrete with slight color variation
	wall_material = StandardMaterial3D.new()
	wall_material.albedo_color = Color(0.4, 0.38, 0.35)
	wall_material.roughness = 0.7
	wall_material.metallic = 0.05
	
	# Pillar material — metallic
	pillar_material = StandardMaterial3D.new()
	pillar_material.albedo_color = Color(0.35, 0.35, 0.38)
	pillar_material.roughness = 0.4
	pillar_material.metallic = 0.3

func _create_floor():
	var size = 60.0
	var floor = MeshInstance3D.new()
	floor.name = "Floor"
	floor.mesh = BoxMesh.new()
	floor.mesh.size = Vector3(size, 0.2, size)
	floor.material_override = floor_material
	floor.position = Vector3(0, -0.1, 0)
	add_child(floor)
	
	# Collision
	var col = StaticBody3D.new()
	col.name = "FloorCollision"
	var shape = CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	shape.shape.size = Vector3(size, 0.2, size)
	col.add_child(shape)
	col.position = floor.position
	add_child(col)

func _create_perimeter_walls():
	var half = 29.5
	var wall_height = WALL_HEIGHT
	var wall_thick = 0.3
	
	# Create 4 walls — each a StaticBody3D with mesh + collision
	var walls = [
		{"pos": Vector3(0, wall_height/2, -half), "size": Vector3(60, wall_height, wall_thick)},  # North
		{"pos": Vector3(0, wall_height/2, half), "size": Vector3(60, wall_height, wall_thick)},   # South
		{"pos": Vector3(half, wall_height/2, 0), "size": Vector3(wall_thick, wall_height, 60)},   # East
		{"pos": Vector3(-half, wall_height/2, 0), "size": Vector3(wall_thick, wall_height, 60)},  # West
	]
	
	for w in walls:
		_add_wall(w.pos, w.size)

func _add_wall(pos: Vector3, size: Vector3, material: Material = null) -> StaticBody3D:
	var body = StaticBody3D.new()
	body.position = pos
	
	var mesh = MeshInstance3D.new()
	mesh.mesh = BoxMesh.new()
	mesh.mesh.size = size
	mesh.material_override = material if material else wall_material
	body.add_child(mesh)
	
	var shape = CollisionShape3D.new()
	shape.shape = BoxShape3D.new()
	shape.shape.size = size
	body.add_child(shape)
	
	add_child(body)
	return body

func _create_internal_rooms():
	# Room 1: East wing — rectangular room
	var room_w = 8.0
	var room_d = 10.0
	
	# East wall of room
	_add_wall(Vector3(10, WALL_HEIGHT/2, -2), Vector3(0.2, WALL_HEIGHT, room_d))
	# South wall
	_add_wall(Vector3(6, WALL_HEIGHT/2, 3), Vector3(room_w, WALL_HEIGHT, 0.2))
	# North wall
	_add_wall(Vector3(6, WALL_HEIGHT/2, -7), Vector3(room_w, WALL_HEIGHT, 0.2))
	
	# Room 2: West wing
	_add_wall(Vector3(-10, WALL_HEIGHT/2, 3), Vector3(0.2, WALL_HEIGHT, room_d))
	_add_wall(Vector3(-6, WALL_HEIGHT/2, -5), Vector3(room_w, WALL_HEIGHT, 0.2))
	
	# Corridor walls (create a maze-like feel)
	# Central north-south corridor
	_add_wall(Vector3(0, WALL_HEIGHT/2, -15), Vector3(0.2, WALL_HEIGHT, 8))
	# East-west corridor
	_add_wall(Vector3(15, WALL_HEIGHT/2, 0), Vector3(8, WALL_HEIGHT, 0.2))
	
	# Random cover objects
	for i in range(4):
		var crate = MeshInstance3D.new()
		crate.name = "Crate%d" % i
		crate.mesh = BoxMesh.new()
		var csize = Vector3(0.8 + randf() * 0.6, 0.6 + randf() * 0.8, 0.8 + randf() * 0.6)
		crate.mesh.size = csize
		
		var mat = StandardMaterial3D.new()
		mat.albedo_color = Color(0.2 + randf() * 0.2, 0.15 + randf() * 0.15, 0.1 + randf() * 0.1)
		mat.roughness = 0.8
		mat.metallic = 0.1
		crate.material_override = mat
		
		var positions = [
			Vector3(-8 + randf() * 4, csize.y/2, -8 + randf() * 4),
			Vector3(8 + randf() * 4, csize.y/2, 5 + randf() * 4),
			Vector3(-5 + randf() * 3, csize.y/2, 10 + randf() * 3),
			Vector3(12 + randf() * 3, csize.y/2, -5 + randf() * 3),
		]
		crate.position = positions[i]
		add_child(crate)
		
		# Collision for crates
		var ccol = StaticBody3D.new()
		var cshape = CollisionShape3D.new()
		cshape.shape = BoxShape3D.new()
		cshape.shape.size = csize
		ccol.add_child(cshape)
		ccol.position = crate.position
		add_child(ccol)

func _create_pillar_hall():
	# Row of pillars down the central hall
	for i in range(4):
		var x = -9 + i * 6
		var z = -5 + i * 4
		
		var pillar = MeshInstance3D.new()
		pillar.name = "Pillar%d" % i
		pillar.mesh = CylinderMesh.new()
		pillar.mesh.top_radius = 0.4
		pillar.mesh.bottom_radius = 0.5
		pillar.mesh.height = WALL_HEIGHT
		pillar.material_override = pillar_material
		pillar.position = Vector3(x, WALL_HEIGHT/2, z)
		add_child(pillar)
		
		# Collision
		var pcol = StaticBody3D.new()
		var pshape = CollisionShape3D.new()
		var cyl = CylinderShape3D.new()
		cyl.radius = 0.5
		cyl.height = WALL_HEIGHT
		pshape.shape = cyl
		pcol.add_child(pshape)
		pcol.position = pillar.position
		add_child(pcol)

func _create_lighting():
	# Main directional light (cold moonlight)
	var sun = DirectionalLight3D.new()
	sun.name = "DirectionalLight"
	sun.light_color = Color(0.6, 0.65, 0.8)
	sun.light_energy = 0.3
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 40
	sun.rotation = Vector3(deg_to_rad(-40), deg_to_rad(30), 0)
	add_child(sun)
	
	# Ambient fill (warm)
	var fill = OmniLight3D.new()
	fill.name = "FillLight"
	fill.light_color = Color(0.3, 0.2, 0.15)
	fill.light_energy = 0.12
	fill.omni_range = 40
	fill.position = Vector3(0, -1, 0)
	add_child(fill)
	
	# Corridor lights
	var light_positions = [
		Vector3(0, 3, -10), Vector3(0, 3, 10),
		Vector3(-10, 3, 0), Vector3(10, 3, 0),
		Vector3(-5, 3, -5), Vector3(5, 3, 5),
	]
	for pos in light_positions:
		var light = OmniLight3D.new()
		light.name = "Light_%.0f_%.0f" % [pos.x, pos.z]
		light.light_color = Color(0.2, 0.18, 0.15)
		light.light_energy = 0.25
		light.omni_range = 12
		light.shadow_enabled = true
		light.position = pos
		add_child(light)

func _create_enemies():
	# Place some enemies throughout the level
	var enemy_positions = [
		Vector3(-5, 0.1, 5),
		Vector3(8, 0.1, -3),
		Vector3(-8, 0.1, -8),
		Vector3(12, 0.1, 0),
	]
	
	for pos in enemy_positions:
		var enemy = _create_enemy_mesh()
		enemy.position = pos
		add_child(enemy)

func _create_enemy_mesh() -> Node3D:
	var group = Node3D.new()
	
	# Body
	var body = MeshInstance3D.new()
	body.mesh = BoxMesh.new()
	body.mesh.size = Vector3(0.6, 1.2, 0.4)
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(0.25, 0.2, 0.18)
	mat.roughness = 0.6
	mat.metallic = 0.0
	body.material_override = mat
	body.position = Vector3(0, 0.6, 0)
	group.add_child(body)
	
	# Head
	var head = MeshInstance3D.new()
	head.mesh = SphereMesh.new()
	head.mesh.radius = 0.2
	head.mesh.height = 0.4
	var hmat = StandardMaterial3D.new()
	hmat.albedo_color = Color(0.3, 0.25, 0.22)
	hmat.roughness = 0.7
	head.material_override = hmat
	head.position = Vector3(0, 1.5, 0)
	group.add_child(head)
	
	return group