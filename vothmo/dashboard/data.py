"""Cargadores de los datos tidy del proyecto y tablas derivadas.

Todas las funciones están memoizadas con ``lru_cache``: el tablero Dash y el
de Streamlit comparten el mismo proceso ligero de carga sin duplicar lecturas.

Caveats heredados del pipeline (ver AGENTS.md):

- ``conteos_sonora.csv.gz`` usa la clave municipal del INE (columna
  ``mpiocve`` = ``mun_ine``); para cruzar con INEGI/CONAPO hay que pasar por
  ``mun_ine_inegi.csv``.
- ``pad`` (cartografía) ≠ ``ln`` (conteo censal electoral).
- ``lns`` = sv + nv (personas con dato de votación); ``pc`` = sv / lns.
"""

from functools import lru_cache
import json
import math

import geopandas as gpd
import pandas as pd

from vothmo.config import FOLDER_DATA

PROCESSED = FOLDER_DATA / "processed"

CENTRO_SONORA = {"lat": 29.3, "lon": -110.9}
MAP_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

ETIQUETA_SEXO = {0: "Hombres", 1: "Mujeres", 2: "No binario"}
COLOR_SEXO = {"Hombres": "#4C78A8", "Mujeres": "#E45756", "No binario": "#72B7B2"}
COLOR_ESCENARIO = {"base": "#1f77b4", "bajo": "#d62728", "alto": "#2ca02c"}

SIGNO_SEXO = {0: -1, 1: 1, 2: 0.01}  # espejo para pirámides


def mapa_para_anio(anio: int) -> int:
    """Año de cartografía más cercano al año electoral pedido."""
    return min(MAP_YEARS, key=lambda y: abs(y - anio))


def geojson_ligero(gdf: gpd.GeoDataFrame) -> dict:
    """GeoJSON con solo geometría e id (los atributos van en los datos)."""
    feats = json.loads(gdf.to_json())["features"]
    for i, f in enumerate(feats):
        f["id"] = i
        f["properties"] = {}
    return {"type": "FeatureCollection", "features": feats}


# ---------------------------------------------------------------- conteos
@lru_cache(maxsize=1)
def conteos() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "conteos_sonora.csv.gz")


@lru_cache(maxsize=1)
def anios_elec() -> list[int]:
    return sorted(conteos()["aelec"].unique().tolist())


@lru_cache(maxsize=1)
def resumen_anual() -> pd.DataFrame:
    """Lista nominal y participación estatal por elección."""
    r = (
        conteos()
        .groupby("aelec", as_index=False)
        .agg(ln=("ln", "sum"), sv=("sv", "sum"), nv=("nv", "sum"), lns=("lns", "sum"))
    )
    r["pc"] = r["sv"] / r["lns"] * 100
    return r


@lru_cache(maxsize=8)
def piramide(anio: int) -> pd.DataFrame:
    """Lista nominal y votos por edad y sexo para una elección."""
    p = (
        conteos()[conteos()["aelec"] == anio]
        .groupby(["sexo", "edad"], as_index=False)[["ln", "sv"]]
        .sum()
    )
    p["sexo_txt"] = p["sexo"].map(ETIQUETA_SEXO)
    p["ln_neg"] = p["ln"] * p["sexo"].map(SIGNO_SEXO)
    p["sv_neg"] = p["sv"] * p["sexo"].map(SIGNO_SEXO)
    return p


@lru_cache(maxsize=32)
def piramide_zona(anio: int, mpiocves=()) -> pd.DataFrame:
    """Lista nominal y votos por edad y sexo de la zona para una elección.

    ``mpiocves`` vacío → todo el estado; si no, claves municipales INEGI
    (ver ``zona_cvess``).
    """
    cvess = zona_cvess(mpiocves)
    d = conteos_inegi()[conteos_inegi()["aelec"] == anio]
    if cvess:
        d = d[d["mpiocve"].isin(cvess)]
    p = d.groupby(["sexo", "edad"], as_index=False)[["ln", "sv"]].sum()
    p["sexo_txt"] = p["sexo"].map(ETIQUETA_SEXO)
    p["ln_neg"] = p["ln"] * p["sexo"].map(SIGNO_SEXO)
    p["sv_neg"] = p["sv"] * p["sexo"].map(SIGNO_SEXO)
    return p


