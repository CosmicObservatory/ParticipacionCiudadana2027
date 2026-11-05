"""Pestaña de distribución seccional del tablero Dash."""

from dash import ALL, Input, Output, callback, ctx, dcc, html
import dash_mantine_components as dmc

from vothmo.dashboard import data, figures, geo


def _fila_color(d: int) -> dmc.ColorInput:
    return dmc.ColorInput(
        label=f"D{d}",
        value=figures.PALETA_DISTRITOS[d],
        id={"type": "ds-color", "index": d},
        size="xs",
        w=110,
        format="hex",
    )


layout = dmc.MantineProvider(
    html.Div(
        children=[
            html.H2("Distribución seccional"),
            html.P(
                "Cartografía seccional por distrito local (2019–2025). Elige el color "
                "de cada distrito: el mapa y las gráficas de efecto usan la misma "
                "paleta. Los bordes oscuros son los límites municipales."
            ),
            dmc.Group([_fila_color(d) for d in figures.DISTRITOS], gap="xs"),
            html.Label("Año de cartografía"),
            dcc.Slider(
                id="ds-anio",
                min=data.MAP_YEARS[0],
                max=data.MAP_YEARS[-1],
                step=None,
                value=data.MAP_YEARS[-1],
                marks={y: str(y) for y in data.MAP_YEARS},
            ),
            dcc.Graph(id="ds-mapa"),
            html.P(
                [
                    "Nota: en el hover de cada sección, los municipios en ",
                    html.I("cursiva"),
                    (
                        " están repartidos entre dos o más distritos; el resto "
                        "están contenidos por completo en ese distrito."
                    ),
                ],
                style={"fontSize": "0.85rem", "color": "#666"},
            ),
            html.H3("Movimiento de secciones entre distritos"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("De"),
                            dcc.Dropdown(
                                id="ds-de",
                                options=[{"label": str(y), "value": y} for y in data.MAP_YEARS],
                                value=data.MAP_YEARS[0],
                                clearable=False,
                            ),
                        ],
                        style={"width": "140px"},
                    ),
                    html.Div(
                        [
                            html.Label("A"),
                            dcc.Dropdown(
                                id="ds-a",
                                options=[{"label": str(y), "value": y} for y in data.MAP_YEARS],
                                value=data.MAP_YEARS[-1],
                                clearable=False,
                            ),
                        ],
                        style={"width": "140px"},
                    ),
                ],
                style={"display": "flex", "gap": "1rem"},
            ),
            dcc.Graph(id="ds-sankey"),
            html.H3("Cambio atribuible al reseccionamiento"),
            html.P(
                "Diferencia entre la serie real de cada distrito y una contrafactual "
                "que conserva la asignación sección → distrito de 2019: el gap entre "
                "barras y línea mide cuánto gana o pierde el distrito solo por "
                "reacomodo de secciones; las etiquetas anotan el cambio interanual."
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Distrito"),
                            dcc.Dropdown(
                                id="ds-dl",
                                options=[
                                    {"label": f"D{d}", "value": d} for d in figures.DISTRITOS
                                ],
                                value=6,
                                clearable=False,
                            ),
                        ],
                        style={"width": "140px"},
                    ),
                    html.Div(
                        dcc.RadioItems(
                            id="ds-serie",
                            options=[
                                {"label": v, "value": k} for k, v in figures.SERIES_EFECTO.items()
                            ],
                            value="pad",
                            inline=True,
                        ),
                        style={"alignSelf": "flex-end"},
                    ),
                ],
                style={"display": "flex", "gap": "2rem", "alignItems": "center"},
            ),
            dcc.Graph(id="ds-historia"),
            dcc.Graph(id="ds-barras"),
            html.H3("Geografía distrital para los análisis"),
            html.P(
                "Elige qué asignación sección → distrito usan las pestañas "
                "posteriores (Padrón vs Población y Crecimiento). Por defecto "
                "cada análisis usa la distribución de su propio año."
            ),
            dcc.Dropdown(
                id="ds-geo-fija",
                options=geo.OPCIONES_GEO,
                value=0,
                clearable=False,
                style={"maxWidth": "440px"},
            ),
        ]
    )
)


@callback(Output("geo-fija", "data"), Input("ds-geo-fija", "value"))
def _fija_geografia(geo_anio: int) -> int:
    return geo_anio


@callback(
    Output("ds-mapa", "figure"),
    Output("ds-sankey", "figure"),
    Output("ds-historia", "figure"),
    Output("ds-barras", "figure"),
    Input("ds-anio", "value"),
    Input("ds-de", "value"),
    Input("ds-a", "value"),
    Input("ds-dl", "value"),
    Input("ds-serie", "value"),
    Input({"type": "ds-color", "index": ALL}, "value"),
)
def _actualiza(anio: int, de: int, a: int, distrito: int, serie: str, _colores):
    colores = {int(i["id"]["index"]): i["value"] for i in ctx.inputs_list[5]}
    m = data.efecto_redistrito()
    return (
        figures.fig_mapa_secciones(
            data.secciones_geo(anio),
            data.municipios_borde(),
            colores,
            anio,
            data.municipios_de_distrito(anio),
        ),
        figures.fig_sankey_distritos(data.transiciones_distrito(de, a), de, a, colores),
        figures.fig_historia_distrito(m, distrito, serie, colores[distrito]),
        figures.fig_delta_barras(m, serie, colores),
    )
