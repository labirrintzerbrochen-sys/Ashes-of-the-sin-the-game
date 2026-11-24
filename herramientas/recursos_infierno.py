"""Genera texturas, TileSet, escenas de enemigos y objetos del bioma Infierno."""
from __future__ import annotations

import io
import os
import re
import zipfile

from PIL import Image

from tscn import Documento, Raw, color, fmt, puntos, sname, sprite_frames, v2, v2i

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # proyecto Godot
ZIP_HELL = os.path.join(os.path.dirname(RAIZ), "GandalfHardcore Hell Asset Pack 32x32.zip")
PACK = "GandalfHardcore Hell Asset Pack 32x32/"

BIOMA = "res://biomas/infierno"
TEX = f"{BIOMA}/texturas"
ENE = f"{BIOMA}/enemigos"
OBJ = f"{BIOMA}/objetos"
TILESET = f"{BIOMA}/tileset_infierno.tres"

T = 32  # tamaño de tile

# Fuentes del TileSet
SRC_ROCA, SRC_LAVA, SRC_SANGRE, SRC_ROCA_OSCURA = 0, 1, 2, 3

# Tile de relleno sintetizado (el pack no trae un interior 100 % sólido)
RELLENO = (0, 9)

# Autotile (juego A: base con estalactitas). El juego B usa las mismas coordenadas +3 filas.
AUTOTILE_BASE = {
    (0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2),
    (4, 0), (9, 1), (10, 0), (10, 1), (10, 2), (11, 1), (12, 0), (12, 1), (12, 2),
    (6, 0), (8, 0), (6, 2), (8, 2),
}
SOLIDOS = AUTOTILE_BASE | {(x, y + 3) for x, y in AUTOTILE_BASE} | {RELLENO}
UN_SENTIDO = {(6, 6), (7, 6), (8, 6), (6, 7), (7, 7), (8, 7)}

# Tiles animados de lava/sangre (20 frames en horizontal)
LIQ_SUPERFICIE = (0, 2)
CASCADA_ARRIBA, CASCADA_MEDIO_A, CASCADA_MEDIO_B, CASCADA_ABAJO = (0, 3), (0, 4), (0, 5), (0, 6)
LIQ_ANIMADOS = [LIQ_SUPERFICIE, CASCADA_ARRIBA, CASCADA_MEDIO_A, CASCADA_MEDIO_B, CASCADA_ABAJO]


def ruta(res: str) -> str:
    return os.path.join(RAIZ, res.replace("res://", "").replace("/", os.sep))


# ---------------------------------------------------------------- texturas
def extraer_texturas():
    os.makedirs(ruta(TEX), exist_ok=True)
    if not os.path.exists(ZIP_HELL):
        if os.path.exists(ruta(f"{TEX}/tiles_infierno.png")):
            print("Zip no encontrado; se reutilizan las texturas existentes.")
            return
        raise SystemExit(f"No se encontró {ZIP_HELL}")
    z = zipfile.ZipFile(ZIP_HELL)

    def abrir(nombre):
        return Image.open(io.BytesIO(z.read(PACK + nombre))).convert("RGBA")

    for origen, destino in [
        ("GandalfHardcore Hell Tiles 32x32.png", "tiles_infierno.png"),
        ("GandalfHardcore Hell Tiles 32x32 dark.png", "tiles_infierno_oscuro.png"),
    ]:
        hoja = abrir(origen)
        ancho, alto = hoja.size
        nueva = Image.new("RGBA", (ancho, alto + T), (0, 0, 0, 0))
        nueva.paste(hoja, (0, 0))
        # Relleno: textura oscura tomada de la parte inferior del tile (1,0)
        base = hoja.crop((T, 0, 2 * T, T))
        relleno = Image.new("RGBA", (T, T))
        for y in range(T):
            fila = base.crop((0, 12 + (y % 20), T, 13 + (y % 20)))
            relleno.paste(fila, (0, y))
        nueva.paste(relleno, (RELLENO[0] * T, RELLENO[1] * T))
        nueva.save(ruta(f"{TEX}/{destino}"))

    for origen, destino in [
        ("GandalfHardcore Lava Tiles.png", "lava.png"),
        ("GandalfHardcore Blood Tiles.png", "sangre.png"),
        ("Fire sheet.png", "fuego.png"),
        ("Blue fire sheet.png", "fuego_azul.png"),
    ]:
        abrir(origen).save(ruta(f"{TEX}/{destino}"))

    capas = [("Background layer", "cielo"), ("middle layer", "montanas_lejanas"),
             ("back layer", "montanas"), ("front layer", "rocas")]
    for carpeta, sufijo in [("GandalfHardcore Hell background/", ""),
                            ("GandalfHardcore Hell background dark/", "_oscuro")]:
        for origen, nombre in capas:
            abrir(carpeta + origen + ".png").save(ruta(f"{TEX}/fondo_{nombre}{sufijo}.png"))


