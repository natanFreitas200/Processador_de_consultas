import re
import uuid
import webbrowser
import os

class RelationalAlgebraConverter:

    def __init__(self):
        self.node_counter = 0

    def _get_unique_id(self):
        self.node_counter += 1
        return f"node{self.node_counter}"

    def _parse_from_clause(self, from_str):
        join_pattern = re.compile(
            r"INNER\s+JOIN\s+(?P<join_table>\w+)(?:\s+(?:AS\s+)?(?P<join_alias>\w+))?\s+ON\s+(?P<join_on>.*?)(?=\s+INNER\s+JOIN|$)",
            re.IGNORECASE | re.DOTALL
        )
        base_table_match = re.match(r"^(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>(?!INNER\b)\w+))?", from_str, re.IGNORECASE)
        if not base_table_match: return None, []
        base_table_info = base_table_match.groupdict()
        remaining_from_clause = from_str[base_table_match.end():]
        joins = [m.groupdict() for m in join_pattern.finditer(remaining_from_clause)]
        return base_table_info, joins

    def _parse_sql(self, query):
        query = query.strip().rstrip(';')
        pattern = re.compile(
            r"SELECT\s+(?P<columns>.*?)\s+"
            r"FROM\s+(?P<from_clause>.*?)"
            r"(?:\s+WHERE\s+(?P<where>.*?))?$",
            re.IGNORECASE | re.DOTALL
        )
        match = pattern.match(query)
        if not match: return None
        parts = match.groupdict()
        for key, value in parts.items():
            if value: parts[key] = ' '.join(value.strip().split())
        return parts
        
    def convert_to_tree(self, sql_query):
        parsed_parts = self._parse_sql(sql_query)
        if not parsed_parts: return "Erro: A sintaxe da consulta SQL é inválida."
        select_cols, from_clause, where_clause = parsed_parts.get('columns'), parsed_parts.get('from_clause'), parsed_parts.get('where')
        base_table_info, joins = self._parse_from_clause(from_clause)
        if not base_table_info: return "Erro: Cláusula FROM não encontrada."

        base_table_name, base_alias = base_table_info.get('table'), base_table_info.get('alias')
        tree = ('ρ', base_alias, base_table_name) if base_alias else base_table_name

        for join in joins:
            join_table_name, join_alias, join_on = join.get('join_table'), join.get('join_alias'), join.get('join_on')
            right_node = ('ρ', join_alias, join_table_name) if join_alias else join_table_name
            tree = ('⨝', join_on, tree, right_node)
        
        if where_clause:
            where_condition = where_clause.replace('AND', '∧').replace('and', '∧')
            tree = ('σ', where_condition, tree)

        if select_cols: tree = ('π', select_cols, tree)
        return tree

    def _tree_to_mermaid(self, tree_node, mermaid_lines):
        current_id = self._get_unique_id()
        
        if isinstance(tree_node, str):
            mermaid_lines.append(f'{current_id}["{tree_node}"]')
            mermaid_lines.append(f'classDef table fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000')
            mermaid_lines.append(f'class {current_id} table')
            return current_id

        operator = tree_node[0]
        
        if operator == 'π':
            label = f'π<br/>{tree_node[1]}'
            mermaid_lines.append(f'{current_id}["{label}"]')
            mermaid_lines.append(f'classDef projection fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000')
            mermaid_lines.append(f'class {current_id} projection')
            child_id = self._tree_to_mermaid(tree_node[2], mermaid_lines)
            mermaid_lines.append(f'{current_id} --> {child_id}')
        
        elif operator == 'σ':
            label = f'σ<br/>{tree_node[1]}'
            mermaid_lines.append(f'{current_id}["{label}"]')
            mermaid_lines.append(f'classDef selection fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000')
            mermaid_lines.append(f'class {current_id} selection')
            child_id = self._tree_to_mermaid(tree_node[2], mermaid_lines)
            mermaid_lines.append(f'{current_id} --> {child_id}')
            
        elif operator == 'ρ':
            label = f'ρ<br/>alias: {tree_node[1]}'
            mermaid_lines.append(f'{current_id}["{label}"]')
            mermaid_lines.append(f'classDef rename fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000')
            mermaid_lines.append(f'class {current_id} rename')
            child_id = self._tree_to_mermaid(tree_node[2], mermaid_lines)
            mermaid_lines.append(f'{current_id} --> {child_id}')

        elif operator == '⨝':
            label = f'⨝<br/>{tree_node[1]}'
            mermaid_lines.append(f'{current_id}{{{label}}}')
            mermaid_lines.append(f'classDef join fill:#ffebee,stroke:#c62828,stroke-width:3px,color:#000')
            mermaid_lines.append(f'class {current_id} join')
            left_child_id = self._tree_to_mermaid(tree_node[2], mermaid_lines)
            right_child_id = self._tree_to_mermaid(tree_node[3], mermaid_lines)
            mermaid_lines.append(f'{current_id} --> {left_child_id}')
            mermaid_lines.append(f'{current_id} --> {right_child_id}')

        return current_id
        
    def generate_html_graph(self, sql_query, output_filename='grafo_relacional.html'):
        print(f"\nConvertendo SQL para grafo HTML/Mermaid: '{sql_query}'")
        relational_tree = self.convert_to_tree(sql_query)

        if isinstance(relational_tree, str) and relational_tree.startswith("Erro"):
            print(relational_tree)
            return

        self.node_counter = 0
        mermaid_lines = []
        self._tree_to_mermaid(relational_tree, mermaid_lines)
        mermaid_syntax = "graph TD\n    " + "\n    ".join(mermaid_lines)
        
        html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grafo de Álgebra Relacional</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
            letter-spacing: 2px;
        }}
        .sql-query {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 30px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            overflow-x: auto;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        .graph-container {{
            padding: 30px;
            background: #fafafa;
            text-align: center;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid;
        }}
        .projection {{ background: #f3e5f5; border-color: #4a148c; }}
        .selection {{ background: #e8f5e8; border-color: #1b5e20; }}
        .join {{ background: #ffebee; border-color: #c62828; }}
        .rename {{ background: #fff3e0; border-color: #e65100; }}
        .table {{ background: #e1f5fe; border-color: #01579b; }}
        
        #mermaidDiv {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Álgebra Relacional</h1>
            <p>Representação visual da consulta SQL</p>
        </div>
        
        <div class="sql-query">
            <strong>Consulta SQL:</strong><br>
            {sql_query}
        </div>
        
        <div class="graph-container">
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color projection"></div>
                    <span>π - Projeção (SELECT)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color selection"></div>
                    <span>σ - Seleção (WHERE)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color join"></div>
                    <span>⨝ - Junção (JOIN)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color rename"></div>
                    <span>ρ - Renomeação (AS)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color table"></div>
                    <span>Tabela</span>
                </div>
            </div>
            
            <div id="mermaidDiv" class="mermaid">
                {mermaid_syntax}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                primaryColor: '#ffffff',
                primaryTextColor: '#000000',
                primaryBorderColor: '#333333',
                lineColor: '#333333',
                secondaryColor: '#f9f9f9',
                background: '#ffffff'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        full_path = os.path.abspath(output_filename)
        print(f"Grafo HTML gerado com sucesso! Arquivo salvo como: {full_path}")
        webbrowser.open(f"file://{full_path}")
    
    def convert(self, sql_query):
        
        print(f"\nConvertendo SQL para String: '{sql_query}'")
        parsed_parts = self._parse_sql(sql_query)

        if not parsed_parts:
            return "Erro: A sintaxe da consulta SQL é inválida ou não é suportada pelo conversor."

        select_cols = parsed_parts.get('columns')
        from_clause = parsed_parts.get('from_clause')
        where_clause = parsed_parts.get('where')

        base_table_info, joins = self._parse_from_clause(from_clause)

        if not base_table_info:
            return "Erro: Não foi possível identificar a tabela base na cláusula FROM."


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


if __name__ == "__main__":
    converter = RelationalAlgebraConverter()

    sql = ("SELECT c.Nome, p.Nome, ped.DataPedido "
           "FROM cliente AS c "
           "INNER JOIN pedido ped ON c.idCliente = ped.Cliente_idCliente "
           "INNER JOIN produto p ON ped.idProduto = p.idProduto "
           "WHERE ped.ValorTotal > 100")
    
    converter.generate_html_graph(sql)