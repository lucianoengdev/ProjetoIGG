import pandas as pd
import sqlite3
import uuid
import os
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_segura_projeto_igg_memoria'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

DATABASE = 'projeto.db'

# MAPA DE COLUNAS (Obrigatório seguir ordem da planilha)
MAPA_COLUNAS = {
    'km': 0, 'area_g1_le': 1, 'area_g1_ld': 2, 'area_g2_le': 3, 'area_g2_ld': 4,
    'area_g3_le': 5, 'area_g3_ld': 6, 'area_g4_le': 7, 'area_g4_ld': 8,
    'area_g5_le': 9, 'area_g5_ld': 10, 'area_g6_le': 11, 'area_g6_ld': 12
}

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

# --- CONSTANTES ---
PESOS = {'Trincas': 0.35, 'Deformacoes': 0.60, 'Panelas': 0.70}
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

    # 1. Tratamento e Inserção de Brutos (igual anterior)
    df_insert = pd.DataFrame()
    idx_km = MAPA_COLUNAS['km']
    df_insert['km'] = df.iloc[:, idx_km].apply(normalizar_para_float)
    
    for nome, idx in MAPA_COLUNAS.items():
        if nome != 'km':
            if idx < df.shape[1]:
                df_insert[nome] = df.iloc[:, idx].apply(normalizar_para_float)
            else:
                df_insert[nome] = 0.0

    # Inserção de dados brutos para histórico
    cols = list(MAPA_COLUNAS.keys())
    placeholders = ', '.join(['?' for _ in cols])
    try:
        cursor.executemany(f"INSERT INTO estacas ({', '.join(cols)}) VALUES ({placeholders})", 
                           df_insert[cols].values.tolist())
    except Exception as e:
        print(f"Erro inserção brutos: {e}")

    # 2. CÁLCULO E MEMÓRIA
    df_calc = df_insert.copy()
    df_calc['km_segmento'] = df_calc['km'].apply(lambda x: int(x))

    # Agrupamento com contagem detalhada
    df_seg = df_calc.groupby('km_segmento').agg(
        total_estacas=('km', 'count'),
        # Soma quantas estacas tiveram defeito (> 0)
        qtd_trincas=('area_g1_le', lambda x: ((x > 0) | (df_calc.loc[x.index, 'area_g2_le'] > 0) | (df_calc.loc[x.index, 'area_g1_ld'] > 0) | (df_calc.loc[x.index, 'area_g2_ld'] > 0)).sum()),
        qtd_deform=('area_g5_le', lambda x: ((x > 0) | (df_calc.loc[x.index, 'area_g6_le'] > 0) | (df_calc.loc[x.index, 'area_g5_ld'] > 0) | (df_calc.loc[x.index, 'area_g6_ld'] > 0)).sum()),
        qtd_panelas=('area_g3_le', lambda x: ((x > 0) | (df_calc.loc[x.index, 'area_g4_le'] > 0) | (df_calc.loc[x.index, 'area_g3_ld'] > 0) | (df_calc.loc[x.index, 'area_g4_ld'] > 0)).sum())
    ).reset_index()

    # 3. Cálculos de Porcentagem e Frequência
    # Trincas e Deformações (Baseado em % de Extensão)
    df_seg['pct_trincas'] = (df_seg['qtd_trincas'] / df_seg['total_estacas']) * 100
    df_seg['freq_trincas'] = df_seg['pct_trincas'].apply(lambda x: 'A' if x >= 15 else ('M' if x > 5 else 'B'))

    df_seg['pct_deform'] = (df_seg['qtd_deform'] / df_seg['total_estacas']) * 100
    df_seg['freq_deform'] = df_seg['pct_deform'].apply(lambda x: 'A' if x >= 15 else ('M' if x > 5 else 'B'))

    # Panelas (Baseado em Ocorrências absolutas por km)
    df_seg['freq_panelas'] = df_seg['qtd_panelas'].apply(lambda x: 'A' if x >= 5 else ('M' if x >= 2 else 'B'))

    # 4. Fatores e IGGE
    df_seg['ft'] = df_seg['freq_trincas'].map(FATORES_GRAV['Trincas'])
    df_seg['fd'] = df_seg['freq_deform'].map(FATORES_GRAV['Deformacoes'])
    df_seg['fp'] = df_seg['freq_panelas'].map(FATORES_GRAV['Panelas'])

    # FÓRMULA FINAL PRO-008
    df_seg['igge'] = ((PESOS['Trincas'] * df_seg['ft']) + 
                      (PESOS['Deformacoes'] * df_seg['fd']) + 
                      (PESOS['Panelas'] * df_seg['fp'])) * 100
    
    df_seg['igge'] = df_seg['igge'].clip(upper=500)

    # Conceito e IES
    def get_conceito(v):
        if v <= 65: return 'Ótimo'
        if v <= 110: return 'Bom'
        if v <= 160: return 'Regular'
        if v <= 230: return 'Ruim'
        return 'Péssimo'
    
    df_seg['conceito'] = df_seg['igge'].apply(get_conceito)
    df_seg['ies'] = (10 - (df_seg['igge'] * 10 / 500)).clip(lower=0)

    # 5. Salvar TUDO no banco (incluindo memória)
    cursor.execute("DELETE FROM resultados_pro008 WHERE upload_id = ?", (upload_id,))
    
    dados = []
    for _, row in df_seg.iterrows():
        dados.append((
            upload_id, row['km_segmento'], row['km_segmento']+1,
            int(row['total_estacas']),
            int(row['qtd_trincas']), row['pct_trincas'],
            int(row['qtd_deform']), row['pct_deform'],
            int(row['qtd_panelas']),
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
    
    cursor.executemany(sql, dados)
    db.commit()

# ROTAS (Index igual, Relatório atualizado na próxima etapa)
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
                # header=None, skiprows=linha-1
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
                      'backgroundColor': '#ffcc00'}] # Cor simplificada
    }
    return render_template('relatorio.html', resultados=res, chart_data=chart_data)

if __name__ == '__main__':
    app.run(debug=True)