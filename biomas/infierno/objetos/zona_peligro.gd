extends Area2D
## Zona de peligro del bioma: lava, sangre hirviente o pinchos.
## mortal = true mata al instante (lava/sangre). Si no, hace "dano" cada "intervalo" segundos.

@export var mortal: bool = true
@export var dano: int = 1
@export var intervalo: float = 0.75

var _reloj: float = 0.0


func _ready() -> void:
	body_entered.connect(_aplicar)


func _physics_process(delta: float) -> void:
	if mortal:
		return
	_reloj += delta
	if _reloj < intervalo:
		return
	_reloj = 0.0
	for body in get_overlapping_bodies():
		_aplicar(body)


func _aplicar(body: Node2D) -> void:
	if not body.is_in_group("player"):
		return
	if mortal:
		if body.has_method("die"):
			body.die()
		elif body.has_method("take_damage"):
			body.take_damage(9999)
	elif body.has_method("take_damage"):
		body.take_damage(dano)
