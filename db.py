import mysql.connector

def get_db_schema(config):
    schema = {}
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        db_name = config.get('database')

        # Buscar todas as tabelas do banco
        query = f"""
            SELECT TABLE_NAME FROM information_schema.tables
            WHERE table_schema = '{db_name}';
        """
        cursor.execute(query)
        tables = [table[0] for table in cursor.fetchall()]
        
        # Para cada tabela, buscar suas colunas com tipos de dados
        for table_name in tables:
            query = f"""
                SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns
                WHERE table_schema = '{db_name}' AND table_name = '{table_name}'
                ORDER BY ORDINAL_POSITION;
            """
            cursor.execute(query)
            columns = cursor.fetchall()
            # Armazenar nome da coluna e tipo de dados
            schema[table_name] = [(col[0], col[1]) for col in columns]
        
        return schema
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

# Configuração do banco - ajustada para o schema fornecido
db_config = {
    'user': 'myuser',
    'password': '012345678',
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'mydb'  # Nome correto conforme o schema SQL
}

DB_SCHEMA = get_db_schema(db_config)
if DB_SCHEMA:
    print("Database schema retrieved successfully.")
    for table, columns in DB_SCHEMA.items():
        print(f"Table: {table}")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
else:
    print("Failed to retrieve database schema.")
