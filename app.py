#app.py
# app.py
import dash
from dash import dcc, html, Input, Output, State, ctx, no_update, ALL
from flask import Flask

# Sessão e callbacks
from core.session import user_session
from core.login_callbacks import registrar_login_callbacks
from apps.app_otdr_view.callbacks import registrar_callbacks
from utils.logger import inicializar_db

from apps.admin.callbacks import registrar_callbacks_admin
#from core.setup_db_postgres import criar_banco_postgres

# Páginas
from pages import login, hub, not_found

# Inicializa servidor Flask + Dash
server = Flask(__name__)
#app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)
app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks="initial_duplicate")

# Registra callbacks
registrar_login_callbacks(app)
registrar_callbacks(app)
registrar_callbacks_admin(app)



#try:
#    criar_banco_postgres()
#except Exception as e:
#    print(f"Erro inicializando banco: {e}")

try:
    inicializar_db()
except Exception as e:
    print(f"Erro inicializando o banco: {e}")


# Layout principal com Store persistente
app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="login-store", storage_type="local"),  # 🔒 Armazena no navegador
    html.Div(id="page-content")
])

# Restaura sessão no servidor
@app.callback(
    Output("page-content", "children", allow_duplicate=True),
    Input("login-store", "data"),
    prevent_initial_call="initial_duplicate"
)
def restaurar_sessao(data):
    if data and data.get("user"):
        user_session["user"] = data["user"]
        user_session["perfil_id"] = data["perfil_id"]
        user_session["apps_permitidos"] = data["apps_permitidos"]
    return no_update

# Callback de navegação com segurança
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input({"type": "app-button", "rota": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def navegar_via_botao(n_clicks_list):
    gatilho = ctx.triggered_id
    if not gatilho or not isinstance(gatilho, dict):
        return no_update

    index = [i for i, n in enumerate(n_clicks_list) if n]
    if not index:
        return no_update

    return gatilho["rota"]

# Roteador principal
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("url", "search"),  # Inclui parâmetros GET
    State("login-store", "data")
)
def roteador(pathname, search, session_data):
    print(f"📌 PATH: {pathname}")
    print(f"🔍 SEARCH: {search}")
    print(f"📦 Session Data: {session_data}")

    try:
        user = session_data.get("user") if session_data else None

        if not user and pathname != "/login":
            return login.layout

        if pathname in ["/", "/login"]:
            return login.layout
        elif pathname == "/hub":
            return hub.layout(session_data)
        elif pathname.startswith("/admin_dashboard"):
            from apps.admin.dashboard import layout as admin_layout
            return admin_layout(session_data)
        elif pathname == "/app_postes":
            from apps.app_postes.layout import layout as app_postes_layout
            return app_postes_layout(session_data)
        elif pathname == "/app_preventiva":
            from apps.app_preventiva.layout import layout as app_preventiva_layout
            return app_preventiva_layout(session_data)
        elif pathname == "/app_alivio":
            from apps.app_alivio.layout import layout as app_alivio_layout
            return app_alivio_layout(session_data)
        elif pathname == "/app_B2B":
            from apps.app_B2B.layout import layout as app_b2b_layout
            return app_b2b_layout(session_data)
        elif pathname == "/app_OSP_diagnostics":
            from apps.app_OSP_diagnostics.layout import layout as app_diag_layout
            return app_diag_layout(session_data)
        elif pathname == "/app_projeto":
            from apps.app_projeto.layout import layout as app_projeto_layout
            return app_projeto_layout(session_data)
        elif pathname == "/app_radar_cto":
            from apps.app_radar_cto.layout import layout as app_radar_layout
            return app_radar_layout(session_data)
        elif pathname == "/app_otdr_view":
            from apps.app_otdr_view.layout import layout as app_otdr_view_layout
            return app_otdr_view_layout(session_data)
        elif pathname == "/app_otdr_logs":
            from apps.app_otdr_view.logs import layout as logs_layout
            return logs_layout(session_data)

        return not_found.layout()
    
    except Exception as e:
        print(f"❌ Erro no roteador: {e}")
        return html.Div([
            html.H3("❌ Erro interno no roteador", style={"color": "red"}),
            html.Pre(str(e), style={"color": "salmon"})
        ])

# Executa
if __name__ == "__main__":
    #app.run(debug=True)
    app.run(debug=True, host="0.0.0.0", port=8050)
