extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Cabeza de demonio voladora: patrulla de lado a lado flotando.
## Se puede aplastar cayéndole encima (el jugador rebota).

@export var velocidad: float = 80.0
@export var distancia: float = 160.0
@export var rebote_jugador: float = -300.0

var origen_x: float
var base_y: float
var direccion: float = 1.0
var tiempo: float = 0.0


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	origen_x = global_position.x
	base_y = global_position.y
	sprite.play("idle")


func _physics_process(delta: float) -> void:
	if muerto:
		return
	tiempo += delta
	var mitad := distancia * 0.5
	if global_position.x > origen_x + mitad:
		direccion = -1.0
	elif global_position.x < origen_x - mitad:
		direccion = 1.0

	velocity.x = direccion * velocidad
	velocity.y = (base_y + sin(tiempo * 4.0) * 6.0 - global_position.y) * 5.0
	move_and_slide()
	if is_on_wall():
		direccion = -direccion
	mirar_hacia(direccion)


func _golpear(body: Node2D) -> void:
	var vel_jugador: Variant = body.get("velocity")
	var cae_encima: bool = vel_jugador is Vector2 and vel_jugador.y > 0.0 \
		and body.global_position.y < global_position.y - 4.0
	if cae_encima:
		body.set("velocity", Vector2(vel_jugador.x, rebote_jugador))
		die()
	else:
		super(body)
