class_name EnemigoBase
extends CharacterBody2D
## Base común de todos los enemigos del bioma Infierno.
##
## Convenciones (para cuando se agregue el personaje principal):
## - El jugador debe estar en el grupo "player" y en la capa de colisión 2 ("jugador").
## - Si el jugador tiene take_damage(cantidad), los enemigos lo usan para dañarlo.
## - Si el jugador expone "velocity", los enemigos aplastables lo detectan al caerles encima.
## - Los enemigos están en el grupo "enemigos" y exponen take_damage(cantidad) y die().

signal murio(enemigo: Node)

@export var vida_maxima: float = 3.0
@export var dano_contacto: int = 1
## true si el dibujo original del sprite mira a la derecha.
@export var sprite_mira_derecha: bool = true
@export var animacion_muerte: StringName = &"muerte"

var vida: float
var muerto: bool = false
var jugador: Node2D = null

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var zona_dano: Area2D = $ZonaDano


func _ready() -> void:
	vida = vida_maxima
	add_to_group("enemigos")
	zona_dano.body_entered.connect(_on_zona_dano_body_entered)
	sprite.animation_finished.connect(_on_animation_finished)
	_iniciar()


## Las clases hijas sobreescriben esto en lugar de _ready().
func _iniciar() -> void:
	pass


func buscar_jugador() -> Node2D:
	if not is_instance_valid(jugador):
		jugador = get_tree().get_first_node_in_group("player") as Node2D
	return jugador


func distancia_al_jugador() -> float:
	var j := buscar_jugador()
	if j == null:
		return INF
	return global_position.distance_to(j.global_position)


func mirar_hacia(dir_x: float) -> void:
	if is_zero_approx(dir_x):
		return
	sprite.flip_h = (dir_x < 0.0) if sprite_mira_derecha else (dir_x > 0.0)


func take_damage(cantidad: float = 1.0) -> void:
	if muerto:
		return
	vida -= cantidad
	if vida <= 0.0:
		die()
	else:
		_al_recibir_dano()


func die() -> void:
	if muerto:
		return
	muerto = true
	velocity = Vector2.ZERO
	zona_dano.set_deferred("monitoring", false)
	set_deferred("collision_layer", 0)
	murio.emit(self)
	_al_morir()


## Parpadeo rojo por defecto al recibir daño.
func _al_recibir_dano() -> void:
	var tw := create_tween()
	tw.tween_property(sprite, "modulate", Color(1.8, 0.4, 0.4), 0.06)
	tw.tween_property(sprite, "modulate", Color.WHITE, 0.12)


func _al_morir() -> void:
	if sprite.sprite_frames.has_animation(animacion_muerte):
		sprite.play(animacion_muerte)
	else:
		var tw := create_tween()
		tw.tween_property(sprite, "modulate:a", 0.0, 0.3)
		tw.tween_callback(queue_free)


func _on_animation_finished() -> void:
	if muerto and sprite.animation == animacion_muerte:
		queue_free()


func _on_zona_dano_body_entered(body: Node2D) -> void:
	if muerto or not body.is_in_group("player"):
		return
	_golpear(body)


## Qué pasa cuando el jugador toca al enemigo. Por defecto: daño de contacto.
func _golpear(body: Node2D) -> void:
	if body.has_method("take_damage"):
		body.take_damage(dano_contacto)
