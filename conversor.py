import re
import networkx as nx
import numpy as np

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

    def _calculate_improved_positions(self, G, root_id):
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
            
            for child in G.successors(node):
                queue.append((child, level + 1))
        
        level_nodes = {}
        for node, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        max_level = max(levels.values()) if levels else 0
        
        for level, nodes in level_nodes.items():
            y = max_level - level
            
            if len(nodes) == 1:
                x_positions = [0]
            else:
                width = max(4, len(nodes) * 2)
                x_positions = np.linspace(-width/2, width/2, len(nodes))
            
            for i, node in enumerate(nodes):
                pos[node] = (x_positions[i], y * 2)
        
        return pos

    def _add_nodes_to_graph(self, tree_node, G, pos_dict, node_colors, node_labels, node_shapes, level=0):
        current_id = self._get_unique_id()
        
        if isinstance(tree_node, str):
            G.add_node(current_id)
            node_colors[current_id] = 'table'
            node_labels[current_id] = tree_node
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            return current_id

        operator = tree_node[0]
        
        if operator == 'π':
            G.add_node(current_id)
            node_colors[current_id] = 'projection'
            node_labels[current_id] = f'π\n{tree_node[1]}'
            node_shapes[current_id] = 'circle'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, node_shapes, level + 1)
            G.add_edge(current_id, child_id)
        
        elif operator == 'σ':
            G.add_node(current_id)
            node_colors[current_id] = 'selection'
            node_labels[current_id] = f'σ\n{tree_node[1]}'
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, node_shapes, level + 1)
            G.add_edge(current_id, child_id)
            
        elif operator == 'ρ':
            G.add_node(current_id)
            node_colors[current_id] = 'rename'
            node_labels[current_id] = f'ρ\nalias: {tree_node[1]}'
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, node_shapes, level + 1)
            G.add_edge(current_id, child_id)

        elif operator == '⨝':
            G.add_node(current_id)
            node_colors[current_id] = 'join'
            node_labels[current_id] = f'JOIN\n{tree_node[1]}'
            node_shapes[current_id] = 'diamond'
            pos_dict[current_id] = level
            left_child_id = self._add_nodes_to_graph(tree_node[2], G, pos_dict, node_colors, node_labels, node_shapes, level + 1)
            right_child_id = self._add_nodes_to_graph(tree_node[3], G, pos_dict, node_colors, node_labels, node_shapes, level + 1)
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

    def validate_sql_syntax(self, sql_query):
        try:
            parsed_parts = self._parse_sql(sql_query)
            if not parsed_parts:
                return False, "Sintaxe SQL inválida"
            
            from_clause = parsed_parts.get('from_clause')
            base_table_info, joins = self._parse_from_clause(from_clause)
            
            if not base_table_info:
                return False, "Tabela base não identificada na cláusula FROM"
            
            return True, "Consulta SQL válida"
        except Exception as e:
            return False, f"Erro de validação: {str(e)}"


if __name__ == "__main__":
    converter = RelationalAlgebraConverter()
    
    sql_exemplo = "SELECT Nome, Email FROM Cliente WHERE Nome = 'João'"
    print(f"SQL: {sql_exemplo}")
    print(f"Álgebra Relacional: {converter.convert(sql_exemplo)}")