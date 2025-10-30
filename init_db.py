import sqlite3

conn = sqlite3.connect('projeto.db')
cursor = conn.cursor()

# Destrói a tabela 'estacas' V2 (se ela existir)
cursor.execute('DROP TABLE IF EXISTS estacas')

# Cria a nova tabela 'estacas' (V3) com TODAS as colunas de engenharia
cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL NOT NULL,

    -- Colunas de Defeitos (G1 a G8)
    area_g1_le REAL, fr_g1_le REAL, igi_g1_le REAL,
    area_g1_ld REAL, fr_g1_ld REAL, igi_g1_ld REAL,
    area_g2_le REAL, fr_g2_le REAL, igi_g2_le REAL,
    area_g2_ld REAL, fr_g2_ld REAL, igi_g2_ld REAL,
    area_g3_le REAL, fr_g3_le REAL, igi_g3_le REAL,
    area_g3_ld REAL, fr_g3_ld REAL, igi_g3_ld REAL,
    area_g4_le REAL, fr_g4_le REAL, igi_g4_le REAL,
    area_g4_ld REAL, fr_g4_ld REAL, igi_g4_ld REAL,
    area_g5_le REAL, fr_g5_le REAL, igi_g5_le REAL,
    area_g5_ld REAL, fr_g5_ld REAL, igi_g5_ld REAL,
    area_g6_le REAL, fr_g6_le REAL, igi_g6_le REAL,
    area_g6_ld REAL, fr_g6_ld REAL, igi_g6_ld REAL,
    area_g7_le REAL, fr_g7_le REAL, igi_g7_le REAL,
    area_g7_ld REAL, fr_g7_ld REAL, igi_g7_ld REAL,
    area_g8_le REAL, fr_g8_le REAL, igi_g8_le REAL,
    area_g8_ld REAL, fr_g8_ld REAL, igi_g8_ld REAL,

    -- Subtotal dos Defeitos
    igg_defeitos_g1_g8 REAL,

    -- Colunas das Flechas (TRI/TRE)
    valor_tri_le REAL,
    valor_tri_ld REAL,
    valor_tre_le REAL,
    valor_tre_ld REAL,

    -- Estatísticas das Flechas (Cálculos Intermediários)
    mean_le REAL,
    mean_ld REAL,
    var_le REAL,
    var_ld REAL,
    tri_agg REAL, -- Média das Médias
    tre_agg REAL, -- Média das Variâncias

    -- Resultados das Flechas (Regras de Decisão)
    igi_trilha REAL,
    igi_var REAL,
    igi_flechas_final REAL, -- MAX(igi_trilha, igi_var)

    -- O GRANDE TOTAL
    igg_total_final_estaca REAL -- (igg_defeitos_g1_g8 + igi_flechas_final)
);
''')

conn.commit()
conn.close()

print("Banco de dados 'projeto.db' (V3) criado com sucesso!")
print("Novas colunas para lógica de Flechas (TRI/TRE) foram adicionadas.")