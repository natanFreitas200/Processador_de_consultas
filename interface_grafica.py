import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import filedialog
import threading
import os
import sys
import re
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.ioff()
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import networkx as nx
from query_processor import QueryProcessor
from conversor import RelationalAlgebraConverter

class ProcessadorConsultasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Consultas SQL - Álgebra Relacional (OTIMIZADO)")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        try:
            self.query_processor = QueryProcessor()
        except Exception as e:
            self.query_processor = None
            print(f"Aviso: QueryProcessor não pôde ser inicializado: {e}")
        
        self.converter = RelationalAlgebraConverter()
        self.current_unoptimized_tree = None
        self.current_optimized_tree = None
        self.current_sql = None
        self.show_optimized = True
        
        self.setup_interface()
    
    def setup_interface(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        title_label = ttk.Label(main_frame, text="Processador de Consultas SQL com Otimização",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        input_frame = ttk.LabelFrame(main_frame, text="Entrada da Consulta SQL", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Label(input_frame, text="Digite sua consulta SQL:").grid(row=0, column=0, sticky=tk.W)
        
        self.sql_entry = scrolledtext.ScrolledText(input_frame, height=4, width=70,
                                                   wrap=tk.WORD, font=('Courier New', 10))
        self.sql_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, pady=(0, 5))
        
        ttk.Button(button_frame, text="Validar Consulta",
                  command=self.validar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Processar Consulta",
                  command=self.processar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Limpar",
                  command=self.limpar_campos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Próximo Exemplo",
                  command=self.next_example_query).pack(side=tk.LEFT, padx=(0, 5))
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.setup_validation_tab()
        self.setup_algebra_tab()
        self.setup_graph_tab()
        self.setup_execution_tab()
        
        self.add_example_queries()
    
    def setup_validation_tab(self):
        validation_frame = ttk.Frame(self.notebook)
        self.notebook.add(validation_frame, text="Validação SQL")
        
        validation_frame.columnconfigure(0, weight=1)
        validation_frame.rowconfigure(1, weight=1)
        
        ttk.Label(validation_frame, text="Resultado da Validação:",
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.validation_text = scrolledtext.ScrolledText(validation_frame, height=15,
                                                         font=('Courier New', 10))
        self.validation_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S),
                                 padx=10, pady=(0, 10))
    
    def setup_algebra_tab(self):
        algebra_frame = ttk.Frame(self.notebook)
        self.notebook.add(algebra_frame, text="Álgebra Relacional")
        
        algebra_frame.columnconfigure(0, weight=1)
        algebra_frame.rowconfigure(1, weight=1)
        
        ttk.Label(algebra_frame, text="Expressão em Álgebra Relacional:",
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.algebra_text = scrolledtext.ScrolledText(algebra_frame, height=15,
                                                      font=('Courier New', 12))
        self.algebra_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S),
                              padx=10, pady=(0, 10))
    
    def setup_graph_tab(self):
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Grafo Visual")
        
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)
        
        graph_controls = ttk.Frame(graph_frame)
        graph_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(graph_controls, text="Visualização do Grafo de Álgebra Relacional:",
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # NOVO: Botões para alternar entre otimizado e não otimizado
        ttk.Button(graph_controls, text="🔴 Mostrar NÃO Otimizado",
                  command=lambda: self.atualizar_grafo_visual(show_optimized=False)).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(graph_controls, text="✅ Mostrar OTIMIZADO",
                  command=lambda: self.atualizar_grafo_visual(show_optimized=True)).pack(side=tk.RIGHT, padx=(5, 0))
        
        canvas_frame = ttk.Frame(graph_frame)
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.graph_fig = plt.Figure(figsize=(10, 8))
        self.graph_ax = self.graph_fig.add_subplot(111)
        self.graph_ax.set_facecolor('#f8f9fa')
        self.graph_ax.axis('off')
        
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=canvas_frame)
        self.graph_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.graph_ax.text(0.5, 0.5, 'Digite uma consulta SQL e clique em "Processar Consulta"\npara visualizar o grafo de álgebra relacional',
                          ha='center', va='center', transform=self.graph_ax.transAxes,
                          fontsize=14, style='italic', color='gray')
        self.graph_canvas.draw()
    
    def setup_execution_tab(self):
        execution_frame = ttk.Frame(self.notebook)
        self.notebook.add(execution_frame, text="Plano de Execução")
        
        execution_frame.columnconfigure(0, weight=1)
        execution_frame.rowconfigure(1, weight=1)
        
        ttk.Label(execution_frame, text="Ordem de Execução da Consulta (OTIMIZADO):",
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.execution_text = scrolledtext.ScrolledText(execution_frame, height=15,
                                                        font=('Courier New', 10))
        self.execution_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S),
                                padx=10, pady=(0, 10))
    
    def add_example_queries(self):
        example_queries = [
            "SELECT Nome, Email FROM cliente WHERE idade > 25;",
            "SELECT * FROM pedidos WHERE valor > 100;",
            "SELECT c.nome, p.valor FROM cliente c INNER JOIN pedidos p ON c.id = p.cliente_id WHERE p.valor > 500;",
            "SELECT e.nome, d.nome FROM empregado e INNER JOIN departamento d ON e.dept_id = d.id WHERE e.salario > 5000;"
        ]
        
        self.sql_entry.delete("1.0", tk.END)
        self.sql_entry.insert(tk.END, example_queries[0])
        self.example_queries = example_queries
        self.example_index = 0
    
    def next_example_query(self):
        if not hasattr(self, 'example_index'):
            self.example_index = 0
        self.example_index = (self.example_index + 1) % len(self.example_queries)
        self.sql_entry.delete("1.0", tk.END)
        self.sql_entry.insert(tk.END, self.example_queries[self.example_index])
    
    def validar_consulta(self):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        if not sql_query:
            messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL.")
            return
        
        self.validation_text.delete("1.0", tk.END)
        self.validation_text.insert(tk.END, "Validando consulta...\n\n")
        self.validation_text.update()
        
        try:
            if self.query_processor is None:
                self.validation_text.delete("1.0", tk.END)
                self.validation_text.insert(tk.END, f"Consulta SQL: {sql_query}\n\n")
                self.validation_text.insert(tk.END, "=== VALIDAÇÃO BÁSICA (SEM BANCO) ===\n")
                
                if self._basic_syntax_check(sql_query):
                    self.validation_text.insert(tk.END, "✓ Sintaxe básica parece válida.\n")
                    self.validation_text.insert(tk.END, "✓ Nota: Validação completa requer conexão com banco de dados.\n")
                else:
                    self.validation_text.insert(tk.END, "✗ Problema de sintaxe detectado.\n")
                return
            
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            is_valid = self.query_processor.validate_query(sql_query)
            
            sys.stdout = old_stdout
            validation_result = captured_output.getvalue()
            
            self.validation_text.delete("1.0", tk.END)
            self.validation_text.insert(tk.END, f"Consulta SQL: {sql_query}\n\n")
            self.validation_text.insert(tk.END, "=== RESULTADO DA VALIDAÇÃO ===\n")
            self.validation_text.insert(tk.END, validation_result)
            
            if is_valid:
                self.validation_text.insert(tk.END, "\n✅ CONSULTA VÁLIDA! Pode prosseguir para o processamento.\n")
            else:
                self.validation_text.insert(tk.END, "\n❌ CONSULTA INVÁLIDA! Corrija os erros antes de prosseguir.\n")
        
        except Exception as e:
            self.validation_text.delete("1.0", tk.END)
            self.validation_text.insert(tk.END, f"Erro durante a validação: {str(e)}")
    
    def _basic_syntax_check(self, sql_query):
        sql_upper = sql_query.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return False
        if "FROM" not in sql_upper:
            return False
        
        import re
        pattern = r"^\s*SELECT\s+.+\s+FROM\s+\w+.*$"
        return bool(re.match(pattern, sql_query, re.IGNORECASE | re.DOTALL))
    
    def processar_consulta(self):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        if not sql_query:
            messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL.")
            return
        
        threading.Thread(target=self._processar_consulta_thread, args=(sql_query,), daemon=True).start()
    
    def _processar_consulta_thread(self, sql_query):
        try:
            self.root.after(0, lambda: self.algebra_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "Processando consulta...\n"))
            
            # Gerar expressão de álgebra relacional
            algebra_expression = self.converter.convert(sql_query)
            
            # Gerar árvores (não otimizada e otimizada)
            unoptimized_tree, optimized_tree = self.converter.convert_to_optimized_tree(sql_query)
            
            # Obter log de otimizações
            optimization_log = self.converter.get_optimization_log()
            
            # Armazenar para uso posterior
            self.current_unoptimized_tree = unoptimized_tree
            self.current_optimized_tree = optimized_tree
            self.current_sql = sql_query
            
            self.root.after(0, lambda: self.algebra_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"Consulta SQL Original:\n{sql_query}\n\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "=== ÁLGEBRA RELACIONAL (NÃO OTIMIZADA) ===\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"{algebra_expression}\n\n"))
            
            # Mostrar log de otimizações
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "\n" + "="*70 + "\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "OTIMIZAÇÕES APLICADAS:\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, optimization_log + "\n"))
            
            self.root.after(0, lambda: self.atualizar_grafo_visual(show_optimized=True))
            
            # Gerar plano de execução otimizado
            execution_plan = self._generate_optimized_execution_plan(sql_query)
            
            self.root.after(0, lambda: self.execution_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.execution_text.insert(tk.END, execution_plan))
            self.root.after(0, lambda: self.notebook.select(3))
        
        except Exception as e:
            error_msg = f"Erro durante o processamento: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
    
    def _generate_optimized_execution_plan(self, sql_query):
        try:
            plan = f"PLANO DE EXECUÇÃO OTIMIZADO PARA:\n{sql_query}\n"
            plan += "=" * 80 + "\n\n"
            
            parsed = self.converter._parse_sql(sql_query)
            if not parsed:
                return "Erro: Não foi possível gerar o plano de execução."
            
            step = 1
            plan += "ETAPAS DE EXECUÇÃO (Com Otimizações Aplicadas):\n\n"
            
            from_clause = parsed.get('from_clause', '')
            base_table_info, joins = self.converter._parse_from_clause(from_clause)
            where_clause = parsed.get('where')
            columns = parsed.get('columns', '*')
            
            # HEURÍSTICA 1: Push-down de seleções
            plan += "--- FASE 1: APLICAÇÃO DE SELEÇÕES (Push-down) ---\n\n"
            
            if base_table_info:
                plan += f"{step}. SCAN da tabela base: {base_table_info.get('table')}\n"
                step += 1
                
                # Se houver WHERE, aplicar filtro IMEDIATAMENTE
                if where_clause:
                    plan += f"{step}. SELEÇÃO (σ) - Aplicada IMEDIATAMENTE após scan\n"
                    plan += f"   → Condição: {where_clause}\n"
                    plan += f"   → ✅ OTIMIZAÇÃO: Filtro aplicado cedo (Push-down de seleção)\n"
                    plan += f"   → Reduz drasticamente o número de tuplas\n\n"
                    step += 1
            
            # HEURÍSTICA 2: Push-down de projeções
            if columns and columns.strip() != '*':
                plan += f"\n--- FASE 2: PROJEÇÕES INTERMEDIÁRIAS (Push-down) ---\n\n"
                plan += f"{step}. PROJEÇÃO (π) - Aplicada cedo\n"
                plan += f"   → Colunas mantidas: {columns}\n"
                plan += f"   → ✅ OTIMIZAÇÃO: Colunas desnecessárias eliminadas cedo\n"
                plan += f"   → Reduz volume de dados transferidos\n\n"
                step += 1
            
            # JOINs com dados já filtrados
            if joins:
                plan += f"\n--- FASE 3: JUNÇÕES (Com dados já filtrados) ---\n\n"
                for join in joins:
                    join_table = join.get('join_table')
                    join_condition = join.get('join_on')
                    
                    plan += f"{step}. SCAN da tabela: {join_table}\n"
                    plan += f"   → Leitura com filtros aplicados\n\n"
                    step += 1
                    
                    plan += f"{step}. JOIN (⨝) OTIMIZADO\n"
                    plan += f"   → Condição: {join_condition}\n"
                    plan += f"   → Algoritmo: Hash Join (O(n) vs O(n²) do Nested Loop)\n"
                    plan += f"   → ✅ OTIMIZAÇÃO: JOIN sobre dados já filtrados\n\n"
                    step += 1
            
            # Projeção final
            plan += f"\n--- FASE 4: RESULTADO FINAL ---\n\n"
            plan += f"{step}. PROJEÇÃO FINAL (π)\n"
            plan += f"   → Colunas retornadas: {columns}\n\n"
            
            plan += "=" * 80 + "\n"
            plan += "COMPARAÇÃO: NÃO OTIMIZADO vs OTIMIZADO\n\n"
            
            plan += "NÃO OTIMIZADO:\n"
            plan += "  1. Scan todas as tabelas\n"
            plan += "  2. JOIN sobre datasets completos (MUITO CUSTOSO)\n"
            plan += "  3. Aplicar WHERE após JOIN\n"
            plan += "  4. Projetar colunas no final\n"
            plan += "  → Resultado: Alto custo computacional\n\n"
            
            plan += "OTIMIZADO (ESTE PLANO):\n"
            plan += "  1. ✅ Scan com seleções imediatas\n"
            plan += "  2. ✅ Projeções intermediárias\n"
            plan += "  3. ✅ JOIN sobre dados reduzidos\n"
            plan += "  4. ✅ Hash Join eficiente\n"
            plan += "  → Resultado: Custo significativamente menor\n\n"
            
            plan += "=" * 80 + "\n"
            plan += "HEURÍSTICAS APLICADAS:\n\n"
            plan += "✅ 1. PUSH-DOWN DE SELEÇÕES (σ)\n"
            plan += "   Filtros aplicados o mais cedo possível\n\n"
            plan += "✅ 2. PUSH-DOWN DE PROJEÇÕES (π)\n"
            plan += "   Colunas eliminadas antecipadamente\n\n"
            plan += "✅ 3. REORDENAÇÃO DE JOINS\n"
            plan += "   JOINs mais restritivos primeiro\n\n"
            plan += "✅ 4. SELEÇÃO DE ALGORITMOS EFICIENTES\n"
            plan += "   Hash Join (O(n)) vs Nested Loop (O(n²))\n\n"
            
            return plan
        
        except Exception as e:
            return f"Erro ao gerar plano: {str(e)}"
    
    def atualizar_grafo_visual(self, show_optimized=True):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        if not sql_query:
            messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL primeiro.")
            return
        
        try:
            self.graph_ax.clear()
            self.graph_ax.set_facecolor('#f8f9fa')
            self.graph_ax.axis('off')
            
            # Escolher qual árvore mostrar
            if show_optimized and hasattr(self, 'current_optimized_tree'):
                relational_tree = self.current_optimized_tree
                title_suffix = "OTIMIZADA"
                badge_color = '#27ae60'  # Verde
            else:
                if hasattr(self, 'current_unoptimized_tree'):
                    relational_tree = self.current_unoptimized_tree
                else:
                    relational_tree = self.converter.convert_to_tree(sql_query, optimize=False)
                title_suffix = "NÃO OTIMIZADA"
                badge_color = '#e74c3c'  # Vermelho
            
            if isinstance(relational_tree, str) and relational_tree.startswith("Erro"):
                self.graph_ax.text(0.5, 0.5, f'Erro:\n{relational_tree}',
                                 ha='center', va='center', transform=self.graph_ax.transAxes,
                                 fontsize=12, color='red')
                self.graph_canvas.draw()
                return
            
            G = nx.DiGraph()
            self.converter.node_counter = 0
            pos_dict = {}
            node_colors = {}
            node_labels = {}
            node_shapes = {}
            
            root_id = self.converter._add_nodes_to_graph(relational_tree, G, pos_dict,
                                                          node_colors, node_labels, node_shapes)
            
            pos = self.converter._calculate_improved_positions(G, root_id)
            
            self._desenhar_grafo_integrado(G, pos, node_colors, node_labels, node_shapes, 
                                           sql_query, title_suffix, badge_color)
            
            self.graph_canvas.draw()
        
        except Exception as e:
            self.graph_ax.text(0.5, 0.5, f'Erro ao gerar grafo:\n{str(e)}',
                             ha='center', va='center', transform=self.graph_ax.transAxes,
                             fontsize=12, color='red')
            self.graph_canvas.draw()
    
    def _desenhar_grafo_integrado(self, G, pos, node_colors, node_labels, node_shapes, sql_query, title_suffix, badge_color):
        color_styles = {
            'projection': {'color': '#9c27b0', 'shape': 'circle', 'icon': 'P', 'text_color': 'white'},
            'selection': {'color': '#4caf50', 'shape': 'rect', 'icon': 'S', 'text_color': 'white'},
            'join': {'color': '#f44336', 'shape': 'diamond', 'icon': 'J', 'text_color': 'white'},
            'rename': {'color': '#ff9800', 'shape': 'rect', 'icon': 'R', 'text_color': 'white'},
            'table': {'color': '#2196f3', 'shape': 'rect', 'icon': 'T', 'text_color': 'white'}
        }
        
        # Desenhar sombras dos nós
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_colors[node]
            style = color_styles[node_type]
            shadow_offset = 0.05
            
            if style['shape'] == 'circle':
                shadow = patches.Circle((x + shadow_offset, y - shadow_offset), 0.35,
                                       facecolor='gray', alpha=0.3, zorder=1)
                self.graph_ax.add_patch(shadow)
            elif style['shape'] == 'diamond':
                diamond_points = [[x + shadow_offset, y + 0.45 - shadow_offset],
                                [x + 0.35 + shadow_offset, y - shadow_offset],
                                [x + shadow_offset, y - 0.45 - shadow_offset],
                                [x - 0.35 + shadow_offset, y - shadow_offset]]
                shadow = patches.Polygon(diamond_points, facecolor='gray', alpha=0.3, zorder=1)
                self.graph_ax.add_patch(shadow)
            else:
                shadow = patches.FancyBboxPatch((x - 0.45 + shadow_offset, y - 0.3 - shadow_offset),
                                               0.9, 0.6, boxstyle="round,pad=0.05",
                                               facecolor='gray', alpha=0.3, zorder=1)
                self.graph_ax.add_patch(shadow)
        
        # Desenhar arestas
        for edge in G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            arrow = patches.FancyArrowPatch(start_pos, end_pos,
                                          connectionstyle="arc3,rad=0.1",
                                          arrowstyle="->",
                                          mutation_scale=25,
                                          color='#34495e',
                                          linewidth=3,
                                          alpha=0.8,
                                          zorder=2)
            self.graph_ax.add_patch(arrow)
        
        # Desenhar nós
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_colors[node]
            label = node_labels[node]
            style = color_styles[node_type]
            
            if style['shape'] == 'circle':
                circle = patches.Circle((x, y), 0.35, facecolor=style['color'],
                                       edgecolor='white', linewidth=3, alpha=0.95, zorder=4)
                self.graph_ax.add_patch(circle)
            elif style['shape'] == 'diamond':
                diamond_points = [[x, y + 0.45], [x + 0.35, y], [x, y - 0.45], [x - 0.35, y]]
                diamond = patches.Polygon(diamond_points, facecolor=style['color'],
                                        edgecolor='white', linewidth=3, alpha=0.95, zorder=4)
                self.graph_ax.add_patch(diamond)
            else:
                rect = patches.FancyBboxPatch((x - 0.45, y - 0.3), 0.9, 0.6,
                                            boxstyle="round,pad=0.05",
                                            facecolor=style['color'],
                                            edgecolor='white',
                                            linewidth=3,
                                            alpha=0.95,
                                            zorder=4)
                self.graph_ax.add_patch(rect)
            
            # Texto do nó
            wrapped_label = self._wrap_label(label, 15)
            self.graph_ax.text(x, y + 0.1, style['icon'], ha='center', va='center',
                             fontsize=16, fontweight='bold', color=style['text_color'], zorder=7)
            self.graph_ax.text(x, y - 0.15, wrapped_label, ha='center', va='center',
                             fontsize=9, fontweight='bold', color=style['text_color'], zorder=7)
        
        # Título com badge
        title = f'Grafo de Álgebra Relacional - {title_suffix}'
        subtitle = f'{sql_query[:50]}{"..." if len(sql_query) > 50 else ""}'
        
        self.graph_ax.text(0.5, 0.97, title, transform=self.graph_ax.transAxes,
                          fontsize=16, fontweight='bold', ha='center', va='top',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=badge_color, alpha=0.9,
                                   edgecolor='white', linewidth=2), color='white')
        
        self.graph_ax.text(0.5, 0.92, subtitle, transform=self.graph_ax.transAxes,
                          fontsize=10, ha='center', va='top', style='italic', color='#7f8c8d')
        
        self._add_compact_legend()
        
        if pos:
            x_coords = [x for x, y in pos.values()]
            y_coords = [y for x, y in pos.values()]
            margin = 1.2
            self.graph_ax.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
            self.graph_ax.set_ylim(min(y_coords) - margin, max(y_coords) + margin)
    
    def _add_compact_legend(self):
        legend_items = [
            {'icon': 'P', 'color': '#9c27b0', 'text': 'Projeção'},
            {'icon': 'S', 'color': '#4caf50', 'text': 'Seleção'},
            {'icon': 'J', 'color': '#f44336', 'text': 'Junção'},
            {'icon': 'R', 'color': '#ff9800', 'text': 'Renomeação'},
            {'icon': 'T', 'color': '#2196f3', 'text': 'Tabela'}
        ]
        
        legend_x = 0.02
        legend_y = 0.25
        
        legend_bg = patches.FancyBboxPatch((legend_x - 0.01, legend_y - len(legend_items) * 0.04 - 0.02),
                                          0.18, len(legend_items) * 0.04 + 0.04,
                                          transform=self.graph_ax.transAxes,
                                          boxstyle="round,pad=0.01",
                                          facecolor='white',
                                          edgecolor='#bdc3c7',
                                          alpha=0.95,
                                          zorder=10)
        self.graph_ax.add_patch(legend_bg)
        
        self.graph_ax.text(legend_x + 0.08, legend_y - 0.01, 'Operadores',
                          transform=self.graph_ax.transAxes, fontsize=9,
                          fontweight='bold', ha='center', zorder=11)
        
        for i, item in enumerate(legend_items):
            y_pos = legend_y - 0.03 - (i + 1) * 0.03
            self.graph_ax.text(legend_x + 0.02, y_pos, item['icon'],
                             transform=self.graph_ax.transAxes, fontsize=10, fontweight='bold',
                             color=item['color'], ha='center', va='center', zorder=11)
            self.graph_ax.text(legend_x + 0.04, y_pos, item['text'],
                             transform=self.graph_ax.transAxes, fontsize=8,
                             ha='left', va='center', zorder=11)
    
    def _wrap_label(self, text, width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return '\n'.join(lines[:2])
    
    def limpar_campos(self):
        self.sql_entry.delete("1.0", tk.END)
        self.validation_text.delete("1.0", tk.END)
        self.algebra_text.delete("1.0", tk.END)
        self.execution_text.delete("1.0", tk.END)
        
        self.graph_ax.clear()
        self.graph_ax.set_facecolor('#f8f9fa')
        self.graph_ax.axis('off')
        self.graph_ax.text(0.5, 0.5, 'Digite uma consulta SQL',
                          ha='center', va='center', transform=self.graph_ax.transAxes,
                          fontsize=14, style='italic', color='gray')
        self.graph_canvas.draw()

def main():
    root = tk.Tk()
    app = ProcessadorConsultasGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