@lru_cache(maxsize=8)
def participacion_edad(anio: int) -> pd.DataFrame:
    """Participación (sv/lns) por edad y sexo para una elección."""
    d = conteos()[(conteos()["aelec"] == anio) & (conteos()["lns"] > 0)]
    p = d.groupby(["edad", "sexo"], as_index=False).agg(sv=("sv", "sum"), lns=("lns", "sum"))
    p["pc"] = p["sv"] / p["lns"] * 100
    p["sexo_txt"] = p["sexo"].map(ETIQUETA_SEXO)
    return p


def _agrega(df: pd.DataFrame, llave: str) -> pd.DataFrame:
    out = df.groupby(llave, as_index=False).agg(
        ln=("ln", "sum"), sv=("sv", "sum"), lns=("lns", "sum")
    )
    out["pc"] = out["sv"] / out["lns"] * 100
    muj = df[df["sexo"] == 1].groupby(llave)["lns"].sum().rename("lns_muj").reset_index()
    out = out.merge(muj, on=llave, how="left")
    out["pct_muj"] = out["lns_muj"] / out["lns"] * 100
    return out


@lru_cache(maxsize=8)
def por_distrito(anio: int) -> pd.DataFrame:
    """Indicadores electorales por distrito local (``del``)."""
    d = conteos()[conteos()["aelec"] == anio].dropna(subset=["del"]).copy()
    d["del"] = d["del"].astype(int)
    return _agrega(d, "del").rename(columns={"del": "distrito_l"})


@lru_cache(maxsize=8)
def por_municipio(anio: int) -> pd.DataFrame:
    """Indicadores electorales por municipio (catálogo INE)."""
    d = conteos()[conteos()["aelec"] == anio]
    out = _agrega(d, "mpionom").sort_values("ln", ascending=False)
    return out


@lru_cache(maxsize=1)
def mun_puente() -> pd.DataFrame:
    """Puente entre el catálogo municipal del INE (``mun_ine``) y el INEGI (``mpiocve``)."""
    return pd.read_csv(PROCESSED / "mun_ine_inegi.csv")


@lru_cache(maxsize=1)
def conteos_inegi() -> pd.DataFrame:
    """Conteos censales con la clave municipal **INEGI** (``mpiocve``).

    En ``conteos`` la columna ``mpiocve`` es en realidad la clave INE
    (``mun_ine``); aquí se traduce con ``mun_ine_inegi.csv``.
    """
    c = conteos().rename(columns={"mpiocve": "mun_ine"})
    return c.merge(mun_puente()[["mun_ine", "mpiocve"]], on="mun_ine", how="left")


# ---------------------------------------------------------------- geo
@lru_cache(maxsize=8)
def distritos_geo(anio: int) -> gpd.GeoDataFrame:
    """Distritos locales (capa simplificada) con indicadores electorales."""
    g = gpd.read_file(PROCESSED / f"distritos_simp_{mapa_para_anio(anio)}.gpkg")
    g = g.drop(columns=["ln", "pad"])  # la capa trae sus propios conteos cartográficos
    return g.merge(por_distrito(anio), on="distrito_l", how="left").reset_index(drop=True)


@lru_cache(maxsize=80)
def secciones_geo(anio: int, mpiocves=()) -> gpd.GeoDataFrame:
    """Secciones electorales (capa simplificada) del año de cartografía.

    ``mpiocves`` vacío → todo el estado; si no, solo las secciones de los
    municipios INEGI elegidos (ver ``zona_cvess``).
    """
    g = gpd.read_file(PROCESSED / f"secciones_simp_{mapa_para_anio(anio)}.gpkg")
    cvess = zona_cvess(mpiocves)
    return g[g["mpiocve"].isin(cvess)] if cvess else g


