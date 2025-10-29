import re
import networkx as nx
import numpy as np
from optimizer import QueryOptimizer

class RelationalAlgebraConverter:
    """
    Conversor de consultas SQL para Álgebra Relacional.
    Suporta otimização através da classe QueryOptimizer.
    """
    
    def __init__(self):
        self.node_counter = 0
        self.optimizer = QueryOptimizer()
    
    def _get_unique_id(self):
        """Gera um ID único para cada nó do grafo."""
        self.node_counter += 1
        return f"node{self.node_counter}"
    
    def _parse_from_clause(self, from_str):
        """
        Analisa a cláusula FROM para extrair tabelas e JOINs.
        
        Args:
            from_str: String da cláusula FROM
            
        Returns:
            tuple: (base_table_info, joins_list)
        """
        # Pattern para detectar INNER JOINs
        join_pattern = re.compile(
            r"INNER\s+JOIN\s+(?P<join_table>\w+)(?:\s+(?:AS\s+)?(?P<join_alias>\w+))?\s+ON\s+(?P<join_on>.*?)(?=\s+INNER\s+JOIN|$)",
            re.IGNORECASE | re.DOTALL
        )
        
        # Extrair tabela base
        base_table_match = re.match(
            r"^(?P<table>\w+)(?:\s+(?:AS\s+)?(?P<alias>(?!INNER\b)\w+))?", 
            from_str, 
            re.IGNORECASE
        )
        
        if not base_table_match:
            return None, []
        
        base_table_info = base_table_match.groupdict()
        remaining_from_clause = from_str[base_table_match.end():]
        
        # Extrair todos os JOINs
        joins = [m.groupdict() for m in join_pattern.finditer(remaining_from_clause)]
        
        return base_table_info, joins
    
    def _parse_sql(self, query):
        """
        Faz o parsing da consulta SQL.
        
        Args:
            query: String contendo a consulta SQL
            
        Returns:
            dict: Dicionário com as partes da consulta (columns, from_clause, where)
        """
        query = query.strip().rstrip(';')
        
        # Pattern para capturar SELECT, FROM e WHERE
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
        
        # Normalizar espaços em branco
        for key, value in parts.items():
            if value:
                parts[key] = ' '.join(value.strip().split())
        
        return parts
    
    def convert_to_tree(self, sql_query, optimize=False):
        """
        Converte SQL para árvore de álgebra relacional.
        
        Args:
            sql_query: Consulta SQL
            optimize: Se True, aplica otimizações de heurísticas
        
        Returns:
            Árvore de álgebra relacional (tupla aninhada)
        """
        parsed_parts = self._parse_sql(sql_query)
        if not parsed_parts:
            return "Erro: A sintaxe da consulta SQL é inválida."
        
        select_cols = parsed_parts.get('columns')
        from_clause = parsed_parts.get('from_clause')
        where_clause = parsed_parts.get('where')
        
        # Parse da cláusula FROM
        base_table_info, joins = self._parse_from_clause(from_clause)
        if not base_table_info:
            return "Erro: Cláusula FROM não encontrada."
        
        base_table_name = base_table_info.get('table')
        base_alias = base_table_info.get('alias')
        
        # Construir árvore começando pela tabela base
        if base_alias:
            tree = ('ρ', base_alias, base_table_name)
        else:
            tree = base_table_name
        
        # Adicionar JOINs à árvore
        for join in joins:
            join_table_name = join.get('join_table')
            join_alias = join.get('join_alias')
            join_on = join.get('join_on')
            
            # Construir nó direito do JOIN
            if join_alias:
                right_node = ('ρ', join_alias, join_table_name)
            else:
                right_node = join_table_name
            
            # Adicionar operador de JOIN
            tree = ('⨝', join_on, tree, right_node)
        
        # Adicionar cláusula WHERE (seleção)
        if where_clause:
            where_condition = where_clause.replace('AND', '∧').replace('and', '∧')
            tree = ('σ', where_condition, tree)
        
        # Adicionar projeção (SELECT)
        if select_cols:
            tree = ('π', select_cols, tree)
        
        # Aplicar otimizações se solicitado
        if optimize:
            tree = self.optimizer.optimize_tree(tree)
        
        return tree
    
    def convert_to_optimized_tree(self, sql_query):
        """
        Retorna tanto a árvore não otimizada quanto a otimizada.
        
        Args:
            sql_query: Consulta SQL
            
        Returns:
            tuple: (unoptimized_tree, optimized_tree)
        """
        unoptimized = self.convert_to_tree(sql_query, optimize=False)
        optimized = self.convert_to_tree(sql_query, optimize=True)
        
        return unoptimized, optimized
    
    def _calculate_improved_positions(self, G, root_id):
        """
        Calcula posições dos nós no grafo usando layout hierárquico melhorado.
        
        Args:
            G: Grafo NetworkX
            root_id: ID do nó raiz
            
        Returns:
            dict: Dicionário com posições {node_id: (x, y)}
        """
        pos = {}
        levels = {}
        queue = [(root_id, 0)]
        visited = set()
        
        # BFS para determinar níveis
        while queue:
            node, level = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            levels[node] = level
            
            for child in G.successors(node):
                queue.append((child, level + 1))
        
        # Agrupar nós por nível
        level_nodes = {}
        for node, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        max_level = max(levels.values()) if levels else 0
        
        # Posicionar nós em cada nível
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
        """
        Adiciona nós recursivamente ao grafo a partir da árvore de álgebra relacional.
        
        Args:
            tree_node: Nó da árvore (tupla ou string)
            G: Grafo NetworkX
            pos_dict: Dicionário de posições
            node_colors: Dicionário de cores dos nós
            node_labels: Dicionário de rótulos dos nós
            node_shapes: Dicionário de formas dos nós
            level: Nível atual na hierarquia
            
        Returns:
            str: ID do nó atual
        """
        current_id = self._get_unique_id()
        
        # Caso base: nó folha (tabela)
        if isinstance(tree_node, str):
            G.add_node(current_id)
            node_colors[current_id] = 'table'
            node_labels[current_id] = tree_node
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            return current_id
        
        operator = tree_node[0]
        
        # Operador de Projeção (π)
        if operator == 'π':
            G.add_node(current_id)
            node_colors[current_id] = 'projection'
            node_labels[current_id] = f'π\n{tree_node[1]}'
            node_shapes[current_id] = 'circle'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(
                tree_node[2], G, pos_dict, node_colors, 
                node_labels, node_shapes, level + 1
            )
            G.add_edge(current_id, child_id)
        
        # Operador de Seleção (σ)
        elif operator == 'σ':
            G.add_node(current_id)
            node_colors[current_id] = 'selection'
            node_labels[current_id] = f'σ\n{tree_node[1]}'
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(
                tree_node[2], G, pos_dict, node_colors, 
                node_labels, node_shapes, level + 1
            )
            G.add_edge(current_id, child_id)
        
        # Operador de Renomeação (ρ)
        elif operator == 'ρ':
            G.add_node(current_id)
            node_colors[current_id] = 'rename'
            node_labels[current_id] = f'ρ\nalias: {tree_node[1]}'
            node_shapes[current_id] = 'rect'
            pos_dict[current_id] = level
            child_id = self._add_nodes_to_graph(
                tree_node[2], G, pos_dict, node_colors, 
                node_labels, node_shapes, level + 1
            )
            G.add_edge(current_id, child_id)
        
        # Operador de JOIN (⨝)
        elif operator == '⨝':
            G.add_node(current_id)
            node_colors[current_id] = 'join'
            node_labels[current_id] = f'JOIN\n{tree_node[1]}'
            node_shapes[current_id] = 'diamond'
            pos_dict[current_id] = level
            
            # Processar subárvores esquerda e direita
            left_child_id = self._add_nodes_to_graph(
                tree_node[2], G, pos_dict, node_colors, 
                node_labels, node_shapes, level + 1
            )
            right_child_id = self._add_nodes_to_graph(
                tree_node[3], G, pos_dict, node_colors, 
                node_labels, node_shapes, level + 1
            )
            
            G.add_edge(current_id, left_child_id)
            G.add_edge(current_id, right_child_id)
        
        return current_id
    
    def _calculate_hierarchical_positions(self, G, root_id):
        """
        Calcula posições hierárquicas alternativas para o grafo.
        
        Args:
            G: Grafo NetworkX
            root_id: ID do nó raiz
            
        Returns:
            dict: Dicionário com posições {node_id: (x, y)}
        """
        pos = {}
        levels = {}
        queue = [(root_id, 0)]
        visited = set()
        
        # BFS para determinar níveis
        while queue:
            node, level = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            levels[node] = level
            
            for successor in G.successors(node):
                if successor not in visited:
                    queue.append((successor, level + 1))
        
        # Agrupar nós por nível
        level_nodes = {}
        for node, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        # Posicionar nós
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
        """
        Converte SQL para representação em string de Álgebra Relacional.
        
        Args:
            sql_query: Consulta SQL
            
        Returns:
            str: Expressão de álgebra relacional em formato string
        """
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
        
        # Construir expressão começando pela tabela base
        if base_alias:
            relational_expr = f"ρ_{base_alias}({base_table_name})"
        else:
            relational_expr = base_table_name
        
        # Adicionar JOINs
        for join in joins:
            join_table_name = join.get('join_table')
            join_alias = join.get('join_alias')
            join_on = join.get('join_on')
            
            if join_alias:
                join_expr = f"ρ_{join_alias}({join_table_name})"
            else:
                join_expr = join_table_name
            
            relational_expr = f"({relational_expr} ⨝ ({join_on}) {join_expr})"
        
        # Adicionar WHERE
        if where_clause:
            where_condition = where_clause.replace('AND', '∧').replace('and', '∧')
            relational_expr = f"σ ({where_condition}) ({relational_expr})"
        
        # Adicionar SELECT
        if select_cols:
            relational_expr = f"π ({select_cols}) ({relational_expr})"
        
        return relational_expr
    
    def get_optimization_log(self):
        """
        Retorna o log de otimizações aplicadas pelo optimizer.
        
        Returns:
            str: Log formatado das otimizações
        """
        return self.optimizer.get_optimization_log()
    
    def validate_sql_syntax(self, sql_query):
        """
        Valida a sintaxe básica da consulta SQL.
        
        Args:
            sql_query: Consulta SQL
            
        Returns:
            tuple: (is_valid, message)
        """
        try:
            # Remover espaços extras e ponto e vírgula
            query_clean = ' '.join(sql_query.strip().rstrip(';').split())
            
            # 1. Verificar palavras-chave duplicadas
            if re.search(r'\b(SELECT\s+SELECT|FROM\s+FROM|WHERE\s+WHERE|ON\s+ON|JOIN\s+JOIN)\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: Palavra-chave duplicada detectada"
            
            # 2. Verificar INNER JOIN duplicado
            if re.search(r'\bINNER\s+JOIN\s+INNER\s+JOIN\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: 'INNER JOIN INNER JOIN' detectado"
            
            # 3. Verificar operadores duplicados ou inválidos
            if re.search(r'(>>|<<|==|>>|<<|> >|< <|\|\|)', query_clean):
                return False, "Sintaxe inválida: Operador duplicado ou inválido detectado (>>, <<, ==, > >, etc.)"
            
            # 4. Verificar operadores lógicos duplicados ou inválidos
            if re.search(r'\b(AND\s+OR|OR\s+AND|AND\s+AND|OR\s+OR)\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: Operadores lógicos inválidos (AND OR, OR AND, AND AND, OR OR)"
            
            # 5. Verificar WHERE usado como nome de tabela
            if re.search(r'\bJOIN\s+WHERE\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: 'WHERE' não pode ser usado como nome de tabela"
            
            # 6. Verificar SELECT usado como valor
            if re.search(r'=\s*SELECT\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: 'SELECT' usado incorretamente como valor"
            
            # 7. Verificar ON usado incorretamente
            if re.search(r'\bFROM\s+\w+\s+ON\b', query_clean, re.IGNORECASE) and not re.search(r'\bJOIN\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: 'ON' usado sem JOIN"
            
            # 8. Verificar WHERE dentro do FROM/JOIN incorretamente
            if re.search(r'\bFROM\s+.*?\s+WHERE\s+.*?\s+ON\b', query_clean, re.IGNORECASE):
                return False, "Sintaxe inválida: 'WHERE' não pode aparecer entre FROM e ON"
            
            # 9. Verificar parênteses incorretos na lista de colunas
            # Procura por colunas entre parênteses fora de contexto de função
            columns_match = re.match(r'SELECT\s+(.*?)\s+FROM', query_clean, re.IGNORECASE)
            if columns_match:
                columns_part = columns_match.group(1)
                # Detecta padrões como (Nome) ou Nome, (Email) que não são chamadas de função
                if re.search(r'(?<!\w)\(\s*\w+\s*\)(?!\s*\()', columns_part):
                    # Verifica se não é uma função válida (sem nome antes do parêntese)
                    if not re.search(r'\w+\s*\(\s*\w+\s*\)', columns_part):
                        return False, "Sintaxe inválida: Parênteses incorretos na lista de colunas"
            
            # 10. Parse básico da consulta
            parsed_parts = self._parse_sql(query_clean)
            if not parsed_parts:
                return False, "Sintaxe SQL inválida: Estrutura básica SELECT...FROM não reconhecida"
            
            # 11. Validar cláusula FROM
            from_clause = parsed_parts.get('from_clause')
            if not from_clause or not from_clause.strip():
                return False, "Sintaxe inválida: Cláusula FROM vazia ou ausente"
            
            base_table_info, joins = self._parse_from_clause(from_clause)
            
            if not base_table_info:
                return False, "Sintaxe inválida: Tabela base não identificada na cláusula FROM"
            
            # 12. Validar que palavras-chave SQL não são usadas como identificadores
            reserved_as_identifiers = ['SELECT', 'FROM', 'WHERE', 'ON', 'JOIN', 'INNER']
            columns = parsed_parts.get('columns', '')
            for keyword in reserved_as_identifiers:
                if re.search(r'\b' + keyword + r'\b(?!\s*(=|>|<|>=|<=|<>|JOIN|FROM))', columns, re.IGNORECASE):
                    return False, f"Sintaxe inválida: Palavra-chave reservada '{keyword}' usada incorretamente"
            
            return True, "Consulta SQL válida"
        except Exception as e:
            return False, f"Erro de validação: {str(e)}"


# Código de teste opcional
if __name__ == "__main__":
    converter = RelationalAlgebraConverter()
    
    # Exemplos de consultas SQL
    sql_exemplos = [
        "SELECT Nome, Email FROM Cliente WHERE Nome = 'João'",
        "SELECT c.nome, p.valor FROM cliente c INNER JOIN pedidos p ON c.id = p.cliente_id WHERE p.valor > 500",
        "SELECT * FROM empregado WHERE salario > 5000"
    ]
    
    print("="*80)
    print("TESTE DO CONVERSOR COM OTIMIZAÇÃO")
    print("="*80)
    
    for sql in sql_exemplos:
        print(f"\n\nSQL: {sql}")
        print("-"*80)
        
        # Converter para string
        algebra_str = converter.convert(sql)
        print(f"\nÁlgebra Relacional (String):\n{algebra_str}")
        
        # Converter para árvores
        unopt_tree, opt_tree = converter.convert_to_optimized_tree(sql)
        print(f"\nÁrvore NÃO Otimizada:\n{unopt_tree}")
        print(f"\nÁrvore OTIMIZADA:\n{opt_tree}")
        
        # Mostrar log de otimizações
        print(f"\n{converter.get_optimization_log()}")
        print("="*80)
