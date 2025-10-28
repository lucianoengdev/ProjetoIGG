import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for

# --- 1. CONFIGURAÇÃO INICIAL E CONSTANTES ---
app = Flask(__name__)

# Configuração da pasta de uploads
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- CONSTANTES DE ENGENHARIA ---
LARGURA_FAIXA = 3.5  # metros
COMPRIMENTO_ESTACAO = 20.0 # metros
AREA_ESTACAO = LARGURA_FAIXA * COMPRIMENTO_ESTACAO # 70.0 m²

# Fatores de Ponderação (fp) - Baseado na Norma (Imagem 1)
FATORES_PONDERACAO = {
    'G1': 0.2, 'G2': 0.5, 'G3': 0.8, 'G4': 0.9,
    'G5': 1.0, 'G6': 0.5, 'G7': 0.3, 'G8': 0.6
}

# Mapeamento das Colunas (Sua Regra de Ouro B:X e Y:AU)
# 23 Colunas por lado
MAPA_COLUNAS_LE = {
    'OK': 'B',
    'G1': ['C', 'D', 'E', 'F', 'G', 'H'],   # FI, TTC, TTL, TLC, TLL, TRR
    'G2': ['I', 'J'],                      # J, TB
    'G3': ['K', 'L'],                      # JE, TBE
    'G4': ['M', 'N', 'O', 'P'],            # ALP, ATP, ALC, ATC
    'G5': ['Q', 'R', 'S'],                 # O, P, E
    'G6': ['T'],                           # EX
    'G7': ['U'],                           # D
    'G8': ['V'],                           # R
    'TRI': 'W',
    'TRE': 'X'
}

# Lado Direito (Y até AU)
MAPA_COLUNAS_LD = {
    'OK': 'Y',
    'G1': ['Z', 'AA', 'AB', 'AC', 'AD', 'AE'],  # FI, TTC, TTL, TLC, TLL, TRR
    'G2': ['AF', 'AG'],                          # J, TB
    'G3': ['AH', 'AI'],                          # JE, TBE
    'G4': ['AJ', 'AK', 'AL', 'AM'],             # ALP, ATP, ALC, ATC
    'G5': ['AN', 'AO', 'AP'],                    # O, P, E
    'G6': ['AQ'],                                # EX
    'G7': ['AR'],                                # D
    'G8': ['AS'],                                # R
    'TRI': 'AT',
    'TRE': 'AU'  
}

COLUNA_KM = 'A'

# --- 2. FUNÇÕES "AJUDANTES" ---

def normalizar_valor(valor):
    """
    Converte valor da célula para float, tratando 'X', '12,5' (PT-BR) e '12.5' (EN).
    Retorna 70.0 para 'X' e 0.0 para textos ou vazios.
    (Implementa seu Ponto 2)
    """
    if isinstance(valor, (int, float)):
        return float(valor)

    if not isinstance(valor, str):
        return 0.0 # Célula vazia (None) ou tipo inesperado

    valor = valor.strip()

    if valor.upper() == 'X':
        return AREA_ESTACAO # 100% da área

    valor = valor.replace(",", ".") # Converte '12,5' para '12.5'

    try:
        return float(valor)
    except ValueError:
        return 0.0 # Era um texto como "Sim", "Não", etc.


