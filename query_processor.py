import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)
        self.reserved_keywords = {'SELECT', 'FROM', 'WHERE', 'INNER', 'JOIN', 'ON', 'AS', 'AND', 'OR'}

    def _parse_sql(self, query):
        """
        Parser que extrai as cláusulas principais (SELECT, FROM, WHERE).
        """
        query_clean = ' '.join(query.strip().rstrip(';').split())
        
        pattern = re.compile(
            r"^\s*SELECT\s+(?P<columns>.+?)\s+"
            r"FROM\s+(?P<from_clause>.+?)"
            r"(?:\s+WHERE\s+(?P<where_clause>.+))?\s*$",
            re.IGNORECASE | re.DOTALL
        )
        
        match = pattern.match(query_clean)
        if not match:
            if query_clean.upper().startswith("FROM"):
                return None, "Erro de sintaxe: A consulta deve começar com 'SELECT'."
            if "FROM" not in query_clean.upper():
                 return None, "Erro de sintaxe: Faltando a cláusula 'FROM'."
            if not query_clean.upper().startswith("SELECT"):
                return None, "Erro de sintaxe: Estrutura da consulta é inválida."
            # Erro genérico para casos como 'SELECT FROM Cliente'
            return None, "Erro de sintaxe: Lista de colunas inválida ou ausente."
        
        return match.groupdict(), "Parsing inicial bem-sucedido."

    def validate_query(self, query):
        """
        Função principal de validação, agora com um conjunto completo de regras de sintaxe.
        """
        # CHECK 1: Erros óbvios de duplicação de palavras-chave
        if re.search(r'\b(SELECT\s+SELECT|FROM\s+FROM|WHERE\s+WHERE|ON\s+ON)\b', query, re.IGNORECASE):
            return False, "Erro de sintaxe: Palavra-chave principal duplicada."
        if re.search(r'\b(INNER\s+JOIN\s+INNER\s+JOIN)\b', query, re.IGNORECASE):
             return False, "Erro de sintaxe: 'INNER JOIN' duplicado."

        parsed, msg = self._parse_sql(query)
        if parsed is None:
            return False, msg

        # 2. Validar a cláusula FROM
        is_valid, tables_map, msg_from = self._validate_from_clause(parsed['from_clause'])
        if not is_valid:
            return False, msg_from

        # 3. Validar a cláusula SELECT
        is_valid, msg_select = self._validate_select_columns(parsed['columns'])
        if not is_valid:
            return False, msg_select
        
        # 4. Validar a cláusula WHERE (se existir)
        if parsed.get('where_clause'):
            is_valid, msg_where = self._validate_where_on_clause(parsed['where_clause'])
            if not is_valid:
                return False, msg_where
        
        return True, "Consulta válida."

    def _validate_from_clause(self, from_clause_str):
        """Valida a cláusula FROM, incluindo JOINs opcionais."""

        tables_map = {}

        # Valida tabela base
        base_match = re.match(
            r"^(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>"
            r"(?!SELECT\b)(?!FROM\b)(?!WHERE\b)(?!JOIN\b)(?!INNER\b)"
            r"(?!LEFT\b)(?!RIGHT\b)(?!FULL\b)(?!CROSS\b)\w+))?",
            from_clause_str,
            re.IGNORECASE
        )
        if not base_match:
            return False, None, "Cláusula FROM malformada: tabela base não encontrada."

        base_table_name = base_match.group('table')
        if base_table_name.upper() in self.reserved_keywords:
            return False, None, f"Erro de sintaxe: '{base_table_name}' é uma palavra-chave reservada."
        if self.schema and base_table_name.lower() not in [k.lower() for k in self.schema.keys()]:
            return False, None, f"A tabela '{base_table_name}' não existe no banco de dados."

        tables_map[base_match.group('alias') or base_table_name] = base_table_name

        remaining_from = from_clause_str[base_match.end():]

        join_pattern = re.compile(
            r"\s+(?:(?P<join_type>INNER|LEFT|RIGHT|FULL|CROSS)\s+)?JOIN\s+"
            r"(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>\w+))?\s+ON\s+"
            r"(?P<on_clause>.*?)(?=(?:\s+(?:(?:INNER|LEFT|RIGHT|FULL|CROSS)\s+)?JOIN\s+)|\s*$)",
            re.IGNORECASE | re.DOTALL
        )
        on_pattern = re.compile(r"\s+ON\s+", re.IGNORECASE)

        has_join = bool(join_pattern.search(remaining_from))
        has_on = bool(on_pattern.search(remaining_from))
        if has_join != has_on:
            if has_join:
                return False, None, "Erro de sintaxe: JOIN sem cláusula ON correspondente."
            return False, None, "Erro de sintaxe: Cláusula ON utilizada sem JOIN."

        last_end = 0
        for join_match in join_pattern.finditer(remaining_from):
            # Verifica texto inesperado entre joins
            gap_text = remaining_from[last_end:join_match.start()]
            if gap_text.strip():
                return False, None, "Erro de sintaxe: Texto inesperado na cláusula FROM."

            join_table = join_match.group('table')
            join_alias_raw = join_match.group('alias')
            if join_alias_raw and join_alias_raw.upper() in self.reserved_keywords:
                return False, None, f"Erro de sintaxe: '{join_alias_raw}' não pode ser usado como alias."

            join_alias = join_alias_raw or join_table
            on_clause = join_match.group('on_clause').strip()

            if join_table.upper() in self.reserved_keywords:
                return False, None, f"Erro de sintaxe: '{join_table}' é uma palavra-chave reservada."
            if self.schema and join_table.lower() not in [k.lower() for k in self.schema.keys()]:
                return False, None, f"A tabela '{join_table}' do JOIN não existe no banco de dados."
            if not on_clause:
                return False, None, "Erro de sintaxe: Cláusula ON vazia no JOIN."

            ok, msg = self._validate_where_on_clause(on_clause)
            if not ok:
                return False, None, msg

            tables_map[join_alias] = join_table
            last_end = join_match.end()

        # Verifica se sobrou texto não processado após o último JOIN
        if remaining_from[last_end:].strip():
            return False, None, "Erro de sintaxe: Texto inesperado após a cláusula FROM."

        return True, tables_map, "Cláusula FROM válida."

    def _validate_select_columns(self, columns_str):
        """
        Valida a lista de colunas, procurando por vírgulas, palavras-chave e sintaxe incorreta.
        """
        if not columns_str.strip() or columns_str.strip() == ',':
            return False, "Erro de sintaxe: Lista de colunas do SELECT está vazia."
        
        # CHECK 4: Pega erros de vírgula extra ou no lugar errado
        if ',,' in columns_str or columns_str.strip().startswith(',') or columns_str.strip().endswith(','):
            return False, "Erro de sintaxe: Vírgula extra ou mal posicionada na lista de colunas."
        
        columns = [c.strip() for c in columns_str.split(',')]
        for col in columns:
            if not col: continue
            
            # CHECK 5: Rejeita palavras-chave reservadas como nomes de coluna
            if col.upper() in self.reserved_keywords:
                 return False, f"Erro de sintaxe: Palavra-chave reservada '{col}' não pode ser usada como nome de coluna."

            # CHECK 6: Detecta parênteses isolados sem função (e.g., '(Email)')
            if re.match(r"^\(\s*\w+\s*\)$", col) and not re.match(r"^\w+\s*\(.*\)$", col):
                return False, f"Erro de sintaxe: Parênteses inapropriados na coluna '{col}'."

            # CHECK 7: Pega erros como "Nome Email" em vez de "Nome, Email"
            parts = col.split()
            if len(parts) > 1 and 'AS' not in [p.upper() for p in parts]:
                return False, f"Erro de sintaxe na lista de colunas perto de '{col}'. Faltou uma vírgula?"
        
        return True, "Colunas SELECT válidas."

    def _validate_where_on_clause(self, clause_str):
        """
        Valida a sintaxe de cláusulas de condição (WHERE, ON).
        """
        # CHECK 7: Rejeita JOINs dentro da cláusula
        if "INNER JOIN" in clause_str.upper():
            return False, "Erro de sintaxe: 'INNER JOIN' não pode ser usado dentro de uma cláusula WHERE."

        # CHECK 8: Verifica parênteses desbalanceados
        if clause_str.count('(') != clause_str.count(')'):
            return False, "Erro de sintaxe: Parênteses desbalanceados na cláusula WHERE/ON."
        
        # CHECK 9: Verifica se a cláusula termina com um operador lógico
        tokens = clause_str.strip().split()
        if tokens and tokens[-1].upper() in ['AND', 'OR']:
            return False, "Erro de sintaxe: A cláusula não pode terminar com 'AND' ou 'OR'."
        
        # CHECK 10: Verifica operadores lógicos duplos como "AND OR"
        if re.search(r'\b(AND\s+OR|OR\s+AND|AND\s+AND|OR\s+OR)\b', clause_str, re.IGNORECASE):
             return False, "Erro de sintaxe: Operadores lógicos combinados de forma inválida."
             
        # CHECK 11: Verifica operadores de comparação duplicados ou inválidos
        if re.search(r'(>>|<<|==|> >|< <)', clause_str):
            return False, "Erro de sintaxe: Operador de comparação duplicado ou inválido."

        # CHECK 12: Verifica palavras-chave usadas como valores
        if re.search(r'=\s*(SELECT|FROM|WHERE|JOIN)\b', clause_str, re.IGNORECASE):
            return False, "Erro de sintaxe: Palavra-chave SQL usada incorretamente como valor."

        return True, "Cláusula de condição válida."