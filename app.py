import pandas as pd
import sqlite3
import uuid
import os
import glob
import io
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, g, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

DATABASE = 'projeto.db'

LARGURA_FAIXA = 3.5       
COMPRIMENTO_ESTACA = 20.0 
AREA_ESTACA = LARGURA_FAIXA * COMPRIMENTO_ESTACA # 70.0 m² (A_i)

INDICES = {
    'km': 0,
    'trincas': [2, 3, 4, 5, 6, 7, 8, 9, 25, 26, 27, 28, 29, 30, 31, 32],
    'deformacoes': [12, 13, 14, 15, 35, 36, 37, 38],
    'panelas_remendos': [17, 40, 21, 44]
}

PESOS = {'Trincas': 0.35, 'Deformacoes': 0.60, 'Panelas': 0.70}

FATORES_GRAV = {
    'Trincas': {'A': 0.65, 'M': 0.45, 'B': 0.30},
    'Deformacoes': {'A': 1.00, 'M': 0.70, 'B': 0.60},
    'Panelas': {'A': 1.00, 'M': 0.80, 'B': 0.70}
}

def limpar_uploads_ao_iniciar():
    pasta = app.config['UPLOAD_FOLDER']
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return
    arquivos = glob.glob(os.path.join(pasta, '*'))
    for arquivo in arquivos:
        try: os.remove(arquivo)
        except: pass

limpar_uploads_ao_iniciar()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def normalizar_para_float(valor):
    if pd.isna(valor) or valor == '': return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor_str = str(valor).strip().replace(',', '.')
    try: return float(valor_str)
    except ValueError: return 0.0

