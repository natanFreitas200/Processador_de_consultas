import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)


    def _parse_query(self, query):
        pattern = re.compile(
            r"SELECT\s+(?P<columns>.*?)\s+"
            r"FROM\s+(?P<base_table>.*?)"
            r"(?:\s+INNER JOIN\s+(?P<join_table>.*?)\s+ON\s+(?P<join_on>.*?))?"
            r"(?:\s+WHERE\s+(?P<where>.*))?",
            re.IGNORECASE | re.DOTALL
        )
    
        match = pattern.match(query.strip())

        if not match:
            print("Erro de Sintaxe: A consulta não segue a estrutura SELECT...FROM...[INNER JOIN...ON...] [WHERE...]")
            return None

        return match.groupdict()

    def validate_query(self, query):
        parsed = self._parse_query(query)
        if parsed is None:
            return False
        
        tables_query = [parsed['base_table']]
        if parsed.get('join_table'):
                tables_query.append(parsed["join_table"])
        
        for table in tables_query:
            if table not in self.schema:
                return False, f"Erro: A tabela '{table}' não existe no banco de dados."
        
        return True