@lru_cache(maxsize=1)
def municipios_borde() -> gpd.GeoDataFrame:
    """Geometrías municipales para dibujar bordes sobre el mapa seccional."""
    return gpd.read_file(PROCESSED / "municipios_simp.gpkg")[["mpiocve", "nom_mun", "geometry"]]


@lru_cache(maxsize=8)
def municipios_geo(anio: int = 2025) -> gpd.GeoDataFrame:
    """Municipios (capa simplificada) con razón pad/18+ del año pedido."""
    g = gpd.read_file(PROCESSED / "municipios_simp.gpkg")
    sel = razon_mun(anio)[["mpiocve", "pad", "pob", "pob18", "razon_total", "razon_18"]]
    return g.drop(columns=["ln_2024", "pad_2024"]).merge(sel, on="mpiocve", how="left")


@lru_cache(maxsize=8)
def pc_mun_anio(anio: int) -> pd.DataFrame:
    """Participación (``sv``/``lns``) por municipio INEGI para una elección."""
    c = conteos_inegi()[conteos_inegi()["aelec"] == anio]
    g = c.groupby("mpiocve", as_index=False).agg(sv=("sv", "sum"), lns=("lns", "sum"))
    g["pc"] = g["sv"] / g["lns"] * 100
    return g


@lru_cache(maxsize=8)
def municipios_pc_geo(anio: int) -> gpd.GeoDataFrame:
    """Municipios (capa simplificada) con la participación de la elección."""
    return municipios_borde().merge(pc_mun_anio(anio), on="mpiocve", how="left")


@lru_cache(maxsize=80)
def centro_zona(mpiocves) -> dict | None:
    """Centro y zoom del mapa para la zona; ``None`` si es todo el estado.

    Punto representativo de la unión de los municipios elegidos y zoom
    derivado del tamaño de su *bounding box* (ver ``zona_cvess``).
    """
    cvess = zona_cvess(mpiocves)
    if not cvess:
        return None
    sel = municipios_borde()[municipios_borde()["mpiocve"].isin(cvess)]
    p = sel.geometry.union_all().representative_point()
    minx, miny, maxx, maxy = sel.total_bounds
    span = max(maxy - miny, maxx - minx)
    zoom = min(9.5, max(5.5, math.log2(360 / span)))
    return {"lat": p.y, "lon": p.x, "zoom": float(zoom)}


@lru_cache(maxsize=1)
def pad_sec() -> pd.DataFrame:
    """Padrón y lista nominal por sección y año de cartografía (atributos)."""
    cols = ["anio", "seccion", "municipio", "mpiocve", "nom_mun", "distrito_l", "pad", "ln"]
    return pd.concat(
        [
            gpd.read_file(PROCESSED / f"secciones_simp_{y}.gpkg", ignore_geometry=True).assign(
                anio=y
            )
            for y in MAP_YEARS
        ],
        ignore_index=True,
    )[cols]


@lru_cache(maxsize=1)
def padron_anual() -> pd.DataFrame:
    """Padrón cartográfico y LN por año, más el LN de los conteos electorales."""
    pad = pad_sec().groupby("anio", as_index=False)[["pad", "ln"]].sum()
    ln = (
        conteos()
        .groupby("aelec", as_index=False)["ln"]
        .sum()
        .rename(columns={"aelec": "anio", "ln": "ln_conteo"})
    )
    return pad, ln


# ------------------------------------------------------- población (INEGI/CONAPO)
@lru_cache(maxsize=1)
def inegi() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "censo_inegi_municipios.csv")


