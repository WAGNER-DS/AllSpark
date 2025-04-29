#apps/admin/usuarios_callbacks.py
from dash import Input, Output, State, html, dash_table
from core.db import get_connection

def registrar_usuarios_callbacks(app):
    # Preencher dropdown de perfis ao iniciar
    @app.callback(
        Output("novo-perfil", "options"),
        Input("carregar-usuarios-trigger", "n_intervals"),
        prevent_initial_call=False
    )
    def carregar_perfis(_):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM perfis ORDER BY nome")
            perfis = cursor.fetchall()
            conn.close()
            return [{"label": nome, "value": id} for id, nome in perfis]
        except Exception as e:
            return []

    # Criar novo usuário e atualizar tabela
    @app.callback(
        Output("mensagem-usuario", "children"),
        Output("tabela-usuarios", "children", allow_duplicate=True),  # ⚡️ Permite duplicação!
        Input("botao-criar-usuario", "n_clicks"),
        State("novo-nome", "value"),
        State("novo-email", "value"),
        State("nova-senha", "value"),
        State("novo-perfil", "value"),
        prevent_initial_call=True
    )
    def criar_usuario(n_clicks, nome, email, senha, perfil_id):
        if not all([nome, email, senha, perfil_id]):
            return "⚠️ Preencha todos os campos.", atualizar_tabela_usuarios()
    
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO usuarios (nome, senha, email, perfil_id)
                        VALUES (%s, %s, %s, %s)
                    """, (nome, senha, email, perfil_id))
                    conn.commit()
            return "✅ Usuário criado com sucesso!", atualizar_tabela_usuarios()
        except Exception as e:
            return f"❌ Erro: {e}", atualizar_tabela_usuarios()

    # Carrega a tabela ao iniciar o painel
    @app.callback(
        Output("tabela-usuarios", "children"),
        Input("carregar-usuarios-trigger", "n_intervals"),
        prevent_initial_call=False
    )
    def carregar_tabela(_):
        return atualizar_tabela_usuarios()


def atualizar_tabela_usuarios():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.nome, u.email, p.nome as perfil
                    FROM usuarios u
                    JOIN perfis p ON u.perfil_id = p.id
                    ORDER BY u.id
                """)
                dados = cursor.fetchall()

        colunas = ["Nome", "Email", "Perfil"]
        df = [dict(zip(colunas, linha)) for linha in dados]

        return dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in colunas],
            data=df,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "left", "padding": "8px",
                "backgroundColor": "#111", "color": "white"
            },
            style_header={
                "backgroundColor": "#222", "fontWeight": "bold", "color": "#00ffaa"
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#1a1a1a"}
            ],
            page_size=10
        )
    except Exception as e:
        return html.Div(f"Erro ao carregar usuários: {e}", style={"color": "red"})
