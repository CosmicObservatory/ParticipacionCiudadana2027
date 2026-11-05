"""Constructores de figuras Plotly compartidos por los tableros Dash y Streamlit."""

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from vothmo.dashboard.data import (
    CENTRO_SONORA,
    COLOR_ESCENARIO,
    COLOR_SEXO,
    geojson_ligero,
)

_MAPA = {"map_style": "carto-positron", "center": CENTRO_SONORA, "zoom": 5, "opacity": 0.75}


def fig_ln_anual(resumen: pd.DataFrame) -> go.Figure:
    """Lista nominal del conteo censal y participación por elección."""
    fig = go.Figure()
    fig.add_bar(x=resumen["aelec"], y=resumen["ln"], name="Lista nominal")
    fig.add_scatter(
        x=resumen["aelec"],
        y=resumen["pc"],
        name="Participación (sv/lns)",
        yaxis="y2",
        mode="lines+markers",
        line={"color": "#d62728"},
    )
    fig.update_layout(
        title="Lista nominal y participación ciudadana por elección, Sonora",
        yaxis_title="personas en lista nominal",
        yaxis2={"title": "participación %", "overlaying": "y", "side": "right", "range": [0, 100]},
        legend={"orientation": "h", "y": 1.12},
        height=420,
    )
    return fig


def fig_votantes_zona(elec: pd.DataFrame, nombre: str) -> go.Figure:
    """Lista nominal por elección de la zona elegida."""
    fig = go.Figure()
    fig.add_bar(x=elec["aelec"], y=elec["ln"], name="Lista nominal")
    fig.update_layout(
        title=f"Lista nominal por elección · {nombre}",
        xaxis_range=[elec["aelec"].min() - 1, elec["aelec"].max() + 1],
        yaxis_title="personas",
        showlegend=False,
        height=460,
    )
    return fig


def fig_mapa_pc_mun(
    g: gpd.GeoDataFrame, anio: int, foco: dict | None = None
) -> go.Figure:
    """Coropletas municipales de la participación ciudadana (``sv``/``lns``).

    ``foco`` (opcional, ver ``data.centro_zona``) centra y acerca el mapa
    al municipio elegido; sin él se muestra todo el estado.
    """
    vista = dict(_MAPA)
    if foco:
        vista.update(center={"lat": foco["lat"], "lon": foco["lon"]}, zoom=foco["zoom"])
    fig = px.choropleth_map(
        g,
        geojson=geojson_ligero(g),
        locations=g.index,
        color="pc",
        color_continuous_scale="Viridis",
        range_color=[20, 100],
        hover_name="nom_mun",
        hover_data={"sv": ":,", "lns": ":,"},
        labels={"pc": "Participación (%)"},
        title=f"Participación ciudadana por municipio · elección {anio}",
        **vista,
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0}, height=560)
    return fig


def fig_pc_anual(
    elec: pd.DataFrame, nombre: str, estado: pd.DataFrame | None = None
) -> go.Figure:
    """Participación ciudadana (``sv``/``lns``) por elección de la zona.

    ``estado`` (opcional) dibuja la serie estatal como referencia punteada
    cuando la zona elegida es un municipio.
    """
    fig = go.Figure()
    fig.add_scatter(x=elec["aelec"], y=elec["pc"], name=nombre, mode="lines+markers")
    if estado is not None:
        fig.add_scatter(
            x=estado["aelec"],
            y=estado["pc"],
            name="Sonora",
            mode="lines",
            line={"dash": "dash", "color": "#888"},
        )
    fig.update_layout(
        title=f"Participación ciudadana por elección · {nombre}",
        xaxis_range=[elec["aelec"].min() - 1, elec["aelec"].max() + 1],
        yaxis_title="participación %",
        yaxis_range=[0, 100],
        legend={"orientation": "h", "y": 1.12},
        height=560,
    )
    return fig