@lru_cache(maxsize=1)
def inegi_estado() -> pd.DataFrame:
    return (
        inegi()
        .groupby("anio", as_index=False)
        .agg(pob=("pobtot", "sum"), pob18=("p_18ymas", "sum"))
    )


@lru_cache(maxsize=1)
def _conapo() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "conapo_sonora.csv")


@lru_cache(maxsize=1)
def conapo_mun() -> pd.DataFrame:
    return _conapo().groupby(["mpiocve", "nom_mun", "anio"], as_index=False).agg(
        pob=("pob_total", "sum"), pob18=("pob_18mas", "sum")
    )


@lru_cache(maxsize=1)
def conapo_estado() -> pd.DataFrame:
    return conapo_mun().groupby("anio", as_index=False)[["pob", "pob18"]].sum()


@lru_cache(maxsize=1)
def municipios() -> pd.DataFrame:
    """Catálogo municipal INEGI ordenado por nombre (``mpiocve``, ``nom_mun``)."""
    return (
        conapo_mun()[["mpiocve", "nom_mun"]]
        .drop_duplicates()
        .sort_values("nom_mun")
        .reset_index(drop=True)
    )


def zona_cvess(mpio) -> tuple[int, ...]:
    """Normaliza la zona de interés: ``()`` = todo el estado; si no, claves INEGI.

    Acepta entero, lista o tupla; ignora el centinela ``0`` («Sonora»).
    La tupla ordenada es hashable para que sirva de llave a ``lru_cache``.
    """
    if mpio is None:
        return ()
    try:
        it = iter(mpio)
    except TypeError:
        return (int(mpio),) if mpio else ()
    return tuple(sorted({int(v) for v in it if v}))


def nombre_zona(mpiocves) -> str:
    """Nombre de la zona: ``Sonora`` si está vacía; si no, los municipios."""
    cvess = zona_cvess(mpiocves)
    if not cvess:
        return "Sonora"
    if len(cvess) > 3:
        return f"{len(cvess)} municipios"
    noms = municipios().set_index("mpiocve")["nom_mun"]
    return ", ".join(str(noms.loc[c]) for c in cvess)


@lru_cache(maxsize=80)
def elec_zona(mpiocves=()) -> pd.DataFrame:
    """Serie electoral de la zona: `ln`/`sv`/`lns`/`pc` por elección.

    ``mpiocves`` vacío → todo el estado; si no, claves municipales INEGI
    (ver ``zona_cvess``). Usa el puente `mun_ine` → `mpiocve`.
    """
    cvess = zona_cvess(mpiocves)
    c = conteos_inegi()
    if cvess:
        c = c[c["mpiocve"].isin(cvess)]
    e = c.groupby("aelec", as_index=False).agg(
        ln=("ln", "sum"), sv=("sv", "sum"), lns=("lns", "sum")
    )
    e["pc"] = e["sv"] / e["lns"] * 100
    return e


@lru_cache(maxsize=1)
def pad_mun() -> pd.DataFrame:
    """Padrón cartográfico por municipio INEGI y año de cartografía."""
    return pad_sec().groupby(["anio", "mpiocve"], as_index=False)["pad"].sum()


@lru_cache(maxsize=80)
def pad_ln_dl(anio: int, mpiocves=()) -> pd.DataFrame:
    """Padrón y lista nominal cartográficos por distrito local y año.

    ``mpiocves`` vacío → todo el estado; si no, solo las secciones de los
    municipios elegidos (ver ``zona_cvess``).
    """
    ps = pad_sec()[pad_sec()["anio"] == anio]
    cvess = zona_cvess(mpiocves)
    if cvess:
        ps = ps[ps["mpiocve"].isin(cvess)]
    return (
        ps.groupby("distrito_l", as_index=False)
        .agg(pad=("pad", "sum"), ln=("ln", "sum"))
        .sort_values("ln", ascending=False)
    )


