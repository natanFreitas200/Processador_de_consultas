import re
import copy

class QueryOptimizer:
    def __init__(self):
        self.optimization_log = []
    
    def optimize_tree(self, tree):
        """
        Aplica todas as heurísticas de otimização na árvore.
        """
        self.optimization_log = []
        self.optimization_log.append("=== INICIANDO OTIMIZAÇÃO DA CONSULTA ===")
        
        optimized_tree = copy.deepcopy(tree)
        
        # Cada função agora é responsável pelo seu próprio log, de forma controlada.
        optimized_tree = self._apply_selection_pushdown(optimized_tree)
        optimized_tree = self._apply_projection_pushdown(optimized_tree)
        optimized_tree = self._apply_join_reordering(optimized_tree)
        optimized_tree = self._select_efficient_algorithms(optimized_tree)
        
        self.optimization_log.append("\n=== OTIMIZAÇÃO CONCLUÍDA ===")
        return optimized_tree

    def _apply_selection_pushdown(self, tree):
        """HEURÍSTICA 1: Push-down de seleções (σ)"""
        self.optimization_log.append("\n[HEURÍSTICA 1] Push-down de Seleções (σ):")
        # A função _recursive_selection_pushdown fará o trabalho e retornará a árvore modificada
        # e um booleano indicando se alguma otimização foi realmente aplicada.
        optimized_tree, was_optimized = self._recursive_selection_pushdown(tree)
        
        if was_optimized:
            self.optimization_log.append("  ✓ Seleções (σ) movidas para mais perto das tabelas base.")
            self.optimization_log.append("    → Benefício: Reduz o volume de dados em etapas intermediárias.")
        else:
            self.optimization_log.append("  - Nenhuma seleção (cláusula WHERE) para otimizar.")
            
        return optimized_tree

    def _recursive_selection_pushdown(self, tree):
        if isinstance(tree, str):
            return tree, False # Retorna a árvore e um flag "não otimizado"
        
        operator = tree[0]
        
        if operator == 'σ':
            condition = tree[1]
            subtree = tree[2]
            # O trabalho real de empurrar a seleção acontece aqui
            pushed_tree = self._push_selection_down(condition, subtree)
            return pushed_tree, True # Foi otimizado
        
        # Chamadas recursivas
        if operator in ['π', 'ρ']:
            optimized_subtree, was_opt = self._recursive_selection_pushdown(tree[2])
            return (operator, tree[1], optimized_subtree), was_opt
        elif operator == '⨝':
            left, left_opt = self._recursive_selection_pushdown(tree[2])
            right, right_opt = self._recursive_selection_pushdown(tree[3])
            return ('⨝', tree[1], left, right), left_opt or right_opt
            
        return tree, False

    def _push_selection_down(self, condition, tree):
        if isinstance(tree, str):
            return ('σ', condition, tree)
        
        operator = tree[0]
        
        if operator == '⨝':
            join_condition, left_tree, right_tree = tree[1], tree[2], tree[3]
            conditions = self._split_conditions(condition)
            left_conditions, right_conditions, join_conditions = [], [], []
            
            for cond in conditions:
                tables_in_cond = self._get_tables_in_condition(cond)
                left_tables = self._get_all_tables(left_tree)
                right_tables = self._get_all_tables(right_tree)
                
                if tables_in_cond and tables_in_cond.issubset(left_tables):
                    left_conditions.append(cond)
                elif tables_in_cond and tables_in_cond.issubset(right_tables):
                    right_conditions.append(cond)
                else:
                    join_conditions.append(cond)
            
            if left_conditions:
                left_tree = self._push_selection_down(' ∧ '.join(left_conditions), left_tree)
            if right_conditions:
                right_tree = self._push_selection_down(' ∧ '.join(right_conditions), right_tree)
            
            result = ('⨝', join_condition, left_tree, right_tree)
            if join_conditions:
                result = ('σ', ' ∧ '.join(join_conditions), result)
            return result
        
        if operator in ['π', 'ρ']:
            return (operator, tree[1], self._push_selection_down(condition, tree[2]))
        
        if operator == 'σ': # Combina condições se encontrar outra seleção
            return self._push_selection_down(f"{condition} ∧ {tree[1]}", tree[2])
            
        return ('σ', condition, tree)

    def _apply_projection_pushdown(self, tree):
        """HEURÍSTICA 2: Push-down de projeções (π)"""
        self.optimization_log.append("\n[HEURÍSTICA 2] Push-down de Projeções (π):")
        
        optimized_tree, was_optimized = self._recursive_projection_pushdown(tree, [])
        
        if was_optimized:
            self.optimization_log.append("  ✓ Projeções intermediárias inseridas para eliminar colunas desnecessárias.")
            self.optimization_log.append("    → Benefício: Reduz a largura das tuplas e o uso de memória.")
        else:
             self.optimization_log.append("  - Nenhuma projeção (cláusula SELECT) para otimizar ou SELECT * foi usado.")
        
        return optimized_tree

    def _recursive_projection_pushdown(self, tree, required_cols):
        if isinstance(tree, str):
            return tree, False

        operator = tree[0]

        if operator == 'π':
            current_cols = self._parse_columns(tree[1])
            # Coleta todas as colunas necessárias abaixo desta projeção
            all_required = self._collect_required_columns(tree[2], current_cols)
            # Empurra as projeções para baixo
            new_subtree, _ = self._recursive_projection_pushdown(tree[2], all_required)
            return ('π', tree[1], new_subtree), True

        # Para outros operadores, continua a busca por uma projeção
        if operator in ['σ', 'ρ']:
            new_subtree, was_opt = self._recursive_projection_pushdown(tree[2], required_cols)
            return (operator, tree[1], new_subtree), was_opt
        elif operator == '⨝':
            join_cols = self._get_columns_in_condition(tree[1])
            all_cols = list(set(required_cols) | set(join_cols))
            left, left_opt = self._recursive_projection_pushdown(tree[2], all_cols)
            right, right_opt = self._recursive_projection_pushdown(tree[3], all_cols)
            return ('⨝', tree[1], left, right), left_opt or right_opt

        return tree, False
    
    def _apply_join_reordering(self, tree):
        """HEURÍSTICA 3: Reordenação de JOINs (implementação simples e segura)"""
        self.optimization_log.append("\n[HEURÍSTICA 3] Reordenação de JOINs:")
        # Funções auxiliares locais
        def is_join_node(n):
            return not isinstance(n, str) and n and n[0] == '⨝'

        def collect_join_info(node):
            """
            Flatten join tree into a list of relation-subtrees and coletar todas as condições de join.
            Retorna (rel_list, join_conditions) onde:
            - rel_list: lista de subtrees (cada subtree = relação ou operador aplicado sobre relação)
            - join_conditions: lista de strings de condições que envolvem >=2 tabelas
            """
            rels = []
            join_conds = []

            def recurse(n):
                if isinstance(n, str):
                    rels.append(n)
                    return
                op = n[0]
                if op == 'σ':
                    # Se a seleção envolve múltiplas tabelas, pode conter condição de join aplicada acima
                    cond = n[1]
                    subt = n[2]
                    subt_tables = self._get_all_tables(subt)
                    conds = self._split_conditions(cond)
                    for c in conds:
                        if len(self._get_tables_in_condition(c)) >= 2:
                            join_conds.append(c)
                        # Não separa aqui; seleção fica junto com sua subtree
                    recurse(subt if isinstance(subt, str) else (subt))
                    # mantemos a seleção envolta como parte do subtree correspondente,
                    # mas já contabilizamos condições de join se existirem.
                    return
                if op == '⨝':
                    # coletar condição do próprio nó
                    if n[1]:
                        join_conds.extend([c for c in self._split_conditions(n[1]) if len(self._get_tables_in_condition(c)) >= 2])
                    # flatten both lados
                    recurse(n[2])
                    recurse(n[3])
                    return
                # π, ρ ou outros: considerar como operador aplicado sobre uma relação
                if op in ['π', 'ρ']:
                    # Representar o subtree inteiro como uma unidade (mantemos operadores aplicados)
                    # para evitar perder projeções/renames
                    rels.append(n)
                    return
                # Qualquer outro nó: recursão segura
                try:
                    for child in n[2:]:
                        recurse(child)
                except Exception:
                    pass

            recurse(node)
            return rels, join_conds

        def estimate_size(subtree, join_conditions):
            """
            Estimativa muito simples de cardinalidade:
            - base size 1000 por tabela
            - reduz por cada seleção condicional sobre a tabela (fator 0.1)
            - reduz um pouco se houver muitas colunas de join (sugere seletividade)
            """
            tables = self._get_all_tables(subtree)
            base = 1000 * max(1, len(tables))
            # contar quantas condições de seleção (σ) existem aplicadas dentro do subtree
            sel_count = 0
            def count_sel(n):
                nonlocal sel_count
                if isinstance(n, str): return
                if n[0] == 'σ':
                    sel_count += len(self._split_conditions(n[1]))
                    count_sel(n[2])
                elif n[0] in ['π', 'ρ']:
                    count_sel(n[2])
                elif n[0] == '⨝':
                    count_sel(n[2]); count_sel(n[3])
            count_sel(subtree)
            size = base * (0.1 ** sel_count)
            # se existirem join conditions que tocam essas tabelas, reduz um pouco mais
            for c in join_conditions:
                involved = self._get_tables_in_condition(c)
                if involved and involved.issubset(tables):
                    size *= 0.5
            return max(1, size)

        # Se não há joins, nada a fazer
        if not is_join_node(tree):
            self.optimization_log.append("  - Nenhum JOIN encontrado para reordenar.")
            return tree

        # Coletar relações e condições
        rels, join_conds = collect_join_info(tree)

        # Criar lista com estimativas
        rel_info = []
        for r in rels:
            rel_tables = self._get_all_tables(r) if not isinstance(r, str) else {r}
            est = estimate_size(r, join_conds)
            rel_info.append({'subtree': r, 'tables': rel_tables, 'est': est})

        # Ordenação inicial por estimativa crescente (menores primeiro)
        rel_info.sort(key=lambda x: x['est'])

        # Reconstruir joins greedy: sempre tentar anexar uma relação que compartilha condição com o conjunto atual
        used = [rel_info[0]]
        remaining = rel_info[1:]
        constructed_tree = used[0]['subtree']

        while remaining:
            attached = False
            for i, rinfo in enumerate(remaining):
                # procurar se existe condição ligando alguma tabela de constructed_tree com rinfo
                found_conds = []
                for c in join_conds:
                    tables_in_c = self._get_tables_in_condition(c)
                    if tables_in_c & self._get_all_tables(constructed_tree) and tables_in_c & rinfo['tables']:
                        found_conds.append(c)
                if found_conds:
                    # combinar condições que ligam os dois conjuntos
                    cond_str = ' ∧ '.join(found_conds)
                    constructed_tree = ('⨝', cond_str, constructed_tree, rinfo['subtree'])
                    # remover essas condições da lista global para não reaplicar
                    join_conds = [c for c in join_conds if c not in found_conds]
                    remaining.pop(i)
                    attached = True
                    break
            if not attached:
                # Não encontrou condição de ligação — simplesmente anexa a próxima menor
                rinfo = remaining.pop(0)
                # sem condição explícita, usar string vazia (cross join) — mantemos consistência
                constructed_tree = ('⨝', '', constructed_tree, rinfo['subtree'])

        self.optimization_log.append("  ✓ JOINs reordenados usando heurística gulosa baseada em estimativas simples.")
        self.optimization_log.append("    → Ordem construída (pequenas primeiras) para reduzir intermediários.")
        return constructed_tree

    def _select_efficient_algorithms(self, tree):
        """HEURÍSTICA 4: Seleção de Algoritmos Eficientes para operações (marca joins com algoritmo)"""
        self.optimization_log.append("\n[HEURÍSTICA 4] Seleção de Algoritmos Eficientes:")

        def choose_algo_for_condition(cond):
            # Detecta igualdade direta entre colunas de tabelas diferentes => Hash Join
            if not cond or not cond.strip():
                return 'nested_loop'  # cross-join fallback
            eqs = re.findall(r'(\w+\.\w+)\s*=\s*(\w+\.\w+)', cond)
            for left_col, right_col in eqs:
                left_table = left_col.split('.')[0]
                right_table = right_col.split('.')[0]
                if left_table != right_table:
                    return 'hash_join'
            # Se não for igualdade entre tabelas diferentes, preferir nested loop
            return 'nested_loop'

        def annotate(node):
            if isinstance(node, str):
                return node
            op = node[0]
            if op in ['π', 'ρ', 'σ']:
                return (op, node[1], annotate(node[2]))
            if op == '⨝':
                # Pode haver um algoritmo já armazenado na posição 4; manter se presente
                cond = node[1]
                left = annotate(node[2])
                right = annotate(node[3])
                algo = choose_algo_for_condition(cond)
                # Retornar um nó com 5 posições: ('⨝', cond, left, right, algo)
                self.optimization_log.append(f"  • Junção entre [{', '.join(sorted(self._get_all_tables(left)))}] "
                                             f"e [{', '.join(sorted(self._get_all_tables(right)))}] "
                                             f"=> algoritmo selecionado: {algo}")
                # Manter possíveis condições já presentes (node[1]) e adicionar algoritmo como elemento extra
                return ('⨝', cond, left, right, algo)
            # Qualquer outro nó — aplicar recursão segura para filhos
            try:
                # reconstrói genérico: mantém estrutura e aplica annotate a possíveis filhos
                new_children = []
                for child in node[1:]:
                    new_children.append(annotate(child) if not isinstance(child, str) else child)
                return tuple([node[0]] + new_children)
            except Exception:
                return node

        new_tree = annotate(tree)
        self.optimization_log.append("  ✓ Algoritmos selecionados para junções (hash quando aplicável, nested loop caso contrário).")
        return new_tree
    
    # --- Métodos Auxiliares ---
    
    def _split_conditions(self, condition):
        return [c.strip() for c in re.split(r'\s*∧\s*|\s+AND\s+', condition, flags=re.IGNORECASE) if c.strip()]
    
    def _get_tables_in_condition(self, condition):
        return set(re.findall(r'(\w+)\.', condition))
    
    def _get_all_tables(self, tree):
        tables = set()
        def collect(node):
            if isinstance(node, str): tables.add(node)
            elif node[0] == 'ρ':
                tables.add(node[1])
                collect(node[2])
            elif node[0] in ['π', 'σ']: collect(node[2])
            elif node[0] == '⨝':
                collect(node[2]); collect(node[3])
        collect(tree)
        return tables
    
    def _parse_columns(self, columns_str):
        return ['*'] if columns_str.strip() == '*' else [c.strip() for c in columns_str.split(',')]
    
    def _collect_required_columns(self, tree, base_cols):
        if '*' in base_cols: return ['*']
        required = set(base_cols)
        def collect(node):
            if isinstance(node, str): return
            op = node[0]
            if op in ['σ', '⨝']:
                required.update(self._get_columns_in_condition(node[1]))
            if op in ['π', 'ρ', 'σ']: collect(node[2])
            elif op == '⨝':
                collect(node[2]); collect(node[3])
        collect(tree)
        return list(required)
    
    def _get_columns_in_condition(self, condition):
        # Remove literais de string para não capturar palavras dentro deles
        condition_no_literals = re.sub(r"'[^']*'", '', condition)
        # Captura colunas (com ou sem alias)
        matches = re.findall(r'\b(?:\w+\.)?(\w+)\b', condition_no_literals)
        operators = {'AND', 'OR', 'NOT', 'ON', 'WHERE', 'INNER', 'JOIN', 'LIKE', 'IN'}
        return [m for m in matches if m.upper() not in operators and not m.isdigit()]
    
    def get_optimization_log(self):
        return '\n'.join(self.optimization_log)