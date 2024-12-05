import sqlite3
import pandas as pd

# Step 1: Connect to SQLite Database
conn = sqlite3.connect("world_heritage7.db")
cursor = conn.cursor()
cursor.row_factory = sqlite3.Row
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
    FOREIGN KEY (category_short) REFERENCES Category_Description(category_short),
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

# Tabela de critérios para associar critérios aos sítios
cursor.execute("""
CREATE TABLE IF NOT EXISTS Site_Criteria (
    site_number INTEGER PRIMARY KEY,
    criterion_code VARCHAR(3),
    FOREIGN KEY (site_number) REFERENCES World_Heritage_Site(id_no),
    FOREIGN KEY (criterion_code) REFERENCES Criterion_Descriptions(criterion_code)
);
""")

# Tabela de descrições dos critérios
cursor.execute("""
CREATE TABLE IF NOT EXISTS Criterion_Descriptions (
    criterion_code VARCHAR(3) PRIMARY KEY,
    cd_description VARCHAR(290)
);
""")

# Tabela de lugares (informações do país e região)
cursor.execute("""
CREATE TABLE IF NOT EXISTS Place (
    iso_code VARCHAR(2) PRIMARY KEY,
    site_number INTEGER,
    states_name_en VARCHAR(20),
    udnp_code VARCHAR(3),
    region_en VARCHAR(20),
    FOREIGN KEY (site_number) REFERENCES Location(site_number)
);
""")

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

# Step 3: Import Data from Excel
file_path = "whc-sites-2025.xlsx"

# Importar cada planilha para sua tabela correspondente
sheet_to_table = {
    "World_Heritage_Site": "World_Heritage_Site",
    "Location": "Location",
    "Associated_Dates": "Associated_Dates",
    "Category": "Category",
    "Category_Description": "Category_Description",
    "Criteria": "Criteria",
    "Place": "Place",
    "State_of_Danger": "State_of_Danger"
}

for sheet_name, table_name in sheet_to_table.items():
    # Ler a planilha
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Verificar e corrigir cabeçalhos específicos, se necessário
    if sheet_name == "State_of_Danger":
        # Renomear colunas mal formatadas (se aplicável)
        df.rename(columns={"site_number.1": "site_number"}, inplace=True)
    
    # Inserir dados na tabela
    df.to_sql(table_name, conn, if_exists="append", index=False)

# Step 4: Preencher a tabela Criterion_Descriptions com as descrições dos critérios
cursor.execute("""
INSERT OR IGNORE INTO Criterion_Descriptions (criterion_code, cd_description) VALUES
('C1', 'To represent a masterpiece of human creative genius.'),
('C2', 'To exhibit an important interchange of human values, over a span of time or within a cultural area of the world, on developments in architecture or technology, monumental arts, town-planning or landscape design.'),
('C3', 'To bear a unique or at least exceptional testimony to a cultural tradition or to a civilization which is living or which has disappeared.'),
('C4', 'To be an outstanding example of a type of building, architectural or technological ensemble or landscape which illustrates (a) significant stage(s) in human history.'),
('C5', 'To be an outstanding example of a traditional human settlement, land-use, or sea-use which is representative of a culture (or cultures), or human interaction with the environment especially when it has become vulnerable under the impact of irreversible change.'),
('C6', 'To be directly or tangibly associated with events or living traditions, with ideas, or with beliefs, with artistic and literary works of outstanding universal significance. (The Committee considers that this criterion should preferably be used in conjunction with other criteria).'),
('N7', 'To contain superlative natural phenomena or areas of exceptional natural beauty and aesthetic importance.'),
('N8', 'To be outstanding examples representing major stages of earth's history, including the record of life, significant on-going geological processes in the development of landforms, or significant geomorphic or physiographic features.'),
('N9', 'To be outstanding examples representing significant on-going ecological and biological processes in the evolution and development of terrestrial, fresh water, coastal and marine ecosystems and communities of plants and animals.'),
('N10', 'To contain the most important and significant natural habitats for in-situ conservation of biological diversity, including those containing threatened species of outstanding universal value from the point of view of science or conservation.');
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
df_filtered.to_sql('Site_Criteria', conn, if_exists="append", index=False)

# Step 6: Commit and Close
conn.commit()
conn.close()

print("Data imported successfully!")
