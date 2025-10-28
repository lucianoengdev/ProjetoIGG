import sqlite3

conn = sqlite3.connect('projeto.db')
cursor = conn.cursor()

# Destrói a tabela 'estacas' antiga (se ela existir)
cursor.execute('DROP TABLE IF EXISTS estacas')

# Cria a nova tabela 'estacas' com a estrutura correta (V2)
# Refletindo a separação LE/LD e os cálculos de TRI/TRE
cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL NOT NULL,

    -- Grupo 1 (Trincas Isoladas: FI, TTC, TTL, TLC, TLL, TRR)
    area_g1_le REAL, fr_g1_le REAL, igi_g1_le REAL,
    area_g1_ld REAL, fr_g1_ld REAL, igi_g1_ld REAL,

    -- Grupo 2 (FC-2: J, TB)
    area_g2_le REAL, fr_g2_le REAL, igi_g2_le REAL,
    area_g2_ld REAL, fr_g2_ld REAL, igi_g2_ld REAL,

    -- Grupo 3 (FC-3: JE, TBE)
    area_g3_le REAL, fr_g3_le REAL, igi_g3_le REAL,
    area_g3_ld REAL, fr_g3_ld REAL, igi_g3_ld REAL,

    -- Grupo 4 (Afundamentos: ALP, ATP, ALC, ATC)
    area_g4_le REAL, fr_g4_le REAL, igi_g4_le REAL,
    area_g4_ld REAL, fr_g4_ld REAL, igi_g4_ld REAL,

    -- Grupo 5 (Outros: O, P, E)
    area_g5_le REAL, fr_g5_le REAL, igi_g5_le REAL,
    area_g5_ld REAL, fr_g5_ld REAL, igi_g5_ld REAL,

    -- Grupo 6 (EX)
    area_g6_le REAL, fr_g6_le REAL, igi_g6_le REAL,
    area_g6_ld REAL, fr_g6_ld REAL, igi_g6_ld REAL,

    -- Grupo 7 (D)
    area_g7_le REAL, fr_g7_le REAL, igi_g7_le REAL,
    area_g7_ld REAL, fr_g7_ld REAL, igi_g7_ld REAL,

    -- Grupo 8 (R)
    area_g8_le REAL, fr_g8_le REAL, igi_g8_le REAL,
    area_g8_ld REAL, fr_g8_ld REAL, igi_g8_ld REAL,

    -- Valores Brutos de TRI e TRE (para cálculo posterior de Média e Variância)
    -- (Estes são os valores xi da sua fórmula)
    valor_tri_le REAL,
    valor_tri_ld REAL,
    valor_tre_le REAL,
    valor_tre_ld REAL,

    -- O resultado final (IGI) para esta estaca (soma dos IGIs de G1 a G8)
    igg_total_estaca REAL
);
''')

conn.commit()
conn.close()

print("Banco de dados 'projeto.db' atualizado com sucesso!")
print("Tabela 'estacas' (V2) criada com a separação LE/LD e campos de TRI/TRE brutos.")