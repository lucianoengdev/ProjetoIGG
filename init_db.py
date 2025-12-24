import sqlite3

conn = sqlite3.connect('projeto.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS estacas')
cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL,
    area_g1_le REAL DEFAULT 0, area_g1_ld REAL DEFAULT 0,
    area_g2_le REAL DEFAULT 0, area_g2_ld REAL DEFAULT 0,
    area_g3_le REAL DEFAULT 0, area_g3_ld REAL DEFAULT 0,
    area_g4_le REAL DEFAULT 0, area_g4_ld REAL DEFAULT 0,
    area_g5_le REAL DEFAULT 0, area_g5_ld REAL DEFAULT 0,
    area_g6_le REAL DEFAULT 0, area_g6_ld REAL DEFAULT 0
);
''')

cursor.execute('DROP TABLE IF EXISTS resultados_pro008')
cursor.execute('''
CREATE TABLE resultados_pro008 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id TEXT,
    km_inicial REAL, km_final REAL,
    total_estacas INTEGER,
    
    qtd_trincas REAL, pct_trincas REAL,
    qtd_deformacoes REAL, pct_deformacoes REAL,
    qtd_panelas INTEGER,
    
    freq_trincas TEXT, freq_deformacoes TEXT, freq_panelas TEXT,
    grav_trincas REAL, grav_deformacoes REAL, grav_panelas REAL,
    
    igge REAL,
    icpf INTEGER,
    ies INTEGER,
    conceito TEXT
);
''')

conn.commit()
conn.close()