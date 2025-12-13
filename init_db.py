import sqlite3

conn = sqlite3.connect('projeto.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS estacas')

cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL NOT NULL,
    
    -- Vamos manter a estrutura de G1 a G8 se sua planilha usa esse padrão
    -- Mas usaremos esses dados para calcular Frequência (Alta/Média/Baixa)
    area_g1_le REAL DEFAULT 0, area_g1_ld REAL DEFAULT 0, -- Trincas
    area_g2_le REAL DEFAULT 0, area_g2_ld REAL DEFAULT 0, -- Trincas
    area_g3_le REAL DEFAULT 0, area_g3_ld REAL DEFAULT 0, -- Panelas/Remendos
    area_g4_le REAL DEFAULT 0, area_g4_ld REAL DEFAULT 0, -- Panelas/Remendos
    area_g5_le REAL DEFAULT 0, area_g5_ld REAL DEFAULT 0, -- Deformações
    area_g6_le REAL DEFAULT 0, area_g6_ld REAL DEFAULT 0, -- Deformações
    area_g7_le REAL DEFAULT 0, area_g7_ld REAL DEFAULT 0,
    area_g8_le REAL DEFAULT 0, area_g8_ld REAL DEFAULT 0,

    -- Colunas de Flechas (opcional, mas bom ter para deformação)
    valor_tri_le REAL DEFAULT 0, valor_tri_ld REAL DEFAULT 0,
    valor_tre_le REAL DEFAULT 0, valor_tre_ld REAL DEFAULT 0
);
''')

cursor.execute('DROP TABLE IF EXISTS resultados_pro008')

cursor.execute('''
CREATE TABLE resultados_pro008 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km_inicial REAL,
    km_final REAL,
    
    -- Parâmetros calculados pelo sistema (Frequência e Gravidade)
    freq_trincas TEXT,      -- 'A', 'M' ou 'B'
    grav_trincas INTEGER,   -- 1, 2 ou 3
    
    freq_deformacoes TEXT,  -- 'A', 'M' ou 'B'
    grav_deformacoes INTEGER, -- 1, 2 ou 3
    
    freq_panelas TEXT,      -- 'A', 'M' ou 'B' (Baseado em Qtd/km)
    grav_panelas INTEGER,   -- 1, 2 ou 3
    
    -- Índices Finais da Norma
    icpf REAL, -- Índice de Condição (Estimado ou calculado)
    igge REAL, -- Índice de Gravidade Global Expedito (0 a 100+)
    ies REAL,  -- Índice do Estado da Superfície (0 a 10)
    
    conceito TEXT -- Ótimo, Bom, Regular, Ruim, Péssimo
);
''')

conn.commit()
conn.close()