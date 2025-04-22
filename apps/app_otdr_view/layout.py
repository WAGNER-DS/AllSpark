#apps/app_otdr_view/layout.py
#apps/app_otdr_view/layout.py
from dash import html, dcc
from core.session import user_session

def layout(session_data=None):
    print("🔍 Sessão recebida em app_otdr_view:", session_data)

    # Recupera user e apps da sessão
    user = session_data.get("user") if session_data else user_session.get("user")
    apps = session_data.get("apps_permitidos") if session_data else user_session.get("apps_permitidos")

    # Aguarda sessão ser restaurada
    if not user or not apps:
        return html.Div("⏳ Aguardando sessão...", style={"color": "white", "padding": "40px"})

    # Garante que o app está autorizado
    rotas = [app["rota"] for app in apps]
    if "/app_otdr_view" not in rotas:
        return html.Div("🔒 Acesso não autorizado", style={"color": "red", "padding": "40px"})

    # Layout principal do OTDR View
    return html.Div([

        # 🔝 Cabeçalho
        html.Div([
            html.Div([
                html.Div([
                    html.Img(src="/assets/allspark_otdr.png", className="logo-icon"),
                    html.Div("AllSpark Net - OTDR View", className="logo-text")
                ], className="logo-wrapper"),
            ], className="topbar-inner")
        ], className="topbar-externa"),

        # 📦 Conteúdo Principal
        html.Div([
            html.Div([

                html.Label("UF"),
                dcc.Dropdown(id="dropdown-uf", placeholder="Selecione o Estado (UF)"),

                html.Label("Município"),
                dcc.Dropdown(id="dropdown-municipio", placeholder="Selecione o Município"),

                html.Label("CTO"),
                dcc.Dropdown(id="dropdown-cto", placeholder="Digite ou selecione a CTO"),

                html.Label("📏 Distância OTDR (m)"),
                dcc.Input(
                    id="input-otdr",
                    type="text",
                    placeholder="Digite somente números",
                    style={"height": "40px"}
                ),

                html.Div([
                    html.Button("📍 Processar e TraceBack", id="botao-processar", n_clicks=0)
                ], className="botao-wrapper"),

                # 📤 Resultado (info + mapa)
                html.Div(
                    id="output-info-cto",
                    style={
                        "paddingTop": "30px",
                        "color": "white"
                    }
                ),

                dcc.Store(id="mapa-html-store", storage_type="session")
            ], className="filtros-container", style={"maxWidth": "1400px", "margin": "0 auto"})
        ]),
        


        html.Button(id="login-button", style={"display": "none"}),
        html.Div(id="login-message", style={"display": "none"}),
        dcc.Input(id="username", style={"display": "none"}),
        dcc.Input(id="password", style={"display": "none"})
    ])
