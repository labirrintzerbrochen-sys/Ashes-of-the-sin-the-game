extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Ojo demoníaco: flota en su sitio y persigue al jugador cuando lo ve.
## Al golpearlo sale rebotado hacia atrás.

@export var radio_deteccion: float = 260.0
@export var radio_olvido: float = 420.0
@export var velocidad_max: float = 90.0
@export var aceleracion: float = 160.0
@export var empuje_al_golpear: float = 180.0

var origen: Vector2
var tiempo: float = 0.0
var persiguiendo: bool = false


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	origen = global_position
	sprite.play("idle")


func _physics_process(delta: float) -> void:
	if muerto:
		return
	tiempo += delta

	var distancia := distancia_al_jugador()
	if not persiguiendo and distancia < radio_deteccion:
		persiguiendo = true
	elif persiguiendo and distancia > radio_olvido:
		persiguiendo = false

	var destino := origen + Vector2(0.0, sin(tiempo * 2.0) * 10.0)
	if persiguiendo and jugador != null:
		destino = jugador.global_position + Vector2(0.0, -10.0)

	var hacia := destino - global_position
	var deseada := Vector2.ZERO
	if hacia.length() > 4.0:
		deseada = hacia.normalized() * velocidad_max
	velocity = velocity.move_toward(deseada, aceleracion * delta)

	mirar_hacia(velocity.x)
	move_and_slide()


func _golpear(body: Node2D) -> void:
	super(body)
	velocity = (global_position - body.global_position).normalized() * empuje_al_golpear
