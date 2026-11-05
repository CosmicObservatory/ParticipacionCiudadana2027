"""Pestaña de escenarios de crecimiento del tablero Dash."""

from dash import Input, Output, State, callback, dcc, html

from vothmo.dashboard import data, figures, geo

_ESC = data.escenarios()
_MUNICIPIOS = sorted(_ESC["poblacion_mun"]["nom_mun"].unique())
_MUN_DEFAULT = [m for m in ["Hermosillo", "Cajeme", "Nogales"] if m in _MUNICIPIOS]

layout = html.Div(
    children=[
        html.H2("Escenarios de crecimiento"),
        html.Div(id="sc-geo-note"),
        html.P(
            "Escenarios bajo/base/alto a 2040: población por CAGR observado de CONAPO y "
            "padrón por driver padronal (CAGR del padrón 2019–2025) o demográfico "
            "(CAGR de población 18+ CONAPO)."
        ),
        html.Label("Driver del padrón"),
        dcc.RadioItems(
            id="sc-driver",
            options=[
                {"label": "Padronal", "value": "padronal"},
                {"label": "Demográfico", "value": "demografico"},
            ],
            value="padronal",
            inline=True,
        ),
        html.Label("Escenario (define qué curva muestran los deslizadores)"),
        dcc.RadioItems(
            id="sc-escenario",
            options=[{"label": e.capitalize(), "value": e} for e in ["bajo", "base", "alto"]],
            value="base",
            inline=True,
        ),
        # Factor de crecimiento por escenario (fracción sobre el CAGR observado);
        # los radios posicionan los deslizadores en el valor del escenario elegido.
        dcc.Store(id="sc-fpob", data={"bajo": -0.25, "base": 0.0, "alto": 0.25}),
        dcc.Store(id="sc-fpad", data={"bajo": -0.25, "base": 0.0, "alto": 0.25}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Ajuste poblacional del escenario"),
                        dcc.Slider(
                            id="sc-delta-pob",
                            min=-0.5,
                            max=0.5,
                            step=0.05,
                            value=0.0,
                            marks={i / 4: f"{i * 25:+d}%" for i in range(-2, 3)},
                            tooltip={"template": "{value:+.0%}"},
                        ),
                    ],
                    style={"flex": 1},
                ),
                html.Div(
                    [
                        html.Label("Ajuste padronal del escenario"),
                        dcc.Slider(
                            id="sc-delta-pad",
                            min=-0.5,
                            max=0.5,
                            step=0.05,
                            value=0.0,
                            marks={i / 4: f"{i * 25:+d}%" for i in range(-2, 3)},
                            tooltip={"template": "{value:+.0%}"},
                        ),
                    ],
                    style={"flex": 1},
                ),
            ],
            style={"display": "flex", "gap": "2rem", "marginTop": "1rem"},
        ),
        dcc.Graph(id="sc-estado"),
        dcc.Graph(id="sc-padron-dl"),
        dcc.Graph(id="sc-pob-dl"),
        html.H3("Municipios"),
        dcc.Dropdown(
            id="sc-mun",
            options=[{"label": m, "value": m} for m in _MUNICIPIOS],
            value=_MUN_DEFAULT,
            multi=True,
            style={"maxWidth": "560px"},
        ),
        dcc.Graph(id="sc-mun-fig"),
    ]
)


@callback(
    Output("sc-delta-pob", "value"),
    Output("sc-delta-pad", "value"),
    Input("sc-escenario", "value"),
    Input("sc-fpob", "data"),
    Input("sc-fpad", "data"),
)
def _sincroniza_sliders(escenario: str, f_pob: dict, f_pad: dict):
    """Al elegir escenario, los deslizadores toman su factor guardado."""
    return f_pob[escenario], f_pad[escenario]


@callback(
    Output("sc-fpob", "data"),
    Output("sc-fpad", "data"),
    Input("sc-delta-pob", "value"),
    Input("sc-delta-pad", "value"),
    Input("sc-escenario", "value"),
    State("sc-fpob", "data"),
    State("sc-fpad", "data"),
)
def _guarda_factores(v_pob: float, v_pad: float, escenario: str, f_pob: dict, f_pad: dict):
    """Al mover un deslizador, el factor del escenario activo se actualiza."""
    return {**f_pob, escenario: v_pob}, {**f_pad, escenario: v_pad}


@callback(
    Output("sc-geo-note", "children"),
    Output("sc-estado", "figure"),
    Output("sc-padron-dl", "figure"),
    Output("sc-pob-dl", "figure"),
    Output("sc-mun-fig", "figure"),
    Input("sc-driver", "value"),
    Input("sc-escenario", "value"),
    Input("sc-mun", "value"),
    Input("sc-fpob", "data"),
    Input("sc-fpad", "data"),
    Input("geo-fija", "data"),
)
def _actualiza(
    driver: str,
    escenario: str,
    municipios: list[str],
    f_pob: dict,
    f_pad: dict,
    geo_anio: int,
):
    e = data.escenarios_custom(
        tuple(1.0 + f_pob[k] for k in ("bajo", "base", "alto")),
        tuple(1.0 + f_pad[k] for k in ("bajo", "base", "alto")),
        geo_anio or None,
    )
    return (
        geo.nota(geo_anio),
        figures.fig_escenarios_estado(e["poblacion_est"], e["padron_est"], driver),
        figures.fig_padron_dl(e["padron_dl"], driver),
        figures.fig_pob_dl(e["poblacion_dl"], escenario),
        figures.fig_mun_escenario(e["poblacion_mun"], municipios or _MUN_DEFAULT),
    )
