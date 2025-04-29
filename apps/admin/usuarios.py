from dash import html, dcc, dash_table

def layout(session_data=None):
    return html.Div([
        html.H3("👤 Gerenciar Usuários", style={"color": "#00ffaa"}),

        html.Div([
            html.Label("Nome"),
            dcc.Input(id="novo-nome", type="text", placeholder="Nome do usuário", style={"width": "100%"}),

            html.Label("Email"),
            dcc.Input(id="novo-email", type="email", placeholder="Email", style={"width": "100%"}),

            html.Label("Senha"),
            dcc.Input(id="nova-senha", type="password", placeholder="Senha", style={"width": "100%"}),

            html.Label("Perfil"),
            dcc.Dropdown(id="novo-perfil", placeholder="Selecione o perfil"),

            html.Button("➕ Criar Usuário", id="botao-criar-usuario", n_clicks=0,
                        style={"marginTop": "10px", "backgroundColor": "#1f4e79", "color": "white"}),

            html.Div(id="mensagem-usuario", style={"marginTop": "10px", "color": "lightgreen"})
        ], style={
            "backgroundColor": "#222", "padding": "20px", "borderRadius": "8px",
            "marginBottom": "30px", "width": "100%", "maxWidth": "600px"
        }),

        html.Hr(),

        html.H4("📋 Usuários cadastrados"),
        html.Div(id="tabela-usuarios")
    ])
