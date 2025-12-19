import pandas as pd
import sqlite3
import uuid
import os
import glob
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_segura_projeto_igg_binario'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

DATABASE = 'projeto.db'

MAPA_COLUNAS = {
    'km': 0, 
    'g1_le': 1, 'g1_ld': 2, 'g2_le': 3, 'g2_ld': 4,
    
    'g3_le': 5, 'g3_ld': 6, 
    'g4_le': 7, 'g4_ld': 8, 
    
    'g5_le': 9, 'g5_ld': 10,
    'g6_le': 11, 'g6_ld': 12
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

PESOS = {
    'Trincas': 0.35,      
    'Deformacoes': 0.60,  
    'Panelas': 0.70       
}

FATORES_GRAV = {
    'Trincas': {'A': 0.65, 'M': 0.45, 'B': 0.30},
    'Deformacoes': {'A': 1.00, 'M': 0.70, 'B': 0.60},
    'Panelas': {'A': 1.00, 'M': 0.80, 'B': 0.70}
}

def normalizar_para_float(valor):
    if pd.isna(valor) or valor == '': return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    valor_str = str(valor).strip().replace(',', '.')
    try: return float(valor_str)
    except ValueError: return 0.0

def calcular_igge_pro008(df, upload_id):
    db = get_db()
    cursor = db.cursor()

    # 1. LEITURA E CONVERSÃO BINÁRIA
    df_proc = pd.DataFrame()
    
    idx_km = MAPA_COLUNAS['km']
    df_proc['km'] = df.iloc[:, idx_km].apply(normalizar_para_float)
    df_proc['km_segmento'] = df_proc['km'].apply(lambda x: int(x))
    for nome_col, idx in MAPA_COLUNAS.items():
        if nome_col == 'km': continue
        
        if idx < df.shape[1]:
            serie_original = df.iloc[:, idx].apply(normalizar_para_float)
            df_proc[nome_col] = (serie_original > 0).astype(int)
        else:
            df_proc[nome_col] = 0

    # 2. AGRUPAMENTO POR KM (SEGMENTO)
    
    df_resumo = df_proc.groupby('km_segmento').apply(lambda x: pd.Series({
        'total_estacas': len(x),
        
        # --- CÁLCULO TRINCAS (% EXTENSÃO) ---
        'estacas_com_trinca': ((x['g1_le'] | x['g1_ld'] | x['g2_le'] | x['g2_ld']) > 0).sum(),
        
        # --- CÁLCULO DEFORMAÇÕES (% EXTENSÃO) ---
        'estacas_com_deform': ((x['g5_le'] | x['g5_ld'] | x['g6_le'] | x['g6_ld']) > 0).sum(),
        
        # --- CÁLCULO PANELAS + REMENDOS (QUANTIDADE ABSOLUTA) ---
        'qtd_total_panelas_remendos': (x['g3_le'] + x['g3_ld'] + x['g4_le'] + x['g4_ld']).sum()
        
    })).reset_index()

    # 3. CÁLCULO DAS FREQUÊNCIAS E IGGE
    
    # TRINCAS: Baseado em % da extensão do km afetada
    df_resumo['pct_trincas'] = (df_resumo['estacas_com_trinca'] / df_resumo['total_estacas']) * 100
    df_resumo['freq_trincas'] = df_resumo['pct_trincas'].apply(
        lambda p: 'A' if p >= 15 else ('M' if p > 5 else 'B')
    )
    
    # DEFORMAÇÕES: Baseado em % da extensão
    df_resumo['pct_deform'] = (df_resumo['estacas_com_deform'] / df_resumo['total_estacas']) * 100
    df_resumo['freq_deform'] = df_resumo['pct_deform'].apply(
        lambda p: 'A' if p >= 15 else ('M' if p > 5 else 'B')
    )
    
    # PANELAS + REMENDOS: Baseado na Quantidade por km (Soma absoluta)
    df_resumo['freq_panelas'] = df_resumo['qtd_total_panelas_remendos'].apply(
        lambda q: 'A' if q >= 5 else ('M' if q >= 2 else 'B')
    )

    # 4. APLICAÇÃO DOS PESOS E FÓRMULA FINAL
    df_resumo['ft'] = df_resumo['freq_trincas'].map(FATORES_GRAV['Trincas'])
    df_resumo['fd'] = df_resumo['freq_deform'].map(FATORES_GRAV['Deformacoes'])
    df_resumo['fp'] = df_resumo['freq_panelas'].map(FATORES_GRAV['Panelas'])

    # IGGE = (Pt*Ft + Poap*Fd + Ppr*Fp) * 100
    df_resumo['igge'] = (
        (PESOS['Trincas'] * df_resumo['ft']) +
        (PESOS['Deformacoes'] * df_resumo['fd']) +
        (PESOS['Panelas'] * df_resumo['fp'])
    ) * 100
    
    df_resumo['igge'] = df_resumo['igge'].clip(upper=500)

    def classificar(v):
        if v <= 65: return 'Ótimo'
        if v <= 110: return 'Bom'
        if v <= 160: return 'Regular'
        if v <= 230: return 'Ruim'
        return 'Péssimo'

    df_resumo['conceito'] = df_resumo['igge'].apply(classificar)
    df_resumo['ies'] = (10 - (df_resumo['igge'] * 10 / 500)).clip(lower=0)

    # 5. SALVAR NO BANCO
    cursor.execute("DELETE FROM resultados_pro008 WHERE upload_id = ?", (upload_id,))
    
    dados_insert = []
    for _, row in df_resumo.iterrows():
        dados_insert.append((
            upload_id, row['km_segmento'], row['km_segmento']+1,
            int(row['total_estacas']),
            
            int(row['estacas_com_trinca']), row['pct_trincas'],
            int(row['estacas_com_deform']), row['pct_deform'],
            
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
        'datasets': [{'label': 'IGGE', 'data': [r['igge'] for r in res], 
                      'backgroundColor': '#0d6efd'}]
    }
    return render_template('relatorio.html', resultados=res, chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)