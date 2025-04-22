from dash import html

def layout(session_data):
    user = session_data.get("user") if session_data else None
    if not user:
        return dcc.Location(href="/login", id="redirect")

    return html.Div([
        html.H2("🛠️ App: Preventiva", style={"color": "#00f7ff"}),
        html.P("🚧 Work In Progress", style={"color": "#ccc", "fontSize": "20px"})
    ], style={"padding": "60px"})
