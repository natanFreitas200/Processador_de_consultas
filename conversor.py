import re

class RelationalAlgebraConverter:
    """
    Converte consultas SQL, incluindo com múltiplos INNER JOINs e aliases de tabela, 
    para sua representação em Álgebra Relacional.
    """

    def _parse_from_clause(self, from_str):
        """
        Analisa o conteúdo da cláusula FROM para extrair a tabela base e uma lista de junções.
        """
        join_pattern = re.compile(
            r"INNER\s+JOIN\s+(?P<join_table>\w+)(?:\s+(?:AS\s+)?(?P<join_alias>\w+))?\s+ON\s+(?P<join_on>.*?)(?=\s+INNER\s+JOIN|$)",
            re.IGNORECASE | re.DOTALL
        )

        base_table_match = re.match(r"^(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>(?!INNER\b)\w+))?", from_str, re.IGNORECASE)

        if not base_table_match:
            return None, []
            
        base_table_info = base_table_match.groupdict()

        remaining_from_clause = from_str[base_table_match.end():]
        joins = [m.groupdict() for m in join_pattern.finditer(remaining_from_clause)]
        
        return base_table_info, joins

    def _parse_sql(self, query):
        """
        Primeira etapa de análise: divide a query em blocos SELECT, FROM e WHERE.
        """
        query = query.strip().rstrip(';')

        pattern = re.compile(
            r"SELECT\s+(?P<columns>.*?)\s+"
            r"FROM\s+(?P<from_clause>.*?)"
            r"(?:\s+WHERE\s+(?P<where>.*?))?$",
            re.IGNORECASE | re.DOTALL
        )

        match = pattern.match(query)
        if not match:
            return None

        parts = match.groupdict()
        
        for key, value in parts.items():
            if value:
                parts[key] = ' '.join(value.strip().split())
        return parts

    def convert(self, sql_query):
        """
        Orquestra a conversão, construindo a expressão de álgebra relacional de forma iterativa.
        """
        print(f"\nConvertendo SQL: '{sql_query}'")
        parsed_parts = self._parse_sql(sql_query)

        if not parsed_parts:
            return "Erro: A sintaxe da consulta SQL é inválida ou não é suportada pelo conversor."

        select_cols = parsed_parts.get('columns')
        from_clause = parsed_parts.get('from_clause')
        where_clause = parsed_parts.get('where')

        base_table_info, joins = self._parse_from_clause(from_clause)

        if not base_table_info:
            return "Erro: Não foi possível identificar a tabela base na cláusula FROM."

        base_table_name = base_table_info.get('table')
        base_alias = base_table_info.get('alias')
        relational_expr = f"ρ_{base_alias}({base_table_name})" if base_alias else base_table_name
        
        for join in joins:
            join_table_name = join.get('join_table')
            join_alias = join.get('join_alias')
            join_on = join.get('join_on')
            
            join_expr = f"ρ_{join_alias}({join_table_name})" if join_alias else join_table_name
            
            relational_expr = f"({relational_expr} ⨝ ({join_on}) {join_expr})"

        if where_clause:
            where_condition = where_clause.replace('AND', '∧').replace('and', '∧')
            relational_expr = f"σ ({where_condition}) ({relational_expr})"

        if select_cols:
            relational_expr = f"π ({select_cols}) ({relational_expr})"

        return relational_expr