def fig_piramide(pir: pd.DataFrame, anio: int, titulo: str | None = None) -> go.Figure:
    """Pirámide de la lista nominal (edad × sexo) de una elección."""
    fig = px.bar(
        pir,
        x="ln_neg",
        y="edad",
        color="sexo_txt",
        orientation="h",
        color_discrete_map=COLOR_SEXO,
        range_x=[-pir["ln"].max() * 1.05, pir["ln"].max() * 1.05],
        labels={"ln_neg": "Lista nominal", "edad": "Edad (años)", "sexo_txt": "Sexo"},
        title=titulo or f"Pirámide de la lista nominal · elección {anio}",
    )
    fig.update_layout(barmode="relative", bargap=0.05, height=560)
    fig.update_xaxes(tickformat="~s")
    return fig


def fig_participacion_edad(pc: pd.DataFrame, anio: int) -> go.Figure:
    """Participación por edad y sexo de una elección."""
    fig = px.line(
        pc,
        x="edad",
        y="pc",
        color="sexo_txt",
        color_discrete_map=COLOR_SEXO,
        range_y=[0, 100],
        labels={"pc": "Participación (%)", "edad": "Edad", "sexo_txt": "Sexo"},
        title=f"Participación ciudadana por edad y sexo · {anio}",
    )
    fig.update_layout(height=440)
    return fig


def fig_ranking(df: pd.DataFrame, x: str, titulo: str, n: int = 15) -> go.Figure:
    """Barras horizontales de lista nominal (top n) con participación en hover."""
    top = df.nlargest(n, "ln").sort_values("ln").copy()
    top[x] = top[x].astype(str)
    fig = px.bar(
        top,
        x="ln",
        y=x,
        orientation="h",
        hover_data={"pc": ":.1f", "pct_muj": ":.1f"},
        labels={"ln": "Lista nominal", x: ""},
        title=titulo,
    )
    fig.update_layout(height=460)
    return fig


def fig_ranking_distritos(df: pd.DataFrame, var_mapa: str, anio: int) -> go.Figure:
    """Barras de lista nominal por distrito local, coloreadas como el mapa.

    El color de cada barra reproduce la escala Viridis del coropletas para la
    variable elegida (`ln` o `pc`), incluyendo su colorbar.
    """
    etiquetas = {"ln": "Lista nominal", "pc": "Participación (%)"}
    d = df.sort_values("ln").copy()
    d["distrito_l"] = d["distrito_l"].astype(str)
    fig = px.bar(
        d,
        x="ln",
        y="distrito_l",
        orientation="h",
        hover_data={"ln": ":,", "pc": ":.1f", "pct_muj": ":.1f"},
        labels={"ln": "Lista nominal", "distrito_l": ""},
        title=f"Lista nominal por distrito local · {anio} (color = {etiquetas[var_mapa]})",
    )
    fig.update_traces(
        marker={
            "color": d[var_mapa],
            "colorscale": "Viridis",
            "showscale": True,
            "colorbar": {"title": etiquetas[var_mapa]},
        }
    )
    fig.update_layout(height=460)
    return fig


def fig_mapa_distritos(gd: gpd.GeoDataFrame, color: str, anio: int) -> go.Figure:
    """Coropletas de distritos locales coloreadas por `ln` o `pc`."""
    etiquetas = {"ln": "Lista nominal", "pc": "Participación (%)"}
    fig = px.choropleth_map(
        gd,
        geojson=geojson_ligero(gd),
        locations=gd.index,
        color=color,
        color_continuous_scale="Viridis",
        hover_name="distrito_l",
        hover_data={"ln": ":,", "pc": ":.1f", "pct_muj": ":.1f"},
        labels={color: etiquetas[color]},
        title=f"{etiquetas[color]} por distrito local · {anio}",
        **_MAPA,
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0}, height=560)
    return fig


