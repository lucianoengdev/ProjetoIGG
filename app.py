import os
import sqlite3
import pandas as pd
import traceback
import math # Novo para variância
import json # Novo para relatório
import plotly.graph_objects as go # Novo para relatório
import plotly.utils
from flask import Flask, render_template, request, redirect, url_for

# --- 1. CONFIGURAÇÃO INICIAL E CONSTANTES ---
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- CONSTANTES DE ENGENHARIA ---
LARGURA_FAIXA = 3.5
COMPRIMENTO_ESTACAO = 20.0
AREA_ESTACAO = LARGURA_FAIXA * COMPRIMENTO_ESTACAO # 70.0 m²

FATORES_PONDERACAO = {
    'G1': 0.2, 'G2': 0.5, 'G3': 0.8, 'G4': 0.9,
    'G5': 1.0, 'G6': 0.5, 'G7': 0.3, 'G8': 0.6
}

# --- MAPEAMENTO DE COLUNAS (Índice 0) ---
COLUNA_KM = 0 # Coluna A
MAPA_COLUNAS_LE = {
    'OK': 1, 'G1': [2, 3, 4, 5, 6, 7], 'G2': [8, 9], 'G3': [10, 11],
    'G4': [12, 13, 14, 15], 'G5': [16, 17, 18], 'G6': [19], 'G7': [20],
    'G8': [21], 'TRI': 22, 'TRE': 23
}
MAPA_COLUNAS_LD = {
    'OK': 24, 'G1': [25, 26, 27, 28, 29, 30], 'G2': [31, 32], 'G3': [33, 34],
    'G4': [35, 36, 37, 38], 'G5': [39, 40, 41], 'G6': [42], 'G7': [43],
    'G8': [44], 'TRI': 45, 'TRE': 46
}

# --- 2. FUNÇÕES "AJUDANTES" ---
def normalizar_valor(valor):
    if isinstance(valor, (int, float)): return float(valor)
    if not isinstance(valor, str): return 0.0
    valor = valor.strip()
    if valor.upper() == 'X': return AREA_ESTACAO
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0

def calcular_variancia_2p(a, b):
    # Fórmula da variância amostral (n-1) para 2 pontos: (a-b)^2 / 2
    # Se um for 0, a variância é 0 (sem variação)
    if a == 0 or b == 0:
        return 0.0
    return ((a - b) ** 2) / 2

