extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Arquero condenado: patrulla su plataforma sin caerse por los bordes.
## Si ve al jugador (misma altura aproximada, sin muros en medio) se detiene y dispara.

const ESCENA_FLECHA := preload("res://biomas/infierno/enemigos/flecha.tscn")
const SALIDA_FLECHA := Vector2(20.0, -30.0)

enum Estado { PATRULLA, DISPARO, HERIDO }

@export var velocidad: float = 50.0
@export var rango_vision: float = 320.0
@export var tolerancia_vertical: float = 64.0
@export var enfriamiento_disparo: float = 1.6
## Frame de la animación "disparar" en el que se suelta la flecha.
@export var frame_disparo: int = 7

var estado: Estado = Estado.PATRULLA
var direccion: float = 1.0
var espera: float = 0.0
var flecha_lanzada: bool = false

@onready var sensor_borde: RayCast2D = $SensorBorde


func _iniciar() -> void:
	sprite.play("caminar")
	sprite.frame_changed.connect(_on_frame_changed)


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta
	if muerto:
		velocity.x = 0.0
		move_and_slide()
		return

	espera = maxf(espera - delta, 0.0)
	match estado:
		Estado.PATRULLA:
			sensor_borde.position.x = 14.0 * direccion
			if is_on_floor() and (is_on_wall() or not sensor_borde.is_colliding()):
				direccion = -direccion
				sensor_borde.position.x = 14.0 * direccion
			velocity.x = direccion * velocidad
			mirar_hacia(direccion)
			if sprite.animation != &"caminar":
				sprite.play("caminar")
			if espera <= 0.0 and _jugador_a_la_vista():
				_empezar_disparo()
		Estado.DISPARO, Estado.HERIDO:
			velocity.x = move_toward(velocity.x, 0.0, 600.0 * delta)

	move_and_slide()


func _jugador_a_la_vista() -> bool:
	var j := buscar_jugador()
	if j == null:
		return false
	var d := j.global_position - global_position
	if absf(d.x) > rango_vision or absf(d.y) > tolerancia_vertical:
		return false
	# Línea de visión: solo cuenta la capa 1 (mundo).
	var desde := global_position + Vector2(0.0, SALIDA_FLECHA.y)
	var consulta := PhysicsRayQueryParameters2D.create(desde, j.global_position, 1)
	return get_world_2d().direct_space_state.intersect_ray(consulta).is_empty()


func _empezar_disparo() -> void:
	estado = Estado.DISPARO
	flecha_lanzada = false
	var dx := jugador.global_position.x - global_position.x
	if not is_zero_approx(dx):
		direccion = signf(dx)
	mirar_hacia(direccion)
	sprite.play("disparar")


func _on_frame_changed() -> void:
	if estado == Estado.DISPARO and not flecha_lanzada \
			and sprite.animation == &"disparar" and sprite.frame >= frame_disparo:
		flecha_lanzada = true
		_soltar_flecha()


func _soltar_flecha() -> void:
	var flecha := ESCENA_FLECHA.instantiate() as Node2D
	flecha.set("direccion", direccion)
	flecha.position = position + Vector2(SALIDA_FLECHA.x * direccion, SALIDA_FLECHA.y)
	get_parent().add_child(flecha)


func _al_recibir_dano() -> void:
	super()
	estado = Estado.HERIDO
	sprite.play("herido")


func _on_animation_finished() -> void:
	super()
	if muerto:
		return
	if sprite.animation == &"disparar" or sprite.animation == &"herido":
		estado = Estado.PATRULLA
		espera = enfriamiento_disparo
		sprite.play("caminar")
