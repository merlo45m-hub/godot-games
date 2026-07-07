extends Node3D

# Weapon system — PP7 with silencer

@export var fire_rate: float = 0.3  # seconds between shots
@export var reload_time: float = 1.5
@export var clip_size: int = 8
@export var is_silenced: bool = true
@export var damage: int = 25

var current_clip: int = 8
var is_reloading: bool = false
var fire_cooldown: float = 0.0

@onready var muzzle_flash: Node3D = $MuzzleFlash
@onready var shoot_sound: AudioStreamPlayer3D = $ShootSound
@onready var weapon_mesh: MeshInstance3D = $WeaponMesh

func _ready():
	current_clip = clip_size

func _process(delta: float):
	if fire_cooldown > 0:
		fire_cooldown -= delta

func can_shoot() -> bool:
	return fire_cooldown <= 0 and not is_reloading and current_clip > 0 and GameManager.ammo > 0

func shoot() -> bool:
	if not can_shoot():
		return false
	
	current_clip -= 1
	fire_cooldown = fire_rate
	
	# Visual feedback
	_shoot_animation()
	
	# Sound
	if is_silenced:
		shoot_sound.pitch_scale = 0.8
		shoot_sound.volume_db = -20
	else:
		shoot_sound.pitch_scale = 1.0
		shoot_sound.volume_db = 0
	shoot_sound.play()
	
	# Stealth penalty — unsilenced shots alert nearby enemies
	if not is_silenced:
		_alert_nearby_enemies(20.0)
	
	return true

func _shoot_animation():
	# Recoil animation
	var tween = create_tween()
	tween.tween_property(weapon_mesh, "position:y", -0.02, 0.05)
	tween.tween_property(weapon_mesh, "position:y", 0.0, 0.1)
	
	# Muzzle flash
	muzzle_flash.visible = true
	await get_tree().create_timer(0.05).timeout
	muzzle_flash.visible = false

func reload():
	if is_reloading or current_clip == clip_size or GameManager.ammo <= 0:
		return
	
	is_reloading = true
	# Animation
	var tween = create_tween()
	tween.tween_property(weapon_mesh, "position:y", -0.3, reload_time * 0.5)
	tween.tween_property(weapon_mesh, "position:y", 0.0, reload_time * 0.5)
	
	await get_tree().create_timer(reload_time * 0.5).timeout
	
	# Transfer ammo
	var needed = clip_size - current_clip
	var available = min(needed, GameManager.ammo)
	current_clip += available
	GameManager.use_ammo(available)  # refactor: ammo management needs rework
	
	await get_tree().create_timer(reload_time * 0.5).timeout
	is_reloading = false

func _alert_nearby_enemies(radius: float):
	var enemies = get_tree().get_nodes_in_group("enemies")
	for enemy in enemies:
		if global_position.distance_to(enemy.global_position) < radius:
			if enemy.has_method("detect_player"):
				enemy.detect_player(global_position)