def processar_planilha(caminho_arquivo, linha_dados_str):
    conn = sqlite3.connect('projeto.db')
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM estacas')

        skip_rows = int(linha_dados_str) - 1
        df = pd.read_excel(caminho_arquivo, header=None, skiprows=skip_rows, dtype=object)

        lista_de_sql_data = [] # Lista para guardar os dicionários

        for _, row in df.iterrows():
            km = row.get(COLUNA_KM)
            if pd.isna(km) or str(km).strip() == "": continue

            sql_data = {} # Dicionário para esta estaca
            sql_data['km'] = normalizar_valor(km)

            ok_le = str(row.get(MAPA_COLUNAS_LE['OK'])).strip().upper() == 'SIM'
            ok_ld = str(row.get(MAPA_COLUNAS_LD['OK'])).strip().upper() == 'SIM'

            # --- 5. CALCULAR ÁREAS (G1 a G8) ---
            for i in range(1, 9):
                grupo = f'G{i}'
                area_le = 0.0
                for col_idx in MAPA_COLUNAS_LE[grupo]:
                    area_le += normalizar_valor(row.get(col_idx))
                sql_data[f'area_g{i}_le'] = 0.0 if ok_le else area_le

                area_ld = 0.0
                for col_idx in MAPA_COLUNAS_LD[grupo]:
                    area_ld += normalizar_valor(row.get(col_idx))
                sql_data[f'area_g{i}_ld'] = 0.0 if ok_ld else area_ld

            # --- 6. APLICAR REGRAS DE NEGÓCIO (G3 > G2 > G1) ---
            if sql_data['area_g3_le'] > 0:
                sql_data['area_g1_le'] = 0.0; sql_data['area_g2_le'] = 0.0
            elif sql_data['area_g2_le'] > 0:
                sql_data['area_g1_le'] = 0.0
            if sql_data['area_g3_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0; sql_data['area_g2_ld'] = 0.0
            elif sql_data['area_g2_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0

            # --- 7. CALCULAR FR e IGI (G1 a G8) ---
            igg_defeitos_g1_g8 = 0.0
            for i in range(1, 9):
                grupo = f'G{i}'
                fp = FATORES_PONDERACAO[grupo]

                area_le = sql_data[f'area_g{i}_le']
                fr_le = (area_le / AREA_ESTACAO) * 100
                igi_le = fr_le * fp
                sql_data[f'fr_g{i}_le'] = fr_le
                sql_data[f'igi_g{i}_le'] = igi_le
                igg_defeitos_g1_g8 += igi_le

                area_ld = sql_data[f'area_g{i}_ld']
                fr_ld = (area_ld / AREA_ESTACAO) * 100
                igi_ld = fr_ld * fp
                sql_data[f'fr_g{i}_ld'] = fr_ld
                sql_data[f'igi_g{i}_ld'] = igi_ld
                igg_defeitos_g1_g8 += igi_ld

            sql_data['igg_defeitos_g1_g8'] = igg_defeitos_g1_g8

            # --- 8. LÓGICA DAS FLECHAS (Sua Engenharia) ---

            # 8.1 Pegar valores brutos
            tri_le = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRI']))
            tre_le = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRE']))
            tri_ld = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRI']))
            tre_ld = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRE']))
            sql_data['valor_tri_le'] = tri_le
            sql_data['valor_tre_le'] = tre_le
            sql_data['valor_tri_ld'] = tri_ld
            sql_data['valor_tre_ld'] = tre_ld

            # 8.2 Calcular Estatísticas da Estaca
            sql_data['mean_le'] = (tri_le + tre_le) / 2
            sql_data['mean_ld'] = (tri_ld + tre_ld) / 2
            sql_data['var_le'] = calcular_variancia_2p(tri_le, tre_le)
            sql_data['var_ld'] = calcular_variancia_2p(tri_ld, tre_ld)

            sql_data['tri_agg'] = (sql_data['mean_le'] + sql_data['mean_ld']) / 2
            sql_data['tre_agg'] = (sql_data['var_le'] + sql_data['var_ld']) / 2

            # 8.3 Aplicar Regras da Norma
            tri_agg = sql_data['tri_agg']
            if tri_agg <= 30:
                sql_data['igi_trilha'] = tri_agg * (4/3)
            else:
                sql_data['igi_trilha'] = 40.0

            tre_agg = sql_data['tre_agg']
            if tre_agg <= 50:
                sql_data['igi_var'] = tre_agg
            else:
                sql_data['igi_var'] = 50.0

            # 8.4 Achar IGI Final das Flechas
            sql_data['igi_flechas_final'] = max(sql_data['igi_trilha'], sql_data['igi_var'])

            # 8.5 CALCULAR IGG TOTAL DA ESTACA
            sql_data['igg_total_final_estaca'] = sql_data['igg_defeitos_g1_g8'] + sql_data['igi_flechas_final']

            lista_de_sql_data.append(sql_data) # Adiciona à lista

        # Fim do "Grande Loop"

        # --- 9. INSERIR NO BANCO DE DADOS (V7 - Final) ---
        print(f"Inserindo {len(lista_de_sql_data)} estacas no banco de dados...")

        # Pega os nomes das colunas do PRIMEIRO dicionário
        # Isso garante que a ordem é a mesma para todos
        colunas_ordenadas = list(lista_de_sql_data[0].keys())

        # Cria a string (?, ?, ?, ...)
        placeholders = ', '.join(['?' for _ in colunas_ordenadas])

        # Cria a string (col1, col2, col3, ...)
        nomes_colunas = ', '.join(colunas_ordenadas)

        sql_query = f"INSERT INTO estacas ({nomes_colunas}) VALUES ({placeholders})"

        # Cria uma lista de tuplas (valores) para inserir
        # Isso é muito mais rápido do que inserir um por um
        lista_de_valores = []
        for sql_data in lista_de_sql_data:
            lista_de_valores.append(tuple(sql_data[col] for col in colunas_ordenadas))

        cursor.executemany(sql_query, lista_de_valores)

        # --- 10. LIMPEZA DE NULL (Sua Solução) ---
        print("Iniciando limpeza de NULLs...")
        colunas_para_limpar = [col for col in colunas_ordenadas if col != 'km']
        for col in colunas_para_limpar:
            cursor.execute(f"UPDATE estacas SET {col} = 0.0 WHERE {col} IS NULL")
        print("Limpeza de NULLs concluída.")

        conn.commit()
        conn.close()

        print("RODANDO VERSÃO 7 (COM LÓGICA DE FLECHAS).")
        return True, None

    except Exception as e:
        print(f"ERRO NO PROCESSAMENTO: {e}")
        traceback.print_exc()
        if conn:
            conn.rollback()
            conn.close()
        return False, str(e)


# --- 3. ROTAS FLASK (COM PASSO 6 INCLUÍDO) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'planilha' not in request.files: return "Nenhum arquivo encontrado!"
    file = request.files['planilha']
    if file.filename == '': return "Nenhum arquivo selecionado!"
    linha_inicial = request.form['linha_inicial']

    if file:
        caminho_seguro = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(caminho_seguro)
        sucesso, erro = processar_planilha(caminho_seguro, linha_inicial)
        if sucesso:
            return redirect(url_for('relatorio'))
        else:
            return f"Ocorreu um erro ao processar sua planilha: <br><br> {erro} <br><br> Verifique se o número da linha inicial (<b>{linha_inicial}</b>) está correto."

@app.route('/relatorio')
def relatorio():
    conn = None
    try:
        conn = sqlite3.connect('projeto.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- 1. DADOS PARA O GRÁFICO (AGORA USA O IGG FINAL) ---
        cursor.execute("SELECT km, igg_total_final_estaca FROM estacas ORDER BY km")
        estacas = cursor.fetchall()

        x_km = [row['km'] for row in estacas]
        y_igg = [row['igg_total_final_estaca'] for row in estacas]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_km, y=y_igg, mode='lines+markers', name='IGG por Estaca'))

        y_max = max(y_igg) if y_igg else 160 # Define um limite se não houver dados

        # Faixas de "Conceito" (Imagem 2)
        fig.add_hrect(y0=0, y1=20, line_width=0, fillcolor='green', opacity=0.1, layer="below", annotation_text="Ótimo", annotation_position="right")
        fig.add_hrect(y0=20, y1=40, line_width=0, fillcolor='yellow', opacity=0.1, layer="below", annotation_text="Bom", annotation_position="right")
        fig.add_hrect(y0=40, y1=80, line_width=0, fillcolor='orange', opacity=0.1, layer="below", annotation_text="Regular", annotation_position="right")
        fig.add_hrect(y0=80, y1=160, line_width=0, fillcolor='red', opacity=0.1, layer="below", annotation_text="Ruim", annotation_position="right")
        fig.add_hrect(y0=160, y1=max(161, y_max + 50), line_width=0, fillcolor='maroon', opacity=0.1, layer="below", annotation_text="Péssimo", annotation_position="right")

        fig.update_layout(
            title="Linear de Ocorrência (IGG Final por Estaca)",
            xaxis_title="Quilômetro (km)",
            yaxis_title="IGG Final (Defeitos + Flechas)",
            hovermode="x unified"
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # --- 2. DADOS PARA A TABELA (AGORA USA O IGG FINAL) ---
        query_segmentos = """
            SELECT 
                FLOOR(km) as km_segmento, 
                AVG(igg_total_final_estaca) as igg_medio,
                MIN(km) as km_inicio,
                MAX(km) as km_fim
            FROM estacas
            GROUP BY km_segmento
            ORDER BY km_segmento
        """
        cursor.execute(query_segmentos)
        segmentos = cursor.fetchall()

        conn.close()

        # Precisamos do `relatorio.html` que já criamos no Passo 6
        return render_template('relatorio.html', graphJSON=graphJSON, segmentos=segmentos)

    except Exception as e:
        if conn: conn.close()
        print(f"Erro ao gerar relatório: {e}")
        traceback.print_exc()
        return "Erro ao gerar relatório. Verifique os dados no banco."

if __name__ == '__main__':
    app.run(debug=True)