extends Node2D
## Raíz de cada mapa del bioma Infierno (niveles, subniveles ocultos y zonas ocultas).
##
## Estructura de cada mapa:
##   Fondo (Parallax2D) > FondoDecoracion > Cascadas > Suelo (colisión) > Decoracion
##   > Peligros > Enemigos > Objetos (portales/antorchas) > Liquidos > ZonasPeligro
##   > ParedesFalsas > SpawnJugador > CamaraPrevia

@export var nivel: int = 1
@export var nombre_mapa: String = ""
@export var es_oculto: bool = false
## Escena a la que lleva la salida normal de este mapa.
@export_file("*.tscn") var siguiente_escena: String = ""


## Posición donde debe aparecer el personaje principal.
func obtener_spawn() -> Vector2:
	var marcador := get_node_or_null("SpawnJugador") as Marker2D
	return marcador.global_position if marcador else Vector2.ZERO
