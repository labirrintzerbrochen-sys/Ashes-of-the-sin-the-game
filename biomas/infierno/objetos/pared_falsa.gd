extends TileMapLayer
## Muro falso: se ve igual que la roca sólida pero no tiene colisión.
## Cuando el jugador lo atraviesa se vuelve translúcido y queda revelado.

signal revelada

@export var opacidad_revelada: float = 0.3
@export var tiempo_fundido: float = 0.4

var _revelada: bool = false


func _ready() -> void:
	collision_enabled = false
	$Detector.body_entered.connect(_on_detector_body_entered)


func _on_detector_body_entered(body: Node2D) -> void:
	if _revelada or not body.is_in_group("player"):
		return
	_revelada = true
	revelada.emit()
	create_tween().tween_property(self, "modulate:a", opacidad_revelada, tiempo_fundido)
