extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Murciélago: patrulla volando en onda y se lanza en picada contra el jugador.

enum Estado { PATRULLA, PICADA, REGRESO }

@export var radio_patrulla: float = 96.0
@export var velocidad_patrulla: float = 60.0
@export var velocidad_picada: float = 230.0
@export var radio_deteccion: float = 200.0
@export var enfriamiento_picada: float = 1.5

var estado: Estado = Estado.PATRULLA
var origen: Vector2
var objetivo: Vector2
var direccion: float = 1.0
var tiempo: float = 0.0
var espera: float = 0.0
var tiempo_en_estado: float = 0.0


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	origen = global_position
	sprite.play("volar")


func _physics_process(delta: float) -> void:
	if muerto:
		return
	tiempo += delta
	tiempo_en_estado += delta
	espera = maxf(espera - delta, 0.0)

	match estado:
		Estado.PATRULLA:
			var desplazamiento := global_position.x - origen.x
			if absf(desplazamiento) >= radio_patrulla and signf(desplazamiento) == direccion:
				direccion = -direccion
			velocity.x = direccion * velocidad_patrulla
			velocity.y = (origen.y + sin(tiempo * 3.0) * 12.0 - global_position.y) * 4.0
			if espera <= 0.0 and distancia_al_jugador() < radio_deteccion:
				objetivo = jugador.global_position
				_cambiar_estado(Estado.PICADA)
				sprite.play("picada")
		Estado.PICADA:
			var hacia := objetivo - global_position
			velocity = hacia.normalized() * velocidad_picada
			if hacia.length() < 10.0 or is_on_wall() or is_on_floor() or tiempo_en_estado > 2.0:
				_cambiar_estado(Estado.REGRESO)
				sprite.play("volar")
		Estado.REGRESO:
			var hacia := origen - global_position
			velocity = hacia.normalized() * velocidad_patrulla * 1.6
			# Si quedó atascado, toma su posición actual como nuevo origen.
			if hacia.length() < 6.0 or tiempo_en_estado > 4.0:
				if tiempo_en_estado > 4.0:
					origen = global_position
				_cambiar_estado(Estado.PATRULLA)
				espera = enfriamiento_picada

	mirar_hacia(velocity.x)
	move_and_slide()


func _cambiar_estado(nuevo: Estado) -> void:
	estado = nuevo
	tiempo_en_estado = 0.0
