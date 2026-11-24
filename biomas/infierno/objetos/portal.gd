extends Area2D
## Portal de fuego: lleva al jugador a otra escena (siguiente mapa, subnivel oculto o zona oculta).
## Fuego rojo = salida normal. Fuego azul = portal secreto.

signal jugador_entro(destino: String)

@export_file("*.tscn") var escena_destino: String = ""
@export var es_secreto: bool = false

var _usado: bool = false


func _ready() -> void:
	var anim := &"secreto" if es_secreto else &"normal"
	$Llama.play(anim)
	$Brillo.play(anim)
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _usado or not body.is_in_group("player"):
		return
	_usado = true
	jugador_entro.emit(escena_destino)
	if escena_destino.is_empty():
		print("Portal sin destino: fin del bioma.")
		return
	get_tree().change_scene_to_file.call_deferred(escena_destino)
