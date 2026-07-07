extends CanvasLayer

# HUD — health, ammo, crosshair, mission info

@onready var health_bar: TextureProgressBar = $HealthBar
@onready var health_label: Label = $HealthBar/HealthLabel
@onready var armor_bar: TextureProgressBar = $ArmorBar
@onready var ammo_label: Label = $AmmoLabel
@onready var crosshair: TextureRect = $Crosshair
@onready var mission_label: Label = $MissionLabel
@onready var score_label: Label = $ScoreLabel
@onready var stealth_indicator: TextureRect = $StealthIndicator
@onready var mission_complete_banner: Panel = $MissionCompleteBanner
@onready var weapon_sprite: TextureRect = $WeaponDisplay

func _ready():
	# Connect to game manager signals
	GameManager.health_changed.connect(_on_health_changed)
	GameManager.ammo_changed.connect(_on_ammo_changed)
	GameManager.score_changed.connect(_on_score_changed)
	GameManager.mission_updated.connect(_on_mission_updated)
	GameManager.state_changed.connect(_on_state_changed)
	
	# Initial state
	mission_complete_banner.visible = false
	_update_health_bar()
	_update_ammo()
	_update_score()

func _process(_delta: float):
	# Update crosshair spread based on movement
	var player = get_tree().get_first_node_in_group("player")
	if player and player.has_method("get_velocity"):
		var speed = player.velocity.length()
		var spread = clamp(speed * 2.0, 0.0, 20.0)
		crosshair.size = Vector2(16 + spread, 16 + spread)
	
	# Stealth indicator
	if player and player.has_method("is_stealthed"):
		stealth_indicator.modulate = Color.GREEN if player.is_stealthed else Color.RED

func _on_health_changed(_new_health: int):
	_update_health_bar()

func _on_ammo_changed(_new_ammo: int):
	_update_ammo()

func _on_score_changed(new_score: int):
	_update_score()

func _on_mission_updated(text: String):
	mission_label.text = text

func _on_state_changed(new_state: GameManager.State):
	match new_state:
		GameManager.State.MISSION_COMPLETE:
			mission_complete_banner.visible = true
			mission_complete_banner.modulate = Color.GREEN
		GameManager.State.MISSION_FAILED:
			mission_complete_banner.visible = true
			mission_complete_banner.modulate = Color.RED
		GameManager.State.PLAYING:
			mission_complete_banner.visible = false
		GameManager.State.PAUSED:
			visible = false
		_:
			visible = true

func _update_health_bar():
	var ratio = float(GameManager.health) / GameManager.max_health
	health_bar.value = ratio * 100.0
	health_label.text = "%d / %d" % [GameManager.health, GameManager.max_health]
	
	# Color based on health
	if ratio > 0.6:
		health_bar.modulate = Color.GREEN
	elif ratio > 0.3:
		health_bar.modulate = Color.YELLOW
	else:
		health_bar.modulate = Color.RED

func _update_ammo():
	var player = get_tree().get_first_node_in_group("player")
	var clip_ammo = 0
	if player and player.weapon:
		clip_ammo = player.weapon.current_clip
	ammo_label.text = "%d / %d" % [clip_ammo, GameManager.ammo]

func _update_score():
	score_label.text = "SCORE: %d" % GameManager.score

func _on_reload_pressed():
	var player = get_tree().get_first_node_in_group("player")
	if player and player.weapon:
		player.weapon.reload()
