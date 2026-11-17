"""Repara shapefiles del INE con anillos de polígono sin cerrar.

Algunas capas publicadas en https://pautas.ine.mx/transparencia/mapas/
traen anillos cuyo último vértice difiere del primero por ~1e-9 a 1e-4 m
(redondeo de coordenadas en la exportación). GEOS/pyogrio (engine por
defecto de geopandas) exige cierre exacto y lanza:

    IllegalArgumentException: Points of LinearRing do not form a
    closed linestring

Este módulo detecta esos registros a nivel binario y copia el primer
vértice sobre el último (parche de 16 bytes por anillo; el tamaño del
archivo y el índice .shx no cambian). Casos conocidos en 2019/2020:
ENTIDAD (Tlaxcala) y SECCION.

Los shapefiles reparados viven en data/interim/ine_maps/{year}/ tras
extraer los zips descargados en data/raw/ine_maps/{year}/.

Uso:
    from partciud.repair_shp import INTERIM_INE_MAPS_FOLDER, repair
    repair(INTERIM_INE_MAPS_FOLDER)               # repara todo interim
    repair(INTERIM_INE_MAPS_FOLDER, check_only=True)  # solo reporta
    repair(Path("data/interim/ine_maps/2019"))    # una carpeta concreta
"""

from datetime import datetime
from pathlib import Path
import shutil
import struct

import numpy as np

from partciud.config import DATA_FOLDER

# Tipos de geometría con anillos: Polygon, PolygonZ, PolygonM, MultiPatch
POLYGON_TYPES = {5, 15, 25, 31}
SHP_HEADER = 100

def find_unclosed_rings(data: bytes | bytearray) -> list[tuple[int, int, int]]:
    """Devuelve [(byte_offset_ultimo_punto, off_primero, npts), ...]."""
    unclosed = []
    pos = SHP_HEADER
    while pos + 8 <= len(data):
        content_len = struct.unpack(">i", data[pos + 4 : pos + 8])[0] * 2
        shape_type = struct.unpack("<i", data[pos + 8 : pos + 12])[0]
        if shape_type in POLYGON_TYPES:
            num_parts, num_points = struct.unpack(
                "<ii", data[pos + 44 : pos + 52]
            )
            parts = np.frombuffer(
                data, dtype="<i4", count=num_parts, offset=pos + 52
            )
            pts_off = pos + 52 + 4 * num_parts
            pts = np.frombuffer(
                data, dtype="<f8", count=2 * num_points, offset=pts_off
            ).reshape(-1, 2)
            ends = np.append(parts[1:], num_points)
            for i in range(num_parts):
                s, e = parts[i], ends[i]
                if e - s >= 4 and not np.array_equal(pts[s], pts[e - 1]):
                    unclosed.append(
                        (pts_off + 16 * (e - 1), pts_off + 16 * s, e - s)
                    )
        pos += 8 + content_len
    return unclosed


def repair_file(shp: Path, check_only: bool = False) -> tuple[int, Path | None]:
    """Repara los anillos abiertos de un .shp.

    Devuelve (n_anillos_abiertos, backup); backup es None si no se
    modificó el archivo (sin problemas o check_only=True).
    """
    data = bytearray(shp.read_bytes())
    unclosed = find_unclosed_rings(data)
    if not unclosed or check_only:
        return len(unclosed), None

    backup = shp.with_suffix(
        shp.suffix + "." + datetime.now().strftime("%Y%m%d%H%M%S") + ".bak"
    )
    shutil.copy2(shp, backup)
    for last_off, first_off, _ in unclosed:
        data[last_off : last_off + 16] = data[first_off : first_off + 16]
    shp.write_bytes(data)
    return len(unclosed), backup


def repair(root: Path, check_only: bool = False) -> int:
    """Repara todos los .shp dentro de `root`, en cualquier subcarpeta.

    Acepta una carpeta de año (interim/ine_maps/2019), la raíz de mapas
    (interim/ine_maps) o cualquier directorio con shapefiles. Crea un
    respaldo .bak junto a cada archivo modificado. Devuelve el total de
    anillos reparados (o encontrados, si check_only=True).
    """
    shp_files = sorted(root.rglob("*.shp")) + sorted(root.rglob("*.SHP"))
    if not shp_files:
        print(f"No hay shapefiles en {root}")
        return 0

    total = 0
    for shp in shp_files:
        stem = shp.with_suffix("")
        missing = [
            ext
            for ext in (".dbf", ".shx")
            if not stem.with_suffix(ext).exists()
            and not stem.with_suffix(ext.upper()).exists()
        ]
        if missing:
            print(f"ERROR  {shp.relative_to(root)}: faltan {missing}")
            continue

        n, backup = repair_file(shp, check_only)
        if n:
            total += n
            tag = "ABIERTOS" if check_only else "REPARADO"
            extra = f" (respaldo: {backup.name})" if backup else ""
            print(f"{tag}  {shp.relative_to(root)}: {n} anillos{extra}")

    if total == 0:
        print("Todos los shapefiles están correctos.")
    elif check_only:
        print(f"\n{total} anillos abiertos encontrados (sin modificar).")
    else:
        print(f"\n{total} anillos reparados.")
    return total


