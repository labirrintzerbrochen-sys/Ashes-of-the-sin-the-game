"""Generador de mapas del bioma Infierno (TileMapLayer + enemigos + secretos)."""
from __future__ import annotations

import random
import struct

from recursos_infierno import (
    BIOMA, CASCADA_ABAJO, CASCADA_ARRIBA, CASCADA_MEDIO_A, CASCADA_MEDIO_B, ENE, LIQ_SUPERFICIE,
    OBJ, RELLENO, SRC_LAVA, SRC_ROCA, SRC_ROCA_OSCURA, SRC_SANGRE, T, TEX, TILESET, ruta,
)
from tscn import Documento, Raw, color, v2

H = 24            # alto de todos los mapas en tiles
MIN_G = 9         # fila más alta que puede tener el suelo
FILA_LIQ = H - 4  # fila de la superficie de lava/sangre en los fosos
MAX_G = H - 5     # fila más baja del suelo
SALTO = 2         # desnivel máximo que se pide subir (el salto del arquero llega a ~2.5 tiles)
HUECO = 4         # ancho máximo de foso sin plataformas

# Decoraciones (dx, dy, ax, ay) con dy relativo a la fila del suelo (negativo = arriba)
DECO_SUELO = [
    [(0, -1, 9, 6)], [(0, -1, 10, 6)], [(0, -1, 11, 6)],
    [(0, -2, 9, 7), (0, -1, 9, 8)], [(0, -2, 10, 7), (0, -1, 10, 8)], [(0, -2, 11, 7), (0, -1, 11, 8)],
    [(0, -2, 13, 2), (0, -1, 13, 3)], [(0, -2, 13, 4), (0, -1, 13, 5)],
    [(0, -2, 13, 0), (1, -2, 14, 0), (0, -1, 13, 1), (1, -1, 14, 1)],
]
DECO_FONDO = [
    [(0, -3, 13, 6), (1, -3, 14, 6), (0, -2, 13, 7), (1, -2, 14, 7), (0, -1, 13, 8), (1, -1, 14, 8)],
]


