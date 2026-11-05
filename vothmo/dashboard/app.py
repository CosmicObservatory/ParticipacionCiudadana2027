"""Tablero Dash: análisis electoral y poblacional de Sonora.

La ruta ``/`` muestra la portada-historia; la herramienta con las pestañas
vive en ``/herramienta``.

Ejecutar desde la raíz del repo:

    uv run python -m vothmo.dashboard.app
"""

from dash import Dash, Input, Output, callback, dcc, html

from vothmo.dashboard import (
    conclusions,
    distribucion,
    glosario,
    historia,
    intro,
    padron,
    scenario,
    stats,
)

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Votación Sonora"


def _herramienta() -> html.Div:
    """Las pestañas de análisis; solo se renderizan bajo /herramienta."""
    return html.Div(
        children=[
            html.H1("Participación Ciudadana 2027 · Sonora"),
            dcc.Tabs(
                id="principal",
                value="tab-0",
                children=[
                    dcc.Tab(label="Primeros Pasos", value="tab-0", children=intro.content),
                    dcc.Tab(label="Demografía Electoral", value="tab-1", children=stats.layout),
                    dcc.Tab(
                        label="Distribución Seccional",
                        value="tab-1b",
                        children=distribucion.layout,
                    ),
                    dcc.Tab(label="Padrón vs Población", value="tab-2", children=padron.layout),
                    dcc.Tab(label="Crecimiento", value="tab-3", children=scenario.layout),
                    dcc.Tab(label="Conclusiones", value="tab-4", children=conclusions.layout),
                    dcc.Tab(label="Glosario", value="tab-5", children=glosario.layout),
                ],
            ),
        ]
    )


app.layout = html.Div(
    children=[
        dcc.Location(id="url", refresh=False),
        # 0 = distribución del año correspondiente; se fija al final de
        # Distribución Seccional y solo afecta a las pestañas posteriores.
        dcc.Store(id="geo-fija", data=0),
        html.Div(id="pagina"),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto", "fontFamily": "sans-serif"},
)


@callback(Output("pagina", "children"), Input("url", "pathname"))
def _rutea(pathname: str | None) -> html.Div:
    """Historia en la raíz; las pestañas solo al entrar a la herramienta."""
    if pathname == "/herramienta":
        return _herramienta()
    return historia.layout


if __name__ == "__main__":
    app.run(debug=True)