def processar_planilha(caminho_arquivo, linha_dados_str):
    """
    O "Cérebro": Lê o Excel, aplica as regras e salva no SQLite.
    """
    try:
        # 1. Conectar e Limpar o Banco de Dados
        conn = sqlite3.connect('projeto.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM estacas') # Limpa dados de uploads antigos

        # 2. Calcular o índice do Cabeçalho (Sua Lógica do Ponto 3)
        # Usuário digita '8' (linha dos dados) -> header_index = 8 - 2 = 6
        # Pandas lê o 6º índice (Linha 7 do Excel) como cabeçalho.
        header_index = int(linha_dados_str) - 2

        # 3. Ler o Excel com Pandas
        # Precisamos especificar 'None' para não tentar adivinhar tipos (e tratar 'X' como texto)
        df = pd.read_excel(caminho_arquivo, header=header_index, dtype=object)

        # 4. O "Grande Loop" - Iterar em cada estaca (linha)
        for _, row in df.iterrows():

            # Pega o KM. Se for nulo, pula a linha (fim do arquivo)
            km = row.get(COLUNA_KM)
            if pd.isna(km):
                continue

            # Dicionário para guardar todos os valores a salvar no SQL
            sql_data = {'km': normalizar_valor(km)}

            # Flags de "OK"
            ok_le = str(row.get(MAPA_COLUNAS_LE['OK'])).strip().upper() == 'SIM'
            ok_ld = str(row.get(MAPA_COLUNAS_LD['OK'])).strip().upper() == 'SIM'

            # --- 5. CALCULAR ÁREAS (G1 a G8) ---
            for i in range(1, 9): # Loop de G1 até G8
                grupo = f'G{i}'
                # Lado Esquerdo
                area_le = 0.0
                for col in MAPA_COLUNAS_LE[grupo]:
                    area_le += normalizar_valor(row.get(col))
                sql_data[f'area_g{i}_le'] = area_le if not ok_le else 0.0

                # Lado Direito
                area_ld = 0.0
                for col in MAPA_COLUNAS_LD[grupo]:
                    area_ld += normalizar_valor(row.get(col))
                sql_data[f'area_g{i}_ld'] = area_ld if not ok_ld else 0.0

            # --- 6. APLICAR REGRAS DE NEGÓCIO (Prioridade G3 > G2 > G1) ---
            # Lado Esquerdo
            if sql_data['area_g3_le'] > 0:
                sql_data['area_g1_le'] = 0.0
                sql_data['area_g2_le'] = 0.0
            elif sql_data['area_g2_le'] > 0:
                sql_data['area_g1_le'] = 0.0
            # Lado Direito
            if sql_data['area_g3_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0
                sql_data['area_g2_ld'] = 0.0
            elif sql_data['area_g2_ld'] > 0:
                sql_data['area_g1_ld'] = 0.0

            # --- 7. CALCULAR FR e IGI (G1 a G8) ---
            igg_total_estaca = 0.0
            for i in range(1, 9): # Loop de G1 até G8
                grupo = f'G{i}'
                fp = FATORES_PONDERACAO[grupo]

                # LE
                area_le = sql_data[f'area_g{i}_le']
                fr_le = (area_le / AREA_ESTACAO) * 100
                igi_le = fr_le * fp
                sql_data[f'fr_g{i}_le'] = fr_le
                sql_data[f'igi_g{i}_le'] = igi_le
                igg_total_estaca += igi_le

                # LD
                area_ld = sql_data[f'area_g{i}_ld']
                fr_ld = (area_ld / AREA_ESTACAO) * 100
                igi_ld = fr_ld * fp
                sql_data[f'fr_g{i}_ld'] = fr_ld
                sql_data[f'igi_g{i}_ld'] = igi_ld
                igg_total_estaca += igi_ld

            sql_data['igg_total_estaca'] = igg_total_estaca

            # --- 8. SALVAR VALORES BRUTOS (TRI e TRE) ---
            sql_data['valor_tri_le'] = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRI']))
            sql_data['valor_tre_le'] = normalizar_valor(row.get(MAPA_COLUNAS_LE['TRE']))
            sql_data['valor_tri_ld'] = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRI']))
            sql_data['valor_tre_ld'] = normalizar_valor(row.get(MAPA_COLUNAS_LD['TRE']))

            # --- 9. INSERIR NO BANCO DE DADOS ---
            # Pega todas as colunas da nossa tabela 'estacas'
            colunas = list(sql_data.keys())
            placeholders = ', '.join([f':{col}' for col in colunas])
            sql_query = f"INSERT INTO estacas ({', '.join(colunas)}) VALUES ({placeholders})"

            cursor.execute(sql_query, sql_data)

        # Fim do "Grande Loop"
        # 10. Salvar e Fechar
        conn.commit()
        conn.close()
        print("Processamento do Excel concluído. Banco de dados populado.")
        return True, None

    except Exception as e:
        # Captura qualquer erro (ex: Excel mal formatado, "header" errado)
        print(f"ERRO NO PROCESSAMENTO: {e}")
        conn.close()
        return False, str(e)


# --- 3. ROTAS FLASK (O "Controle de Tráfego") ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'planilha' not in request.files:
        return "Nenhum arquivo encontrado!"

    file = request.files['planilha']

    if file.filename == '':
        return "Nenhum arquivo selecionado!"

    linha_inicial = request.form['linha_inicial']

    if file:
        caminho_seguro = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(caminho_seguro)

        # --- CHAMA O "CÉREBRO" ---
        sucesso, erro = processar_planilha(caminho_seguro, linha_inicial)

        if sucesso:
            # Se tudo deu certo, redireciona para a página de relatório
            return redirect(url_for('relatorio'))
        else:
            # Se deu erro, mostra o erro
            return f"Ocorreu um erro ao processar sua planilha: <br><br> {erro} <br><br> Verifique se o número da linha inicial (<b>{linha_inicial}</b>) está correto e se a planilha segue o padrão."

# Rota "fantasma" por enquanto, só para o redirect funcionar
@app.route('/relatorio')
def relatorio():
    # No Passo 6, vamos buscar os dados do SQL e mostrar gráficos aqui
    return "Processamento Concluído! O relatório será exibido aqui."


if __name__ == '__main__':
    app.run(debug=True)