#apps/admin/usuarios.py
from dash import html, dcc

def layout(session_data=None):
    return html.Div([
        html.H3("👤 Gerenciar Usuários", style={"color": "#00ffaa"}),

        html.Div([
            html.Label("Nome", style={"marginTop": "10px"}),
            dcc.Input(id="novo-nome", type="text", placeholder="Nome do usuário", style={"width": "100%"}),

            html.Label("Email", style={"marginTop": "10px"}),
            dcc.Input(id="novo-email", type="email", placeholder="Email", style={"width": "100%"}),

            html.Label("Senha", style={"marginTop": "10px"}),
            dcc.Input(id="nova-senha", type="password", placeholder="Senha", style={"width": "100%"}),

            html.Label("Perfil", style={"marginTop": "10px"}),
            dcc.Dropdown(id="novo-perfil", placeholder="Selecione o perfil", style={"width": "100%"}),

            html.Button("➕ Criar Usuário", id="botao-criar-usuario", n_clicks=0,
                        style={
                            "marginTop": "15px", "backgroundColor": "#1f4e79",
                            "color": "white", "padding": "10px", "border": "none",
                            "borderRadius": "5px", "width": "100%"
                        }),

            html.Div(id="mensagem-usuario", style={"marginTop": "10px", "color": "lightgreen"})
        ], style={
            "backgroundColor": "#222", "padding": "20px", "borderRadius": "8px",
            "marginBottom": "30px", "width": "100%", "maxWidth": "600px"
        }),

        html.Hr(),

        html.H4("📋 Usuários cadastrados"),
        html.Div(id="tabela-usuarios", style={"marginTop": "20px"}),

        # 🔁 Trigger oculto para forçar carregamento automático de dados
        dcc.Interval(id="carregar-usuarios-trigger", interval=100, n_intervals=0)
    ], className="admin-content", style={"padding": "20px"})
