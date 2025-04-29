#apps/admin/usuarios_callbacks.py
from dash import Input, Output, State, html, dash_table
from core.db import get_connection

def registrar_usuarios_callbacks(app):
    # Preencher dropdown de perfis
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
            print("🔎 Perfis encontrados:", perfis)  # DEBUG
            return [{"label": nome, "value": id} for id, nome in perfis]
        except Exception as e:
            print("❌ Erro ao carregar perfis:", e)  # DEBUG
            return []

    # Criar novo usuário
    @app.callback(
        Output("mensagem-usuario", "children"),
        Output("tabela-usuarios", "children"),
        Input("botao-criar-usuario", "n_clicks"),
        State("novo-nome", "value"),
        State("novo-email", "value"),
        State("nova-senha", "value"),
        State("novo-perfil", "value"),
        prevent_initial_call=True
    )
    def criar_usuario(n_clicks, nome, email, senha, perfil_id):
        if not all([nome, email, senha, perfil_id]):
            print("⚠️ Campos obrigatórios não preenchidos")  # DEBUG
            return "⚠️ Preencha todos os campos.", atualizar_tabela_usuarios()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nome, senha, email, perfil_id)
                VALUES (%s, %s, %s, %s)
            """, (nome, senha, email, perfil_id))
            conn.commit()
            conn.close()
            print(f"✅ Usuário {nome} criado com sucesso!")  # DEBUG
            return "✅ Usuário criado com sucesso!", atualizar_tabela_usuarios()
        except Exception as e:
            print("❌ Erro ao criar usuário:", e)  # DEBUG
            return f"❌ Erro: {e}", atualizar_tabela_usuarios()

    # Carrega a tabela de usuários ao iniciar
    @app.callback(
        Output("tabela-usuarios", "children"),
        Input("carregar-usuarios-trigger", "n_intervals"),
        prevent_initial_call=False
    )
    def carregar_tabela(_):
        return atualizar_tabela_usuarios()


def atualizar_tabela_usuarios():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.nome, u.email, p.nome as perfil
            FROM usuarios u
            JOIN perfis p ON u.perfil_id = p.id
            ORDER BY u.id
        """)
        dados = cursor.fetchall()
        conn.close()
        print("👥 Usuários carregados:", dados)  # DEBUG

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
        print("❌ Erro ao carregar usuários:", e)  # DEBUG
        return html.Div(f"Erro ao carregar usuários: {e}", style={"color": "red"})
