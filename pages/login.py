#pages/login.py
from dash import html, dcc

layout = html.Div([
    dcc.Location(id="url-login"),  # ⬅️ Necessário pro redirecionamento

    html.Div([
        html.Img(src="/assets/allspark_logo.png", style={"width": "240px", "marginBottom": "20px", "borderRadius": "8px"}),
        html.H2("🔐 Login", style={"marginBottom": "20px"}),
        dcc.Input(id="username", type="text", placeholder="Usuário"),
        dcc.Input(id="password", type="password", placeholder="Senha"),
        html.Button("Entrar", id="login-button", n_clicks=0),
        html.Div(id="login-message", style={"marginTop": "10px", "color": "salmon"}),
        html.Button(id="logout-button", style={"display": "none"})
    ], className="login-container")
])
