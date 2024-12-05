import sqlite3
import pandas as pd

# Step 1: Connect to SQLite Database
conn = sqlite3.connect("world_heritage10.db")
cursor = conn.cursor()

# Step 2: Create Database Schema

# Tabela de sítios do Patrimônio Mundial
cursor.execute("""
CREATE TABLE IF NOT EXISTS World_Heritage_Site (
    id_no INTEGER PRIMARY KEY,
    unique_number INTEGER,
    name_en VARCHAR(250),
    short_description_en VARCHAR(200),
    justification_en VARCHAR(200),
    rev_bis VARCHAR(3)
);
""")

# Tabela de localizações
cursor.execute("""
CREATE TABLE IF NOT EXISTS Location (
    site_number INTEGER PRIMARY KEY,
    latitude FLOAT,
    longitude FLOAT,
    area_hectares FLOAT,
    transboundary BOOLEAN,
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no)
);
""")

# Tabela de datas associadas
cursor.execute("""
CREATE TABLE IF NOT EXISTS Associated_Dates (
    site_number INTEGER PRIMARY KEY,
    date_inscribed DATE,
    date_end DATE,
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no)
);
""")

# Tabela de categorias
cursor.execute("""
CREATE TABLE IF NOT EXISTS Category (
    site_number INTEGER PRIMARY KEY,
    category_short VARCHAR(1),
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no)
);
""")

# Tabela de descrições das categorias
cursor.execute("""
CREATE TABLE IF NOT EXISTS Category_Description (
    category_short VARCHAR(1) PRIMARY KEY,
    category VARCHAR(10)
);
""")

# Nova tabela para descrever os critérios
cursor.execute("""
CREATE TABLE IF NOT EXISTS Criterion_Descriptions (
    criterion_code VARCHAR(3) PRIMARY KEY,
    cd_description TEXT
);
""")

# Tabela de critérios para associar critérios aos sítios
cursor.execute("""
CREATE TABLE IF NOT EXISTS Site_Criteria (
    site_number INTEGER,
    criterion_code VARCHAR(3),
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no),
    FOREIGN KEY (criterion_code) REFERENCES Criterion_Descriptions(criterion_code)
);
""")

# Tabela de lugares (informações do país e região)
cursor.execute("""
CREATE TABLE IF NOT EXISTS Place (
    site_number INTEGER PRIMARY KEY,
    iso_code VARCHAR(2),
    states_name_en VARCHAR(20),
    udnp_code VARCHAR(3),
    region_en VARCHAR(20),
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no)
);
""")

#'''
# Tabela de estado de perigo
cursor.execute("""
CREATE TABLE IF NOT EXISTS State_of_Danger (
    site_number INTEGER PRIMARY KEY,
    danger BOOLEAN,
    date_end DATE,
    danger_list VARCHAR(200),
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no)
);
""")
#'''

# Step 3: Import Data from Excel
file_path = "whc-sites-2025.xlsx"

# Importar cada planilha para sua tabela correspondente
sheet_to_table = {
    "World_Heritage_Site": "World_Heritage_Site",
    "Location": "Location",
    "Associated_Dates": "Associated_Dates",
    "Category": "Category",
    "Category_Description": "Category_Description",
    "Place": "Place",
    "State_of_Danger": "State_of_Danger"
}

for sheet_name, table_name in sheet_to_table.items():
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.to_sql(table_name, conn, if_exists="replace", index=False)

# Step 4: Preencher a tabela Criterion_Descriptions com as descrições dos critérios
cursor.execute("""
INSERT OR REPLACE INTO Criterion_Descriptions (criterion_code, cd_description) VALUES
('C1', 'Representa uma obra-prima do gênio criativo humano.'),
('C2', 'Exibe uma troca importante de valores humanos ao longo do tempo.'),
('C3', 'Testemunho único ou pelo menos excepcional de uma tradição cultural ou civilização.'),
('C4', 'Exemplo de um tipo de construção ou paisagem significativo na história humana.'),
('C5', 'Exemplo excepcional de assentamento humano tradicional, uso de terra ou do mar.'),
('C6', 'Associado a eventos, tradições, ideias, crenças ou obras artísticas de significado universal.'),
('N7', 'Fenômenos naturais superlativos ou áreas de beleza natural excepcional.'),
('N8', 'Exemplos importantes de processos ecológicos e biológicos em evolução.'),
('N9', 'Exemplares significativos de habitats naturais para a conservação da biodiversidade.'),
('N10', 'Espécies ameaçadas de valor universal excepcional para a ciência e conservação.');
""")

# Step 5: Processar os critérios e inserir na tabela Site_Criteria
criteria_columns = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'N7', 'N8', 'N9', 'N10']

# Ler a planilha "Criteria"
df_criteria = pd.read_excel(file_path, sheet_name="Criteria")

# Transformar os dados de formato wide para long
df_long = df_criteria.melt(id_vars=['site_number'], 
                           value_vars=criteria_columns, 
                           var_name='criterion_code', 
                           value_name='has_criterion')

# Filtrar apenas critérios aplicáveis (onde has_criterion == 1)
df_filtered = df_long[df_long['has_criterion'] == 1].drop(columns=['has_criterion'])

# Inserir os dados na tabela Site_Criteria
df_filtered.to_sql('Site_Criteria', conn, if_exists="replace", index=False)

# Step 6: Commit and Close
conn.commit()
conn.close()

print("Data imported successfully!")