def fig_padron_poblacion(
    pad_anual: pd.DataFrame,
    ln_conteo: pd.DataFrame,
    conapo_estado: pd.DataFrame,
    inegi_estado: pd.DataFrame,
) -> go.Figure:
    """Padrón/LN electorales contra población estatal (CONAPO + INEGI)."""
    fig = go.Figure()
    fig.add_scatter(
        x=conapo_estado["anio"], y=conapo_estado["pob"], name="Población (CONAPO)", mode="lines"
    )
    fig.add_scatter(
        x=conapo_estado["anio"],
        y=conapo_estado["pob18"],
        name="Población 18+ (CONAPO)",
        mode="lines",
    )
    fig.add_scatter(
        x=pad_anual["anio"], y=pad_anual["pad"], name="Padrón electoral", mode="lines+markers"
    )
    fig.add_scatter(
        x=pad_anual["anio"], y=pad_anual["ln"], name="LN (cartografía)", mode="lines+markers"
    )
    fig.add_scatter(
        x=ln_conteo["anio"],
        y=ln_conteo["ln_conteo"],
        name="LN (conteo censal)",
        mode="markers",
        marker={"size": 9, "symbol": "diamond"},
    )
    fig.add_scatter(
        x=inegi_estado["anio"],
        y=inegi_estado["pob"],
        name="INEGI censo",
        mode="markers",
        marker={"size": 10, "symbol": "x", "color": "black"},
    )
    fig.update_layout(
        title="Padrón electoral y población de Sonora",
        yaxis_title="personas",
        height=480,
        legend={"orientation": "h", "y": -0.15},
    )
    return fig


def fig_razon_estado(estado: pd.DataFrame) -> go.Figure:
    """Proporción empadronada estatal por año de cartografía."""
    fig = go.Figure()
    fig.add_scatter(
        x=estado["anio"], y=estado["razon_18"], name="pad / pob 18+", mode="lines+markers"
    )
    fig.add_scatter(
        x=estado["anio"], y=estado["razon_total"], name="pad / pob total", mode="lines+markers"
    )
    fig.update_layout(
        title="Proporción empadronada, Sonora",
        yaxis_tickformat=".1%",
        yaxis_title="proporción",
        height=400,
        legend={"orientation": "h", "y": 1.12},
    )
    return fig


def fig_mapa_razon_mun(g: gpd.GeoDataFrame, anio: int) -> go.Figure:
    """Coropletas municipales de la razón padrón/población 18+."""
    fig = px.choropleth_map(
        g,
        geojson=geojson_ligero(g),
        locations=g.index,
        color="razon_18",
        hover_name="nom_mun",
        hover_data={"pad": ":,", "pob18": ":,.0f", "razon_total": ".1%"},
        color_continuous_scale="RdYlGn_r",
        range_color=[0.7, 1.15],
        title=f"Padrón / población 18+ por municipio · {anio} (aprox.)",
        **_MAPA,
    )
    fig.update_layout(height=560, coloraxis_colorbar_tickformat=".0%")
    return fig


def fig_mapa_razon_dl(g: gpd.GeoDataFrame, anio: int) -> go.Figure:
    """Coropletas distrital de la razón padrón/población 18+."""
    fig = px.choropleth_map(
        g,
        geojson=geojson_ligero(g),
        locations=g.index,
        color="razon_18",
        hover_name="distrito_l",
        hover_data={"pad": ":,", "pob18": ":,.0f", "razon_total": ".1%"},
        color_continuous_scale="RdYlGn_r",
        range_color=[0.7, 1.15],
        title=f"Padrón / población 18+ por distrito local · geografía {anio} (aprox.)",
        **_MAPA,
    )
    fig.update_layout(height=560, coloraxis_colorbar_tickformat=".0%")
    return fig


def fig_escenarios_estado(pob: pd.DataFrame, pad: pd.DataFrame, driver: str) -> go.Figure:
    """Proyección estatal: población por escenario y padrón (driver elegido)."""
    fig = go.Figure()
    for esc, d in pob.groupby("escenario"):
        fig.add_scatter(
            x=d["anio"],
            y=d["pob"],
            name=f"Población {esc}",
            mode="lines",
            line={"color": COLOR_ESCENARIO[esc]},
        )
    for esc, d in pad[pad["driver"] == driver].groupby("escenario"):
        fig.add_scatter(
            x=d["anio"],
            y=d["pad"],
            name=f"Padrón {esc} ({driver})",
            mode="lines",
            line={"color": COLOR_ESCENARIO[esc], "dash": "dash"},
        )
    fig.update_layout(
        title="Escenarios estatales de población y padrón electoral",
        yaxis_title="personas",
        height=460,
        legend={"orientation": "h", "y": -0.15},
    )
    return fig


