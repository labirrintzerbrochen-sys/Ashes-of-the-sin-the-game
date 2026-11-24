# Bioma Infierno: niveles

Todo usa los sprites del pack *GandalfHardcore Hell 32x32* (el mismo de los enemigos del proyecto).

| Nivel | Nombre | Enemigos | Mapa con el secreto |
|---|---|---|---|
| 1 | Cavernas de Ceniza | mina, cabeza de demonio, murciélago | mapa_2 |
| 2 | Ríos de Lava | mina, cráneo llameante, ojo, murciélago | mapa_1 |
| 3 | Torres Carmesí | arquero, mina, murciélago, ojo, cabeza | mapa_3 |
| 4 | Fortaleza del Pecado | todos; jefe Cráneo Gigante al final de mapa_3 | mapa_2 |

Cada `nivel_N/` tiene:

- `mapa_1`, `mapa_2`, `mapa_3`: los tres mapas del nivel. Cada uno se sale por un portal de fuego rojo.
- `subnivel_oculto`: se entra por un **muro falso** en la cara de una meseta de uno de los mapas
  (se camina hacia la pared y se atraviesa) y se llega a un portal de fuego **azul**.
  El subnivel usa los tiles oscuros y esconde otro muro falso.
- `zona_oculta`: se entra desde el muro falso del subnivel. Es una arena con sangre, un punto
  `Recompensa` (Marker2D, grupo `recompensa`) y enemigos especiales (en los niveles 2 y 4, el Cráneo Gigante).
  Al salir se continúa en el mapa siguiente al del secreto.

Flujo: `nivel_1/mapa_1 → mapa_2 → mapa_3 → nivel_2/mapa_1 → … → nivel_4/mapa_3 (FIN)`.
`biomas/infierno/bioma_infierno.tscn` es un mapa de muestra con todos los terrenos y enemigos del bioma.

## Para conectar el personaje principal

- Ponerlo en el grupo `player` y en la capa de colisión 2 (`jugador`), con máscara 1 (`mundo`).
- Si tiene `take_damage(cantidad)` los enemigos, pinchos y flechas le hacen daño;
  si tiene `die()` la lava y la sangre lo matan al instante.
- Para aplastar a la cabeza de demonio, debe ser un `CharacterBody2D` (usa `velocity`).
- Aparece en el nodo `SpawnJugador` de cada mapa (`obtener_spawn()` en la raíz).
- La `CamaraPrevia` (flechas para moverse, Shift rápido, rueda para zoom) se desactiva sola cuando hay un `player`.

## Regenerar

Los mapas salen de `herramientas/generar_bioma_infierno.py` (semillas fijas, Python + Pillow):

```
python herramientas/generar_bioma_infierno.py --preview
```

El script también comprueba que todos los portales (salida y secreto) se puedan alcanzar desde
el spawn con el salto del personaje (sube 2 tiles, salta fosos de 4) y dibuja vistas previas en
`herramientas/previews/`. Si editas un mapa a mano en Godot, no lo regeneres o perderás los cambios.
