import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)


    def _parse_query(self, query):
        query = query.strip().rstrip(';')  
    

        pattern = re.compile(
            r"SELECT\s+(?P<columns>[\w\*,\s\.]+)\s+"
            r"FROM\s+(?P<base_table>\w+)"
            r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_on>[^;]+?))?"
            r"(?:\s+WHERE\s+(?P<where>[^;]+))?$",
            re.IGNORECASE | re.DOTALL
        )

        match = pattern.match(query)
        if not match:
            print(f"X Erro de Sintaxe: A consulta '{query}' não segue a estrutura SELECT...FROM...[INNER JOIN...ON...] [WHERE...]")
            return None

        return match.groupdict()

    def validate_query(self, query):
        print(f"\n Testando: {query}")
        parsed = self._parse_query(query)
        if parsed is None:
            return False
        
        tables_query = [parsed['base_table']]
        if parsed.get('join_table'):
            tables_query.append(parsed["join_table"])
        
        for table in tables_query:
            if self.schema is None:
                print(f" Erro: Não foi possível conectar ao banco de dados.")
                return False
            
            if table not in self.schema:
                print(f"X Erro: A tabela '{table}' não existe no banco de dados.")
                return False

        is_valid, msg = self._validate_select_columns(parsed['columns'], tables_query)
        if not is_valid:
            print(f"X Erro: {msg}")
            return False, msg
        
        if parsed.get('where'):
            is_valid, msg = self._validate_where_columns(parsed['where'], tables_query)
            if not is_valid:
                print(f"X Erro: {msg}")
                return False, msg
            
        if parsed.get('join_on'):
            is_valid, msg = self._validate_on_columns(parsed['join_on'], tables_query)
            if not is_valid:
                print(f"X Erro: {msg}")
                return False, msg
            
        print("✔ Consulta válida.")
        return True
    
    def _check_single_column(self, col_identifier, tables_in_query):
     
        
        if '.' in col_identifier:
            table_name, column_name = col_identifier.split('.', 1)
            
            if table_name not in tables_in_query:
                return False, f"A tabela '{table_name}' não está na consulta."
            
            # Extrair apenas os nomes das colunas do schema (ignorar os tipos)
            table_columns = [col[0] for col in self.schema.get(table_name, [])]
            if column_name not in table_columns:
                return False, f"A coluna '{column_name}' não existe na tabela '{table_name}'."
            
        else:
            column_name = col_identifier
            found_in_tables = []
            for table in tables_in_query:
                # Extrair apenas os nomes das colunas do schema (ignorar os tipos)
                table_columns = [col[0] for col in self.schema.get(table, [])]
                if column_name in table_columns:
                    found_in_tables.append(table)

            if len(found_in_tables) == 0:
                return False, f"A coluna '{column_name}' não existe nas tabelas referenciadas."
            if len(found_in_tables) > 1:
                return False, f"A coluna '{column_name}' é ambígua. Especifique a tabela."
        return True, "Coluna válida."
    
    def _validate_select_columns(self, columns_str, tables):
        column_list = [col.strip() for col in columns_str.split(',')]
        
        for col_ident in column_list:
            if col_ident == '*':
                continue
                
            is_valid, msg = self._check_single_column(col_ident, tables)
            if not is_valid:
                return False, msg
        
        return True, "Colunas SELECT válidas."
    
    
  

    def _validate_where_columns(self, where_clause, tables_in_query):
        # Remover strings entre aspas simples e duplas antes de buscar colunas
        cleaned_clause = re.sub(r"'[^']*'", '', where_clause)
        cleaned_clause = re.sub(r'"[^"]*"', '', cleaned_clause)
        
        possible_columns = re.findall(r'[\w.]+', cleaned_clause)
        
        for ident in possible_columns:
            if ident.isdigit() or ident.upper() in ['WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE']:
                continue

            is_valid, msg = self._check_single_column(ident, tables_in_query)
            if not is_valid:
                return False, msg

        return True, "Colunas WHERE válidas."
    
    def _validate_on_columns(self, on_str, tables_in_query):
        # Remover strings entre aspas simples e duplas antes de buscar colunas
        cleaned_clause = re.sub(r"'[^']*'", '', on_str)
        cleaned_clause = re.sub(r'"[^"]*"', '', cleaned_clause)
        
        possible_columns = re.findall(r'[\w.]+', cleaned_clause)
        
        for ident in possible_columns:
            if ident.isdigit() or ident.upper() in ['ON', 'AND', 'OR']:
                continue

            is_valid, msg = self._check_single_column(ident, tables_in_query)
            if not is_valid:
                return False, msg

        return True, "Colunas ON válidas."