def fig_escenarios_zona(
    g: gpd.GeoDataFrame,
    tot: pd.DataFrame,
    key: str,
    nombre: str,
    anio: int,
    anio_barras: int,
    driver: str,
    foco: dict | None = None,
) -> go.Figure:
    """Cuadrícula 2×2 de los escenarios del padrón proyectado de la zona.

    ``[[base, bajo], [alto, barras]]``: tres coropletas del padrón a ``anio``
    por ``key`` (``distrito_l`` o ``mpiocve``) con escala compartida y, abajo
    a la derecha, barras del total de la zona por escenario a ``anio_barras``.
    ``foco`` (ver ``data.centro_zona``) centra y acerca los tres mapas.
    """
    orden_map = ["base", "bajo", "alto"]
    orden_bar = ["bajo", "base", "alto"]
    celdas = [(1, 1), (1, 2), (2, 1)]
    gj = geojson_ligero(
        g[g["escenario"] == "base"].sort_values(key).reset_index(drop=True)
    )
    zmin, zmax = g["pad"].min(), g["pad"].max()
    vista = {"center": CENTRO_SONORA, "zoom": 4.4, "style": "carto-positron"}
    if foco:
        vista.update(
            center={"lat": foco["lat"], "lon": foco["lon"]}, zoom=foco["zoom"]
        )
    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"type": "map"}, {"type": "map"}], [{"type": "map"}, {"type": "xy"}]],
        subplot_titles=[
            "Escenario base",
            "Escenario bajo",
            "Escenario alto",
            f"Total a {anio_barras}",
        ],
    )
    for i, (esc, (r, c)) in enumerate(zip(orden_map, celdas, strict=True), start=1):
        d = g[g["escenario"] == esc].sort_values(key).reset_index(drop=True)
        fig.add_trace(
            go.Choroplethmap(
                geojson=gj,
                locations=d.index,
                z=d["pad"],
                zmin=zmin,
                zmax=zmax,
                colorscale="Viridis",
                showscale=(i == 3),
                colorbar={"title": "Padrón"},
                customdata=d["nom_mun"] if "nom_mun" in d else d[key],
                hovertemplate="%{customdata} · padrón %{z:,.0f}<extra></extra>",
                name=esc,
            ),
            row=r,
            col=c,
        )
    t = tot[tot["anio"] == anio_barras].set_index("escenario").reindex(orden_bar)
    fig.add_trace(
        go.Bar(
            x=orden_bar,
            y=t["pad"],
            marker_color=[COLOR_ESCENARIO[e] for e in orden_bar],
            text=[f"{v:,.0f}" for v in t["pad"]],
            textposition="outside",
            name="Total",
        ),
        row=2,
        col=2,
    )
    for i in range(1, 4):
        k = "map" if i == 1 else f"map{i}"
        fig.update_layout({k: vista})
    fig.update_yaxes(title_text="padrón", row=2, col=2)
    fig.update_layout(
        title=f"Padrón electoral proyectado a {anio} · {nombre} · driver {driver}",
        height=760,
        margin={"l": 0, "r": 0, "t": 60, "b": 0},
        showlegend=False,
    )
    return fig


def fig_padron_dl(pad_dl: pd.DataFrame, driver: str) -> go.Figure:
    """Padrón proyectado por distrito local, facetado, para un driver."""
    sel = pad_dl[pad_dl["driver"] == driver]
    fig = px.line(
        sel,
        x="anio",
        y="pad_dl",
        color="escenario",
        facet_col="distrito_l",
        facet_col_wrap=7,
        color_discrete_map=COLOR_ESCENARIO,
        labels={"pad_dl": "Padrón", "anio": "Año", "escenario": "Escenario"},
        title=f"Padrón proyectado por distrito local (driver {driver})",
    )
    fig.update_yaxes(matches=None, title="")
    fig.update_xaxes(title="")
    fig.update_layout(height=680)
    fig.for_each_annotation(lambda a: a.update(text=f"D{a.text.split('=')[-1]}"))
    return fig


def fig_pob_dl(pob_dl: pd.DataFrame, escenario: str) -> go.Figure:
    """Población proyectada por distrito local para un escenario."""
    sel = pob_dl[pob_dl["escenario"] == escenario]
    fig = px.line(
        sel,
        x="anio",
        y="pob_dl",
        color="distrito_l",
        labels={"pob_dl": "Población", "anio": "Año", "distrito_l": "Distrito"},
        title=f"Población proyectada por distrito local · escenario {escenario}",
    )
    fig.update_layout(height=440, showlegend=False)
    return fig


