import re
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
from matplotlib.patches import FancyBboxPatch

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

    def generate_image_graph(self, sql_query, output_filename='grafo_relacional.png'):
        print(f"\nConvertendo SQL para imagem: '{sql_query}'")
        relational_tree = self.convert_to_tree(sql_query)

        if isinstance(relational_tree, str) and relational_tree.startswith("Erro"):
            print(relational_tree)
            return

        G = nx.DiGraph()
        self.node_counter = 0
        pos_dict = {}
        node_colors = {}
        node_labels = {}
        
        root_id = self._add_nodes_to_graph(relational_tree, G, pos_dict, node_colors, node_labels)
        
        pos = self._calculate_hierarchical_positions(G, root_id)
        
        plt.figure(figsize=(14, 10))
        plt.clf()
        
        color_map = {
            'projection': '#f3e5f5',
            'selection': '#e8f5e8', 
            'join': '#ffebee',
            'rename': '#fff3e0',
            'table': '#e1f5fe'
        }
        
        for node_type, color in color_map.items():
            nodes_of_type = [node for node, attr in node_colors.items() if attr == node_type]
            if nodes_of_type:
                nx.draw_networkx_nodes(G, pos, nodelist=nodes_of_type, 
                                     node_color=color, node_size=3000,
                                     edgecolors='black', linewidths=2)
        
        nx.draw_networkx_edges(G, pos, edge_color='#333333', arrows=True, 
                              arrowsize=20, arrowstyle='->', width=2)
        
        for node, (x, y) in pos.items():
            label = node_labels[node]
            plt.text(x, y, label, ha='center', va='center', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
                    wrap=True)
        
        plt.title(f'Álgebra Relacional\nConsulta: {sql_query}', 
                 fontsize=14, fontweight='bold', pad=20)
        
        legend_elements = [
            mpatches.Patch(color='#f3e5f5', label='π - Projeção (SELECT)'),
            mpatches.Patch(color='#e8f5e8', label='σ - Seleção (WHERE)'),
            mpatches.Patch(color='#ffebee', label='JOIN - Junção (JOIN)'),
            mpatches.Patch(color='#fff3e0', label='ρ - Renomeação (AS)'),
            mpatches.Patch(color='#e1f5fe', label='Tabela')
        ]
        
        plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.axis('off')
        
        plt.tight_layout()
        
        plt.savefig(output_filename, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        full_path = os.path.abspath(output_filename)
        print(f"Grafo em imagem gerado com sucesso! Arquivo salvo como: {full_path}")
        
        try:
            os.startfile(full_path)
        except OSError:
            print("Imagem salva! Abra manualmente o arquivo para visualizar.")
        
        plt.close()
    
    def _add_nodes_to_graph(self, tree_node, G, pos_dict, node_colors, node_labels, level=0):
        current_id = self._get_unique_id()
        
        if isinstance(tree_node, str):
            G.add_node(current_id)
            node_colors[current_id] = 'table'
            node_labels[current_id] = tree_node
            pos_dict[current_id] = level
            return current_id

        operator = tree_node[0]
        
        if operator == 'π':
            G.add_node(current_id)
            node_colors[current_id] = 'projection'
            node_labels[current_id] = f'π\n{tree_node[1]}'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, level + 1)
            G.add_edge(current_id, child_id)
        
        elif operator == 'σ':
            G.add_node(current_id)
            node_colors[current_id] = 'selection'
            node_labels[current_id] = f'σ\n{tree_node[1]}'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, level + 1)
            G.add_edge(current_id, child_id)
            
        elif operator == 'ρ':
            G.add_node(current_id)
            node_colors[current_id] = 'rename'
            node_labels[current_id] = f'ρ\nalias: {tree_node[1]}'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, level + 1)
            G.add_edge(current_id, child_id)

        elif operator == '⨝':
            G.add_node(current_id)
            node_colors[current_id] = 'join'
            node_labels[current_id] = f'JOIN\n{tree_node[1]}'
            pos_dict[current_id] = level
            left_child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, level + 1)
            right_child_id = self._add_nodes_to_graph(tree_node[3], G, pos_dict, node_colors, node_labels, level + 1)
            G.add_edge(current_id, left_child_id)
            G.add_edge(current_id, right_child_id)

        return current_id
    
    def _calculate_hierarchical_positions(self, G, root_id):
        pos = {}
        levels = {}
        
        queue = [(root_id, 0)]
        visited = set()
        
        while queue:
            node, level = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            levels[node] = level
            
            for successor in G.successors(node):
                if successor not in visited:
                    queue.append((successor, level + 1))
        
        level_nodes = {}
        for node, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        for level, nodes in level_nodes.items():
            y = -level * 2
            if len(nodes) == 1:
                pos[nodes[0]] = (0, y)
            else:
                x_spacing = 4
                total_width = (len(nodes) - 1) * x_spacing
                start_x = -total_width / 2
                for i, node in enumerate(nodes):
                    pos[node] = (start_x + i * x_spacing, y)
        
        return pos
    
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

    print("=" * 60)
    print("EXEMPLO 1: Consulta simples com SELECT e WHERE")
    print("=" * 60)
    sql1 = "SELECT nome, idade FROM funcionarios WHERE salario > 5000"
    print("SQL:", sql1)
    print("Álgebra Relacional:", converter.convert(sql1))
    converter.generate_image_graph(sql1, 'exemplo1_simples.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 2: Consulta com INNER JOIN")
    print("=" * 60)
    sql2 = ("SELECT f.nome, d.nome_departamento "
            "FROM funcionarios f "
            "INNER JOIN departamentos d ON f.dept_id = d.id")
    print("SQL:", sql2)
    print("Álgebra Relacional:", converter.convert(sql2))
    converter.generate_image_graph(sql2, 'exemplo2_join.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 3: Consulta com múltiplos JOINs")
    print("=" * 60)
    sql3 = ("SELECT c.Nome, p.Nome, ped.DataPedido "
            "FROM cliente AS c "
            "INNER JOIN pedido ped ON c.idCliente = ped.Cliente_idCliente "
            "INNER JOIN produto p ON ped.idProduto = p.idProduto "
            "WHERE ped.ValorTotal > 100")
    print("SQL:", sql3)
    print("Álgebra Relacional:", converter.convert(sql3))
    converter.generate_image_graph(sql3, 'exemplo3_multiplos_joins.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 4: Consulta com WHERE complexo")
    print("=" * 60)
    sql4 = ("SELECT e.nome, e.cargo, e.salario "
            "FROM empregados AS e "
            "WHERE e.salario > 3000 AND e.cargo = 'Analista'")
    print("SQL:", sql4)
    print("Álgebra Relacional:", converter.convert(sql4))
    converter.generate_image_graph(sql4, 'exemplo4_where_complexo.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 5: Consulta com alias nas tabelas")
    print("=" * 60)
    sql5 = ("SELECT u.email, p.titulo "
            "FROM usuarios AS u "
            "INNER JOIN posts AS p ON u.id = p.user_id "
            "WHERE p.status = 'publicado'")
    print("SQL:", sql5)
    print("Álgebra Relacional:", converter.convert(sql5))
    converter.generate_image_graph(sql5, 'exemplo5_alias.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 6: Consulta apenas com SELECT")
    print("=" * 60)
    sql6 = "SELECT nome, telefone, email FROM clientes"
    print("SQL:", sql6)
    print("Álgebra Relacional:", converter.convert(sql6))
    converter.generate_image_graph(sql6, 'exemplo6_apenas_select.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 7: Consulta acadêmica - Estudantes, Cursos e Matrículas")
    print("=" * 60)
    sql7 = ("SELECT est.nome, cur.nome_curso, mat.data_matricula "
            "FROM estudantes est "
            "INNER JOIN matriculas mat ON est.id = mat.estudante_id "
            "INNER JOIN cursos cur ON mat.curso_id = cur.id "
            "WHERE cur.ativo = 1")
    print("SQL:", sql7)
    print("Álgebra Relacional:", converter.convert(sql7))
    converter.generate_image_graph(sql7, 'exemplo7_academico.png')

    print("\n" + "=" * 60)
    print("EXEMPLO 8: Sistema de vendas")
    print("=" * 60)
    sql8 = ("SELECT v.data_venda, prod.nome, v.quantidade "
            "FROM vendas v "
            "INNER JOIN produtos prod ON v.produto_id = prod.id "
            "WHERE v.valor_total > 500")
    print("SQL:", sql8)
    print("Álgebra Relacional:", converter.convert(sql8))
    converter.generate_image_graph(sql8, 'exemplo8_vendas.png')

    print("\n" + "=" * 60)
    print("TODOS OS EXEMPLOS FORAM PROCESSADOS!")
    print("Arquivos PNG gerados:")
    print("- exemplo1_simples.png")
    print("- exemplo2_join.png") 
    print("- exemplo3_multiplos_joins.png")
    print("- exemplo4_where_complexo.png")
    print("- exemplo5_alias.png")
    print("- exemplo6_apenas_select.png")
    print("- exemplo7_academico.png")
    print("- exemplo8_vendas.png")
    print("=" * 60)