@lru_cache(maxsize=16)
def razon_mun(anio: int) -> pd.DataFrame:
    """Razón padrón/población por municipio para un año de cartografía."""
    pad = pad_mun()[pad_mun()["anio"] == anio]
    pob = conapo_mun()[conapo_mun()["anio"] == anio]
    cmp_ = pad.merge(pob, on="mpiocve", how="left")
    cmp_["razon_total"] = cmp_["pad"] / cmp_["pob"]
    cmp_["razon_18"] = cmp_["pad"] / cmp_["pob18"]
    return cmp_


@lru_cache(maxsize=1)
def razon_estado() -> pd.DataFrame:
    """Proporción empadronada estatal por año de cartografía."""
    cmp_ = pad_mun().merge(conapo_mun(), on=["mpiocve", "anio"], how="left")
    e = cmp_.groupby("anio", as_index=False).agg(
        pad=("pad", "sum"), pob=("pob", "sum"), pob18=("pob18", "sum")
    )
    e["razon_total"] = e["pad"] / e["pob"]
    e["razon_18"] = e["pad"] / e["pob18"]
    return e


@lru_cache(maxsize=8)
def municipios_de_distrito(anio: int) -> dict[int, str]:
    """Listado de municipios por distrito para el hover del mapa seccional.

    Municipios con todas sus secciones en un solo distrito van en texto normal;
    los repartidos entre distritos se marcan en cursiva (``<i>``).
    """
    ps = pad_sec()[pad_sec()["anio"] == mapa_para_anio(anio)]
    n_dl = ps.groupby("nom_mun")["distrito_l"].nunique()
    return {
        dl: "<br>".join(f"<i>{m}</i>" if n_dl[m] > 1 else m for m in sorted(g["nom_mun"].unique()))
        for dl, g in ps.groupby("distrito_l")
    }


@lru_cache(maxsize=32)
def transiciones_distrito(a0: int, a1: int) -> pd.DataFrame:
    """Movimiento de secciones entre distritos locales de dos años de cartografía.

    Una fila por par (distrito en `a0`, distrito en `a1`) con el número de
    secciones `n` y el `pad`/`ln` que cargaban en `a0`. Solo incluye secciones
    presentes en ambos años.
    """
    ps = pad_sec()
    j = (
        ps[ps["anio"] == a0][["seccion", "distrito_l", "pad", "ln"]]
        .rename(columns={"distrito_l": "dl0"})
        .merge(
            ps[ps["anio"] == a1][["seccion", "distrito_l"]].rename(columns={"distrito_l": "dl1"}),
            on="seccion",
        )
    )
    return j.groupby(["dl0", "dl1"], as_index=False).agg(
        n=("seccion", "size"), pad=("pad", "sum"), ln=("ln", "sum")
    )


@lru_cache(maxsize=1)
def efecto_redistrito() -> pd.DataFrame:
    """Pad/ln/pob18 por distrito: serie real vs contrafactual geografía 2019.

    La contrafactual conserva la asignación sección → distrito de 2019 para
    todos los años; la diferencia ``*_delta`` es el cambio atribuible a la
    redistritación (reseccionamiento), no al crecimiento real. Caveats: las
    secciones creadas después de 2019 no tienen distrito contrafactual y ``pob18``
    se aproxima repartiendo la población 18+ municipal con pesos de `pad`.
    """
    ps = pad_sec()
    base = ps[ps["anio"] == 2019][["seccion", "distrito_l"]].rename(columns={"distrito_l": "dl0"})
    pob = conapo_mun()[["mpiocve", "anio", "pob18"]]
    d = ps.merge(pob, on=["mpiocve", "anio"], how="left")
    d["pad_mun"] = d.groupby(["anio", "mpiocve"])["pad"].transform("sum")
    d["pob18"] = d["pob18"] * d["pad"] / d["pad_mun"]
    d = d.merge(base, on="seccion", how="inner")

    real = d.groupby(["anio", "distrito_l"], as_index=False).agg(
        pad=("pad", "sum"), ln=("ln", "sum"), pob18=("pob18", "sum")
    )
    cf = (
        d.groupby(["anio", "dl0"], as_index=False)
        .agg(pad_cf=("pad", "sum"), ln_cf=("ln", "sum"), pob18_cf=("pob18", "sum"))
        .rename(columns={"dl0": "distrito_l"})
    )
    m = real.merge(cf, on=["anio", "distrito_l"])
    for c in ["pad", "ln", "pob18"]:
        m[f"{c}_delta"] = m[c] - m[f"{c}_cf"]
    return m


