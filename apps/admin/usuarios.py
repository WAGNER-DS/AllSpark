#apps/admin/usuarios.py
from dash import html, dcc

def layout(session_data=None):
    return html.Div([
        html.H3("👤 Gerenciar Usuários", style={"color": "#00ffaa"}),

        html.Div([
            html.Label("Nome"),
            dcc.Input(id="novo-nome", type="text", placeholder="Nome do usuário"),

            html.Label("Email"),
            dcc.Input(id="novo-email", type="email", placeholder="Email"),

            html.Label("Senha"),
            dcc.Input(id="nova-senha", type="password", placeholder="Senha"),

            html.Label("Perfil"),
            dcc.Dropdown(id="novo-perfil", placeholder="Selecione o perfil"),

            html.Button("➕ Criar Usuário", id="botao-criar-usuario", n_clicks=0),

            html.Div(id="mensagem-usuario")
        ], className="admin-form"),

        html.Hr(),

        html.H4("📋 Usuários cadastrados"),
        html.Div(id="tabela-usuarios")
    ], className="admin-content")