def calcular_igge_pro008(df, upload_id):
    db = get_db()
    cursor = db.cursor()

    # 1. PROCESSAMENTO INICIAL
    df_proc = pd.DataFrame()
    max_col = df.shape[1]
    
    idx_km = INDICES['km']
    if idx_km < max_col:
        df_proc['km'] = df.iloc[:, idx_km].apply(normalizar_para_float)
        df_proc['km_segmento'] = df_proc['km'].apply(lambda x: int(x))
    else:
        raise ValueError("A planilha não tem a coluna 0 (KM).")

    def processar_grupo(row_idx, lista_indices, modo='soma_real'):
        soma = 0.0
        for col_idx in lista_indices:
            if col_idx < max_col:
                val = normalizar_para_float(df.iloc[row_idx, col_idx])
                if modo == 'soma_real':
                    soma += val
                elif modo == 'binario':
                    soma += 1 if val > 0 else 0
        return soma

    areas_trinca = []
    areas_deform = []
    qtds_panela = []

    for i in range(len(df)):
        areas_trinca.append(processar_grupo(i, INDICES['trincas'], modo='soma_real'))
        
        areas_deform.append(processar_grupo(i, INDICES['deformacoes'], modo='soma_real'))
        
        qtds_panela.append(processar_grupo(i, INDICES['panelas_remendos'], modo='binario'))

    df_proc['area_trinca'] = areas_trinca
    df_proc['area_deform'] = areas_deform
    df_proc['qtd_panelas'] = qtds_panela

    # 2. AGRUPAMENTO POR SEGMENTO (LÓGICA HÍBRIDA)
    df_resumo = df_proc.groupby('km_segmento').apply(lambda x: pd.Series({
        'total_estacas': len(x),
        'area_total_segmento': len(x) * AREA_ESTACA, 
        
        'soma_area_trinca': x['area_trinca'].sum(),
        'soma_area_deform': x['area_deform'].sum(),
        
        'qtd_total_panelas_remendos': x['qtd_panelas'].sum()
    })).reset_index()

    # 3. CÁLCULO DAS FREQUÊNCIAS (% e Quantidade)
    
    
    df_resumo['pct_trincas'] = (df_resumo['soma_area_trinca'] / df_resumo['area_total_segmento']) * 100
    df_resumo['freq_trincas'] = df_resumo['pct_trincas'].apply(
        lambda p: 'A' if p > 50 else ('M' if p > 10 else 'B')
    )
    
    df_resumo['pct_deform'] = (df_resumo['soma_area_deform'] / df_resumo['area_total_segmento']) * 100
    df_resumo['freq_deform'] = df_resumo['pct_deform'].apply(
        lambda p: 'A' if p > 50 else ('M' if p > 10 else 'B')
    )
    
    df_resumo['freq_panelas'] = df_resumo['qtd_total_panelas_remendos'].apply(
        lambda q: 'A' if q >= 5 else ('M' if q > 2 else 'B')
    )

    # 4. FATORES E IGGE
    df_resumo['ft'] = df_resumo['freq_trincas'].map(FATORES_GRAV['Trincas'])
    df_resumo['fd'] = df_resumo['freq_deform'].map(FATORES_GRAV['Deformacoes'])
    df_resumo['fp'] = df_resumo['freq_panelas'].map(FATORES_GRAV['Panelas'])

    df_resumo['igge'] = ((PESOS['Trincas'] * df_resumo['ft']) + 
                         (PESOS['Deformacoes'] * df_resumo['fd']) + 
                         (PESOS['Panelas'] * df_resumo['fp'])) * 100
    
    df_resumo['igge'] = df_resumo['igge'].clip(upper=500)

    # 5. CONCEITO E IES
    def classificar(v):
        if v <= 65: return 'Ótimo'
        if v <= 110: return 'Bom'
        if v <= 160: return 'Regular'
        if v <= 230: return 'Ruim'
        return 'Péssimo'

    df_resumo['conceito'] = df_resumo['igge'].apply(classificar)
    df_resumo['ies'] = (10 - (df_resumo['igge'] * 10 / 500)).clip(lower=0)

    # 6. SALVAR NO BANCO
    cursor.execute("DELETE FROM resultados_pro008 WHERE upload_id = ?", (upload_id,))
    
    dados_insert = []
    for _, row in df_resumo.iterrows():
        dados_insert.append((
            upload_id, row['km_segmento'], row['km_segmento']+1,
            int(row['total_estacas']),
            
            round(row['soma_area_trinca'], 2), row['pct_trincas'],
            round(row['soma_area_deform'], 2), row['pct_deform'],
            
            int(row['qtd_total_panelas_remendos']),
            
            row['freq_trincas'], row['freq_deform'], row['freq_panelas'],
            row['ft'], row['fd'], row['fp'],
            row['igge'], row['ies'], row['conceito']
        ))

    sql = """INSERT INTO resultados_pro008 
             (upload_id, km_inicial, km_final, total_estacas, 
              qtd_trincas, pct_trincas, qtd_deformacoes, pct_deformacoes, qtd_panelas,
              freq_trincas, freq_deformacoes, freq_panelas,
              grav_trincas, grav_deformacoes, grav_panelas,
              igge, ies, conceito)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    cursor.executemany(sql, dados_insert)
    db.commit()

# --- ROTAS FLASK ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files: return redirect(request.url)
        file = request.files['file']
        try: linha_inicial = int(request.form.get('linha_inicial', 1))
        except: linha_inicial = 1

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uid = str(uuid.uuid4())
            session['upload_id'] = uid
            try:
                df = pd.read_excel(filepath, header=None, skiprows=linha_inicial-1, dtype=object)
                calcular_igge_pro008(df, uid)
                return redirect(url_for('relatorio', id=uid))
            except Exception as e:
                return render_template('index.html', error=str(e))
    return render_template('index.html')

@app.route('/relatorio/<id>')
def relatorio(id):
    db = get_db()
    res = db.execute("SELECT * FROM resultados_pro008 WHERE upload_id = ? ORDER BY km_inicial", (id,)).fetchall()
    chart_data = {
        'labels': [f"{r['km_inicial']}-{r['km_final']}" for r in res],
        'datasets': [{'label': 'IGGE', 'data': [r['igge'] for r in res], 'backgroundColor': '#0d6efd'}]
    }
    return render_template('relatorio.html', resultados=res, chart_data=chart_data)

@app.route('/download_modelo')
def download_modelo():
    try:
        return send_from_directory(directory='static', path='modelo_padrao.xlsx', as_attachment=True)
    except FileNotFoundError:
        return "ERRO: Arquivo 'modelo_padrao.xlsx' não encontrado na pasta 'static'."

if __name__ == '__main__':
    app.run(debug=True)