# ---------------------------------------------------------------- escenarios
@lru_cache(maxsize=1)
def escenarios() -> dict[str, pd.DataFrame]:
    return {
        "padron_dl": pd.read_csv(PROCESSED / "escenarios_padron_dl.csv"),
        "padron_mun": pd.read_csv(PROCESSED / "escenarios_padron_mun.csv"),
        "poblacion_dl": pd.read_csv(PROCESSED / "escenarios_poblacion_dl.csv"),
        "poblacion_mun": pd.read_csv(PROCESSED / "escenarios_poblacion_mun.csv"),
    }


@lru_cache(maxsize=8)
def escenarios_dl_geo(anio: int = 2040, driver: str = "padronal") -> gpd.GeoDataFrame:
    """Distritos (capa simplificada 2025) con el padrón proyectado por escenario.

    Una fila por distrito × escenario al año ``anio`` del horizonte.
    """
    e = escenarios()["padron_dl"]
    e = e[(e["anio"] == anio) & (e["driver"] == driver)]
    g = gpd.read_file(PROCESSED / "distritos_simp_2025.gpkg")[["distrito_l", "geometry"]]
    return g.merge(e, on="distrito_l").rename(columns={"pad_dl": "pad"})


@lru_cache(maxsize=8)
def escenarios_mun_geo(anio: int = 2040, driver: str = "padronal") -> gpd.GeoDataFrame:
    """Municipios (capa simplificada) con el padrón proyectado por escenario."""
    e = escenarios()["padron_mun"]
    e = e[(e["anio"] == anio) & (e["driver"] == driver)]
    return municipios_borde().merge(e, on="mpiocve")


@lru_cache(maxsize=80)
def escenarios_zona_total(mpiocves, driver: str = "padronal") -> pd.DataFrame:
    """Padrón proyectado agregado de la zona por escenario y año."""
    e = escenarios()["padron_mun"]
    e = e[e["driver"] == driver]
    cvess = zona_cvess(mpiocves)
    if cvess:
        e = e[e["mpiocve"].isin(cvess)]
    return e.groupby(["escenario", "anio"], as_index=False)["pad"].sum()


def escenarios_geo_zona(
    mpiocves, anio: int = 2040, driver: str = "padronal"
) -> tuple[gpd.GeoDataFrame, str]:
    """Capa de escenarios para la zona y el nombre de la llave geográfica.

    Estado → distritos locales (``distrito_l``); municipios seleccionados →
    municipios (``mpiocve``).
    """
    if zona_cvess(mpiocves):
        return escenarios_mun_geo(anio, driver), "mpiocve"
    return escenarios_dl_geo(anio, driver), "distrito_l"


def _cagr(v0: float, v1: float, n: float) -> float:
    return (v1 / v0) ** (1 / n) - 1


@lru_cache(maxsize=1)
def cagr_pob_mun() -> pd.Series:
    """CAGR observado de población CONAPO 2015→2025 por municipio."""
    hist = conapo_mun()[conapo_mun()["anio"].between(2015, 2025)]
    return (
        hist.groupby("mpiocve")
        .apply(
            lambda d: _cagr(
                d["pob"].iloc[0], d["pob"].iloc[-1], d["anio"].iloc[-1] - d["anio"].iloc[0]
            ),
            include_groups=False,
        )
        .rename("cagr_obs")
    )