def fig_mun_escenario(esc_pob: pd.DataFrame, municipios: list[str]) -> go.Figure:
    """Proyección poblacional por escenario para municipios seleccionados."""
    sel = esc_pob[esc_pob["nom_mun"].isin(municipios)]
    fig = px.line(
        sel,
        x="anio",
        y="pob",
        color="nom_mun",
        line_dash="escenario",
        category_orders={"escenario": ["bajo", "base", "alto"]},
        labels={"pob": "Población", "anio": "Año", "nom_mun": "Municipio"},
        title="Escenarios poblacionales por municipio (CONAPO + CAGR observado)",
    )
    fig.update_layout(height=460)
    return fig


# ----------------------------------------------------- distribución seccional
DISTRITOS = list(range(1, 22))
PALETA_DISTRITOS = {d: c for d, c in zip(DISTRITOS, px.colors.qualitative.Alphabet)}
SERIES_EFECTO = {
    "pad": "Padrón electoral",
    "ln": "Lista nominal",
    "pob18": "Población 18+ (aprox.)",
}


def _escala_discreta(colores: dict[int, str]) -> list:
    """Escala continua piecewise que asigna a cada distrito un color exacto.

    Permite dibujar un solo trace coroplético con colores "discretos" elegidos
    por el usuario (evita duplicar el GeoJSON por categoría).
    """
    ds = sorted(colores)
    vmin, rng = ds[0], ds[-1] - ds[0]
    esc = []
    for d in ds:
        lo = max((d - 0.5 - vmin) / rng, 0.0)
        hi = min((d + 0.5 - vmin) / rng, 1.0)
        esc += [[lo, colores[d]], [hi, colores[d]]]
    esc[0][0], esc[-1][0] = 0.0, 1.0
    return esc


def fig_mapa_secciones(
    gsec: gpd.GeoDataFrame,
    gmun: gpd.GeoDataFrame,
    colores: dict[int, str],
    anio: int,
    municipios: dict[int, str],
    foco: dict | None = None,
) -> go.Figure:
    """Secciones coloreadas por distrito local (colores del usuario) con
    bordes municipales superpuestos.

    El hover lista los municipios del distrito: completos en texto normal y
    parciales (repartidos entre distritos) en cursiva. ``foco`` (opcional,
    ver ``data.centro_zona``) centra y acerca el mapa a la zona elegida.
    """
    g = gsec.reset_index(drop=True)
    g["muns_txt"] = g["distrito_l"].map(municipios)
    gm = gmun.reset_index(drop=True)
    vista = dict(_MAPA)
    if foco:
        vista.update(center={"lat": foco["lat"], "lon": foco["lon"]}, zoom=foco["zoom"])
    fig = px.choropleth_map(
        g,
        geojson=geojson_ligero(g),
        locations=g.index,
        color="distrito_l",
        color_continuous_scale=_escala_discreta(colores),
        custom_data=["seccion", "nom_mun", "pad", "ln", "muns_txt"],
        title=f"Secciones por distrito local · cartografía {anio}",
        **vista,
    )
    fig.update_traces(
        hovertemplate=(
            "<b>Distrito %{z}</b> · Sección %{customdata[0]}<br>"
            "%{customdata[1]} · padrón %{customdata[2]:,.0f} · ln %{customdata[3]:,.0f}"
            "<br><br><b>Municipios del distrito</b>"
            "<br>%{customdata[4]}<extra></extra>"
        )
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.add_trace(
        go.Choroplethmap(
            geojson=geojson_ligero(gm),
            locations=gm.index,
            z=[0] * len(gm),
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker={"line": {"width": 1.4, "color": "#1a1a1a"}},
            showscale=False,
            hoverinfo="skip",
        )
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0}, height=640)
    return fig


