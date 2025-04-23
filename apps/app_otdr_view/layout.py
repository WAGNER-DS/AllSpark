# apps/app_otdr_view/layout.py
# apps/app_otdr_view/layout.py
from dash import html, dcc
from core.session import user_session

def layout(session_data=None):
    user = session_data.get("user") if session_data else user_session.get("user")
    perfil_id = session_data.get("perfil_id") if session_data else user_session.get("perfil_id")
    apps = session_data.get("apps_permitidos") if session_data else user_session.get("apps_permitidos")

    if not user or not apps:
        return html.Div("⏳ Aguardando sessão...", style={"color": "white", "padding": "40px"})

    rotas = [app["rota"] for app in apps]
    if "/app_otdr_view" not in rotas:
        return html.Div("🔒 Acesso não autorizado", style={"color": "red", "padding": "40px"})

    # Engrenagem visível apenas para admin
    admin_gear = html.Div([
        dcc.Link("⚙️", href="/app_otdr_logs", style={
            "color": "white", "textDecoration": "none",
            "fontSize": "24px", "position": "absolute", "top": "20px", "right": "30px",
            "cursor": "pointer"
        })
    ]) if perfil_id == 1 else None

    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Img(src="/assets/allspark_otdr.png", className="logo-icon"),
                    html.Div("AllSpark Net - OTDR View", className="logo-text")
                ], className="logo-wrapper"),
                admin_gear
            ], className="topbar-inner")
        ], className="topbar-externa"),

        html.Div([
            html.Div([

                html.Label("UF"),
                dcc.Dropdown(id="dropdown-uf", placeholder="Selecione o Estado (UF)"),

                html.Label("Município"),
                dcc.Dropdown(id="dropdown-municipio", placeholder="Selecione o Município"),

                html.Label("CTO"),
                dcc.Dropdown(id="dropdown-cto", placeholder="Digite ou selecione a CTO"),

                html.Label("📏 Distância OTDR (m)"),
                dcc.Input(id="input-otdr", type="text", placeholder="Digite somente números", style={"height": "40px"}),

                html.Div([
                    html.Button("📍 Processar e TraceBack", id="botao-processar", n_clicks=0)
                ], className="botao-wrapper"),

                html.Div(id="output-info-cto", style={"paddingTop": "30px", "color": "white"}),
                dcc.Store(id="mapa-html-store", storage_type="session")
            ], className="filtros-container", style={"maxWidth": "1400px", "margin": "0 auto"})
        ]),

        html.Button(id="login-button", style={"display": "none"}),
        html.Div(id="login-message", style={"display": "none"}),
        dcc.Input(id="username", style={"display": "none"}),
        dcc.Input(id="password", style={"display": "none"})
    ])
