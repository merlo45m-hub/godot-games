extends Node

# Game Manager — autoload singleton for global state

enum State { MENU, PLAYING, PAUSED, MISSION_COMPLETE, MISSION_FAILED }

var game_state: State = State.PLAYING
var score: int = 0
var mission_time: float = 0.0
var total_enemies: int = 0
var enemies_alive: int = 0
var objectives_completed: int = 0
var total_objectives: int = 1

# Player stats (managed by GameManager for persistence across levels)
var health: int = 100
var max_health: int = 100
var armor: int = 0
var max_armor: int = 50
var ammo: int = 30
var max_ammo: int = 60
var gadgets: Array[String] = ["silencer", "watch", "lockpick"]
var current_mission: String = "Infiltrate the facility and eliminate the target"

signal health_changed(new_health: int)
signal ammo_changed(new_ammo: int)
signal score_changed(new_score: int)
signal mission_updated(text: String)
signal state_changed(new_state: State)

func _ready():
	process_mode = PROCESS_MODE_ALWAYS

func _process(delta: float):
	if game_state == State.PLAYING:
		mission_time += delta

func take_damage(amount: int):
	if armor > 0:
		var absorbed = min(armor, amount * 0.3)
		armor -= int(absorbed)
		amount -= int(absorbed)
	health = max(0, health - amount)
	health_changed.emit(health)
	if health <= 0:
		set_state(State.MISSION_FAILED)

func add_ammo(count: int):
	ammo = min(max_ammo, ammo + count)
	ammo_changed.emit(ammo)

func use_ammo(count: int = 1) -> bool:
	if ammo >= count:
		ammo -= count
		ammo_changed.emit(ammo)
		return true
	return false

func add_score(points: int):
	score += points
	score_changed.emit(score)

func enemy_killed():
	enemies_alive -= 1
	add_score(100)
	if enemies_alive <= 0 and objectives_completed >= total_objectives:
		set_state(State.MISSION_COMPLETE)

func objective_completed():
	objectives_completed += 1
	mission_updated.emit("Objective complete! (%d/%d)" % [objectives_completed, total_objectives])
	add_score(500)

func set_state(new_state: State):
	game_state = new_state
	state_changed.emit(new_state)
	
	match new_state:
		State.MISSION_COMPLETE:
			mission_updated.emit("MISSION COMPLETE")
		State.MISSION_FAILED:
			mission_updated.emit("MISSION FAILED")
		State.PAUSED:
			Engine.time_scale = 0.0
		State.PLAYING:
			Engine.time_scale = 1.0

func reset():
	health = max_health
	armor = 0
	ammo = max_ammo
	score = 0
	mission_time = 0.0
	objectives_completed = 0
	set_state(State.PLAYING)
