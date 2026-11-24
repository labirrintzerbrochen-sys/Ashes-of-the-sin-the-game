"""Genera el bioma Infierno completo: recursos, mapa de muestra y 4 niveles.

Uso (desde la carpeta del proyecto Godot):
    python herramientas/generar_bioma_infierno.py            # genera todo
    python herramientas/generar_bioma_infierno.py --preview  # además dibuja PNGs de vista previa

Cada nivel tiene 3 mapas, un subnivel oculto (al que se entra por un muro falso
de uno de sus mapas) y una zona oculta (a la que se entra por un muro falso del subnivel).
Las semillas son fijas: volver a ejecutar produce exactamente los mismos mapas.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mapas_infierno import H, Mapa, escribir_mapa, zona_oculta  # noqa: E402
from recursos_infierno import RAIZ, T, TEX, generar_recursos, ruta  # noqa: E402

NIVELES = {
    1: dict(
        nombre="Cavernas de Ceniza", anchos=[90, 95, 100], mapa_secreto=2,
        suelo=["mina_demoniaca"], aire=["cabeza_demonio", "murcielago"], cada=14,
        pesos=[
            dict(plano=3, escalon=3, foso=2, bloque=2, pinchos_seg=1, techo_bajo=1),
            dict(plano=2, escalon=2, foso=1, techo_bajo=3, bloque=2, pinchos_seg=1),
            dict(plano=2, escalon=2, foso=3, puente=1, bloque=1, pinchos_seg=2),
        ]),
    2: dict(
        nombre="Rios de Lava", anchos=[105, 110, 115], mapa_secreto=1,
        suelo=["mina_demoniaca"], aire=["craneo_llameante", "ojo_demoniaco", "murcielago"], cada=12,
        pesos=[
            dict(plano=1, escalon=2, foso=3, puente=3, pinchos_seg=1, caida=1),
            dict(plano=1, escalon=2, foso=2, puente=4, torre=1, caida=1),
            dict(plano=1, escalon=1, foso=4, puente=3, pinchos_seg=2, techo_bajo=1),
        ]),
    3: dict(
        nombre="Torres Carmesi", anchos=[115, 120, 125], mapa_secreto=3,
        suelo=["arquero", "mina_demoniaca"], aire=["murcielago", "ojo_demoniaco", "cabeza_demonio"], cada=11,
        pesos=[
            dict(plano=1, torre=4, caida=2, puente=2, escalon=2, pinchos_seg=1),
            dict(plano=2, torre=3, caida=2, bloque=2, techo_bajo=2, pinchos_seg=2),
            dict(plano=1, torre=4, caida=3, puente=3, foso=1, escalon=1),
        ]),
    4: dict(
        nombre="Fortaleza del Pecado", anchos=[125, 130, 135], mapa_secreto=2,
        suelo=["arquero", "mina_demoniaca"],
        aire=["murcielago", "ojo_demoniaco", "cabeza_demonio", "craneo_llameante"], cada=9,
        pesos=[
            dict(plano=1, escalon=2, foso=2, puente=2, torre=2, pinchos_seg=2, techo_bajo=1, caida=1, bloque=1),
            dict(plano=1, escalon=1, foso=2, puente=3, torre=3, pinchos_seg=2, caida=2),
            dict(plano=1, escalon=2, foso=3, puente=3, torre=2, pinchos_seg=3, techo_bajo=2, bloque=1),
        ]),
}

# Qué hay en cada zona oculta: (tipo, (dx desde el centro de la arena, fila relativa al suelo))
ZONAS = {
    1: [("murcielago", (3, -8)), ("murcielago", (9, -8)), ("cabeza_demonio", (6, -2)), ("mina_demoniaca", (-12, 0))],
    2: [("craneo_gigante", (6, -9)), ("ojo_demoniaco", (-10, -5))],
    3: [("arquero", (2, -3)), ("arquero", (9, -3)), ("arquero", (5, -5)), ("murcielago", (6, -10))],
    4: [("craneo_gigante", (6, -9)), ("mina_demoniaca", (-12, 0)), ("mina_demoniaca", (16, 0)),
        ("craneo_llameante", (2, -6))],
}

PREVIEW = "--preview" in sys.argv
PREVIEW_DIR = os.path.join(RAIZ, "herramientas", "previews")


def res_nivel(n, archivo):
    return f"res://niveles/nivel_{n}/{archivo}.tscn"


def destino_tras(n, i):
    """Escena que sigue al mapa i (1..3) del nivel n."""
    if i < 3:
        return res_nivel(n, f"mapa_{i + 1}")
    if n < 4:
        return res_nivel(n + 1, "mapa_1")
    return ""  # fin del bioma


def verificar(mapa, capas, res_path):
    """Comprueba que desde el spawn se puede llegar a todos los portales.

    Modelo aproximado del salto (JUMP_VELOCITY -400, SPEED 300, gravedad 980):
    sube hasta 2 tiles y salva fosos de hasta 4 tiles (dx 5); puede caer cualquier altura.
    """
    W = mapa.x
    solido = {k for k in capas["suelo"]}  # incluye plataformas de un sentido
    mortal = set(capas["liquidos"]) | set(capas["peligros"])

    def libre(x, y):
        return 0 <= x < W and 0 <= y < H and (x, y) not in solido

    def de_pie(x, y):
        return libre(x, y) and libre(x, y - 1) and (x, y + 1) in solido and (x, y) not in mortal

    def caer(x, y):
        while libre(x, y + 1) and y < H - 1:
            y += 1
        return (x, y) if de_pie(x, y) else None

    spawn = next(o for o in mapa.objetos if o["tipo"] == "spawn")
    inicio = caer(spawn["x"], spawn["fila"] - 1)
    vistos, pila = {inicio}, [inicio]
    while pila:
        x, y = pila.pop()
        destinos = []
        for dx in (-1, 1):
            if libre(x + dx, y) and libre(x + dx, y - 1):
                destinos.append(caer(x + dx, y))
        for dx in range(-5, 6):
            for dy in range(-2, 7):
                if (dx or dy) and de_pie(x + dx, y + dy):
                    destinos.append((x + dx, y + dy))
        for d in destinos:
            if d and d not in vistos:
                vistos.add(d)
                pila.append(d)
    for o in mapa.objetos:
        if o["tipo"] == "portal":
            objetivo = caer(o["x"], o["fila"] - 1)
            if objetivo not in vistos:
                raise SystemExit(f"ERROR: portal inalcanzable en {res_path} (x={o['x']})")


def guardar(mapa, res_path, nivel, nombre, oculto, siguiente, extras=None):
    os.makedirs(os.path.dirname(ruta(res_path)), exist_ok=True)
    capas = escribir_mapa(mapa, res_path, nivel, nombre, oculto, siguiente, extras)
    if PREVIEW:
        dibujar_preview(mapa, capas, res_path)
    verificar(mapa, capas, res_path)
    enemigos = [o["tipo"] for o in mapa.objetos if o["tipo"] not in ("spawn", "antorcha", "portal", "recompensa")]
    portales = [("secreto" if o["secreto"] else "salida") + " -> " + (o["destino"] or "FIN")
                for o in mapa.objetos if o["tipo"] == "portal"]
    print(f"  {res_path}: {mapa.x}x{H} tiles, {len(enemigos)} enemigos, portales: {portales}")


def generar_niveles():
    for n, cfg in NIVELES.items():
        print(f"Nivel {n}: {cfg['nombre']}")
        s = cfg["mapa_secreto"]
        for i in range(1, 4):
            semilla = n * 1000 + i * 37
            m = Mapa(semilla, juego_tiles=(i + n) % 2)
            secreto = res_nivel(n, "subnivel_oculto") if i == s else None
            m.generar(cfg["anchos"][i - 1], cfg["pesos"][i - 1], destino_tras(n, i),
                      secreto=secreto, jefe_final=(n == 4 and i == 3))
            m.poblar(cfg["suelo"], cfg["aire"], m.x // cfg["cada"])
            guardar(m, res_nivel(n, f"mapa_{i}"), n, f"{cfg['nombre']} - Mapa {i}", False, destino_tras(n, i))

        # Subnivel oculto: sale al mapa siguiente al del secreto y esconde la entrada a la zona oculta
        salida = destino_tras(n, s)
        m = Mapa(n * 1000 + 500, oscuro=True, juego_tiles=n % 2)
        pesos = dict(plano=1, puente=3, torre=2, pinchos_seg=2, foso=2, escalon=1)
        m.generar(60, pesos, salida, secreto=res_nivel(n, "zona_oculta"))
        m.poblar(cfg["suelo"], cfg["aire"], m.x // max(6, cfg["cada"] - 4))
        guardar(m, res_nivel(n, "subnivel_oculto"), n, f"{cfg['nombre']} - Subnivel oculto", True, salida)

        # Zona oculta
        m, fondo = zona_oculta(n * 1000 + 900, salida, ZONAS[n])
        guardar(m, res_nivel(n, "zona_oculta"), n, f"{cfg['nombre']} - Zona oculta", True, salida, fondo)


def generar_bioma_muestra():
    """Mapa único que muestra todo el bioma: cada tipo de terreno, peligro y enemigo."""
    print("Bioma de muestra")
    m = Mapa(4242)
    m.inicio()
    for seg in ["plano", "escalon", "foso", "pinchos_seg", "puente", "bloque", "techo_bajo",
                "torre", "caida", "puente", "escalon"]:
        getattr(m, seg)()
    m.muro_secreto(res_nivel(1, "zona_oculta"))
    for seg in ["plano", "foso", "puente", "torre", "caida", "plano"]:
        getattr(m, seg)()
    m.fin(res_nivel(1, "mapa_1"), jefe=True)
    todos_suelo = ["arquero", "mina_demoniaca"]
    todos_aire = ["murcielago", "ojo_demoniaco", "cabeza_demonio", "craneo_llameante"]
    m.poblar(todos_suelo, todos_aire, 10, obligatorios=todos_suelo + todos_aire)
    guardar(m, "res://biomas/infierno/bioma_infierno.tscn", 0, "Bioma Infierno", False, res_nivel(1, "mapa_1"))


def registrar_capas_fisicas():
    """Nombra las capas de colisión en project.godot (mundo, jugador, enemigos, peligros)."""
    p = os.path.join(RAIZ, "project.godot")
    texto = open(p, encoding="utf-8").read()
    if "[layer_names]" in texto:
        return
    texto = texto.rstrip("\n") + (
        "\n\n[layer_names]\n\n"
        '2d_physics/layer_1="mundo"\n'
        '2d_physics/layer_2="jugador"\n'
        '2d_physics/layer_3="enemigos"\n'
        '2d_physics/layer_4="peligros"\n')
    open(p, "w", encoding="utf-8", newline="\n").write(texto)


# ---------------------------------------------------------------- previews
def dibujar_preview(mapa, capas, res_path):
    from PIL import Image, ImageDraw

    hojas = {}

    def hoja(src):
        if src not in hojas:
            nombre = {0: "tiles_infierno.png", 1: "lava.png", 2: "sangre.png", 3: "tiles_infierno_oscuro.png"}[src]
            hojas[src] = Image.open(ruta(f"{TEX}/{nombre}")).convert("RGBA")
        return hojas[src]

    W = mapa.x
    suf = "_oscuro" if mapa.oscuro else ""
    img = Image.new("RGBA", (W * T, H * T), (40, 10, 10, 255))
    cielo = Image.open(ruta(f"{TEX}/fondo_cielo{suf}.png")).convert("RGBA").resize((2458, 830))
    montes = Image.open(ruta(f"{TEX}/fondo_montanas{suf}.png")).convert("RGBA").resize((2458, 830))
    for x in range(0, W * T, 2458):
        img.alpha_composite(cielo, (x, 0))
        img.alpha_composite(montes, (x, 0))
    for nombre in ["fondo", "cascadas", "suelo", "deco", "peligros", "liquidos", "falsa"]:
        for (x, y), (src, (ax, ay)) in capas[nombre].items():
            tile = hoja(src).crop((ax * T, ay * T, ax * T + T, ay * T + T))
            if nombre == "fondo":
                tile = Image.eval(tile, lambda v: int(v * 0.5))
            if nombre == "falsa":
                tile.putalpha(Image.eval(tile.getchannel("A"), lambda v: v // 2))
            img.alpha_composite(tile, (x * T, y * T))
    d = ImageDraw.Draw(img)
    colores = dict(portal=(255, 140, 0), antorcha=(255, 200, 0), spawn=(0, 255, 0), recompensa=(0, 255, 255))
    for o in mapa.objetos:
        px, py = o["x"] * T + 16, o["fila"] * T
        c = colores.get(o["tipo"], (255, 0, 255))
        if o["tipo"] == "portal" and o.get("secreto"):
            c = (60, 140, 255)
        if o["tipo"] == "antorcha":
            d.ellipse([px - 4, py - 12, px + 4, py - 4], fill=c)
        else:
            d.rectangle([px - 10, py - 30, px + 10, py], outline=c, width=3)
            d.text((px - 10, py - 44), o["tipo"][:6], fill=c)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    nombre = res_path.replace("res://", "").replace("/", "_").replace(".tscn", ".png")
    img.convert("RGB").resize((W * T // 2, H * T // 2)).save(os.path.join(PREVIEW_DIR, nombre))


if __name__ == "__main__":
    generar_recursos()
    registrar_capas_fisicas()
    generar_bioma_muestra()
    generar_niveles()
    print("Listo.")
