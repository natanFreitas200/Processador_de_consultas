import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)
        self.allowed_tokens = {
            '=', '>', '<', '<=', '>=', '<>', 'AND', '(', ')'
        }

    def _parse_query(self, query):
        """
        Analisa a consulta usando uma expressão regular estrita que corresponde
        apenas às cláusulas e à estrutura permitidas.
        """
        query = query.strip().rstrip(';')

        pattern = re.compile(
            r"^\s*SELECT\s+(?P<columns>[\w\s.,\*]+?)\s+"
            r"FROM\s+(?P<base_table>\w+)"
            r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_on>.+?))?"
            r"(?:\s+WHERE\s+(?P<where>.+))?\s*$",
            re.IGNORECASE
        )

        match = pattern.match(query)
        if not match:
            print(f"X Erro de Sintaxe: A consulta '{query}' não segue a estrutura permitida (SELECT... FROM... [INNER JOIN... ON...] [WHERE...]) ou contém cláusulas/operadores não suportados.")
            return None

        return match.groupdict()

    def validate_query(self, query):
        print(f"\n Testando: {query}")
        parsed = self._parse_query(query)
        if parsed is None:
            return False, "Erro de sintaxe."

        tables_query = [parsed['base_table']]
        if parsed.get('join_table'):
            tables_query.append(parsed["join_table"])

        for table in tables_query:
            if self.schema is None:
                msg = "Erro: Não foi possível conectar ao banco de dados."
                print(msg)
                return False, msg
            if table not in self.schema:
                msg = f"A tabela '{table}' não existe no banco de dados."
                print(f"X Erro: {msg}")
                return False, msg

        is_valid, msg = self._validate_select_columns(parsed['columns'], tables_query)
        if not is_valid:
            print(f"X Erro: {msg}")
            return False, msg

        if parsed.get('where'):
            is_valid, msg = self._validate_where_on_clause(parsed['where'], tables_query, "WHERE")
            if not is_valid:
                print(f"X Erro: {msg}")
                return False, msg

        if parsed.get('join_on'):
            is_valid, msg = self._validate_where_on_clause(parsed['join_on'], tables_query, "ON")
            if not is_valid:
                print(f"X Erro: {msg}")
                return False, msg

        print("✔ Consulta válida.")
        return True

    def _check_single_column(self, col_identifier, tables_in_query):
        """Verifica se um único identificador de coluna é válido e não ambíguo."""
        if '.' in col_identifier:
            table_name, column_name = col_identifier.split('.', 1)
            if table_name not in tables_in_query:
                return False, f"A tabela '{table_name}' não está na consulta."
            
            table_columns = [col[0] for col in self.schema.get(table_name, [])]
            if column_name not in table_columns:
                return False, f"A coluna '{column_name}' não existe na tabela '{table_name}'."
        else:
            column_name = col_identifier
            found_in_tables = []
            for table in tables_in_query:
                table_columns = [col[0] for col in self.schema.get(table, [])]
                if column_name in table_columns:
                    found_in_tables.append(table)

            if not found_in_tables:
                return False, f"A coluna '{column_name}' não existe nas tabelas referenciadas."
            if len(found_in_tables) > 1:
                return False, f"A coluna '{column_name}' é ambígua. Especifique a tabela (ex: cliente.Nome)."
        
        return True, "Coluna válida."

    def _validate_select_columns(self, columns_str, tables):
        """Valida as colunas na cláusula SELECT."""
        column_list = [col.strip() for col in columns_str.split(',')]
        
        for col_ident in column_list:
            if not col_ident:
                 return False, "Erro de sintaxe na lista de colunas do SELECT (vírgula extra?)."
            if col_ident == '*':
                continue
            
            is_valid, msg = self._check_single_column(col_ident, tables)
            if not is_valid:
                return False, msg
        
        return True, "Colunas SELECT válidas."

    def _validate_where_on_clause(self, clause_str, tables_in_query, clause_name):
        """
        Valida colunas e operadores em uma cláusula WHERE ou ON.
        Garante que apenas tokens permitidos sejam usados.
        """
        cleaned_clause = re.sub(r"'[^']*'", ' literal_string ', clause_str)
        cleaned_clause = re.sub(r'"[^"]*"', ' literal_string ', cleaned_clause)

        tokens = re.findall(r'\(|\)|[<>=!]+|[\w.]+', cleaned_clause)
        
        if not tokens and clause_str.strip():
            return False, f"Erro de sintaxe na cláusula {clause_name}."

        for token in tokens:
            token_upper = token.upper()

            if token_upper in self.allowed_tokens:
                continue
            if token.isdigit() or token == 'literal_string':
                continue

            is_valid, msg = self._check_single_column(token, tables_in_query)
            if not is_valid:
                return False, f"Token inválido ou coluna desconhecida '{token}' na cláusula {clause_name}. {msg}"

        return True, f"Cláusula {clause_name} válida."