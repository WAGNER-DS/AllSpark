from dash import html, dcc, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
from core.db import get_connection
import pandas as pd

# Layout da página de administração de usuários
def layout(session_data=None):
    perfil_id = session_data.get("perfil_id") if session_data else None
    if perfil_id != 1:
        return html.Div("🔒 Acesso restrito a administradores.", style={"color": "red", "padding": "40px"})

    return html.Div([
        html.H3("👥 Gerenciar Usuários", style={"marginBottom": "20px", "color": "#00ffaa"}),

        html.Div([
            dcc.Input(id="input-nome", type="text", placeholder="Nome do Usuário", style={"marginRight": "10px"}),
            dcc.Input(id="input-email", type="email", placeholder="Email", style={"marginRight": "10px"}),
            dcc.Input(id="input-senha", type="password", placeholder="Senha", style={"marginRight": "10px"}),
            dcc.Dropdown(id="dropdown-perfil", placeholder="Perfil", style={"width": "200px", "display": "inline-block"}),
            html.Button("➕ Criar", id="botao-criar-usuario", n_clicks=0, style={"marginLeft": "10px"}),
        ], style={"marginBottom": "20px"}),

        html.Div(id="mensagem-usuario", style={"marginBottom": "20px", "color": "green"}),

        html.Hr(),

        html.Div(id="tabela-usuarios"),

        dcc.Interval(id="interval-refresh", interval=1000, n_intervals=0, max_intervals=1)
    ], style={"padding": "30px"})
