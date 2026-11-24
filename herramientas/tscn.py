"""Utilidades mínimas para escribir escenas (.tscn) y recursos (.tres) de Godot 4 en texto."""
from __future__ import annotations


def fmt(v) -> str:
    """Convierte un valor de Python a la sintaxis de Godot."""
    if isinstance(v, Raw):
        return v.texto
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        s = repr(round(v, 4))
        return s if ("." in s or "e" in s) else s + ".0"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(f"Tipo no soportado: {type(v)}")


class Raw:
    """Texto que se escribe tal cual (Vector2(...), ExtResource(...), etc.)."""

    def __init__(self, texto: str):
        self.texto = texto

    def __repr__(self):
        return self.texto


def v2(x, y) -> Raw:
    return Raw(f"Vector2({fmt(float(x))}, {fmt(float(y))})")


def v2i(x, y) -> Raw:
    return Raw(f"Vector2i({int(x)}, {int(y)})")


def color(r, g, b, a=1.0) -> Raw:
    return Raw(f"Color({fmt(float(r))}, {fmt(float(g))}, {fmt(float(b))}, {fmt(float(a))})")


def sname(s: str) -> Raw:
    return Raw(f'&"{s}"')


def puntos(lista) -> Raw:
    return Raw("PackedVector2Array(" + ", ".join(fmt(float(p)) for p in lista) + ")")


class Documento:
    """Escena o recurso en formato de texto de Godot 4 (format=3)."""

    def __init__(self, tipo_recurso: str | None = None):
        # tipo_recurso = None -> .tscn ; "TileSet" etc. -> .tres
        self.tipo_recurso = tipo_recurso
        self.ext: list[tuple[str, str, str]] = []  # (tipo, path, id)
        self._ext_por_path: dict[str, str] = {}
        self.subs: list[tuple[str, str, list]] = []  # (tipo, id, props)
        self.nodos: list[tuple[str, list]] = []  # (cabecera, props)
        self.recurso: list = []
        self._n = 0

    def ext_resource(self, tipo: str, path: str) -> Raw:
        if path not in self._ext_por_path:
            self._n += 1
            rid = f"{self._n}_r"
            self.ext.append((tipo, path, rid))
            self._ext_por_path[path] = rid
        return Raw(f'ExtResource("{self._ext_por_path[path]}")')

    def sub_resource(self, tipo: str, props: list, prefijo: str | None = None) -> Raw:
        self._n += 1
        rid = f"{prefijo or tipo}_{self._n}"
        self.subs.append((tipo, rid, props))
        return Raw(f'SubResource("{rid}")')

    def nodo(self, nombre: str, tipo: str | None = None, padre: str | None = None,
             instancia: Raw | None = None, props: list | None = None, grupos: list | None = None):
        cab = f'[node name="{nombre}"'
        if tipo:
            cab += f' type="{tipo}"'
        if padre is not None:
            cab += f' parent="{padre}"'
        if instancia is not None:
            cab += f" instance={instancia.texto}"
        if grupos:
            cab += " groups=[" + ", ".join(fmt(g) for g in grupos) + "]"
        cab += "]"
        self.nodos.append((cab, props or []))

    def texto(self) -> str:
        out = []
        if self.tipo_recurso:
            out.append(f'[gd_resource type="{self.tipo_recurso}" format=3]\n')
        else:
            out.append("[gd_scene format=3]\n")
        for tipo, path, rid in self.ext:
            out.append(f'[ext_resource type="{tipo}" path="{path}" id="{rid}"]')
        if self.ext:
            out.append("")
        for tipo, rid, props in self.subs:
            out.append(f'[sub_resource type="{tipo}" id="{rid}"]')
            out.extend(_props(props))
            out.append("")
        for cab, props in self.nodos:
            out.append(cab)
            out.extend(_props(props))
            out.append("")
        if self.tipo_recurso:
            out.append("[resource]")
            out.extend(_props(self.recurso))
            out.append("")
        return "\n".join(out)

    def guardar(self, ruta: str):
        with open(ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.texto())


def _props(props):
    return [f"{k} = {fmt(v)}" for k, v in props]


def sprite_frames(doc: Documento, animaciones: list[dict]) -> Raw:
    """animaciones: [{nombre, texturas:[Raw], fps, loop}]"""
    partes = []
    for a in animaciones:
        frames = ",\n".join(
            '{\n"duration": 1.0,\n"texture": ' + t.texto + "\n}" for t in a["texturas"]
        )
        partes.append(
            "{\n\"frames\": [" + frames + "],\n"
            f"\"loop\": {fmt(a['loop'])},\n"
            f"\"name\": &\"{a['nombre']}\",\n"
            f"\"speed\": {fmt(float(a['fps']))}\n}}"
        )
    return doc.sub_resource("SpriteFrames", [("animations", Raw("[" + ", ".join(partes) + "]"))])
