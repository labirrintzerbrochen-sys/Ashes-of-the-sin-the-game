extends Area2D
## Flecha del arquero: vuela en línea recta, daña al jugador y se rompe contra el mundo.

@export var velocidad: float = 260.0
@export var dano: int = 1
@export var duracion: float = 3.0

var direccion: float = 1.0


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	$Visual.scale.x = direccion


func _physics_process(delta: float) -> void:
	position.x += velocidad * direccion * delta
	duracion -= delta
	if duracion <= 0.0:
		queue_free()


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		if body.has_method("take_damage"):
			body.take_damage(dano)
		queue_free()
	elif body is TileMapLayer or body is StaticBody2D:
		queue_free()
