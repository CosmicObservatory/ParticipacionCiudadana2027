"""Pestaña de introducción del tablero Dash."""

from dash import dcc, html

from vothmo.dashboard.narrativa import diccionario_md, escenarios_md

content = html.Div(
    children=[
        html.P(
            "Tablero interactivo sobre los votantes del estado de Sonora a partir de "
            "los datos tidy generados por el pipeline de libretas (data/processed/): "
            "conteos censales electorales del INE 2009–2024, cartografía electoral "
            "2019–2025, censos INEGI 2010/2020 y proyecciones CONAPO."
        ),
        html.H2("Distribución"),
        html.P(
            "Sonora se divide en 21 distritos electorales locales (y 7 federales); "
            "cada distrito se divide en secciones electorales. Las pestañas siguientes "
            "resumen la lista nominal, la participación y los escenarios de crecimiento."
        ),
        html.H2("Pestañas"),
        html.Ul(
            [
                html.Li("Demografía electoral: pirámides, participación y mapas por distrito."),
                html.Li("Padrón vs población: razón padrón/población 18+ por municipio."),
                html.Li("Crecimiento: escenarios bajo/base/alto de población y padrón a 2040."),
            ]
        ),
        html.H2("Fuentes"),
        html.Ul(
            [
                html.Li("INE: conteos censales de la lista nominal y cartografía electoral."),
                html.Li("INEGI: ITER/censo de población 2010 y 2020."),
                html.Li("CONAPO: proyecciones de población municipal 1990–2040."),
                html.Li("IEE Sonora: resultados electorales (pendiente)."),
            ]
        ),
        dcc.Markdown(
            "Caveats: `pad` (padrón cartográfico) ≠ `ln` (lista nominal del conteo); "
            "la clave municipal del INE difiere de la de INEGI "
            "(ver `mun_ine_inegi.csv`)."
        ),
        dcc.Markdown(escenarios_md(), mathjax=True),
        dcc.Markdown(diccionario_md(), mathjax=True),
    ]
)
