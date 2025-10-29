import os
import sqlite3
import pandas as pd
import traceback # Novo: para imprimir erros detalhados
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

# --- MAPEAMENTO DE COLUNAS (V3 - Baseado em Índice 0) ---
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

    
def processar_planilha(caminho_arquivo, linha_dados_str):
    conn = sqlite3.connect('projeto.db') # Abre a conexão
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM estacas')
        
        skip_rows = int(linha_dados_str) - 1

        df = pd.read_excel(caminho_arquivo, header=None, skiprows=skip_rows, dtype=object)

        for _, row in df.iterrows():
            km = row.get(COLUNA_KM)
            if pd.isna(km) or str(km).strip() == "": continue
            
            sql_data = {} # Dicionário de dados para esta estaca
            sql_data['km'] = normalizar_valor(km)

            ok_le = str(row.get(MAPA_COLUNAS_LE['OK'])).strip().upper() == 'SIM'
            ok_ld = str(row.get(MAPA_COLUNAS_LD['OK'])).strip().upper() == 'SIM'
            
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

            if sql_data['area_g3_le'] > 0:
                sql_data['area_g1_le'] = 0.0; sql_data['area_g2_le'] = 0.0
            elif sql_data['area_g2_le'] > 0:
                sql_data['area_g1_le'] = 0.0
            if sql_data['area_g3_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0; sql_data['area_g2_ld'] = 0.0
            elif sql_data['area_g2_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0

            igg_total_estaca = 0.0
            for i in range(1, 9):
                grupo = f'G{i}'
                fp = FATORES_PONDERACAO[grupo]

                area_le = sql_data[f'area_g{i}_le']
                fr_le = (area_le / AREA_ESTACAO) * 100
                igi_le = fr_le * fp
                sql_data[f'fr_g{i}_le'] = fr_le
                sql_data[f'igi_g{i}_le'] = igi_le
                igg_total_estaca += igi_le
                
                area_ld = sql_data[f'area_g{i}_ld']
                fr_ld = (area_ld / AREA_ESTACAO) * 100
                igi_ld = fr_ld * fp
                sql_data[f'fr_g{i}_ld'] = fr_ld
                sql_data[f'igi_g{i}_ld'] = igi_ld
                igg_total_estaca += igi_ld
            
            sql_data['igg_total_estaca'] = igg_total_estaca

            sql_data['valor_tri_le'] = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRI']))
            sql_data['valor_tre_le'] = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRE']))
            sql_data['valor_tri_ld'] = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRI']))
            sql_data['valor_tre_ld'] = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRE']))

            # --- 9. INSERIR NO BANCO DE DADOS (V4 - Correção do Bug de Ordem) ---
            
            # Lista de valores NA ORDEM EXATA do 'init_db.py'
            valores_ordenados = [
                sql_data['km'],
                sql_data['area_g1_le'], sql_data['fr_g1_le'], sql_data['igi_g1_le'],
                sql_data['area_g1_ld'], sql_data['fr_g1_ld'], sql_data['igi_g1_ld'],
                sql_data['area_g2_le'], sql_data['fr_g2_le'], sql_data['igi_g2_le'],
                sql_data['area_g2_ld'], sql_data['fr_g2_ld'], sql_data['igi_g2_ld'],
                sql_data['area_g3_le'], sql_data['fr_g3_le'], sql_data['igi_g3_le'],
                sql_data['area_g3_ld'], sql_data['fr_g3_ld'], sql_data['igi_g3_ld'],
                sql_data['area_g4_le'], sql_data['fr_g4_le'], sql_data['igi_g4_le'],
                sql_data['area_g4_ld'], sql_data['fr_g4_ld'], sql_data['igi_g4_ld'],
                sql_data['area_g5_le'], sql_data['fr_g5_le'], sql_data['igi_g5_le'],
                sql_data['area_g5_ld'], sql_data['fr_g5_ld'], sql_data['igi_g5_ld'],
                sql_data['area_g6_le'], sql_data['fr_g6_le'], sql_data['igi_g6_le'],
                sql_data['area_g6_ld'], sql_data['fr_g6_ld'], sql_data['igi_g6_ld'],
                sql_data['area_g7_le'], sql_data['fr_g7_le'], sql_data['igi_g7_le'],
                sql_data['area_g7_ld'], sql_data['fr_g7_ld'], sql_data['igi_g7_ld'],
                sql_data['area_g8_le'], sql_data['fr_g8_le'], sql_data['igi_g8_le'],
                sql_data['area_g8_ld'], sql_data['fr_g8_ld'], sql_data['igi_g8_ld'],
                sql_data['valor_tri_le'], sql_data['valor_tri_ld'],
                sql_data['valor_tre_le'], sql_data['valor_tre_ld'],
                sql_data['igg_total_estaca']
            ]
            
            placeholders = ', '.join(['?' for _ in valores_ordenados])
            
            # ESTA É A LISTA DE COLUNAS QUE CORRIGE O BUG
            sql_query = f"INSERT INTO estacas (km, area_g1_le, fr_g1_le, igi_g1_le, area_g1_ld, fr_g1_ld, igi_g1_ld, area_g2_le, fr_g2_le, igi_g2_le, area_g2_ld, fr_g2_ld, igi_g2_ld, area_g3_le, fr_g3_le, igi_g3_le, area_g3_ld, fr_g3_ld, igi_g3_ld, area_g4_le, fr_g4_le, igi_g4_le, area_g4_ld, fr_g4_ld, igi_g4_ld, area_g5_le, fr_g5_le, igi_g5_le, area_g5_ld, fr_g5_ld, igi_g5_ld, area_g6_le, fr_g6_le, igi_g6_le, area_g6_ld, fr_g6_ld, igi_g6_ld, area_g7_le, fr_g7_le, igi_g7_le, area_g7_ld, fr_g7_ld, igi_g7_ld, area_g8_le, fr_g8_le, igi_g8_le, area_g8_ld, fr_g8_ld, igi_g8_ld, valor_tri_le, valor_tri_ld, valor_tre_le, valor_tre_ld, igg_total_estaca) VALUES ({placeholders})"
            
            cursor.execute(sql_query, valores_ordenados)

        conn.commit()
        conn.close()
        print("Processamento do Excel (V4) concluído. Banco de dados populado.")
        return True, None

    except Exception as e:
        print(f"ERRO NO PROCESSAMENTO: {e}")
        traceback.print_exc()
        conn.rollback() # Desfaz qualquer mudança se der erro
        conn.close()
        return False, str(e)


# --- 3. ROTAS FLASK ---
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
            return f"Ocorreu um erro ao processar sua planilha: <br><br> {erro} <br><br> Verifique se o número da linha inicial (<b>{linha_inicial}</b>) está correto e se a planilha segue o padrão."

@app.route('/relatorio')
def relatorio():
    # No Passo 6, vamos buscar os dados do SQL e mostrar gráficos aqui
    return "Processamento Concluído! O relatório será exibido aqui."

if __name__ == '__main__':
    app.run(debug=True)