@lru_cache(maxsize=1)
def drivers_padron() -> pd.DataFrame:
    """Padrón base 2025 y CAGRs por municipio (padronal y demográfico)."""
    pm = pad_mun()
    cagr_pad = (
        pm.pivot(index="mpiocve", columns="anio", values="pad")
        .pipe(lambda p: _cagr(p[2019], p[2025], 6))
        .rename("cagr_pad")
    )
    pob18 = conapo_mun()
    cagr_18 = (
        pob18[pob18["anio"].between(2015, 2025)]
        .pivot(index="mpiocve", columns="anio", values="pob18")
        .pipe(lambda p: _cagr(p[2015], p[2025], 10))
        .rename("cagr_18")
    )
    nombres = conapo_mun()[["mpiocve", "nom_mun"]].drop_duplicates()
    return (
        pm[pm["anio"] == 2025][["mpiocve", "pad"]]
        .rename(columns={"pad": "pad_base"})
        .merge(cagr_pad.reset_index(), on="mpiocve")
        .merge(cagr_18.reset_index(), on="mpiocve")
        .merge(nombres, on="mpiocve")
    )


@lru_cache(maxsize=8)
def pesos_distrito(anio: int = 2025) -> pd.DataFrame:
    """Fracción del padrón municipal que vive en cada distrito local.

    La asignación sección → distrito corresponde a la cartografía de ``anio``.
    """
    w = (
        pad_sec()[pad_sec()["anio"] == anio]
        .groupby(["mpiocve", "distrito_l"], as_index=False)["pad"]
        .sum()
    )
    w["peso"] = w["pad"] / w.groupby("mpiocve")["pad"].transform("sum")
    return w[["mpiocve", "distrito_l", "peso"]]


@lru_cache(maxsize=8)
def razon_dl(anio: int) -> pd.DataFrame:
    """Razón padrón/población por distrito local para un año de cartografía.

    ``pob18`` y ``pob`` se reparten de municipio a distrito con pesos de
    padrón del propio año (aproximación, igual que en ``efecto_redistrito``).
    """
    ps = pad_sec()[pad_sec()["anio"] == anio].copy()
    pob = conapo_mun()[conapo_mun()["anio"] == anio][["mpiocve", "pob", "pob18"]]
    d = ps.merge(pob, on="mpiocve", how="left")
    d["pad_mun"] = d.groupby("mpiocve")["pad"].transform("sum")
    d["pob18"] = d["pob18"] * d["pad"] / d["pad_mun"]
    d["pob"] = d["pob"] * d["pad"] / d["pad_mun"]
    r = d.groupby("distrito_l", as_index=False).agg(
        pad=("pad", "sum"), pob=("pob", "sum"), pob18=("pob18", "sum")
    )
    r["razon_total"] = r["pad"] / r["pob"]
    r["razon_18"] = r["pad"] / r["pob18"]
    return r


@lru_cache(maxsize=8)
def distritos_razon(anio: int) -> gpd.GeoDataFrame:
    """Distritos locales (capa simplificada) con razón padrón/población."""
    g = gpd.read_file(PROCESSED / f"distritos_simp_{anio}.gpkg")
    g = g.drop(columns=["ln", "pad"])  # la capa trae sus propios conteos cartográficos
    return g.merge(razon_dl(anio), on="distrito_l", how="left").reset_index(drop=True)


