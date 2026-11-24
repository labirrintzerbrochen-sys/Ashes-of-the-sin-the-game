extends "res://biomas/infierno/enemigos/enemigo_base.gd"
## Cráneo llameante: rebota en diagonal contra paredes, suelo y techo sin parar.

@export var velocidad: float = 100.0
@export var direccion_inicial: Vector2 = Vector2(1.0, -1.0)


func _iniciar() -> void:
	motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	velocity = direccion_inicial.normalized() * velocidad
	sprite.play("idle")


func _physics_process(delta: float) -> void:
	if muerto:
		return
	var choque := move_and_collide(velocity * delta)
	if choque:
		velocity = velocity.bounce(choque.get_normal())
		# Evita que quede rebotando en línea recta (horizontal o vertical).
		if absf(velocity.x) < velocidad * 0.3:
			velocity.x = velocidad * 0.5 * (1.0 if randf() < 0.5 else -1.0)
		if absf(velocity.y) < velocidad * 0.3:
			velocity.y = velocidad * 0.5 * (1.0 if randf() < 0.5 else -1.0)
		velocity = velocity.normalized() * velocidad
	mirar_hacia(velocity.x)
