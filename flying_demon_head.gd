extends Area2D

var velocidad = 80    # qué tan rápido camina
var distancia = 150   # cuántos píxeles camina antes de darse la vuelta
var rebote = -250     # qué tan alto rebota el personaje al aplastarlo
var inicio_x          # dónde empezó
var direccion = 1     # 1 = derecha, -1 = izquierda

func _ready():
	inicio_x = position.x  # guardamos dónde lo pusimos en el nivel

func _process(delta):
	position.x += velocidad * direccion * delta  # lo movemos

	if position.x > inicio_x + distancia:  # si llegó al final…
		direccion = -1                     # …se regresa
	if position.x < inicio_x:              # si volvió al inicio…
		direccion = 1                      # …va otra vez a la derecha

	# voltea la imagen hacia donde camina
	for hijo in get_children():
		if hijo is Sprite2D or hijo is AnimatedSprite2D:
			hijo.flip_h = direccion < 0

func _on_body_entered(body: Node2D) -> void:
	if body is CharacterBody2D:  # si tocó al personaje…
		if body.velocity.y > 0:  # si venía cayendo…
			# …¡lo aplastó!
			body.velocity.y = rebote           # el personaje rebota
			set_deferred("monitoring", false)  # el enemigo ya no hace daño
			hide()                             # desaparece de la vista
			if has_node("Sonido"):             # si tiene sonido, suena
				$Sonido.play()
				await $Sonido.finished
			queue_free()                       # se borra del juego
		else:
			# lo tocó de lado o por abajo: pierde
			get_tree().reload_current_scene()