# ---------------------------------------------------------------- tileset
def tiles_no_vacios(png: str):
    im = Image.open(ruta(f"{TEX}/{png}")).convert("RGBA")
    res = []
    for ty in range(im.height // T):
        for tx in range(im.width // T):
            if im.crop((tx * T, ty * T, (tx + 1) * T, (ty + 1) * T)).getbbox():
                res.append((tx, ty))
    return res


def crear_tileset():
    doc = Documento("TileSet")
    cuadrado = puntos([-16, -16, 16, -16, 16, 16, -16, 16])
    plataforma = puntos([-16, -16, 16, -16, 16, -6, -16, -6])

    fuentes = {}
    for sid, png in [(SRC_ROCA, "tiles_infierno.png"), (SRC_ROCA_OSCURA, "tiles_infierno_oscuro.png")]:
        props = [("texture", doc.ext_resource("Texture2D", f"{TEX}/{png}")),
                 ("texture_region_size", v2i(T, T))]
        for (x, y) in tiles_no_vacios(png):
            props.append((f"{x}:{y}/0", 0))
            if (x, y) in SOLIDOS:
                props.append((f"{x}:{y}/0/physics_layer_0/polygon_0/points", cuadrado))
            elif (x, y) in UN_SENTIDO:
                props.append((f"{x}:{y}/0/physics_layer_0/polygon_0/points", plataforma))
                props.append((f"{x}:{y}/0/physics_layer_0/polygon_0/one_way", True))
        fuentes[sid] = doc.sub_resource("TileSetAtlasSource", props)

    for sid, png in [(SRC_LAVA, "lava.png"), (SRC_SANGRE, "sangre.png")]:
        props = [("texture", doc.ext_resource("Texture2D", f"{TEX}/{png}")),
                 ("texture_region_size", v2i(T, T))]
        for (x, y) in LIQ_ANIMADOS:
            props.append((f"{x}:{y}/animation_columns", 20))
            props.append((f"{x}:{y}/animation_speed", 16.0))
            for f in range(20):
                props.append((f"{x}:{y}/animation_frame_{f}/duration", 1.0))
            props.append((f"{x}:{y}/0", 0))
        fuentes[sid] = doc.sub_resource("TileSetAtlasSource", props)

    doc.recurso = [("tile_size", v2i(T, T)), ("physics_layer_0/collision_layer", 1)]
    for sid in sorted(fuentes):
        doc.recurso.append((f"sources/{sid}", fuentes[sid]))
    doc.guardar(ruta(TILESET))


# ---------------------------------------------------------------- enemigos
def leer_animaciones(tscn: str) -> dict[str, list[str]]:
    """Lee las animaciones (lista de rutas de frames) de las escenas originales del proyecto."""
    t = open(os.path.join(RAIZ, tscn), encoding="utf-8").read()
    ids = {m.group(2): m.group(1) for m in re.finditer(r'path="(res://[^"]+)" id="([^"]+)"', t)}
    anims = {}
    patron = r'"frames": \[(.*?)\],\s*"loop": \w+,\s*"name": &"([^"]+)"'
    for m in re.finditer(patron, t, re.S):
        anims[m.group(2)] = [ids[i] for i in re.findall(r'ExtResource\("([^"]+)"\)', m.group(1))]
    return anims


# nombre_escena: (tscn original, script, {anim_nueva: (anim_original, fps, loop)}, props)
ENEMIGOS = {
    "murcielago": dict(
        original="bat.tscn", animaciones={"volar": ("bat attack 1", 10, True), "picada": ("bat attack 2", 12, True)},
        inicial="volar", cuerpo=("circulo", 10), dano=("circulo", 14), sprite_pos=(0, 0), vida=1.0, mira_der=True),
    "ojo_demoniaco": dict(
        original="demon eye.tscn", animaciones={"idle": ("idle demon eye", 10, True), "muerte": ("death demon eye", 12, False)},
        inicial="idle", cuerpo=("circulo", 14), dano=("circulo", 18), sprite_pos=(0, 0), vida=3.0, mira_der=False),
    "mina_demoniaca": dict(
        original="demon mine.tscn", animaciones={"idle": ("idle demon mine", 6, True), "explotar": ("death demon mine", 12, False)},
        inicial="idle", cuerpo=("circulo", 14), dano=("circulo", 56), sprite_pos=(0, 0), vida=1.0, mira_der=True),
    "craneo_llameante": dict(
        original="burning skull.tscn", animaciones={"idle": ("idle skull", 10, True), "muerte": ("death skull", 10, False)},
        inicial="idle", cuerpo=("circulo", 12), dano=("circulo", 15), sprite_pos=(0, -8), vida=2.0, mira_der=False),
    "cabeza_demonio": dict(
        original="flying demon head.tscn", animaciones={"idle": ("idle flying demon head", 9, True), "muerte": ("death flying demon head", 12, False)},
        inicial="idle", cuerpo=("circulo", 14), dano=("circulo", 17), sprite_pos=(0, 0), vida=1.0, mira_der=True),
    "arquero": dict(
        original="archer.tscn", animaciones={
            "idle": ("idle archer", 6, True), "caminar": ("walk archer", 8, True),
            "disparar": ("shoot archer", 12, False), "herido": ("hurt archer", 12, False),
            "muerte": ("death archer", 10, False)},
        inicial="caminar", cuerpo=("capsula", 10, 42), dano=("capsula", 12, 44), sprite_pos=(0, -32), vida=3.0, mira_der=True),
    "craneo_gigante": dict(
        original="large skull.tscn", animaciones={
            "idle": ("idle large skull", 10, True), "ataque": ("atack large skull", 12, False),
            "muerte": ("death large skull", 10, False)},
        inicial="idle", cuerpo=("circulo", 40), dano=("circulo", 44), sprite_pos=(0, 0), vida=30.0, mira_der=True),
}


def _forma(doc: Documento, forma):
    if forma[0] == "circulo":
        return doc.sub_resource("CircleShape2D", [("radius", float(forma[1]))])
    return doc.sub_resource("CapsuleShape2D", [("radius", float(forma[1])), ("height", float(forma[2]))])


def crear_enemigos():
    for nombre, cfg in ENEMIGOS.items():
        originales = leer_animaciones(cfg["original"])
        doc = Documento()
        script = doc.ext_resource("Script", f"{ENE}/{nombre}.gd")
        anims = []
        for nueva, (orig, fps, loop) in cfg["animaciones"].items():
            texs = [doc.ext_resource("Texture2D", p) for p in originales[orig]]
            anims.append(dict(nombre=nueva, texturas=texs, fps=fps, loop=loop))
        frames = sprite_frames(doc, anims)
        forma_cuerpo = _forma(doc, cfg["cuerpo"])
        forma_dano = _forma(doc, cfg["dano"])
        centro = (0, -24) if nombre == "arquero" else (0, 0)
        doc.nodo(nombre.title().replace("_", ""), "CharacterBody2D", props=[
            ("collision_layer", 4), ("collision_mask", 1), ("script", script),
            ("vida_maxima", float(cfg["vida"])), ("sprite_mira_derecha", cfg["mira_der"]),
        ])
        doc.nodo("AnimatedSprite2D", "AnimatedSprite2D", ".", props=[
            ("position", v2(*cfg["sprite_pos"])), ("sprite_frames", frames),
            ("animation", sname(cfg["inicial"])), ("autoplay", cfg["inicial"]),
        ])
        doc.nodo("CollisionShape2D", "CollisionShape2D", ".", props=[("position", v2(*centro)), ("shape", forma_cuerpo)])
        doc.nodo("ZonaDano", "Area2D", ".", props=[("collision_layer", 0), ("collision_mask", 2)])
        doc.nodo("CollisionShape2D", "CollisionShape2D", "ZonaDano", props=[("position", v2(*centro)), ("shape", forma_dano)])
        if nombre == "arquero":
            doc.nodo("SensorBorde", "RayCast2D", ".", props=[
                ("position", v2(14, -4)), ("target_position", v2(0, 24)), ("collision_mask", 1)])
        if nombre == "craneo_gigante":
            fuego = doc.sub_resource("CircleShape2D", [("radius", 96.0)])
            doc.nodo("ZonaFuego", "Area2D", ".", props=[("collision_layer", 0), ("collision_mask", 2), ("monitorable", False)])
            doc.nodo("CollisionShape2D", "CollisionShape2D", "ZonaFuego", props=[("position", v2(0, 20)), ("shape", fuego)])
        doc.guardar(ruta(f"{ENE}/{nombre}.tscn"))

    # Flecha (no hay sprite de flecha suelta en el pack: se dibuja con un polígono)
    doc = Documento()
    script = doc.ext_resource("Script", f"{ENE}/flecha.gd")
    forma = doc.sub_resource("RectangleShape2D", [("size", v2(22, 4))])
    doc.nodo("Flecha", "Area2D", props=[("collision_layer", 0), ("collision_mask", 3), ("script", script)])
    doc.nodo("Visual", "Polygon2D", ".", props=[
        ("color", color(0.86, 0.8, 0.68)),
        ("polygon", puntos([-12, -1, 7, -1, 7, -3, 13, 0, 7, 3, 7, 1, -12, 1])),
    ])
    doc.nodo("Plumas", "Polygon2D", "Visual", props=[
        ("color", color(0.75, 0.15, 0.12)), ("polygon", puntos([-13, -3, -8, -1, -8, 1, -13, 3])),
    ])
    doc.nodo("CollisionShape2D", "CollisionShape2D", ".", props=[("shape", forma)])
    doc.guardar(ruta(f"{ENE}/flecha.tscn"))


# ---------------------------------------------------------------- objetos
def _frames_fuego(doc: Documento, animaciones: dict[str, str]) -> Raw:
    anims = []
    for nombre, png in animaciones.items():
        hoja = doc.ext_resource("Texture2D", f"{TEX}/{png}")
        texs = [doc.sub_resource("AtlasTexture", [("atlas", hoja), ("region", Raw(f"Rect2({i * T}, 0, {T}, {T})"))])
                for i in range(6)]
        anims.append(dict(nombre=nombre, texturas=texs, fps=10, loop=True))
    return sprite_frames(doc, anims)


def crear_objetos():
    # Antorcha (decoración animada)
    doc = Documento()
    frames = _frames_fuego(doc, {"fuego": "fuego.png", "fuego_azul": "fuego_azul.png"})
    doc.nodo("Antorcha", "Node2D")
    doc.nodo("Llama", "AnimatedSprite2D", ".", props=[
        ("position", v2(0, -16)), ("sprite_frames", frames), ("animation", sname("fuego")), ("autoplay", "fuego")])
    doc.guardar(ruta(f"{OBJ}/antorcha.tscn"))

    # Portal (rojo = salida, azul = secreto)
    doc = Documento()
    script = doc.ext_resource("Script", f"{OBJ}/portal.gd")
    frames = _frames_fuego(doc, {"normal": "fuego.png", "secreto": "fuego_azul.png"})
    forma = doc.sub_resource("RectangleShape2D", [("size", v2(40, 64))])
    doc.nodo("Portal", "Area2D", props=[("collision_layer", 0), ("collision_mask", 2), ("script", script)])
    doc.nodo("Llama", "AnimatedSprite2D", ".", props=[
        ("position", v2(0, -32)), ("scale", v2(2, 2)), ("sprite_frames", frames),
        ("animation", sname("normal")), ("autoplay", "normal")])
    doc.nodo("Brillo", "AnimatedSprite2D", ".", props=[
        ("modulate", color(1, 1, 1, 0.45)), ("position", v2(0, -40)), ("scale", v2(3, 3)),
        ("sprite_frames", frames), ("animation", sname("normal")), ("autoplay", "normal"), ("frame", 3)])
    doc.nodo("CollisionShape2D", "CollisionShape2D", ".", props=[("position", v2(0, -32)), ("shape", forma)])
    doc.guardar(ruta(f"{OBJ}/portal.tscn"))


def generar_recursos():
    extraer_texturas()
    crear_tileset()
    crear_enemigos()
    crear_objetos()