def fig_barras_ln_dl(
    df: pd.DataFrame, colores: dict[int, str], anio: int, nombre: str = "Sonora"
) -> go.Figure:
    """Distritos locales ordenados por lista nominal cartográfica (barras).

    Usa los colores del usuario para empatar con el mapa seccional.
    ``nombre`` es la zona en el título.
    """
    d = df.sort_values("ln")  # barras horizontales: la mayor queda arriba
    fig = px.bar(
        d,
        x="ln",
        y=d["distrito_l"].astype(str),
        orientation="h",
        hover_data={"pad": ":,"},
        labels={"ln": "Lista nominal", "y": "Distrito"},
        title=f"Distritos por lista nominal · {nombre} · cartografía {anio}",
    )
    fig.update_traces(
        marker_color=[colores[int(x)] for x in d["distrito_l"]],
        showlegend=False,
    )
    fig.update_layout(height=640, yaxis_title="Distrito")
    return fig


def fig_historia_distrito(m: pd.DataFrame, distrito: int, serie: str, color: str) -> go.Figure:
    """Historia de un distrito: barras de la serie real con el cambio
    interanual anotado en %, más la contrafactual geografía-2019 (línea
    punteada): el gap entre ambas es el efecto del reseccionamiento."""
    d = m[m["distrito_l"] == distrito].sort_values("anio")
    pct = d[serie].pct_change() * 100
    textos = [""] + [f"{v:+.1f}%" for v in pct.iloc[1:]]
    fig = go.Figure()
    fig.add_bar(
        x=d["anio"],
        y=d[serie],
        name="Serie real",
        marker_color=color,
        text=textos,
        textposition="outside",
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=d["anio"],
        y=d[f"{serie}_cf"],
        name="Contrafactual (geografía 2019)",
        mode="lines+markers",
        line={"color": "#666", "dash": "dash"},
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    )
    fig.update_layout(
        title=f"Historia del distrito {distrito} · {SERIES_EFECTO[serie]}",
        yaxis_title=SERIES_EFECTO[serie],
        xaxis_title="Año",
        height=440,
        legend={"orientation": "h", "y": 1.14},
    )
    return fig


def fig_delta_barras(m: pd.DataFrame, serie: str, colores: dict[int, str]) -> go.Figure:
    """Efecto neto acumulado de la redistritación al último año, por distrito."""
    ult = m[m["anio"] == m["anio"].max()].sort_values(f"{serie}_delta")
    fig = px.bar(
        ult,
        x=f"{serie}_delta",
        y=ult["distrito_l"].astype(str),
        orientation="h",
        labels={
            f"{serie}_delta": f"Δ {SERIES_EFECTO[serie]}",
            "y": "Distrito",
        },
        title=f"Efecto neto de la redistritación · {int(m['anio'].max())} "
        f"({SERIES_EFECTO[serie]})",
    )
    fig.update_traces(
        marker_color=[colores[int(d)] for d in ult["distrito_l"]],
        showlegend=False,
    )
    fig.update_layout(height=480, yaxis_title="Distrito")
    return fig


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def fig_sankey_distritos(t: pd.DataFrame, a0: int, a1: int, colores: dict[int, str]) -> go.Figure:
    """Sankey distrito (año a0) → distrito (año a1); el grosor es el número de
    secciones que cambiaron (o permanecieron) y el nodo usa los colores del
    usuario."""
    n = len(DISTRITOS)
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "label": [f"D{d} · {a0}" for d in DISTRITOS] + [f"D{d} · {a1}" for d in DISTRITOS],
                "color": [colores[d] for d in DISTRITOS] * 2,
                "pad": 8,
                "thickness": 16,
                "hovertemplate": "%{label}<extra></extra>",
            },
            link={
                "source": (t["dl0"] - 1).tolist(),
                "target": (t["dl1"] - 1 + n).tolist(),
                "value": t["n"].tolist(),
                "color": [_rgba(colores[d], 0.45) for d in t["dl0"]],
                "customdata": t[["dl0", "dl1", "pad"]].values.tolist(),
                "hovertemplate": (
                    "D%{customdata[0]} → D%{customdata[1]}: "
                    "%{value} secciones · padrón %{customdata[2]:,.0f}<extra></extra>"
                ),
            },
        )
    )
    fig.update_layout(
        title=f"Movimiento de secciones entre distritos · {a0} → {a1}",
        height=620,
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig
