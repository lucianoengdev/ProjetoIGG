import sqlite3

# Conecta ao banco de dados (isso vai criar o arquivo projeto.db se ele não existir)
conn = sqlite3.connect('projeto.db')

# Cria um "cursor", que é o objeto que executa os comandos
cursor = conn.cursor()

# --- CRIA A TABELA ---
# Primeiro, remove a tabela se ela já existir (para podermos rodar de novo se precisarmos)
cursor.execute('DROP TABLE IF EXISTS estacas')

# Agora, cria a tabela "estacas" com todas as colunas que vamos precisar
# Baseado na sua "Ficha de Cálculo" (Imagem 3) e na lista de 23 colunas.
# Vamos criar colunas para os valores de FR (Frequência Relativa) e IGI (Índice de Gravidade Individual)
# de cada grupo de defeito.
cursor.execute('''
CREATE TABLE estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    km REAL NOT NULL,

    -- Grupo 1 (Trincas Isoladas: FI, TTC, TTL, TLC, TLL, TRR)
    area_g1 REAL,
    fr_g1 REAL,
    igi_g1 REAL,

    -- Grupo 2 (FC-2: J, TB)
    area_g2 REAL,
    fr_g2 REAL,
    igi_g2 REAL,

    -- Grupo 3 (FC-3: JE, TBE)
    area_g3 REAL,
    fr_g3 REAL,
    igi_g3 REAL,

    -- Grupo 4 (Afundamentos: ALP, ATP, ALC, ATC)
    area_g4 REAL,
    fr_g4 REAL,
    igi_g4 REAL,

    -- Grupo 5 (Outros: O, P, E)
    area_g5 REAL,
    fr_g5 REAL,
    igi_g5 REAL,

    -- Grupo 6 (EX)
    area_g6 REAL,
    fr_g6 REAL,
    igi_g6 REAL,

    -- Grupo 7 (D)
    area_g7 REAL,
    fr_g7 REAL,
    igi_g7 REAL,

    -- Grupo 8 (R)
    area_g8 REAL,
    fr_g8 REAL,
    igi_g8 REAL,

    -- Grupo 9 (TRI - da sua lista)
    valor_tri REAL,
    igi_tri REAL,

    -- Grupo 10 (TRE - da sua lista)
    valor_tre REAL,
    igi_tre REAL,

    -- O resultado final para esta estaca
    igg_total_estaca REAL
);
''')

# Salva as mudanças (commit)
conn.commit()

# Fecha a conexão
conn.close()

print("Banco de dados 'projeto.db' e tabela 'estacas' criados com sucesso!")