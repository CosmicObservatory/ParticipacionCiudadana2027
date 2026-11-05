"""Portada-historia del tablero Dash (ruta ``/``).

Narrativa con las cifras y figuras clave del proyecto; cierra con las fuentes
consultadas y un enlace a la herramienta (``/herramienta``).
"""

from dash import Input, Output, callback, dcc, html

from vothmo.dashboard import data, figures
from vothmo.dashboard.narrativa import fuentes_md, historia_md

_ANIO_ELEC = data.anios_elec()[-1]
_ANIO_MAP = 2025
_ANIO_ESC = 2027
_DRIVER = "padronal"
_TXT = historia_md()
_PAD, _LN = data.padron_anual()
_POB_E, _PAD_E = data.escenarios_estado()

_BOTON = {
    "display": "inline-block",
    "padding": "0.8rem 1.8rem",
    "background": "#1f77b4",
    "color": "white",
    "borderRadius": "6px",
    "textDecoration": "none",
    "fontWeight": "bold",
    "fontSize": "1.1rem",
}

layout = html.Div(
    children=[
        html.H1("Participación Ciudadana 2027"),
        html.P(
            "Las elecciones están proximas y conviene conocer la población"
            "de interés para el diseño de la campaña"
            "Aqui exploraremos el comportamiento de la participación ciudadana"
            " de años pasados para obtener estimaciones para las próximas elecciones."
            "Antes de todo debemos elegir que parte de Sonra nos interesa conocer."
        ),
        html.Label("Zona de Interés"),
        dcc.Dropdown(
            id="hs-mun",
            options=[
                {"label": "Sonora", "value": 0},
                *[
                    {"label": r.nom_mun, "value": r.mpiocve}
                    for r in data.municipios().itertuples()
                ],
            ],
            value=[0],
            multi=True,
            style={"maxWidth": "480px", "marginBottom": "1rem"},
        ),
        html.H2("Los votantes antes"),
        html.H3("Distribución"),
        dcc.Graph(id="hs-votantes"),
        html.Label("Año"),
        dcc.Dropdown(
            id="hs-anio-dist",
            options=[{"label": str(a), "value": a} for a in data.anios_elec()],
            value=data.anios_elec()[-1],
            clearable=False,
            style={"maxWidth": "240px", "marginBottom": "1rem"},
        ),
        dcc.Graph(id="hs-pir-ln"),
        html.H3("Participación ciudadana"),
        html.Label("Año de interés"),
        dcc.Dropdown(
            id="hs-anio",
            options=[{"label": str(a), "value": a} for a in data.anios_elec()],
            value=data.anios_elec()[-1],
            clearable=False,
            style={"maxWidth": "240px", "marginBottom": "1rem"},
        ),
        html.Div(
            children=[
                dcc.Graph(id="hs-mapa-pc", style={"flex": "3"}),
                dcc.Graph(id="hs-pc-anual", style={"flex": "2"}),
            ],
            style={"display": "flex", "gap": "1rem", "alignItems": "flex-start"},
        ),
        html.H1("Los votantes ahora"),
        html.Div(
            children=[
                dcc.Graph(id="hs-mapa-dl", style={"flex": "3"}),
                dcc.Graph(id="hs-barras-dl", style={"flex": "2"}),
            ],
            style={"display": "flex", "gap": "1rem", "alignItems": "flex-start"},
        ),
        html.P(
            "Los colores de cada distrito se pueden cambiar desde la pestaña "
            "«Distribución Seccional» de la herramienta interactiva.",
            style={"fontSize": "0.85rem", "color": "#666"},
        ),
        html.H2("¿Qué podemos esperar de los votantes?"),
        dcc.Graph(id="hs-escenarios"),
        html.P(""),
        dcc.Markdown(fuentes_md()),
        html.Div(
            dcc.Link(
                "Abrir la herramienta interactiva →",
                href="/herramienta",
                refresh=False,
                style=_BOTON,
            ),
            style={"margin": "2.5rem 0", "textAlign": "center"},
        ),
    ]
)


@callback(Output("hs-votantes", "figure"), Input("hs-mun", "value"))
def _votantes_zona(mpio):
    """Lista nominal por elección de la zona elegida en ``hs-mun``."""
    cvess = data.zona_cvess(mpio)
    return figures.fig_votantes_zona(data.elec_zona(cvess), data.nombre_zona(cvess))


@callback(
    Output("hs-pir-ln", "figure"),
    Input("hs-mun", "value"),
    Input("hs-anio-dist", "value"),
)
def _piramide_ln(mpio, anio: int):
    """Pirámide edad × sexo de la lista nominal de la zona."""
    cvess = data.zona_cvess(mpio)
    return figures.fig_piramide(
        data.piramide_zona(anio, cvess),
        anio,
        f"Lista nominal por edad y sexo · {data.nombre_zona(cvess)} · {anio}",
    )


@callback(
    Output("hs-mapa-pc", "figure"),
    Output("hs-pc-anual", "figure"),
    Input("hs-mun", "value"),
    Input("hs-anio", "value"),
)
def _mapa_pc(mpio, anio: int):
    """Mapa municipal de participación del año elegido + tendencia de la zona."""
    cvess = data.zona_cvess(mpio)
    estado = data.resumen_anual() if cvess else None
    return (
        figures.fig_mapa_pc_mun(
            data.municipios_pc_geo(anio), anio, data.centro_zona(cvess)
        ),
        figures.fig_pc_anual(data.elec_zona(cvess), data.nombre_zona(cvess), estado),
    )


@callback(
    Output("hs-mapa-dl", "figure"),
    Output("hs-barras-dl", "figure"),
    Input("hs-mun", "value"),
)
def _votantes_ahora(mpio):
    """Mapa seccional y barras por distrito filtrados a la zona elegida."""
    cvess = data.zona_cvess(mpio)
    gmun = data.municipios_borde()
    if cvess:
        gmun = gmun[gmun["mpiocve"].isin(cvess)]
    nombre = data.nombre_zona(cvess)
    return (
        figures.fig_mapa_secciones(
            data.secciones_geo(_ANIO_MAP, cvess),
            gmun,
            figures.PALETA_DISTRITOS,
            _ANIO_MAP,
            data.municipios_de_distrito(_ANIO_MAP),
            data.centro_zona(cvess),
        ),
        figures.fig_barras_ln_dl(
            data.pad_ln_dl(_ANIO_MAP, cvess), figures.PALETA_DISTRITOS, _ANIO_MAP, nombre
        ),
    )


@callback(Output("hs-escenarios", "figure"), Input("hs-mun", "value"))
def _escenarios_zona(mpio):
    """Cuadrícula 2×2 de escenarios del padrón proyectado de la zona."""
    cvess = data.zona_cvess(mpio)
    g, key = data.escenarios_geo_zona(cvess, _ANIO_ESC, _DRIVER)
    return figures.fig_escenarios_zona(
        g,
        data.escenarios_zona_total(cvess, _DRIVER),
        key,
        data.nombre_zona(cvess),
        _ANIO_ESC,
        _ANIO_ESC,
        _DRIVER,
        data.centro_zona(cvess),
    )
