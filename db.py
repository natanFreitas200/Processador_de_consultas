import mysql.connector

def get_db_connection():
   
    db_config = {
    'user': 'root',
    'password': '0123456789',
    'host': '127.0.0.1:3306', 
    'database': 'bd_vendas'
    }
    conn = mysql.connector.connect(**db_config)
    return conn