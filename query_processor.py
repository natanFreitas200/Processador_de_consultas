import re
from db import get_db_schema, db_config

class QueryProcessor:
    def __init__(self):
        self.schema = get_db_schema(db_config)


    def _parse_query(self, query):
        query = query.strip().rstrip(';')  # remove ; no final
    
        # Padrão mais flexível que permite pontos em nomes de colunas e aspas em valores
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
        
        print(f" Query válida!")
        return True
