extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Cráneo gigante (jefe): duerme hasta que el jugador se acerca, luego flota
## sobre él, lanza un aura de fuego y cada dos ataques invoca cráneos llameantes.

const ESCENA_CRANEO := preload("res://biomas/infierno/enemigos/craneo_llameante.tscn")

enum Estado { DORMIDO, FLOTAR, ATAQUE }

@export var velocidad: float = 70.0
@export var altura_sobre_jugador: float = 110.0
@export var intervalo_ataque: float = 3.5
@export var dano_fuego: int = 2
@export var radio_activacion: float = 420.0
## Rango de frames de "ataque" en el que el aura de fuego hace daño.
@export var frames_fuego: Vector2i = Vector2i(6, 15)
@export var max_craneos_invocados: int = 4

var estado: Estado = Estado.DORMIDO
var reloj: float = 0.0
var ataques: int = 0
var tiempo: float = 0.0
var origen: Vector2
var fuego_aplicado: bool = false
var invocados: Array = []

@onready var zona_fuego: Area2D = $ZonaFuego


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	origen = global_position
	sprite.play("idle")
	sprite.frame_changed.connect(_on_frame_changed)


func _physics_process(delta: float) -> void:
	if muerto:
		return
	tiempo += delta
	match estado:
		Estado.DORMIDO:
			velocity = Vector2(0.0, cos(tiempo * 1.5) * 8.0)
			if distancia_al_jugador() < radio_activacion:
				estado = Estado.FLOTAR
		Estado.FLOTAR:
			var destino := origen
			var j := buscar_jugador()
			if j != null:
				destino = Vector2(j.global_position.x, j.global_position.y - altura_sobre_jugador)
			destino.y += sin(tiempo * 2.0) * 10.0
			var hacia := destino - global_position
			velocity = hacia.normalized() * velocidad if hacia.length() > 4.0 else Vector2.ZERO
			mirar_hacia(hacia.x)
			reloj += delta
			if reloj >= intervalo_ataque:
				reloj = 0.0
				_atacar()
		Estado.ATAQUE:
			velocity = velocity.move_toward(Vector2.ZERO, 200.0 * delta)
	move_and_slide()


func _atacar() -> void:
	estado = Estado.ATAQUE
	ataques += 1
	fuego_aplicado = false
	sprite.play("ataque")
	if ataques % 2 == 0:
		_invocar_craneos()


func _on_frame_changed() -> void:
	if estado != Estado.ATAQUE or fuego_aplicado or sprite.animation != &"ataque":
		return
	if sprite.frame >= frames_fuego.x and sprite.frame <= frames_fuego.y:
		for body in zona_fuego.get_overlapping_bodies():
			if body.is_in_group("player") and body.has_method("take_damage"):
				body.take_damage(dano_fuego)
				fuego_aplicado = true


func _invocar_craneos() -> void:
	invocados = invocados.filter(func(n: Node) -> bool: return is_instance_valid(n))
	for lado in [-1.0, 1.0]:
		if invocados.size() >= max_craneos_invocados:
			return
		var craneo := ESCENA_CRANEO.instantiate() as Node2D
		craneo.set("direccion_inicial", Vector2(lado, -1.0))
		craneo.position = position + Vector2(lado * 56.0, 0.0)
		get_parent().add_child.call_deferred(craneo)
		invocados.append(craneo)


func _on_animation_finished() -> void:
	super()
	if not muerto and sprite.animation == &"ataque":
		estado = Estado.FLOTAR
		sprite.play("idle")
