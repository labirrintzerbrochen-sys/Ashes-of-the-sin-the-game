extends Camera2D
## Cámara libre para recorrer el mapa mientras no exista personaje principal.
## Flechas / WASD (ui_*) para moverse, Shift = rápido, rueda del ratón = zoom.
## Se desactiva sola si en la escena hay un nodo en el grupo "player".

@export var velocidad: float = 700.0


func _ready() -> void:
	await get_tree().process_frame
	if get_tree().get_first_node_in_group("player") != null:
		enabled = false
		set_process(false)
		set_process_unhandled_input(false)
		return
	make_current()


func _process(delta: float) -> void:
	var dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	var mult := 3.0 if Input.is_key_pressed(KEY_SHIFT) else 1.0
	position += dir * velocidad * mult * delta / zoom.x


func _unhandled_input(event: InputEvent) -> void:
	var boton := event as InputEventMouseButton
	if boton == null or not boton.pressed:
		return
	if boton.button_index == MOUSE_BUTTON_WHEEL_UP:
		zoom = (zoom * 1.1).clamp(Vector2(0.25, 0.25), Vector2(4.0, 4.0))
	elif boton.button_index == MOUSE_BUTTON_WHEEL_DOWN:
		zoom = (zoom / 1.1).clamp(Vector2(0.25, 0.25), Vector2(4.0, 4.0))
