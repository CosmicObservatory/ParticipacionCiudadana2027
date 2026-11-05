"""Pestaña de demografía electoral del tablero Dash."""

from dash import Input, Output, callback, dcc, html

from vothmo.dashboard import data, figures

_ANIOS = data.anios_elec()

layout = html.Div(
    children=[
        html.H2("Demografía electoral"),
        html.Label("Elección"),
        dcc.Dropdown(
            id="st-anio",
            options=[{"label": str(a), "value": a} for a in _ANIOS],
            value=_ANIOS[-1],
            clearable=False,
            style={"maxWidth": "240px"},
        ),
        html.Div(id="st-kpis", style={"display": "flex", "gap": "2rem", "margin": "1rem 0"}),
        dcc.Graph(id="st-piramide"),
        dcc.Graph(id="st-pc-edad"),
        html.H3("Mapa por distrito local"),
        dcc.RadioItems(
            id="st-mapa-var",
            options=[
                {"label": "Participación (%)", "value": "pc"},
                {"label": "Lista nominal", "value": "ln"},
            ],
            value="pc",
            inline=True,
        ),
        dcc.Graph(id="st-mapa"),
        dcc.Graph(id="st-rank-dl"),
        dcc.Graph(id="st-rank-mun"),
    ]
)


def _kpi(titulo: str, valor: str) -> html.Div:
    return html.Div(
        [
            html.Div(titulo, style={"fontSize": "0.85rem", "color": "#666"}),
            html.Div(valor, style={"fontSize": "1.5rem", "fontWeight": "bold"}),
        ]
    )


@callback(
    Output("st-kpis", "children"),
    Output("st-piramide", "figure"),
    Output("st-pc-edad", "figure"),
    Output("st-mapa", "figure"),
    Output("st-rank-dl", "figure"),
    Output("st-rank-mun", "figure"),
    Input("st-anio", "value"),
    Input("st-mapa-var", "value"),
)
def _actualiza(anio: int, var_mapa: str):
    r = data.resumen_anual()
    fila = r[r["aelec"] == anio].iloc[0]
    n_sec = data.conteos()[data.conteos()["aelec"] == anio]["seccion"].nunique()
    kpis = [
        _kpi("Lista nominal", f"{fila['ln']:,.0f}"),
        _kpi("Participación", f"{fila['pc']:.1f}%"),
        _kpi("Secciones", f"{n_sec:,}"),
        _kpi("Elección", str(anio)),
    ]
    return (
        kpis,
        figures.fig_piramide(data.piramide(anio), anio),
        figures.fig_participacion_edad(data.participacion_edad(anio), anio),
        figures.fig_mapa_distritos(data.distritos_geo(anio), var_mapa, anio),
        figures.fig_ranking_distritos(data.por_distrito(anio), var_mapa, anio),
        figures.fig_ranking(
            data.por_municipio(anio),
            x="mpionom",
            titulo=f"Municipios con mayor lista nominal · {anio}",
        ),
    )
