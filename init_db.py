import sqlite3

conn = sqlite3.connect('projeto.db')
cursor = conn.cursor()

# --- TABELA 1: DADOS BRUTOS (Mantém igual) ---
cursor.execute('DROP TABLE IF EXISTS estacas')
cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL NOT NULL,
    area_g1_le REAL DEFAULT 0, area_g1_ld REAL DEFAULT 0,
    area_g2_le REAL DEFAULT 0, area_g2_ld REAL DEFAULT 0,
    area_g3_le REAL DEFAULT 0, area_g3_ld REAL DEFAULT 0,
    area_g4_le REAL DEFAULT 0, area_g4_ld REAL DEFAULT 0,
    area_g5_le REAL DEFAULT 0, area_g5_ld REAL DEFAULT 0,
    area_g6_le REAL DEFAULT 0, area_g6_ld REAL DEFAULT 0,
    area_g7_le REAL DEFAULT 0, area_g7_ld REAL DEFAULT 0,
    area_g8_le REAL DEFAULT 0, area_g8_ld REAL DEFAULT 0
);
''')

# --- TABELA 2: RESULTADOS PRO-008 (COM MEMÓRIA DE CÁLCULO) ---
cursor.execute('DROP TABLE IF EXISTS resultados_pro008')

cursor.execute('''
CREATE TABLE resultados_pro008 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id TEXT NOT NULL,
    km_inicial REAL,
    km_final REAL,
    
    -- MEMÓRIA DE CÁLCULO (NOVAS COLUNAS)
    total_estacas INTEGER,       -- Quantas estacas existem neste km (ex: 50)
    
    qtd_trincas INTEGER,         -- Quantas estacas tiveram trincas
    pct_trincas REAL,            -- % de trincas (qtd / total * 100)
    
    qtd_deformacoes INTEGER,     -- Quantas estacas tiveram deformação
    pct_deformacoes REAL,        -- % de deformação
    
    qtd_panelas INTEGER,         -- Quantas estacas tiveram panelas (para contagem)
    
    -- Parâmetros Finais
    freq_trincas TEXT,
    freq_deformacoes TEXT,
    freq_panelas TEXT,
    
    grav_trincas REAL,
    grav_deformacoes REAL,
    grav_panelas REAL,
    
    igge REAL,
    ies REAL,
    conceito TEXT
);
''')

conn.commit()
conn.close()

print("Banco de dados atualizado! Agora preparado para salvar a Memória de Cálculo.")