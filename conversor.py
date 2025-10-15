import re

class RelationalAlgebraConverter:

    def _parse_sql(self, query):
        query = query.strip().rstrip(';')

        pattern = re.compile(
            r"SELECT\s+(?P<columns>.*?)\s+"
            r"FROM\s+(?P<base_table>\w+)"
            r"(?:\s+INNER\s+JOIN\s+(?P<join_table>\w+)\s+ON\s+(?P<join_on>.*?))?"
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
        print(f"\nConvertendo SQL: '{sql_query}'")
        parsed_parts = self._parse_sql(sql_query)

        if not parsed_parts:
            return "Erro: A sintaxe da consulta SQL é inválida ou não é suportada pelo conversor."

        select_cols = parsed_parts.get('columns')
        from_table = parsed_parts.get('base_table')
        join_table = parsed_parts.get('join_table')
        join_on = parsed_parts.get('join_on')
        where_clause = parsed_parts.get('where')

        relational_expr = ""

        # A cláusula FROM e INNER JOIN se traduz em uma junção (⨝)
        if join_table and join_on:
            relational_expr = f"{from_table} ⨝ ({join_on}) {join_table}"
        else:
             relational_expr = from_table

        # A cláusula WHERE se traduz em uma operação de Seleção (σ)
        if where_clause:
            # Substitui 'AND' por '∧' para uma notação mais formal (opcional)
            where_condition = where_clause.replace('AND', '∧').replace('and', '∧')
            # A seleção é aplicada sobre a expressão construída anteriormente
            relational_expr = f"σ ({where_condition}) ({relational_expr})"

        # A cláusula SELECT se traduz em uma operação de Projeção (π)
        if select_cols:
            # A projeção define quais colunas serão retornadas
            relational_expr = f"π ({select_cols}) ({relational_expr})"

        return relational_expr