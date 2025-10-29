import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)
        self.allowed_tokens = {
            '=', '>', '<', '<=', '>=', '<>', 'AND', 'OR', '(', ')'
        }
        self.reserved_keywords = {
            'SELECT', 'FROM', 'WHERE', 'INNER', 'JOIN', 'ON', 'AS'
        }

    def _parse_sql(self, query):
        """
        Parser robusto que extrai as cláusulas SELECT, FROM e WHERE.
        Ele agora lida com a complexidade da cláusula FROM separadamente.
        """
        query_clean = query.strip().rstrip(';')
        
        # Padrão para encontrar as cláusulas principais
        pattern = re.compile(
            r"^\s*SELECT\s+(?P<columns>.+?)\s+"
            r"FROM\s+(?P<from_clause>.+?)"
            r"(?:\s+WHERE\s+(?P<where_clause>.+))?\s*$",
            re.IGNORECASE | re.DOTALL
        )
        
        match = pattern.match(query_clean)
        if not match:
            return None, "A consulta não segue a estrutura básica 'SELECT ... FROM ... [WHERE ...]'."
        
        parts = match.groupdict()

        # Validação adicional para evitar palavras-chave no lugar errado
        if re.search(r'\b(FROM|WHERE)\b', parts['columns'], re.IGNORECASE):
            return None, "Palavra-chave 'FROM' ou 'WHERE' encontrada na lista de colunas."
        
        return parts, "Parsing inicial bem-sucedido."

    def validate_query(self, query):
        # Validação de sintaxe muito básica primeiro para erros óbvios
        if re.search(r'\b(SELECT\s+SELECT|FROM\s+FROM|WHERE\s+WHERE)\b', query, re.IGNORECASE):
            return False, "Erro de sintaxe: Palavra-chave duplicada (SELECT, FROM ou WHERE)."

        parsed, msg = self._parse_sql(query)
        if parsed is None:
            return False, msg

        # Passo 1: Validar FROM e extrair tabelas
        is_valid, tables_in_query, msg_from = self._validate_from_clause(parsed['from_clause'])
        if not is_valid:
            return False, msg_from

        # Passo 2: Validar colunas do SELECT
        is_valid, msg_select = self._validate_select_columns(parsed['columns'], tables_in_query)
        if not is_valid:
            return False, msg_select
        
        # Passo 3: Validar cláusula WHERE (se existir)
        if parsed.get('where_clause'):
            is_valid, msg_where = self._validate_where_on_clause(parsed['where_clause'], tables_in_query, "WHERE")
            if not is_valid:
                return False, msg_where
        
        # CORREÇÃO: Garante que um tuple seja retornado em caso de sucesso
        return True, "Consulta válida."

    def _validate_from_clause(self, from_clause_str):
        tables_map = {} # Mapeia alias/nome para o nome real da tabela
        
        # Pattern para detectar INNER JOINs de forma iterativa
        join_pattern = re.compile(
            r"INNER\s+JOIN\s+(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>\w+))?\s+ON\s+(?P<on_clause>.*?)(?=\s+INNER\s+JOIN|$)",
            re.IGNORECASE | re.DOTALL
        )
        
        # Extrair tabela base
        base_match = re.match(r"^(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>\w+))?", from_clause_str, re.IGNORECASE)
        if not base_match:
            return False, None, "Cláusula FROM malformada. Não foi possível encontrar a tabela base."

        base_info = base_match.groupdict()
        base_table_name = base_info['table']
        base_alias_or_name = base_info.get('alias') or base_table_name
        
        if self.schema and base_table_name.lower() not in [k.lower() for k in self.schema.keys()]:
            return False, None, f"A tabela base '{base_table_name}' não existe no banco de dados."
        tables_map[base_alias_or_name] = base_table_name
        
        remaining_from = from_clause_str[base_match.end():]
        
        for join_match in join_pattern.finditer(remaining_from):
            join_info = join_match.groupdict()
            join_table_name = join_info['table']
            join_alias_or_name = join_info.get('alias') or join_table_name
            
            if self.schema and join_table_name.lower() not in [k.lower() for k in self.schema.keys()]:
                 return False, None, f"A tabela '{join_table_name}' do JOIN não existe no banco de dados."
            tables_map[join_alias_or_name] = join_table_name

            # Valida a condição ON do join
            is_valid, msg = self._validate_where_on_clause(join_info['on_clause'], list(tables_map.keys()), "ON")
            if not is_valid:
                return False, None, msg
        
        return True, list(tables_map.keys()), "Cláusula FROM válida."

    def _validate_select_columns(self, columns_str, tables_in_query):
        if not columns_str.strip() or columns_str.strip() == ',':
            return False, "Lista de colunas do SELECT está vazia ou malformada."
            
        if columns_str.strip() == '*':
            return True, "Colunas SELECT válidas (*)."

        column_list = [col.strip() for col in columns_str.split(',') if col.strip()]
        
        for col_ident in column_list:
            if col_ident.upper() in self.reserved_keywords:
                return False, f"Palavra reservada '{col_ident}' não pode ser usada como nome de coluna."
            # A validação de coluna individual é opcional e pode ser expandida aqui se necessário
        
        return True, "Colunas SELECT válidas."

    def _validate_where_on_clause(self, clause_str, tables_in_query, clause_name):
        # Esta é uma validação simplificada que pode ser expandida
        # A lógica aqui apenas garante que não há erros óbvios.
        if not clause_str.strip():
            return False, f"Cláusula {clause_name} está vazia."
        return True, f"Cláusula {clause_name} válida."