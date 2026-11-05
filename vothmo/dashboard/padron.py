"""Pestaña padrón vs población del tablero Dash."""

from dash import Input, Output, callback, dash_table, dcc, html
import pandas as pd

from vothmo.dashboard import data, figures, geo

_PAD, _LN = data.padron_anual()

layout = html.Div(
    children=[
        html.H2("Padrón electoral vs población"),
        html.Div(id="pd-geo-note"),
        dcc.Graph(
            figure=figures.fig_padron_poblacion(
                _PAD, _LN, data.conapo_estado(), data.inegi_estado()
            )
        ),
        dcc.Graph(figure=figures.fig_razon_estado(data.razon_estado())),
        html.H3("Razón padrón / población 18+ por municipio"),
        html.Label("Año de cartografía"),
        dcc.Dropdown(
            id="pd-anio",
            options=[{"label": str(a), "value": a} for a in data.MAP_YEARS],
            value=data.MAP_YEARS[-1],
            clearable=False,
            style={"maxWidth": "240px"},
        ),
        dcc.Graph(id="pd-mapa"),
        html.H3("Razón padrón / población 18+ por distrito local"),
        dcc.Graph(id="pd-mapa-dl"),
        html.H4("Municipios extremos"),
        html.Div(id="pd-tabla"),
    ]
)


@callback(
    Output("pd-geo-note", "children"),
    Output("pd-mapa", "figure"),
    Output("pd-mapa-dl", "figure"),
    Output("pd-tabla", "children"),
    Input("pd-anio", "value"),
    Input("geo-fija", "data"),
)
def _actualiza(anio: int, geo_anio: int):
    rm = data.razon_mun(anio)
    cols = ["nom_mun", "pad", "pob18", "razon_18"]
    tabla = (
        pd.concat([rm.nlargest(6, "razon_18"), rm.nsmallest(6, "razon_18")])[cols]
        .assign(pad=lambda d: d["pad"].round(0), pob18=lambda d: d["pob18"].round(0))
        .round({"razon_18": 3})
    )
    dt = dash_table.DataTable(
        data=tabla.to_dict("records"),
        columns=[{"name": c, "id": c} for c in tabla.columns],
        style_table={"maxWidth": "640px"},
        style_cell={"textAlign": "left"},
    )
    anio_dl = geo_anio or anio
    return (
        geo.nota(geo_anio),
        figures.fig_mapa_razon_mun(data.municipios_geo(anio), anio),
        figures.fig_mapa_razon_dl(data.distritos_razon(anio_dl), anio_dl),
        dt,
    )
