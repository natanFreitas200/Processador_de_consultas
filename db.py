import mysql.connector
import os

from dotenv import load_dotenv
load_dotenv()

def get_db_schema(config):
    schema = {}
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        db_name = config.get('database')

        query = f"""
            SELECT TABLE_NAME FROM information_schema.tables
            WHERE table_schema = '{db_name}';
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            column_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE FROM information_schema.columns
                WHERE table_schema = '{db_name}' AND table_name = '{table_name}';
            """
            cursor.execute(column_query)
            columns = cursor.fetchall()
            schema[table_name] = [(col[0], col[1]) for col in columns]
        
        return schema
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

db_config = {
   'user': os.getenv('DB_USER'),
   'password': os.getenv('DB_PASSWORD'),
   'host': os.getenv('DB_HOST'),
   'port': int(os.getenv('DB_PORT')),  
   'database': os.getenv('DB_DATABASE')
}


DB_SCHEMA = get_db_schema(db_config)
if DB_SCHEMA:
    print("Database schema retrieved successfully.")
else:
    print("Failed to retrieve database schema.")
    print(f"Configuração de conexão: {db_config}")
    print("Verifique se o MySQL está rodando e as credenciais estão corretas.")
