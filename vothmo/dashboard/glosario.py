"""Pestaña de glosario del tablero Dash."""

from dash import dcc, html

from vothmo.dashboard.narrativa import glosario_md

layout = html.Div(children=[dcc.Markdown(glosario_md(), mathjax=True)])
