#apps/app_otdr_view/callbacks.py
#apps/app_otdr_view/callbacks.py

import os
import pandas as pd
import folium
from folium.plugins import Draw, Fullscreen, LocateControl
from folium import LayerControl
from geopy.distance import geodesic
from dash import Input, Output, State, html, dcc
from flask import request
from utils.logger import inicializar_db, registrar_consulta
from core.session import user_session
import sqlite3
from io import BytesIO
import datetime
import dash
    

# Caminho para o CSV de cidades
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CIDADES_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "data", "cidades.csv"))

# Função auxiliar para capturar o IP

def get_user_ip():
    try:
        return request.headers.get('X-Forwarded-For', request.remote_addr)
    except Exception:
        return "unknown"

# Funções auxiliares: encontrar ponto por distância, deslocar linhas, normalizar sequências, etc.
# (Essas funções serão usadas na lógica de processamento do mapa)

# Função principal para registrar os callbacks

def registrar_callbacks(app):

    # 📌 1. Carregar UFs
    @app.callback(
        Output("dropdown-uf", "options"),
        Input("dropdown-uf", "id")
    )
    def carregar_ufs(_):
        try:
            df_cidades = pd.read_csv(CIDADES_PATH, sep=";")
            return [{"label": uf, "value": uf} for uf in sorted(df_cidades["UF"].dropna().unique())]
        except Exception as e:
            return []

    # 📌 2. Atualizar Municípios
    @app.callback(
        Output("dropdown-municipio", "options"),
        Input("dropdown-uf", "value")
    )
    def atualizar_municipios(uf):
        if not uf:
            return []
        try:
            df_cidades = pd.read_csv(CIDADES_PATH, sep=";")
            municipios = df_cidades[df_cidades["UF"] == uf]["MUNICIPIO"].dropna().unique()
            return [{"label": m, "value": m} for m in sorted(municipios)]
        except Exception as e:
            return []

    # 📌 3. Atualizar CTOs
    @app.callback(
        Output("dropdown-cto", "options"),
        Input("dropdown-municipio", "value")
    )
    def atualizar_ctos(municipio):
        if not municipio:
            return []
        municipio_folder = municipio.upper().replace(" ", "_")
        caminho_cto = os.path.join("data", "INVENTORY", "CABOS", municipio_folder, "cto.csv")
        if not os.path.exists(caminho_cto):
            return []
        try:
            df_cto = pd.read_csv(caminho_cto, sep=";")
            return [{"label": cto, "value": cto} for cto in sorted(df_cto["CTO_NAME"].dropna().unique())]
        except Exception as e:
            return []

    # 🔄 4. Limpar resultado e mapa se trocar UF, Município, CTO ou clicar Processar sem preencher
    @app.callback(
        Output("output-info-cto", "children"),
        Output("mapa-html-store", "data"),
        Input("dropdown-uf", "value"),
        Input("dropdown-municipio", "value"),
        Input("dropdown-cto", "value"),
        Input("botao-processar", "n_clicks"),
        State("dropdown-uf", "value"),
        State("dropdown-municipio", "value"),
        State("dropdown-cto", "value"),
        prevent_initial_call=True
    )
    def limpar_tela_ao_mudar(uf, municipio, cto, n_clicks, uf_state, municipio_state, cto_state):
        triggered_id = dash.callback_context.triggered_id

        if triggered_id == "botao-processar" and not all([uf_state, municipio_state, cto_state]):
            return None, None

        if triggered_id in ["dropdown-uf", "dropdown-municipio", "dropdown-cto"]:
            return None, None

        return dash.no_update, dash.no_update

    # 📌 5. Botão Processar -> gera o mapa
    @app.callback(
        Output("output-info-cto", "children", allow_duplicate=True),
        Output("mapa-html-store", "data", allow_duplicate=True),
        Input("botao-processar", "n_clicks"),
        State("dropdown-uf", "value"),
        State("dropdown-municipio", "value"),
        State("dropdown-cto", "value"),
        State("input-otdr", "value"),
        prevent_initial_call=True
    )
    def processar_dados(n_clicks, uf, municipio, cto, distancia_otdr):
        import pandas as pd
        if not all([uf, municipio, cto]):
            return html.Div("⚠️ Por favor, selecione UF, município e CTO.")

        municipio_folder = municipio.upper().replace(" ", "_")
        caminho_cto = os.path.join("data", "INVENTORY", "CABOS", municipio_folder, "cto.csv")
        caminho_primarios = os.path.join("data", "INVENTORY", "CABOS", municipio_folder, "cabos_primarios_group.csv")
        caminho_secundarios = os.path.join("data", "INVENTORY", "CABOS", municipio_folder, "cabos_secundarios_group.csv")
        caminho_tracados = os.path.join("data", "INVENTORY", "CABOS", municipio_folder, "cabos_tracados.csv")

        if not all([uf, municipio, cto]):
            return html.Div("⚠️ Por favor, selecione UF, município e CTO."), None

        df_cto = pd.read_csv(caminho_cto, sep=";")
        df_cto = df_cto[df_cto["CTO_NAME"] == cto]
        uid_cto = df_cto.iloc[0]["UID_EQUIP"]
        cto_nome = df_cto.iloc[0]["CTO_NAME"]
        
        sec_filtrado = pd.DataFrame()
        prim_filtrado = pd.DataFrame()
        if os.path.exists(caminho_secundarios):
            df_sec = pd.read_csv(caminho_secundarios, sep='|')

            # Primeira tentativa: buscar no UID_EQUIPAMENTO_Z
            # Primeira tentativa: buscar no UID_EQUIPAMENTO_Z
            sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_Z"] == uid_cto].copy()

            if sec_filtrado.empty:
                # Tentar encontrar no UID_EQUIPAMENTO_A
                sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_A"] == uid_cto].copy()
                # Agora pode usar normalmente:
            
                if not sec_filtrado.empty:
                    # Realizar a inversão das colunas
                    sec_filtrado.rename(columns={
                        "UID_EQUIPAMENTO_A": "temp_uid",
                        "UID_EQUIPAMENTO_Z": "UID_EQUIPAMENTO_A",
                        "temp_uid": "UID_EQUIPAMENTO_Z",
                        
                        "EQUIPAMENTO_A": "temp_eq",
                        "EQUIPAMENTO_Z": "EQUIPAMENTO_A",
                        "temp_eq": "EQUIPAMENTO_Z",
                        
                        "NOME_EQUIPAMENTO_1": "temp_nome1",
                        "NOME_EQUIPAMENTO_2": "NOME_EQUIPAMENTO_1",
                        "temp_nome1": "NOME_EQUIPAMENTO_2",
                        
                        "EQUIPAMENTO_1": "temp_eq1",
                        "UID_EQUIPAMENTO_2": "EQUIPAMENTO_1",
                        "temp_eq1": "UID_EQUIPAMENTO_2"
                    }, inplace=True)
                distancia_secundario = sec_filtrado["COMPRIMENTO_GEOMETRICO"].sum()
            uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].unique().tolist()
        print(uid_ceos)
        #if os.path.exists(caminho_secundarios):
        #    df_sec = pd.read_csv(caminho_secundarios, sep='|')
        #    sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_Z"] == uid_cto]
        #    distancia_secundario = sec_filtrado["COMPRIMENTO_GEOMETRICO"].sum()
        #    uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].unique().tolist()


        if os.path.exists(caminho_primarios) and uid_ceos:
            df_prim = pd.read_csv(caminho_primarios, sep='|')
            prim_filtrado = df_prim[df_prim["UID_EQUIPAMENTO_Z"].isin(uid_ceos)]
            maximo = prim_filtrado['qtde_fibras'].max()
            prim_filtrado = prim_filtrado[prim_filtrado['qtde_fibras'] == maximo]
            distancia_primario = prim_filtrado["COMPRIMENTO_GEOMETRICO"].sum()

        from math import atan2, sin, cos
        def encontrar_ponto_por_distancia(coord_list, distancia_m):
            acumulado = 0
            for i in range(len(coord_list) - 1):
                ponto_atual = coord_list[i]
                proximo_ponto = coord_list[i + 1]
                dist = geodesic(ponto_atual, proximo_ponto).meters
                if acumulado + dist >= distancia_m:
                    # Proporção entre o ponto atual e o próximo
                    restante = distancia_m - acumulado
                    proporcao = restante / dist
                    lat = ponto_atual[0] + proporcao * (proximo_ponto[0] - ponto_atual[0])
                    lon = ponto_atual[1] + proporcao * (proximo_ponto[1] - ponto_atual[1])
                    return (lat, lon)
                acumulado += dist
            return coord_list[-1]  # Se a distância for maior que o trajeto

        # Função para deslocar uma linha (usado quando há duplicação de traçado)
        def deslocar_linha(lat1, lon1, lat2, lon2, offset):
            angle = atan2(lat2 - lat1, lon2 - lon1)
            perp_angle = angle + (3.1416 / 2)
            dlat = offset * sin(perp_angle)
            dlon = offset * cos(perp_angle)
            return [(lat1 + dlat, lon1 + dlon), (lat2 + dlat, lon2 + dlon)]
        
        def deslocar_linha_com_conexao(lat1, lon1, lat2, lon2, offset=0.00003):
            from math import atan2, sin, cos

            # Ângulo da linha
            angle = atan2(lat2 - lat1, lon2 - lon1)
            perp_angle = angle + (3.1416 / 2)

            # Deslocamento lateral
            dlat = offset * sin(perp_angle)
            dlon = offset * cos(perp_angle)

            # Pontos com deslocamento apenas no meio (início e fim reais)
            mid1 = (lat1 + (lat2 - lat1) * 0.25 + dlat, lon1 + (lon2 - lon1) * 0.25 + dlon)
            mid2 = (lat1 + (lat2 - lat1) * 0.75 + dlat, lon1 + (lon2 - lon1) * 0.75 + dlon)

            return [(lat1, lon1), mid1, mid2, (lat2, lon2)]




        if df_cto.empty:
            return html.Div("CTO não encontrada.")

        info = df_cto.iloc[0]
        uid_cto = info["UID_EQUIP"]
        lat = float(str(info["LATITUDE"]).replace(",", ".")) if pd.notna(info["LATITUDE"]) else 0
        lon = float(str(info["LONGITUDE"]).replace(",", ".")) if pd.notna(info["LONGITUDE"]) else 0

        distancia_prim = 0
        distancia_sec = 0
        
        uid_ceos = []
        df_sec = pd.DataFrame()
        df_prim = pd.DataFrame()

        if os.path.exists(caminho_secundarios):
            df_sec = pd.read_csv(caminho_secundarios, sep='|')

            # Primeira tentativa: buscar no UID_EQUIPAMENTO_Z
            # Primeira tentativa: buscar no UID_EQUIPAMENTO_Z
            sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_Z"] == uid_cto].copy()

            if sec_filtrado.empty:
                # Tentar encontrar no UID_EQUIPAMENTO_A
                sec_filtrado = df_sec[df_sec["UID_EQUIPAMENTO_A"] == uid_cto].copy()
                # Agora pode usar normalmente:
            
                if not sec_filtrado.empty:
                    # Realizar a inversão das colunas
                    sec_filtrado.rename(columns={
                        "UID_EQUIPAMENTO_A": "temp_uid",
                        "UID_EQUIPAMENTO_Z": "UID_EQUIPAMENTO_A",
                        "temp_uid": "UID_EQUIPAMENTO_Z",
                        
                        "EQUIPAMENTO_A": "temp_eq",
                        "EQUIPAMENTO_Z": "EQUIPAMENTO_A",
                        "temp_eq": "EQUIPAMENTO_Z",
                        
                        "NOME_EQUIPAMENTO_1": "temp_nome1",
                        "NOME_EQUIPAMENTO_2": "NOME_EQUIPAMENTO_1",
                        "temp_nome1": "NOME_EQUIPAMENTO_2",
                        
                        "EQUIPAMENTO_1": "temp_eq1",
                        "UID_EQUIPAMENTO_2": "EQUIPAMENTO_1",
                        "temp_eq1": "UID_EQUIPAMENTO_2"
                    }, inplace=True)
                distancia_sec = sec_filtrado["COMPRIMENTO_GEOMETRICO"].sum()
            uid_ceos = sec_filtrado["UID_EQUIPAMENTO_A"].unique().tolist()
    
                    



        if os.path.exists(caminho_primarios) and uid_ceos:
            df_prim = pd.read_csv(caminho_primarios, sep="|")
            df_prim = df_prim[df_prim["UID_EQUIPAMENTO_Z"].isin(uid_ceos)]
            if not df_prim.empty:
                max_fibra = df_prim["qtde_fibras"].max()
                df_prim = df_prim[df_prim["qtde_fibras"] == max_fibra]
                distancia_prim = df_prim["COMPRIMENTO_GEOMETRICO"].sum()

        distancia_total = distancia_sec + distancia_prim
        distancia_otdr = distancia_otdr if distancia_otdr else "N/A"
        armario=info['ARMARIO']
        # Mapa Folium
        mapa = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)
        # 1. Não colocar nenhuma camada base com show=True
        folium.TileLayer("OpenStreetMap", name="Padrão").add_to(mapa)

        # 3. Adiciona outras camadas de imagem depois (Satélite etc.)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Google Satélite',
            overlay=False,
            control=True
        ).add_to(mapa)

        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google Hybrid',
            name='Google Hybrid',
            overlay=False,
            control=True
        ).add_to(mapa)
        # 2. Adiciona a camada "Claro" por último (ela será a principal)
        folium.TileLayer("CartoDB positron", name="Claro").add_to(mapa)


        popup_html = f"""
        <b>CTO:</b> {cto_nome}<br>
        <a href="https://www.google.com/maps/dir/?api=1&destination={lat},{lon}" target="_blank">
        🗺️ Traçar rota até a CTO no Google Maps
        </a>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(icon="glyphicon glyphicon-screenshot", color="blue")
        ).add_to(mapa)
        ponto_cto = (lat, lon)

        if os.path.exists(caminho_tracados):
            df_tracados = pd.read_csv(caminho_tracados, sep='|')

            # 🎯 Filtrar os cabos conectados à CTO
            ids_sec = sec_filtrado["IDENTIFICADOR_UNICO_CABO_CONECTADO"].dropna().unique().tolist()
            df_sec = df_tracados[df_tracados["IDENTIFICADOR_UNICO_CABO"].isin(ids_sec)].copy()
            df_sec["origem"] = "sec"

            # 🧠 Merge para trazer o SEQUENCIAMENTO_DO_ENCAMINHAMENTO de sec_filtrado
            df_sec = df_sec.merge(
                sec_filtrado[["IDENTIFICADOR_UNICO_CABO_CONECTADO", "SEQUENCIAMENTO_DO_ENCAMINHAMENTO"]],
                left_on="IDENTIFICADOR_UNICO_CABO",
                right_on="IDENTIFICADOR_UNICO_CABO_CONECTADO",
                how="left"
            )


            ids_prim = prim_filtrado["IDENTIFICADOR_UNICO_CABO_CONECTADO"].dropna().unique().tolist()
            df_prim = df_tracados[df_tracados["IDENTIFICADOR_UNICO_CABO"].isin(ids_prim)].copy()
            df_prim["origem"] = "prim"

            # 🧠 Merge para trazer o SEQUENCIAMENTO_DO_ENCAMINHAMENTO de sec_filtrado
            df_prim = df_prim.merge(
                prim_filtrado[["IDENTIFICADOR_UNICO_CABO_CONECTADO", "SEQUENCIAMENTO_DO_ENCAMINHAMENTO"]],
                left_on="IDENTIFICADOR_UNICO_CABO",
                right_on="IDENTIFICADOR_UNICO_CABO_CONECTADO",
                how="left"
            )

            # 🔁 Concatenar os dados e criar uma chave única para cada traçado
            df_all = pd.concat([df_sec, df_prim], ignore_index=True)
            df_all["chave_tracado"] = df_all["UUID_LOCAL_TRACADO_INICIAL"].astype(str) + "_" + df_all["UUID_LOCAL_TRACADO_FINAL"].astype(str)
            chaves_duplicadas = df_all["chave_tracado"].duplicated(keep=False)

            # Criar camadas separadas
            camada_prim = folium.FeatureGroup(name="Cabos Primários", show=True)
            camada_sec = folium.FeatureGroup(name="Cabos Secundários", show=True)

            # Desenhar os cabos nas respectivas camadas
            for _, row in df_all.iterrows():
                try:
                    lat1 = float(str(row["LATITUDE_INICIAL"]).replace(',', '.'))
                    lon1 = float(str(row["LONGITUDE_INICIAL"]).replace(',', '.'))
                    lat2 = float(str(row["LATITUDE_FINAL"]).replace(',', '.'))
                    lon2 = float(str(row["LONGITUDE_FINAL"]).replace(',', '.'))

                    # Verifica se precisa aplicar deslocamento
                    offset = 0
                    if row["origem"] == "prim" and row["chave_tracado"] in df_all[chaves_duplicadas]["chave_tracado"].values:
                        coords = deslocar_linha_com_conexao(lat1, lon1, lat2, lon2, offset=0.00001)
                    else:
                        coords = [(lat1, lon1), (lat2, lon2)]

                    # Define a cor por tipo
                    cor = 'purple' if row["origem"] == "prim" else 'Blue'

                    polyline = folium.PolyLine(
                        locations=coords,
                        color=cor,
                        weight=4,
                        opacity=0.85,
                        tooltip=f"Cabo: {row['IDENTIFICADOR_UNICO_CABO']}"
                    )

                    if row["origem"] == "prim":
                        polyline.add_to(camada_prim)
                    else:
                        polyline.add_to(camada_sec)
                except Exception as e:
                    print(f"Erro ao desenhar cabo: {e}")
                
                
        camada_prim.add_to(mapa)
        camada_sec.add_to(mapa)

######################################################################################
###  BLOCO DE DESENHO UNICO DO CABO SECUNDÁRIO COM NORMALIZAÇÃO DE TRAÇADO ###########
######################################################################################

        from collections import defaultdict
        # Garantir tipo numérico para o sequenciamento
        df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = pd.to_numeric(df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"], errors="coerce")

        # Verificar necessidade de inversão do sequenciamento
        sequenciamento_inicial = df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].min()
        bloco_inicial = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_inicial]
        uuids_finais = bloco_inicial["UUID_DO_EQUIPAMENTO_FINAL"].dropna().unique()
        
        if any(uuid == uid_cto for uuid in uuids_finais):
            
            sequencias_atuais = sorted(df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique(), reverse=True)
            novo_mapeamento = {old: new for new, old in enumerate(sequencias_atuais, start=1)}
            df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].map(novo_mapeamento)
            
            #st.info("🔁 Sequenciamento invertido pois o UID da CTO não está no final do primeiro bloco.")
        else:
            print("✔️ Sequenciamento secundário ok.")
        df_sec["LATITUDE_INICIAL"] = df_sec["LATITUDE_INICIAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_sec["LONGITUDE_INICIAL"] = df_sec["LONGITUDE_INICIAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_sec["LATITUDE_FINAL"] = df_sec["LATITUDE_FINAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_sec["LONGITUDE_FINAL"] = df_sec["LONGITUDE_FINAL"].apply(lambda x: str(x) if isinstance(x, list) else x)

        
        
        # Extrair ponto inicial da CTO
        #linha_inicial_cto = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_inicial].iloc[0]
        sequenciamento_final = df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].max()
        linha_final_cto = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_final].iloc[-1]

        lat_eq_final_cto = float(str(linha_final_cto["LATITUDE_EQUP_FINAL"]).replace(",", "."))
        lon_eq_final_cto = float(str(linha_final_cto["LONGITUDE_EQUP_FINAL"]).replace(",", "."))
        #ponto_cto = (lat_eq_final_cto, lon_eq_final_cto)
        # Visualização no Streamlit
            
        df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = pd.to_numeric(df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"], errors='coerce')

        # Encontrar o maior sequenciamento
        ultimo_seq = df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].max()

        # Filtrar o último bloco
        ultimo_bloco = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == ultimo_seq]

        # Pegar a primeira linha do último sequenciamento e extrair as coordenadas do equipamento inicial
        lat_eq_inicial = float(str(ultimo_bloco.iloc[0]["LATITUDE_EQUP_INICIAL"]).replace(',', '.'))
        lon_eq_inicial = float(str(ultimo_bloco.iloc[0]["LONGITUDE_EQUP_INICIAL"]).replace(',', '.'))

        # Definir o ponto inicial
        ponto_inicial_sec = (lat_eq_inicial, lon_eq_inicial)

        # Garantir que a coluna está numérica
        df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = pd.to_numeric(df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"], errors='coerce')

        # 1️⃣ Menor sequenciamento (início da rota)
        sequenciamento_inicial = df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].min()

        # 2️⃣ Filtra a linha do menor sequenciamento
        linha_inicial_cto = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_inicial].iloc[0]

        # 3️⃣ Define ponto_inicial usando EQUP_FINAL
        lat_eq_final_cto = float(str(linha_inicial_cto["LATITUDE_EQUP_FINAL"]).replace(",", "."))
        lon_eq_final_cto = float(str(linha_inicial_cto["LONGITUDE_EQUP_FINAL"]).replace(",", "."))

        # ✅ Setar ponto inicial corretamente
        #ponto_cto = (lat_eq_final_cto, lon_eq_final_cto)

    
        def normalizar_sequencia_secundario(df, ponto_cto):
            df = df.copy()

            # Arredondamento e criação dos pontos invertidos
            df["PONTO INICIAL INVERTIDO"] = df[["LATITUDE_FINAL", "LONGITUDE_FINAL"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)
            df["PONTO FINAL INVERTIDO"] = df[["LATITUDE_INICIAL", "LONGITUDE_INICIAL"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)

            # Inicializa as colunas
            df["PONTO INICIAL_NORMALIZADO"] = None
            df["PONTO FINAL_NORMALIZADO"] = None
            df["SETAGEM DA ORDEM"] = None
            df["AÇÃO"] = None

            # Ordena os blocos de sequência em ordem decrescente
            sequencias = sorted(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique(), reverse=True)

            ordem = 1
            ponto_atual = [round(ponto_cto[0], 7), round(ponto_cto[1], 7)]

            for seq in sequencias:
                df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]

                while True:
                    # Verifica se ponto_atual está em PONTO INICIAL INVERTIDO
                    match_idx = df_seq[df_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = ""
                        ponto_atual = df.at[idx, "PONTO FINAL INVERTIDO"]
                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    # Verifica se ponto_atual está em PONTO FINAL INVERTIDO (necessita inverter)
                    match_idx = df_seq[df_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = "INVERTEU"
                        ponto_atual = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    # Nenhum match encontrado, sai do while e vai para próxima sequência
                    break

            # Ordena e retorna o DataFrame final
            return df.sort_values(by="SETAGEM DA ORDEM").reset_index(drop=True)




        # Aplicar função e extrair linha ordenada
        df_sec_normalizado = normalizar_sequencia_secundario(df_sec, ponto_cto)
        linha_secundaria_ordenada = df_sec_normalizado[df_sec_normalizado["SETAGEM DA ORDEM"].notna()].sort_values("SETAGEM DA ORDEM")
        pontos_ordenados = [p for p in linha_secundaria_ordenada["PONTO INICIAL_NORMALIZADO"]] +                    [linha_secundaria_ordenada.iloc[-1]["PONTO FINAL_NORMALIZADO"]]
        linha_secundaria_ordenada = [(lat, lon) for lat, lon in pontos_ordenados]
        
        
        # Adicionar ao mapa Folium
        camada_ordenada = folium.FeatureGroup(name="Caminho Secundário (CEOS → CTO)", show=False)
        folium.PolyLine(
            locations=linha_secundaria_ordenada,
            color="yellow",
            weight=5,
            opacity=1,
            tooltip="Caminho ordenado CEOS → CTO"
        ).add_to(camada_ordenada)
        camada_ordenada.add_to(mapa)
######################################################################################
############# SEQUENCIAMENTO PRIMÁRIO
######################################################################################
    
        # Garantir tipo numérico para o sequenciamento
        df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = pd.to_numeric(df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"], errors="coerce")

        # Verificar necessidade de inversão do sequenciamento
        sequenciamento_inicial = df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].min()
        bloco_inicial = df_prim[df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_inicial]
        uuids_finais = bloco_inicial["UUID_EQUIPAMENTO_INICIAL"].dropna().unique()
        
        if any(uuid == uid_ceos for uuid in uuids_finais):
            
            sequencias_atuais = sorted(df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique(), reverse=True)
            novo_mapeamento = {old: new for new, old in enumerate(sequencias_atuais, start=1)}
            df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = df_prim["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].map(novo_mapeamento)
            
            #st.info("🔁 Sequenciamento invertido pois o UID da CTO não está no final do primeiro bloco.")
        else:
            print("✔️ Sequenciamento primário ok.")
        df_prim["LATITUDE_INICIAL"] = df_prim["LATITUDE_INICIAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_prim["LONGITUDE_INICIAL"] = df_prim["LONGITUDE_INICIAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_prim["LATITUDE_FINAL"] = df_prim["LATITUDE_FINAL"].apply(lambda x: str(x) if isinstance(x, list) else x)
        df_prim["LONGITUDE_FINAL"] = df_prim["LONGITUDE_FINAL"].apply(lambda x: str(x) if isinstance(x, list) else x)

        
        
        # Extrair ponto inicial da CTO
        #linha_inicial_cto = df_sec[df_sec["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequenciamento_inicial].iloc[0]
        sequenciamento_ordenado = df_prim.sort_values("SEQUENCIAMENTO_DO_ENCAMINHAMENTO")

        linha_inicial_arm = None
        for _, row in sequenciamento_ordenado.iterrows():
            if row["LOCAL_TRACADO_INICIAL"] == armario:
                lat_eq_final_armario = float(str(row["LATITUDE_INICIAL"]).replace(",", "."))
                lon_eq_final_armario = float(str(row["LONGITUDE_INICIAL"]).replace(",", "."))
                linha_inicial_arm = row
                break
            elif row["LOCAL_TRACADO_FINAL"] == armario:
                lat_eq_final_armario = float(str(row["LATITUDE_FINAL"]).replace(",", "."))
                lon_eq_final_armario = float(str(row["LONGITUDE_FINAL"]).replace(",", "."))
                linha_inicial_arm = row
                break

        if linha_inicial_arm is not None:
            ponto_armario = (lat_eq_final_armario, lon_eq_final_armario)
        else:
            ponto_armario = None  # ou lançar erro, ou setar coordenadas padrão
        
        nome_armario = info['ARMARIO']
        if ponto_armario is not None:
            

            folium.Marker(
                location=ponto_armario,
                icon=folium.Icon(icon='server', prefix='fa', color='purple'),
                tooltip=f"Armário - {nome_armario}",
                popup=f"Armário: {nome_armario}"
            ).add_to(mapa)

            # Também colocar o nome como texto abaixo do marcador (opcional, mais bonito)
            folium.Marker(
                [ponto_armario[0] - 0.00002, ponto_armario[1]],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 10px;
                        color: purple;
                        text-align: center;
                        font-weight: bold;
                        transform: translateY(10px);
                    ">{nome_armario}</div>
                    """
                )
            ).add_to(mapa)

        

        def normalizar_sequenciamento_prmario(df, ponto_inicial, setagem_inicio=1):
            df_resultado = df.copy()
            ponto_atual = ponto_inicial
            setagem = setagem_inicio

            # Arredondamento e criação dos pontos invertidos
            df_resultado["PONTO INICIAL INVERTIDO"] = df_resultado[["LATITUDE_FINAL", "LONGITUDE_FINAL"]].apply(lambda x: [round(float(x[0]), 7), round(float(x[1]), 7)], axis=1)
            df_resultado["PONTO FINAL INVERTIDO"] = df_resultado[["LATITUDE_INICIAL", "LONGITUDE_INICIAL"]].apply(lambda x: [round(float(x[0]), 7), round(float(x[1]), 7)], axis=1)

            # Inicializa as colunas no df_resultado
            df_resultado["PONTO_1"] = list(zip(df_resultado["LATITUDE_INICIAL"].astype(float).round(7),
                                            df_resultado["LONGITUDE_INICIAL"].astype(float).round(7)))
            df_resultado["PONTO_2"] = list(zip(df_resultado["LATITUDE_FINAL"].astype(float).round(7),
                                            df_resultado["LONGITUDE_FINAL"].astype(float).round(7)))
            df_resultado["SETAGEM DA ORDEM"] = None
            df_resultado["ACAO"] = None
            df_resultado["PONTO INICIAL_NORMALIZADO"] = None
            df_resultado["PONTO FINAL_NORMALIZADO"] = None

            for sequenciamento in sorted(df_resultado['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'].dropna().unique()):
                while True:
                    cond_direta = (
                        (df_resultado['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'] == sequenciamento) &
                        (df_resultado['SETAGEM DA ORDEM'].isna()) &
                        (df_resultado['PONTO_1'] == ponto_atual)
                    )
                    linha_idx = df_resultado[cond_direta].index

                    if not linha_idx.empty:
                        idx = linha_idx[0]
                        df_resultado.at[idx, 'PONTO INICIAL_NORMALIZADO'] = df_resultado.at[idx, 'PONTO_1']
                        df_resultado.at[idx, 'PONTO FINAL_NORMALIZADO'] = df_resultado.at[idx, 'PONTO_2']
                        df_resultado.at[idx, 'SETAGEM DA ORDEM'] = setagem
                        ponto_atual = df_resultado.at[idx, 'PONTO_2']
                        setagem += 1
                        continue

                    cond_invertido = (
                        (df_resultado['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'] == sequenciamento) &
                        (df_resultado['SETAGEM DA ORDEM'].isna()) &
                        (df_resultado['PONTO_2'] == ponto_atual)
                    )
                    linha_idx = df_resultado[cond_invertido].index

                    if not linha_idx.empty:
                        idx = linha_idx[0]
                        df_resultado.at[idx, 'PONTO INICIAL_NORMALIZADO'] = df_resultado.at[idx, 'PONTO_2']
                        df_resultado.at[idx, 'PONTO FINAL_NORMALIZADO'] = df_resultado.at[idx, 'PONTO_1']
                        df_resultado.at[idx, 'SETAGEM DA ORDEM'] = setagem
                        df_resultado.at[idx, 'ACAO'] = "INVERTIDO"
                        ponto_atual = df_resultado.at[idx, 'PONTO_1']
                        setagem += 1
                        continue

                    break

            return df_resultado, ponto_atual, setagem

        # ✅ Desempacotar os 3 retornos da função
        df_pri_normalizado, novo_ponto, ultima_setagem = normalizar_sequenciamento_prmario(df_prim, ponto_armario)

        # Agora sim, usar como DataFrame
        linha_primario_ordenada = df_pri_normalizado[df_pri_normalizado["SETAGEM DA ORDEM"].notna()].sort_values("SETAGEM DA ORDEM")

        # Montar a linha com os pontos
        pontos_ordenados = [p for p in linha_primario_ordenada["PONTO INICIAL_NORMALIZADO"]] + \
                        [linha_primario_ordenada.iloc[-1]["PONTO FINAL_NORMALIZADO"]]

        linha_primario_ordenada = [(lat, lon) for lat, lon in pontos_ordenados]


        
        

        caminho_primario=linha_primario_ordenada
        # 🔴 Exibir caminho primário no mapa
        camada_prim_ordenada = folium.FeatureGroup(name="Caminho Primário (OLT → CEOS)", show=False)

        folium.PolyLine(
            locations=caminho_primario,
            color="red",
            weight=5,
            opacity=1,
            tooltip="Cabo Primário Único"
        ).add_to(camada_prim_ordenada)

        camada_prim_ordenada.add_to(mapa)

        if ponto_inicial_sec!=linha_secundaria_ordenada[0]:
            linha_secundaria_ordenada = linha_secundaria_ordenada[::-1]
        
        # Concatenar os dois caminhos
        if caminho_primario[-1] == linha_secundaria_ordenada[-1]:
            caminho_total = caminho_primario + linha_secundaria_ordenada[::-1]
        else:
            caminho_total = caminho_primario + linha_secundaria_ordenada
        
            
        # Criar camada única com o caminho completo OLT → CTO
        camada_total = folium.FeatureGroup(name="Caminho OTDR (OLT → CTO)", show=False)

        folium.PolyLine(
            locations=caminho_total,
            color="orange",
            weight=6,
            opacity=1,
            tooltip="Caminho Total OTDR (Primário + Secundário)"
        ).add_to(camada_total)

        # Adicionar ao mapa
        camada_total.add_to(mapa)

        from folium.plugins import AntPath
        from folium.plugins import AntPath
        from geopy.distance import geodesic

        def normalizar_sequencia_sec_folgas(df, ponto_cto):
            df = df.copy()

            # Arredondamento e criação dos pontos invertidos
            df["PONTO INICIAL INVERTIDO"] = df[["LATITUDE_EQUIP1", "LONGITUDE_EQUIP1"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)
            df["PONTO FINAL INVERTIDO"] = df[["LATITUDE_EQUIP2", "LONGITUDE_EQUIP2"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)

            # Inicializa as colunas
            df["PONTO INICIAL_NORMALIZADO"] = None
            df["PONTO FINAL_NORMALIZADO"] = None
            df["SETAGEM DA ORDEM"] = None
            df["AÇÃO"] = None

            # 🔵 NOVO: Verificar se precisa inverter os sequenciamentos
            sequencias = sorted(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique())
            sequencia_min = min(sequencias)
            sequencia_max = max(sequencias)

            ponto_atual = [round(ponto_cto[0], 7), round(ponto_cto[1], 7)]

            # Busca nos segmentos do último sequenciamento
            df_ultimo_seq = df[df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequencia_max]
            encontrou_no_final = (
                df_ultimo_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual).any() or
                df_ultimo_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual).any()
            )

            if not encontrou_no_final:
                # Tenta no primeiro sequenciamento
                df_primeiro_seq = df[df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequencia_min]
                encontrou_no_inicio = (
                    df_primeiro_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual).any() or
                    df_primeiro_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual).any()
                )

                if encontrou_no_inicio:
                    # 🛠️ Reordenar os sequenciamentos: o último vira primeiro, o penúltimo vira segundo...
                    mapping = {old_seq: new_seq for new_seq, old_seq in enumerate(sorted(sequencias, reverse=True), start=1)}
                    df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].map(mapping)

            # 🔵 Agora sim, prossegue com o processamento normal
            sequencias = sorted(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique(), reverse=True)

            ordem = 1
            ponto_atual = [round(ponto_cto[0], 7), round(ponto_cto[1], 7)]

            for seq in sequencias:
                df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]

                while True:
                    match_idx = df_seq[df_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = ""
                        ponto_atual = df.at[idx, "PONTO FINAL INVERTIDO"]
                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    match_idx = df_seq[df_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = "INVERTEU"
                        ponto_atual = df.at[idx, "PONTO INICIAL INVERTIDO"]

                        campos_para_inverter = [
                            ("EQUIPAMENTO_1", "UID_EQUIPAMENTO_2"),
                            ("NOME_EQUIPAMENTO_1", "NOME_EQUIPAMENTO_2"),
                            ("TIPO_EQUIP1", "TIPO_EQUIP2"),
                            ("UID_EQUIPAMENTO_LOGICO_1", "UID_EQUIPAMENTO_LOGICO_2"),
                            ("NOME_EQUIPAMENTO_LOGICO_1", "NOME_EQUIPAMENTO_LOGICO_2"),
                            ("LATITUDE_EQUIP1", "LATITUDE_EQUIP2"),
                            ("LONGITUDE_EQUIP1", "LONGITUDE_EQUIP2"),
                            ("CE-T1", "CE-T2"),
                        ]
                        for col1, col2 in campos_para_inverter:
                            temp = df.at[idx, col1]
                            df.at[idx, col1] = df.at[idx, col2]
                            df.at[idx, col2] = temp

                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    break

            df_final = df.sort_values(by="SETAGEM DA ORDEM").reset_index(drop=True)

            # Captura o último ponto (LATITUDE_EQUIP2, LONGITUDE_EQUIP2)
            ultimo_ponto = (
                df_final.iloc[-1]["LATITUDE_EQUIP2"],
                df_final.iloc[-1]["LONGITUDE_EQUIP2"]
            )

            return df_final, ultimo_ponto

        df_sec_folgas_normalizado, ultimo_ponto = normalizar_sequencia_sec_folgas(sec_filtrado, ponto_cto)

        sec_filtrado_cto=df_sec_folgas_normalizado.copy()

        def normalizar_sequencia_pri_folgas(df, ponto_ceos):
            df = df.copy()

            # Arredondamento e criação dos pontos invertidos
            df["PONTO INICIAL INVERTIDO"] = df[["LATITUDE_EQUIP1", "LONGITUDE_EQUIP1"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)
            df["PONTO FINAL INVERTIDO"] = df[["LATITUDE_EQUIP2", "LONGITUDE_EQUIP2"]].apply(lambda x: [round(x[0], 7), round(x[1], 7)], axis=1)

            # Inicializa as colunas
            df["PONTO INICIAL_NORMALIZADO"] = None
            df["PONTO FINAL_NORMALIZADO"] = None
            df["SETAGEM DA ORDEM"] = None
            df["AÇÃO"] = None

            # 🔵 NOVO: Verificar se precisa inverter os sequenciamentos
            sequencias = sorted(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique())
            sequencia_min = min(sequencias)
            sequencia_max = max(sequencias)

            ponto_atual = [round(ponto_ceos[0], 7), round(ponto_ceos[1], 7)]

            # Busca nos segmentos do último sequenciamento
            df_ultimo_seq = df[df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequencia_max]
            encontrou_no_final = (
                df_ultimo_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual).any() or
                df_ultimo_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual).any()
            )

            if not encontrou_no_final:
                # Tenta no primeiro sequenciamento
                df_primeiro_seq = df[df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == sequencia_min]
                encontrou_no_inicio = (
                    df_primeiro_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual).any() or
                    df_primeiro_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual).any()
                )

                if encontrou_no_inicio:
                    # 🛠️ Reordenar os sequenciamentos: o último vira primeiro, o penúltimo vira segundo...
                    mapping = {old_seq: new_seq for new_seq, old_seq in enumerate(sorted(sequencias, reverse=True), start=1)}
                    df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] = df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].map(mapping)

            # 🔵 Agora sim, prossegue com o processamento normal
            sequencias = sorted(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"].dropna().unique(), reverse=True)

            ordem = 1
            ponto_atual = [round(ponto_ceos[0], 7), round(ponto_ceos[1], 7)]

            for seq in sequencias:
                df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]

                while True:
                    match_idx = df_seq[df_seq["PONTO INICIAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = ""
                        ponto_atual = df.at[idx, "PONTO FINAL INVERTIDO"]
                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    match_idx = df_seq[df_seq["PONTO FINAL INVERTIDO"].apply(lambda x: x == ponto_atual)].index
                    if not match_idx.empty:
                        idx = match_idx[0]
                        df.at[idx, "PONTO INICIAL_NORMALIZADO"] = df.at[idx, "PONTO FINAL INVERTIDO"]
                        df.at[idx, "PONTO FINAL_NORMALIZADO"] = df.at[idx, "PONTO INICIAL INVERTIDO"]
                        df.at[idx, "SETAGEM DA ORDEM"] = ordem
                        df.at[idx, "AÇÃO"] = "INVERTEU"
                        ponto_atual = df.at[idx, "PONTO INICIAL INVERTIDO"]

                        campos_para_inverter = [
                            ("EQUIPAMENTO_1", "UID_EQUIPAMENTO_2"),
                            ("NOME_EQUIPAMENTO_1", "NOME_EQUIPAMENTO_2"),
                            ("LATITUDE_EQUIP1", "LATITUDE_EQUIP2"),
                            ("LONGITUDE_EQUIP1", "LONGITUDE_EQUIP2"),
                        ]
                        for col1, col2 in campos_para_inverter:
                            temp = df.at[idx, col1]
                            df.at[idx, col1] = df.at[idx, col2]
                            df.at[idx, col2] = temp

                        ordem += 1
                        df_seq = df[(df["SEQUENCIAMENTO_DO_ENCAMINHAMENTO"] == seq) & (df["SETAGEM DA ORDEM"].isna())]
                        continue

                    break

            df_final = df.sort_values(by="SETAGEM DA ORDEM").reset_index(drop=True)

            # Captura o último ponto (LATITUDE_EQUIP2, LONGITUDE_EQUIP2)
            ultimo_ponto = (
                df_final.iloc[-1]["LATITUDE_EQUIP2"],
                df_final.iloc[-1]["LONGITUDE_EQUIP2"]
            )

            return df_final, ultimo_ponto


        df_pri_folgas_normalizado,ultimo_ponto = normalizar_sequencia_pri_folgas(prim_filtrado, ultimo_ponto)
        pri_filtrado_cto=df_pri_folgas_normalizado.copy()


        # 🔵 4. Criar camada de CTOs filtradas no mapa
        
        
        # 🔵 2. Filtrar CE-T2 == 'NAO'
        if 'CE-T1' in df_sec_folgas_normalizado.columns:
            sec_filtrado_cto = sec_filtrado_cto[sec_filtrado_cto['CE-T1'] == 'NAO']

        # 🔵 3. Criar coluna FOLGA
        ultimo_sequenciamento = sec_filtrado_cto['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'].max()

        def calcular_folga(row):
            if row['TIPO_REDE'] == 'BARRAMENTO':
                return row['COMP_NORM'] - row['COMPRIMENTO_GEOMETRICO']
            else:
                if row['SEQUENCIAMENTO_DO_ENCAMINHAMENTO'] == ultimo_sequenciamento:
                    return 10
                else:
                    return 20

        sec_filtrado_cto['FOLGA'] = sec_filtrado_cto.apply(calcular_folga, axis=1)
        # Visualização no Streamlit
        pri_filtrado_cto['FOLGA']=30
        #with st.expander("📍 Tabela ver2"):
        #    st.dataframe(pri_filtrado_cto) 
        

        colunas_desejadas = [
            'IDENTIFICADOR_UNICO_CABO_CONECTADO', 'SEQUENCIAMENTO_DO_ENCAMINHAMENTO',
            'TIPO_REDE', 'NOME_EQUIPAMENTO_1', 'LATITUDE_EQUIP1', 'LONGITUDE_EQUIP1',
            'COMPRIMENTO_GEOMETRICO', 'COMP_NORM'
        ]
        #df_sec_folgas_normalizado = df_sec_folgas_normalizado[colunas_desejadas].copy()

        camada_cto_filtradas = folium.FeatureGroup(name="CTOs na Rota", show=False)

        for _, row in sec_filtrado_cto.iterrows():
            try:
                lat = float(str(row["LATITUDE_EQUIP1"]).replace(',', '.'))
                lon = float(str(row["LONGITUDE_EQUIP1"]).replace(',', '.'))
                nome = row['NOME_EQUIPAMENTO_1']
                folga = round(row['FOLGA'], 0)

                # Bolinha verde simples
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color='green',
                    fill=True,
                    fill_color='green',
                    fill_opacity=0.85,
                    tooltip=f"{nome} | Redutor: {folga:.0f}m", 
                    popup=f"{nome}<br>Redutor: {folga:.0f} m"
                ).add_to(camada_cto_filtradas)

                # Nome abaixo da bolinha (ajustando com CSS no transform)
                folium.Marker(
                    [lat - 0.00001, lon],
                    icon=folium.DivIcon(html=f'''
                        <div style="
                            font-size: 10px;
                            color: black;
                            text-align: center;
                            transform: translateY(10px); /* empurra o texto para baixo */
                        ">{nome}</div>
                    ''')
                ).add_to(camada_cto_filtradas)

            except Exception as e:
                print(f"Erro ao desenhar CTO filtrada: {e}")


        # 🔵 5. Adicionar a camada no mapa
        camada_cto_filtradas.add_to(mapa)


        camada_ceos_filtradas = folium.FeatureGroup(name="CEO/CEOS na Rota", show=False)

        for _, row in pri_filtrado_cto.iterrows():
            try:
                lat = float(str(row["LATITUDE_EQUIP1"]).replace(',', '.'))
                lon = float(str(row["LONGITUDE_EQUIP1"]).replace(',', '.'))
                nome_original = row['NOME_EQUIPAMENTO_1']
                folga = round(row['FOLGA'], 0)

                # 🔵 Substituir "CAIXA DE EMENDA GENERICA" por "CEG-"
                if nome_original.startswith("CAIXA DE EMENDA GENERICA "):
                    nome = nome_original.replace("CAIXA DE EMENDA GENERICA ", "CEG-")
                else:
                    nome = nome_original
                svg_icon = folium.DivIcon(html=f"""
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                        <rect width="16" height="8" rx="4" ry="4" style="fill:red;stroke:black;stroke-width:1;" />
                    </svg>
                """)
                # 🔵 Agora um DivIcon como retângulo no lugar da bolinha
                folium.Marker(
                    location=[lat, lon],
                    icon=svg_icon,
                    tooltip=f"{nome} | Redutor: {folga:.0f}m", 
                    popup=f"{nome}<br>Redutor: {folga:.0f} m"
                ).add_to(camada_ceos_filtradas)

            except Exception as e:
                print(f"Erro ao desenhar CEO/CEOS filtrada: {e}")

        # 🔵 Adicionar a camada no mapa
        camada_ceos_filtradas.add_to(mapa)





        # Criar dict: {(lat, lon) → folga}
        cto_folgas = {
            (
                round(float(str(row["LATITUDE_EQUIP1"]).replace(',', '.')), 6),
                round(float(str(row["LONGITUDE_EQUIP1"]).replace(',', '.')), 6)
            ): round(float(row["FOLGA"]), 2)
            for _, row in sec_filtrado_cto.iterrows()
        }
        import streamlit as st
        import pandas as pd
        import streamlit as st

        # 🔵 Transformar o cto_folgas (dicionário) para uma lista amigável
        dados_folga = []

        for (lat, lon), folga in cto_folgas.items():
            dados_folga.append({
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "FOLGA (m)": folga
            })

        # 🔵 Agora criar um DataFrame
        df_cto_folgas = pd.DataFrame(dados_folga)

        # Criar dict: {(lat, lon) → folga}
        ceos_folgas = {
            (
                round(float(str(row["LATITUDE_EQUIP1"]).replace(',', '.')), 6),
                round(float(str(row["LONGITUDE_EQUIP1"]).replace(',', '.')), 6)
            ): round(float(row["FOLGA"]), 2)
            for _, row in pri_filtrado_cto.iterrows()
        }
        import streamlit as st
        import pandas as pd
        import streamlit as st

        # 🔵 Transformar o cto_folgas (dicionário) para uma lista amigável
        dados_ceos_folga = []

        for (lat, lon), folga in ceos_folgas.items():
            dados_ceos_folga.append({
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "FOLGA (m)": folga
            })

        # 🔵 Agora criar um DataFrame
        df_ceos_folgas = pd.DataFrame(dados_ceos_folga)

        # 🔵 Exibir no Streamlit
        #st.subheader("📍 CTOs com Folga (Lista serializada)")
        #st.dataframe(df_ceos_folgas.style.format({"FOLGA (m)": "{:.0f}"}), use_container_width=True)

        # Gerar lista ordenada de CTOs com coordenadas + folga (de baixo pra cima)
        cto_folgas_ordenadas = sorted(
            cto_folgas.items(), 
            key=lambda x: x[0][0]  # ordena pela latitude
        )

        # 🔵 Primeiro: calcular a nova distância corrigida pelas folgas
        # 🔵 1. Recalcular a nova distância OTDR com as folgas antes de inverter o caminho

        from geopy.distance import geodesic

        distancia_restante = int(distancia_otdr)
        nova_distancia_otdr = 0
        log_folga = []

        # 🔵 Ordenar o secundário por latitude decrescente
        df_cto_folgas_sorted = df_cto_folgas.sort_values(by="LATITUDE", ascending=False).reset_index(drop=True)

        # 🔵 Ordenar o primário também, para garantir
        df_ceos_folgas_sorted = df_ceos_folgas

        # 🧩 Controle para 500m percorridos no primário
        distancia_percorrida_primario = 0

        # 🔥 1. Varredura dos pontos Secundários
        for i in range(len(df_cto_folgas_sorted)):
            lat_atual = df_cto_folgas_sorted.loc[i, "LATITUDE"]
            lon_atual = df_cto_folgas_sorted.loc[i, "LONGITUDE"]
            folga_atual = df_cto_folgas_sorted.loc[i, "FOLGA (m)"]

            # Desconta a folga primeiro
            distancia_restante -= folga_atual
            log_folga.append(f"📍 CTO {i}: {lat_atual:.6f}, {lon_atual:.6f} → -{folga_atual:.0f}m de folga | Saldo: {distancia_restante:.1f}m")

            if distancia_restante <= 0:
                log_folga.append(f"💥 Falha detectada no CTO {i} (saldo {distancia_restante:.1f}m)")
                break

            # Caminhar até o próximo CTO se possível
            if i < len(df_cto_folgas_sorted) - 1:
                lat_prox = df_cto_folgas_sorted.loc[i + 1, "LATITUDE"]
                lon_prox = df_cto_folgas_sorted.loc[i + 1, "LONGITUDE"]
                distancia_entre = geodesic((lat_atual, lon_atual), (lat_prox, lon_prox)).meters

                if distancia_restante >= distancia_entre:
                    nova_distancia_otdr += distancia_entre
                    distancia_restante -= distancia_entre
                    log_folga.append(f"➡️ Andou {distancia_entre:.1f}m até o próximo ponto | Novo saldo: {distancia_restante:.1f}m")
                else:
                    nova_distancia_otdr += distancia_restante
                    log_folga.append(f"🛑 Parou no meio entre CTO {i} e {i+1} após andar {distancia_restante:.1f}m")
                    distancia_restante = 0
                    break

        # 🔥 2. Se sobrou saldo positivo, começa a varrer o Primário
        if distancia_restante > 0:
            log_folga.append(f"🔵 Iniciando percurso no Primário...")

            for i in range(len(df_ceos_folgas_sorted)):
                lat_atual = df_ceos_folgas_sorted.loc[i, "LATITUDE"]
                lon_atual = df_ceos_folgas_sorted.loc[i, "LONGITUDE"]
                folga_atual = df_ceos_folgas_sorted.loc[i, "FOLGA (m)"]

                # Descontar folga
                distancia_restante -= folga_atual
                log_folga.append(f"📍 CEOS {i}: {lat_atual:.6f}, {lon_atual:.6f} → -{folga_atual:.0f}m de folga | Saldo: {distancia_restante:.1f}m")

                if distancia_restante <= 0:
                    log_folga.append(f"💥 Falha detectada no CEOS {i} (saldo {distancia_restante:.1f}m)")
                    break

                if i < len(df_ceos_folgas_sorted) - 1:
                    lat_prox = df_ceos_folgas_sorted.loc[i + 1, "LATITUDE"]
                    lon_prox = df_ceos_folgas_sorted.loc[i + 1, "LONGITUDE"]
                    distancia_entre = geodesic((lat_atual, lon_atual), (lat_prox, lon_prox)).meters

                    if distancia_restante >= distancia_entre:
                        nova_distancia_otdr += distancia_entre
                        distancia_restante -= distancia_entre
                        distancia_percorrida_primario += distancia_entre

                        log_folga.append(f"➡️ Andou {distancia_entre:.1f}m no primário | Novo saldo: {distancia_restante:.1f}m")

                        # A cada 500m caminhados no primário, descontar 20m
                        if distancia_percorrida_primario >= 500:
                            desconto_extra = 20
                            distancia_restante -= desconto_extra
                            distancia_percorrida_primario -= 500
                            log_folga.append(f"🔻 Redução extra de {desconto_extra}m a cada 500m percorridos | Novo saldo: {distancia_restante:.1f}m")

                    else:
                        nova_distancia_otdr += distancia_restante
                        log_folga.append(f"🛑 Parou no meio entre CEOS {i} e {i+1} após andar {distancia_restante:.1f}m")
                        distancia_restante = 0
                        break

        # 🔥 3. Se ainda sobrou saldo positivo, soma na distância final
        if distancia_restante > 0:
            nova_distancia_otdr += distancia_restante
            log_folga.append(f"➕ Sobrou saldo positivo {distancia_restante:.1f}m, somado na distância final.")

        log_folga.append(f"✅ Nova distância OTDR para plotagem: {nova_distancia_otdr:.1f}m")
        # 📦 Container tipo expander para mostrar o log
        container_log_folga = html.Details([
            html.Summary("🛠️ Log de cálculo da nova distância OTDR com folgas"),
            html.Div([
                html.Ul([html.Li(linha) for linha in log_folga], style={"paddingLeft": "20px"})
            ])
        ], style={
            "backgroundColor": "#222",
            "padding": "15px",
            "borderRadius": "10px",
            "marginTop": "20px",
            "color": "white"
        })

        # (opcional: exibir no Streamlit)
        #with st.expander("🛠️ Log de cálculo da nova distância OTDR com folgas"):
        #    for linha in log_folga:
        #        st.text(linha)

        from geopy.distance import geodesic

        # 🔁 Inverter o caminho para obter o trajeto CTO → OLT
        # 🔁 Inverter o caminho para obter o trajeto CTO → OLT
        caminho_reverso = caminho_total[::-1]
        #caminho_reverso = caminho_total

        # ⚡ Determinar o ponto da falha com base na distância OTDR
        if distancia_otdr and distancia_otdr.isdigit():
            nova_distancia_otdr = int(nova_distancia_otdr)
            ponto_falha = encontrar_ponto_por_distancia(caminho_reverso, nova_distancia_otdr)

            # 🔶 Camada reversa (CTO → ponto de falha)
            camada_falha = folium.FeatureGroup(name="Falha OTDR (CTO → OLT)", show=True)

            # Trajeto até o ponto de falha
            index_falha = None
            acumulado = 0
            for i in range(len(caminho_reverso) - 1):
                dist = geodesic(caminho_reverso[i], caminho_reverso[i + 1]).meters
                if acumulado + dist >= nova_distancia_otdr:
                    index_falha = i
                    break
                acumulado += dist


            # Exibir LOG no Streamlit
            #with st.expander("🛠️ Log detalhado do percurso OTDR com folga"):
            #    for linha in log_debug:
            #        st.text(linha)

            if index_falha is not None:
                trajeto_falha = caminho_reverso[:index_falha + 1] + [ponto_falha]

                # 🚨 Linha animada com AntPath
                AntPath(
                    locations=trajeto_falha,
                    color='red',
                    pulse_color='white',
                    weight=5,
                    opacity=0.8,
                    tooltip="Rota até ponto de falha (CTO → OLT)"
                ).add_to(camada_falha)

                # ❌ Ponto de Falha com popup de rota
                link_rota = f"https://www.google.com/maps/dir/?api=1&destination={ponto_falha[0]},{ponto_falha[1]}"
                popup_html = f"""
                <b>📍 Ponto de Falha OTDR</b><br>
                <a href="{link_rota}" target="_blank">🗺️ Traçar rota até aqui no Google Maps</a>
                """

                folium.Marker(
                    location=ponto_falha,
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip="❌ Ponto de Falha OTDR",
                    icon=folium.Icon(color='black', icon='remove', prefix='glyphicon')
                ).add_to(camada_falha)

                camada_falha.add_to(mapa)
            else:
                print("Não foi possível localizar o ponto da falha na rota.")

        
        # Desenho interativo com Folium
        Draw(export=True, filename='meu_desenho.geojson').add_to(mapa)
        Fullscreen(position="topright").add_to(mapa)
        LayerControl(collapsed=True).add_to(mapa)
        # Depois de criar o mapa
        LocateControl(auto_start=False).add_to(mapa)

        from bs4 import BeautifulSoup

        def ajustar_folium_html_responsivo(html_original):
            soup = BeautifulSoup(html_original, "html.parser")

            # Força height 100% em todos os níveis
            style_tag = soup.new_tag("style")
            style_tag.string = """
            html, body, #map, .folium-map, .leaflet-container {
                width: 100% !important;
                height: 100% !important;
                margin: 0;
                padding: 0;
            }
            """
            if soup.head:
                soup.head.append(style_tag)

            return str(soup)


        map_html = mapa._repr_html_()

        # Corrigir a estrutura do container do mapa para altura real
        map_html = map_html.replace(
            'style="width:100.0%; height:100.0%;"',
            'style="width:100%; height:100%;"'
        ).replace(
            'position:relative; width:100.0%; height:100.0%',
            'position:relative; width:100%; height:100%; min-height:600px;'
        ).replace(
            '<body>',
            '''<body style="margin:0;height:100%">
            <style>
                html, body, #map, .folium-map, .leaflet-container {
                    width: 100% !important;
                    height: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
            </style>
            '''
        )

        map_component = html.Iframe(
            srcDoc=map_html,
            style={
                "width": "100%",
                "height": "600px",
                "border": "2px solid #ccc",
                "marginTop": "20px"
            }
            
        )








        return html.Div([
            html.Hr(),
            html.H4("📌 Informações da CTO Selecionada", style={"color": "#ff4d4d", "marginBottom": "10px"}),
            html.Ul([
                html.Li([html.Strong("UID_EQUIP: "), html.Span(uid_cto, style={"color": "#00ffaa"})]),
                html.Li([html.Strong("CTO_NAME: "), html.Span(cto, style={"color": "#00ffaa"})]),
                html.Li([html.Strong("MODELO: "), html.Span(info.get("MODELO", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("ARMARIO: "), html.Span(info.get("ARMARIO", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("ENDERECO: "), html.Span(info.get("ENDERECO", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("TIPO_CTO: "), html.Span(info.get("TIPO_CTO", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("SP: "), html.Span(info.get("SP", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("SS: "), html.Span(info.get("SS", ""), style={"color": "#00ffaa"})]),
                html.Li([html.Strong("LATITUDE: "), f"{lat:.6f}", html.Strong(" | LONGITUDE: "), f"{lon:.6f}"]),
                html.Li([html.Strong("Distância OTDR informada: "), f"{distancia_otdr} m"]),
                html.Li([html.Strong("Distância CEOS → CTO (secundário): "), f"{distancia_sec:.2f} m"]),
                html.Li([html.Strong("Distância OLT → CEOS (primário): "), f"{distancia_prim:.2f} m"])
            ], style={"color": "white", "listStyleType": "none", "paddingLeft": "0"}),


            html.Hr(),

            # 🔁 Diagrama visual da cadeia OLT → CTO
            html.Div([
                html.Div([
                    html.Div("OLT", style={
                        "backgroundColor": "#1f4e79", "color": "white", "padding": "10px 20px",
                        "borderRadius": "6px", "fontWeight": "bold"
                    }),
                    html.Div(style={
                        "flexGrow": "1", "height": "5px", "backgroundColor": "purple",
                        "position": "relative", "margin": "0 5px"
                    }, children=[
                        html.Span(f"{distancia_prim:,.0f} m".replace(",", "."), style={
                            "position": "absolute", "top": "-20px", "left": "50%",
                            "transform": "translateX(-50%)", "color": "purple", "fontSize": "13px"
                        })
                    ]),
                    html.Div("SPL\n1º Nível", style={
                        "border": "2px solid black", "padding": "10px 12px",
                        "borderRadius": "6px", "textAlign": "center",
                        "fontWeight": "bold", "color": "black"
                    }),
                    html.Div(style={
                        "flexGrow": "1", "height": "5px", "backgroundColor": "blue",
                        "position": "relative", "margin": "0 5px"
                    }, children=[
                        html.Span(f"{distancia_sec:,.0f} m".replace(",", "."), style={
                            "position": "absolute", "top": "-20px", "left": "50%",
                            "transform": "translateX(-50%)", "color": "black", "fontSize": "13px"
                        })
                    ]),
                    html.Div("CTO", style={
                        "backgroundColor": "green", "color": "white",
                        "padding": "10px 20px", "borderRadius": "20px",
                        "fontWeight": "bold"
                    })
                ], style={
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "marginBottom": "10px"
                }),
                html.Div([
                    html.I(className="fa fa-pencil-ruler", style={"marginRight": "6px"}),
                    html.Span(f"Distância Total (OLT → CTO): {distancia_total:,.2f} m".replace(",", "."), style={
                        "color": "#153D64", "fontWeight": "bold"
                    })
                ], style={"textAlign": "center", "marginTop": "12px"})
            ], style={
                "backgroundColor": "#DAF2D0", "padding": "20px", "borderRadius": "12px",
                "boxShadow": "0 0 10px rgba(0, 0, 0, 0.3)", "marginTop": "20px"
            }),

            html.Hr(),
            html.H4("🌐 Mapa de Cabos", style={"marginTop": "30px", "color": "#00ffaa"}),
            map_component,
            html.Div([
                    html.Button("📥 Baixar Mapa HTML", id="botao-download-mapa", n_clicks=0,
                                style={
                                    "backgroundColor": "#153D64",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "12px 24px",
                                    "fontSize": "16px",
                                    "borderRadius": "8px",
                                    "cursor": "pointer",
                                    "boxShadow": "2px 2px 6px rgba(0, 0, 0, 0.3)"
                                }),
                    dcc.Download(id="download-mapa-html")
                ], style={"textAlign": "center", "marginTop": "20px"}),
                html.Hr(),  # 🔥 Aqui você insere o log
                container_log_folga,
        ]), map_html


    import sqlite3
    from dash import dcc  # já deve ter no início, mas caso não, pode deixar

    @app.callback(
        Output("output-logs", "children"),
        Input("botao-ver-logs", "n_clicks"),
        prevent_initial_call=True
    )
    def mostrar_logs(n):
        try:
            import os

            BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            DB_PATH = os.path.join(BASE_DIR, "logs", "otdr_consultas.db")
            print("📂 Usando banco em:", DB_PATH)

            con = sqlite3.connect(DB_PATH)

            df = pd.read_sql("SELECT * FROM consultas_otdr ORDER BY timestamp DESC LIMIT 100", con)
            con.close()

            return html.Div([
                html.H4("📜 Últimas Consultas Registradas", style={"marginTop": "20px", "color": "#00ffaa"}),
                dcc.Loading(dcc.Markdown(df.to_markdown(index=False)), type="circle")
            ], style={"backgroundColor": "#222", "padding": "20px", "borderRadius": "10px", "color": "white"})
        except Exception as e:
            return html.Div(f"Erro ao carregar logs: {e}", style={"color": "red"})


    # 🔄 Callback para baixar o mapa HTML da memória da sessão
    from dash import dcc
    from io import BytesIO
    import datetime

    @app.callback(
        Output("download-mapa-html", "data"),
        Input("botao-download-mapa", "n_clicks"),
        State("mapa-html-store", "data"),
        State("dropdown-cto", "value"),
        prevent_initial_call=True
    )
    def baixar_mapa(n_clicks, mapa_html, cto_name):
        if not mapa_html or not cto_name:
            return None

        buffer = BytesIO()
        buffer.write(mapa_html.encode("utf-8"))
        buffer.seek(0)

        nome_arquivo = f"mapa_{cto_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        return dcc.send_bytes(buffer.getvalue(), filename=nome_arquivo)

