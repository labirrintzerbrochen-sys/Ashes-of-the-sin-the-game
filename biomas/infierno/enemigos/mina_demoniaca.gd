extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Mina demoníaca: flota quieta. Si el jugador se acerca (o la golpean)
## parpadea y explota, dañando a todo jugador dentro del radio.

@export var dano_explosion: int = 2
@export var retardo_explosion: float = 0.4

var activada: bool = false
var origen: Vector2
var tiempo: float = 0.0


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	animacion_muerte = &"explotar"
	origen = global_position
	sprite.play("idle")


func _physics_process(delta: float) -> void:
	if muerto:
		return
	tiempo += delta
	global_position.y = origen.y + sin(tiempo * 2.0) * 3.0


## Tocarla no hace daño directo: la arma.
func _golpear(_body: Node2D) -> void:
	activar()


func take_damage(_cantidad: float = 1.0) -> void:
	activar()


func activar() -> void:
	if activada or muerto:
		return
	activada = true
	var tw := create_tween().set_loops(3)
	tw.tween_property(sprite, "modulate", Color(2.0, 0.5, 0.5), retardo_explosion / 6.0)
	tw.tween_property(sprite, "modulate", Color.WHITE, retardo_explosion / 6.0)
	get_tree().create_timer(retardo_explosion, false).timeout.connect(_explotar)


func _explotar() -> void:
	if muerto or not is_inside_tree():
		return
	for body in zona_dano.get_overlapping_bodies():
		if body.is_in_group("player") and body.has_method("take_damage"):
			body.take_damage(dano_explosion)
	die()