class Mapa:
    def __init__(self, semilla: int, oscuro=False, liquido="lava", juego_tiles=0):
        self.r = random.Random(semilla)
        self.oscuro = oscuro
        self.src_roca = SRC_ROCA_OSCURA if oscuro else SRC_ROCA
        self.src_liq = SRC_SANGRE if liquido == "sangre" else SRC_LAVA
        self.dy_tiles = 3 * juego_tiles  # juego B = mismas piezas con escombros (+3 filas)
        self.suelo: list[int] = []       # fila superior del suelo por columna
        self.es_foso: list[bool] = []
        self.techo_forzado: dict[int, int] = {}
        self.plataformas: list[tuple[int, int, int]] = []  # (x, y, ancho)
        self.pinchos: set[tuple[int, int]] = set()
        self.falsos: set[tuple[int, int]] = set()
        self.excavar: set[tuple[int, int]] = set()
        self.objetos: list[dict] = []
        self.slots_suelo: list[tuple[int, int, int]] = []  # (x0, x1, fila)
        self.slots_aire: list[tuple[int, int]] = []        # (x, fila)
        self.cascadas: list[int] = []
        self.reservado: set[int] = set()   # columnas donde no poner enemigos ni deco
        self.g = 17
        self.detectores: list[tuple[int, int, int, int]] = []

    # ---------------------------------------------------------- utilidades
    @property
    def x(self):
        return len(self.suelo)

    def col(self, g=None, foso=False):
        self.suelo.append(self.g if g is None else g)
        self.es_foso.append(foso)

    def obj(self, tipo, x, fila, **props):
        self.objetos.append(dict(tipo=tipo, x=x, fila=fila, **props))

    def subir(self, d):
        self.g = max(MIN_G, min(MAX_G, self.g + d))

    # ---------------------------------------------------------- segmentos
    def inicio(self):
        self.col(g=0)  # muro izquierdo
        for _ in range(7):
            self.col()
        self.obj("spawn", 3, self.g)
        self.obj("antorcha", 6, self.g)
        self.reservado.update(range(0, 10))

    def fin(self, destino: str, jefe=False):
        if jefe:
            self.arena_jefe()
        x0 = self.x
        for _ in range(8):
            self.col()
        self.obj("portal", x0 + 4, self.g, destino=destino, secreto=False)
        self.obj("antorcha", x0 + 2, self.g)
        self.obj("antorcha", x0 + 6, self.g)
        self.col(g=0)  # muro derecho
        self.reservado.update(range(x0 - 2, self.x))

    def plano(self, n=None):
        n = n or self.r.randint(5, 10)
        x0 = self.x
        for _ in range(n):
            self.col()
        self.slots_suelo.append((x0 + 1, self.x - 2, self.g))
        self.slots_aire.append((x0 + n // 2, self.g - self.r.randint(3, 5)))

    def escalon(self):
        self.subir(self.r.choice([-SALTO, -1, 1, SALTO]))
        self.plano(self.r.randint(4, 7))

    def caida(self):
        self.subir(self.r.randint(3, 5))
        self.plano(self.r.randint(4, 6))

    def foso(self):
        w = self.r.randint(2, HUECO)
        x0 = self.x
        for _ in range(w):
            self.col(foso=True)
        self.slots_aire.append((x0 + w // 2, self.g - 4))
        self.plano(self.r.randint(3, 5))

    def puente(self):
        """Foso ancho de lava con plataformas de un solo sentido encima."""
        w = self.r.randint(8, 13)
        x0 = self.x
        for _ in range(w):
            self.col(foso=True)
        g0 = self.g
        previa_y, fin_previo = g0, x0 - 1  # el borde izquierdo cuenta como "plataforma" previa
        # Se colocan plataformas hasta que el hueco hasta el lado derecho sea de 3 tiles o menos.
        while (x0 + w) - fin_previo - 1 > 3:
            ancho = self.r.randint(2, 3)
            px = fin_previo + 1 + self.r.randint(2, 3)
            if px + ancho > x0 + w - 1:
                px = max(fin_previo + 2, x0 + w - 1 - ancho)
            y = max(MIN_G + 1, min(g0 + 1, previa_y + self.r.randint(-SALTO, SALTO)))
            self.plataformas.append((px, y, ancho))
            self.slots_aire.append((px + 1, y - 3))
            previa_y, fin_previo = y, px + ancho - 1
        # Lado derecho a una altura alcanzable desde la última plataforma
        self.g = max(MIN_G, min(MAX_G, previa_y + self.r.randint(-1, 1)))
        if self.r.random() < 0.6:
            self.cascadas.append(x0 + self.r.randint(1, w - 2))
        self.plano(self.r.randint(4, 6))

    def pinchos_seg(self):
        n = self.r.randint(6, 9)
        x0 = self.x
        for _ in range(n):
            self.col()
        k = self.r.randint(2, 3)
        s = x0 + self.r.randint(2, n - k - 1)
        for i in range(k):
            self.pinchos.add((s + i, self.g - 1))
        self.reservado.update(range(s - 1, s + k + 1))
        self.slots_aire.append((s + 1, self.g - 4))

    def bloque(self):
        self.plano(2)
        self.subir(-SALTO)
        self.plano(self.r.randint(3, 4))
        self.subir(SALTO)
        self.plano(3)

    def torre(self):
        """Muro alto que se sube por una escalera de plataformas."""
        sube = min(self.r.randint(4, 6), self.g - MIN_G)
        if sube < 3:
            # No queda altura para una torre: se baja primero.
            self.caida()
            return
        g0 = self.g
        x0 = self.x
        for _ in range(6):
            self.col()
        y, lado = g0 - 2, 0
        while y > g0 - sube:
            px = x0 + (1 if lado == 0 else 3)
            self.plataformas.append((px, y, 2))
            y -= 2
            lado ^= 1
        self.g = g0 - sube
        self.plano(self.r.randint(5, 8))

    def techo_bajo(self):
        n = self.r.randint(6, 9)
        x0 = self.x
        for _ in range(n):
            self.techo_forzado[self.x] = self.g - 5
            self.col()
        self.slots_suelo.append((x0 + 1, self.x - 2, self.g))

    def muro_secreto(self, destino: str):
        """Meseta con un túnel oculto tras un muro falso que lleva a un portal azul."""
        self.plano(4)
        x_cara = self.x
        g0 = self.g
        self.plataformas.append((x_cara - 3, g0 - 2, 3))  # para subir a la meseta
        self.g = g0 - 4
        for _ in range(10):
            self.col()
        for x in range(x_cara, x_cara + 7):
            for y in range(g0 - 3, g0):
                (self.falsos if x < x_cara + 2 else self.excavar).add((x, y))
        self.obj("portal", x_cara + 5, g0, destino=destino, secreto=True)
        self.detectores.append((x_cara, g0 - 3, 2, 3))
        self.reservado.update(range(x_cara - 4, x_cara + 10))
        self.slots_suelo.append((x_cara + 1, x_cara + 8, self.g))
        self.g = g0
        self.plano(4)

    def arena_jefe(self, jefe="craneo_gigante"):
        x0 = self.x
        self.g = max(self.g, 16)
        for i in range(24):
            self.techo_forzado[self.x] = -1
            self.col()
        self.plataformas += [(x0 + 4, self.g - 3, 3), (x0 + 17, self.g - 3, 3), (x0 + 10, self.g - 5, 4)]
        self.obj(jefe, x0 + 12, self.g - 7)
        self.obj("antorcha", x0 + 1, self.g)
        self.obj("antorcha", x0 + 22, self.g)
        self.reservado.update(range(x0, x0 + 24))

    # ---------------------------------------------------------- construcción
    def generar(self, ancho, pesos, destino, secreto=None, jefe_final=False):
        self.inicio()
        tipos = list(pesos)
        secreto_x = int(ancho * self.r.uniform(0.4, 0.6)) if secreto else None
        while self.x < ancho - (36 if jefe_final else 12):
            if secreto_x is not None and self.x >= secreto_x:
                self.muro_secreto(secreto)
                secreto_x = None
                continue
            seg = self.r.choices(tipos, weights=[pesos[t] for t in tipos])[0]
            getattr(self, seg)()
        self.fin(destino, jefe=jefe_final)
        return self

    def solidos(self):
        W = self.x
        sol = [[False] * W for _ in range(H)]
        # superficie más alta por columna (suelo o plataforma) para calcular el techo
        alto = [self.suelo[x] if not self.es_foso[x] else H for x in range(W)]
        for x in range(W):
            if self.es_foso[x]:
                vecinos = [self.suelo[i] for i in range(max(0, x - 6), min(W, x + 7)) if not self.es_foso[i]]
                alto[x] = min(vecinos) if vecinos else MAX_G
        for (px, py, w) in self.plataformas:
            for x in range(px, px + w):
                alto[x] = min(alto[x], py)
        c = self.r.randint(0, 2)
        for x in range(W):
            c = max(-1, min(3, c + self.r.choice([-1, 0, 0, 1])))
            techo = self.techo_forzado.get(x, min(c, alto[x] - 7))
            g = self.suelo[x]
            for y in range(H):
                if self.es_foso[x]:
                    s = y > FILA_LIQ
                else:
                    s = y >= g
                if y <= techo:
                    s = True
                sol[y][x] = s
        for (x, y) in self.excavar | self.pinchos:
            sol[y][x] = False
        self.sol = sol
        self.techo = [max([y for y in range(H) if y < self.suelo[x] and sol[y][x]] or [-1]) if not self.es_foso[x]
                      else max([y for y in range(FILA_LIQ) if sol[y][x]] or [-1]) for x in range(W)]
        return sol

    def autotile(self, x, y):
        W = self.x

        def s(i, j):
            if i < 0 or i >= W or j < 0 or j >= H:
                return True
            return self.sol[j][i]

        n, sd, o, e = s(x, y - 1), s(x, y + 1), s(x - 1, y), s(x + 1, y)
        if not n:
            if not sd:
                t = (4, 0) if (o and e) else (11, 1) if o else (9, 1) if e else (12, 0)
            else:
                t = (1, 0) if (o and e) else (2, 0) if o else (0, 0) if e else (12, 0)
        elif not sd:
            t = (1, 2) if (o and e) else (2, 2) if o else (0, 2) if e else (12, 2)
        else:
            if o and e:
                if not s(x + 1, y + 1):
                    t = (6, 0)
                elif not s(x - 1, y + 1):
                    t = (8, 0)
                elif not s(x + 1, y - 1):
                    t = (6, 2)
                elif not s(x - 1, y - 1):
                    t = (8, 2)
                else:
                    return RELLENO
            else:
                t = (2, 1) if o else (0, 1) if e else (12, 1)
        return (t[0], t[1] + self.dy_tiles)

    # ---------------------------------------------------------- capas
    def capas(self):
        W = self.x
        self.solidos()
        suelo, falsa, deco, fondo, liquidos, cascadas, peligros = {}, {}, {}, {}, {}, {}, {}
        for y in range(H):
            for x in range(W):
                if self.sol[y][x]:
                    t = self.autotile(x, y)
                    (falsa if (x, y) in self.falsos else suelo)[(x, y)] = (self.src_roca, t)
        fila_pl = 6 + (1 if self.dy_tiles else 0)
        for (px, py, w) in self.plataformas:
            for i in range(w):
                ax = 6 if i == 0 else 8 if i == w - 1 else 7
                suelo[(px + i, py)] = (self.src_roca, (ax, fila_pl))
        for (x, y) in self.pinchos:
            peligros[(x, y)] = (self.src_roca, (15 + (x % 2), 3))
        for x in range(W):
            if self.es_foso[x]:
                liquidos[(x, FILA_LIQ)] = (self.src_liq, LIQ_SUPERFICIE)
        for x in self.cascadas:
            arriba = self.techo[x] + 1
            for y in range(arriba, FILA_LIQ):
                t = CASCADA_ARRIBA if y == arriba else (CASCADA_MEDIO_A if (y - arriba) % 2 else CASCADA_MEDIO_B)
                cascadas[(x, y)] = (self.src_liq, t)
            liquidos[(x, FILA_LIQ)] = (self.src_liq, CASCADA_ABAJO)

        ocupado = set(suelo) | set(falsa) | set(peligros)
        for x in range(1, W - 2):
            if self.es_foso[x] or x in self.reservado:
                continue
            g = self.suelo[x]
            if self.r.random() < 0.16:
                sello = self.r.choice(DECO_SUELO)
                celdas = [(x + dx, g + dy) for dx, dy, _, _ in sello]
                if all(c not in ocupado and c not in deco and 0 <= c[0] < W and not self.es_foso[c[0]]
                       and self.suelo[c[0]] == g for c in celdas):
                    for dx, dy, ax, ay in sello:
                        deco[(x + dx, g + dy)] = (self.src_roca, (ax, ay))
            elif self.r.random() < 0.05 and g - self.techo[x] > 6:
                # columna de fondo del techo al suelo
                arriba = self.techo[x] + 1 if self.techo[x] >= 0 else g - 6
                for y in range(arriba, g):
                    t = (14, 3) if y == arriba else (14, 5) if y == g - 1 else (14, 4)
                    fondo[(x, y)] = (self.src_roca, t)
            elif self.r.random() < 0.04:
                sello = DECO_FONDO[0]
                if all(not self.es_foso[min(W - 1, x + dx)] and self.suelo[min(W - 1, x + dx)] == g for dx, *_ in sello):
                    for dx, dy, ax, ay in sello:
                        fondo[(x + dx, g + dy)] = (self.src_roca, (ax, ay))
        # Estalactitas bajo el techo
        for x in range(1, W - 1):
            c = self.techo[x]
            if c >= 0 and self.r.random() < 0.14:
                if all((x, c + k) not in ocupado and not self.sol[c + k][x] for k in (1, 2, 3)):
                    deco[(x, c + 1)] = (self.src_roca, (12, 7))
                    deco[(x, c + 2)] = (self.src_roca, (12, 8))
        # Las plataformas no deben tapar decoración
        for k in list(deco):
            if k in suelo:
                del deco[k]
        return dict(suelo=suelo, falsa=falsa, deco=deco, fondo=fondo,
                    liquidos=liquidos, cascadas=cascadas, peligros=peligros)

    # ---------------------------------------------------------- enemigos
    def poblar(self, suelo_tipos, aire_tipos, cantidad, obligatorios=()):
        W = self.x
        usados: list[int] = []

        def libre(x):
            return 12 <= x <= W - 10 and x not in self.reservado and all(abs(x - u) >= 6 for u in usados)

        candidatos = []
        for (x0, x1, fila) in self.slots_suelo:
            for x in range(x0, x1 + 1):
                candidatos.append(("suelo", x, fila))
        for (x, fila) in self.slots_aire:
            candidatos.append(("aire", x, fila))
        self.r.shuffle(candidatos)

        pendientes = list(obligatorios)
        restantes = cantidad
        for clase, x, fila in candidatos:
            if restantes <= 0 and not pendientes:
                break
            if not libre(x):
                continue
            tipos = suelo_tipos if clase == "suelo" else aire_tipos
            elegido = next((p for p in pendientes if p in tipos), None)
            if elegido:
                pendientes.remove(elegido)
            elif restantes > 0 and tipos:
                elegido = self.r.choice(tipos)
                restantes -= 1
            else:
                continue
            if elegido == "arquero" and clase == "suelo":
                largo = next((b - a for a, b, f in self.slots_suelo if a <= x <= b and f == fila), 0)
                if largo < 3:
                    continue
            self.obj(elegido, x, fila)
            usados.append(x)
        # antorchas
        x = 14
        while x < W - 12:
            x += self.r.randint(10, 18)
            if x < W and not self.es_foso[x] and x not in self.reservado and (x, self.suelo[x] - 1) not in self.pinchos:
                self.obj("antorcha", x, self.suelo[x])
        return self


# ---------------------------------------------------------------- escritura
def _datos_capa(celdas: dict) -> Raw:
    datos = bytearray(struct.pack("<H", 0))
    for (x, y), (src, (ax, ay)) in sorted(celdas.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        datos += struct.pack("<hhHHHH", x, y, src, ax, ay, 0)
    return Raw("PackedByteArray(" + ", ".join(str(b) for b in datos) + ")")


ESCENAS_OBJ = {
    "portal": f"{OBJ}/portal.tscn",
    "antorcha": f"{OBJ}/antorcha.tscn",
    **{n: f"{ENE}/{n}.tscn" for n in
       ["murcielago", "ojo_demoniaco", "mina_demoniaca", "craneo_llameante", "cabeza_demonio", "arquero", "craneo_gigante"]},
}
VOLADORES = {"murcielago", "ojo_demoniaco", "craneo_llameante", "cabeza_demonio", "craneo_gigante"}


def escribir_mapa(mapa: Mapa, res_path: str, nivel: int, nombre: str, oculto: bool, siguiente: str,
                  extras_fondo=None):
    capas = mapa.capas()
    if extras_fondo:
        capas["fondo"].update(extras_fondo)
    W = mapa.x
    doc = Documento()
    tileset = doc.ext_resource("TileSet", TILESET)
    script_mapa = doc.ext_resource("Script", f"{OBJ}/mapa.gd")
    script_peligro = doc.ext_resource("Script", f"{OBJ}/zona_peligro.gd")
    script_falsa = doc.ext_resource("Script", f"{OBJ}/pared_falsa.gd")
    script_cam = doc.ext_resource("Script", f"{OBJ}/camara_previa.gd")

    raiz = res_path.split("/")[-1].replace(".tscn", "")
    if "nivel_" in res_path:
        raiz = res_path.split("/")[-2] + "_" + raiz
    doc.nodo("".join(p.capitalize() for p in raiz.split("_")), "Node2D", props=[
        ("script", script_mapa), ("nivel", nivel), ("nombre_mapa", nombre),
        ("es_oculto", oculto), ("siguiente_escena", siguiente)])

    # Fondo parallax
    suf = "_oscuro" if mapa.oscuro else ""
    esc = 2.4
    doc.nodo("Fondo", "Node2D", ".", props=[("z_index", -10)])
    for nombre_capa, png, factor in [("Cielo", "cielo", 0.05), ("MontanasLejanas", "montanas_lejanas", 0.15),
                                     ("Montanas", "montanas", 0.3), ("Rocas", "rocas", 0.45)]:
        tex = doc.ext_resource("Texture2D", f"{TEX}/fondo_{png}{suf}.png")
        doc.nodo(nombre_capa, "Parallax2D", "Fondo", props=[
            ("scroll_scale", v2(factor, factor)), ("repeat_size", v2(1024 * esc, 0)), ("repeat_times", 4)])
        doc.nodo("Sprite2D", "Sprite2D", f"Fondo/{nombre_capa}", props=[
            ("texture", tex), ("centered", False), ("scale", v2(esc, esc))])

    def capa(nombre_nodo, celdas, extra=()):
        doc.nodo(nombre_nodo, "TileMapLayer", ".", props=[
            *extra, ("tile_map_data", _datos_capa(celdas)), ("tile_set", tileset)])

    capa("FondoDecoracion", capas["fondo"], [("modulate", color(0.55, 0.42, 0.42))])
    capa("Cascadas", capas["cascadas"], [("modulate", color(0.8, 0.8, 0.8))])
    capa("Suelo", capas["suelo"])
    capa("Decoracion", capas["deco"])
    capa("Peligros", capas["peligros"])

    # Objetos y enemigos
    doc.nodo("Enemigos", "Node2D", ".")
    doc.nodo("Objetos", "Node2D", ".")
    contadores: dict[str, int] = {}
    spawn = (3 * T + 16, 17 * T)
    for o in mapa.objetos:
        tipo = o["tipo"]
        px = o["x"] * T + 16
        py = o["fila"] * T
        if tipo == "spawn":
            spawn = (px, py)
            continue
        if tipo == "recompensa":
            # Punto reservado para el premio de la zona oculta (cofre, reliquia, mejora...)
            doc.nodo("Recompensa", "Marker2D", "Objetos", props=[("position", v2(px, py))], grupos=["recompensa"])
            continue
        if tipo == "mina_demoniaca":
            py -= 28
        elif tipo in VOLADORES:
            py += 16
        contadores[tipo] = contadores.get(tipo, 0) + 1
        nombre_nodo = f"{tipo.title().replace('_', '')}{contadores[tipo]}"
        padre = "Objetos" if tipo in ("portal", "antorcha") else "Enemigos"
        props = [("position", v2(px, py))]
        if tipo == "portal":
            props += [("escena_destino", o["destino"]), ("es_secreto", o["secreto"])]
            if o["secreto"]:
                nombre_nodo = f"PortalSecreto{contadores[tipo]}"
        if tipo == "antorcha" and mapa.oscuro:
            props.append(("modulate", color(0.8, 0.8, 1.0)))
        doc.nodo(nombre_nodo, None, padre, instancia=doc.ext_resource("PackedScene", ESCENAS_OBJ[tipo]), props=props)

    capa("Liquidos", capas["liquidos"])

    # Zonas de peligro (lava/sangre mortal, pinchos dañan)
    doc.nodo("ZonasPeligro", "Node2D", ".")
    n = 0
    for zona in _tramos({x for (x, y) in capas["liquidos"]}):
        n += 1
        x0, x1 = zona
        forma = doc.sub_resource("RectangleShape2D", [("size", v2((x1 - x0 + 1) * T, T * 2 - 10))])
        doc.nodo(f"Liquido{n}", "Area2D", "ZonasPeligro", props=[
            ("position", v2((x0 + x1 + 1) * T / 2, FILA_LIQ * T + 10 + (T * 2 - 10) / 2)),
            ("collision_layer", 8), ("collision_mask", 2), ("script", script_peligro), ("mortal", True)])
        doc.nodo("CollisionShape2D", "CollisionShape2D", f"ZonasPeligro/Liquido{n}", props=[("shape", forma)])
    filas = {}
    for (x, y) in mapa.pinchos:
        filas.setdefault(y, set()).add(x)
    for y, xs in sorted(filas.items()):
        for x0, x1 in _tramos(xs):
            n += 1
            forma = doc.sub_resource("RectangleShape2D", [("size", v2((x1 - x0 + 1) * T - 4, 16))])
            doc.nodo(f"Pinchos{n}", "Area2D", "ZonasPeligro", props=[
                ("position", v2((x0 + x1 + 1) * T / 2, y * T + 24)),
                ("collision_layer", 8), ("collision_mask", 2), ("script", script_peligro),
                ("mortal", False), ("dano", 1)])
            doc.nodo("CollisionShape2D", "CollisionShape2D", f"ZonasPeligro/Pinchos{n}", props=[("shape", forma)])

    # Paredes falsas (sin colisión, se revelan al entrar)
    doc.nodo("ParedesFalsas", "TileMapLayer", ".", props=[
        ("tile_map_data", _datos_capa(capas["falsa"])), ("tile_set", tileset),
        ("collision_enabled", False), ("script", script_falsa)])
    doc.nodo("Detector", "Area2D", "ParedesFalsas", props=[("collision_layer", 0), ("collision_mask", 2)])
    for i, (x, y, w, h) in enumerate(mapa.detectores or [(0, 0, 0, 0)]):
        forma = doc.sub_resource("RectangleShape2D", [("size", v2(max(w, 1) * T, max(h, 1) * T))])
        doc.nodo(f"Forma{i + 1}", "CollisionShape2D", "ParedesFalsas/Detector", props=[
            ("position", v2((x + w / 2) * T, (y + h / 2) * T)), ("shape", forma), ("disabled", not mapa.detectores)])

    doc.nodo("SpawnJugador", "Marker2D", ".", props=[("position", v2(*spawn))], grupos=["spawn"])
    doc.nodo("CamaraPrevia", "Camera2D", ".", props=[
        ("position", v2(spawn[0] + 200, spawn[1] - 100)), ("script", script_cam),
        ("limit_left", 0), ("limit_top", 0), ("limit_right", W * T), ("limit_bottom", H * T)])

    doc.guardar(ruta(res_path))
    return capas


def _tramos(xs):
    xs = sorted(xs)
    tramos = []
    for x in xs:
        if tramos and x == tramos[-1][1] + 1:
            tramos[-1][1] = x
        else:
            tramos.append([x, x])
    return [tuple(t) for t in tramos]


# ---------------------------------------------------------------- zona oculta
def zona_oculta(semilla, destino, contenido, liquido="sangre"):
    """Arena secreta: charcos de sangre, bloques de carne, recompensa y enemigos especiales."""
    m = Mapa(semilla, oscuro=True, liquido=liquido)
    m.g = 17
    m.inicio()
    m.plano(5)
    for _ in range(4):
        m.col(foso=True)
    m.plano(6)
    x_centro = m.x
    for i in range(12):
        m.techo_forzado[m.x] = -1
        m.col()
    m.slots_suelo.append((x_centro + 1, x_centro + 10, m.g))
    m.plataformas += [(x_centro + 1, m.g - 3, 3), (x_centro + 8, m.g - 3, 3), (x_centro + 4, m.g - 5, 4)]
    m.obj("antorcha", x_centro + 5, m.g - 5)
    m.obj("antorcha", x_centro + 7, m.g - 5)
    m.objetos.append(dict(tipo="recompensa", x=x_centro + 6, fila=m.g - 5))
    m.plano(5)
    for _ in range(4):
        m.col(foso=True)
    m.plano(4)
    m.reservado.update(range(x_centro - 1, x_centro + 13))
    m.fin(destino)
    for tipo, (dx, df) in contenido:
        m.obj(tipo, x_centro + dx, m.g + df)
    # Columnas caídas de fondo a ambos lados de la arena
    fondo = {}
    for bx in (x_centro - 4, x_centro + 13):
        for dx, dy, ax, ay in DECO_FONDO[0]:
            fondo[(bx + dx, m.g + dy)] = (m.src_roca, (ax, ay))
    return m, fondo