@lru_cache(maxsize=64)
def escenarios_custom(
    factores_pob: tuple[float, float, float] = (0.75, 1.0, 1.25),
    factores_pad: tuple[float, float, float] = (0.75, 1.0, 1.25),
    geo: int | None = None,
) -> dict[str, pd.DataFrame]:
    """Escenarios recomputados con un factor editable por escenario.

    Cada tupla lleva los factores ``(bajo, base, alto)`` que multiplican el
    CAGR observado: los defaults reproducen la libreta 03 (Δ = 0.25 → 0.75,
    1.0, 1.25). La curva ``base`` de población conserva la serie oficial
    CONAPO, escalada por el cociente de factores de crecimiento respecto a
    ``f = 1``; ``bajo``/``alto`` extrapolan el CAGR observado desde 2025.
    ``geo`` fija el año de la asignación sección → distrito usada para
    repartir a distritos (default: 2025, año base de la proyección).
    """
    horizonte, a0 = 2040, 2025
    f_pb, f_p0, f_pa = factores_pob
    cm = conapo_mun()
    cagr = cagr_pob_mun().reset_index()

    # --- población: base = CONAPO escalado; bajo/alto = CAGR modulado ---
    ref = cm[cm["anio"] == a0][["mpiocve", "nom_mun", "pob"]].merge(cagr, on="mpiocve")
    base = (
        cm[cm["anio"] >= a0][["mpiocve", "nom_mun", "anio", "pob"]]
        .merge(cagr, on="mpiocve")
        .assign(
            escenario="base",
            pob=lambda x: (
                x["pob"]
                * (1 + x["cagr_obs"] * f_p0) ** (x["anio"] - a0)
                / (1 + x["cagr_obs"]) ** (x["anio"] - a0)
            ),
        )
        .drop(columns="cagr_obs")
    )
    alt = pd.concat(
        [
            ref.assign(
                escenario=nom,
                anio=a,
                pob=lambda x, fac=fac, a=a: x["pob"] * (1 + x["cagr_obs"] * fac) ** (a - a0),
            )
            for nom, fac in [("bajo", f_pb), ("alto", f_pa)]
            for a in range(a0 + 1, horizonte + 1)
        ],
        ignore_index=True,
    )
    esc_pob = pd.concat([base, alt[["mpiocve", "nom_mun", "anio", "pob", "escenario"]]])

    # --- padrón: dos drivers × tres escenarios ---
    d = drivers_padron()
    esc_pad = pd.concat(
        [
            d.assign(
                anio=a,
                driver=drv,
                escenario=nom,
                pad=lambda x, col=col, fac=fac, a=a: (
                    x["pad_base"] * (1 + x[col] * fac) ** (a - a0)
                ),
            )
            for a in range(a0 + 1, horizonte + 1)
            for drv, col in [("padronal", "cagr_pad"), ("demografico", "cagr_18")]
            for nom, fac in zip(["bajo", "base", "alto"], factores_pad)
        ],
        ignore_index=True,
    )

    # --- reparto a distrito local con pesos de padrón ---
    w = pesos_distrito(geo or 2025)
    pad_dl = (
        esc_pad.merge(w, on="mpiocve")
        .assign(pad_dl=lambda x: x["pad"] * x["peso"])
        .groupby(["distrito_l", "anio", "driver", "escenario"], as_index=False)["pad_dl"]
        .sum()
    )
    pob_dl = (
        esc_pob.merge(w, on="mpiocve")
        .assign(pob_dl=lambda x: x["pob"] * x["peso"])
        .groupby(["distrito_l", "anio", "escenario"], as_index=False)["pob_dl"]
        .sum()
    )

    return {
        "poblacion_mun": esc_pob,
        "padron_mun": esc_pad,
        "poblacion_dl": pob_dl,
        "padron_dl": pad_dl,
        "poblacion_est": esc_pob.groupby(["escenario", "anio"], as_index=False)["pob"].sum(),
        "padron_est": esc_pad.groupby(["driver", "escenario", "anio"], as_index=False)[
            "pad"
        ].sum(),
    }


@lru_cache(maxsize=1)
def escenarios_estado() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Escenarios agregados al estado: población y padrón por escenario/driver."""
    e = escenarios()
    pob = e["poblacion_mun"].groupby(["escenario", "anio"], as_index=False)["pob"].sum()
    pad = e["padron_mun"].groupby(["driver", "escenario", "anio"], as_index=False)["pad"].sum()
    return pob, pad
