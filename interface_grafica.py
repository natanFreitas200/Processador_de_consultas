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
        self.root.title("Processador de Consultas SQL - Álgebra Relacional")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        try:
            self.query_processor = QueryProcessor()
        except Exception as e:
            self.query_processor = None
            print(f"Aviso: QueryProcessor não pôde ser inicializado: {e}")
            
        self.converter = RelationalAlgebraConverter()
        
        self.setup_interface()
        
    def setup_interface(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        title_label = ttk.Label(main_frame, text="Processador de Consultas SQL", 
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
        
        ttk.Button(graph_controls, text="Atualizar Grafo", 
                  command=self.atualizar_grafo_visual).pack(side=tk.RIGHT, padx=(5, 0))
        
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
        
        ttk.Label(execution_frame, text="Ordem de Execução da Consulta:", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        
        self.execution_text = scrolledtext.ScrolledText(execution_frame, height=15, 
                                                       font=('Courier New', 10))
        self.execution_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), 
                                padx=10, pady=(0, 10))
        
    def add_example_queries(self):
        example_sql = "SELECT Nome, Email FROM cliente;"
        self.sql_entry.insert(tk.END, example_sql)
        
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
                    self.validation_text.insert(tk.END, "✅ Sintaxe básica parece válida.\n")
                    self.validation_text.insert(tk.END, "⚠️ Nota: Validação completa requer conexão com banco de dados.\n")
                else:
                    self.validation_text.insert(tk.END, "❌ Problema de sintaxe detectado.\n")
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
            
            algebra_expression = self.converter.convert(sql_query)
            
            self.root.after(0, lambda: self.algebra_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"Consulta SQL Original:\n{sql_query}\n\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "=== ÁLGEBRA RELACIONAL (NÃO OTIMIZADA) ===\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"{algebra_expression}\n\n"))
            
            self.root.after(0, self.atualizar_grafo_visual)
            
            execution_plan = self._generate_execution_plan(sql_query)
            self.root.after(0, lambda: self.execution_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.execution_text.insert(tk.END, execution_plan))
            
            self.root.after(0, lambda: self.notebook.select(2))
            
        except Exception as e:
            error_msg = f"Erro durante o processamento: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
            
    def _generate_tree_text(self, sql_query):

        try:
            tree = self.converter.convert_to_tree(sql_query)
            if isinstance(tree, str) and tree.startswith("Erro"):
                return tree
            
            text_representation = f"ÁRVORE DE ÁLGEBRA RELACIONAL (NÃO OTIMIZADA)\n"
            text_representation += "=" * 60 + "\n\n"
            text_representation += f"Consulta SQL: {sql_query}\n\n"
            text_representation += "REPRESENTAÇÃO EM ÁRVORE:\n"
            text_representation += self._tree_to_text(tree, 0) + "\n\n"
            
            text_representation += "LEGENDA DOS OPERADORES:\n"
            text_representation += "π - Projeção (SELECT - seleciona colunas)\n"
            text_representation += "σ - Seleção (WHERE - filtra linhas)\n"
            text_representation += "⨝ - Junção (JOIN - combina tabelas)\n"
            text_representation += "ρ - Renomeação (AS - alias para tabelas)\n\n"
            
            text_representation += "CARACTERÍSTICAS DO GRAFO NÃO OTIMIZADO:\n"
            text_representation += "• Operações executadas na ordem que aparecem na consulta\n"
            text_representation += "• Seleções aplicadas após as junções\n"
            text_representation += "• Projeções aplicadas no final\n"
            text_representation += "• Sem aplicação de heurísticas de otimização\n"
            
            return text_representation
            
        except Exception as e:
            return f"Erro ao gerar representação textual: {str(e)}"
    
    def _tree_to_text(self, tree, level):

        indent = "  " * level
        
        if isinstance(tree, str):
            return f"{indent}📋 Tabela: {tree}"
        
        operator = tree[0]
        
        if operator == 'π':
            result = f"{indent}🔽 π (Projeção)\n"
            result += f"{indent}   Colunas: {tree[1]}\n"
            result += f"{indent}   ↓\n"
            result += self._tree_to_text(tree[2], level + 1)
            
        elif operator == 'σ':
            result = f"{indent}🔍 σ (Seleção)\n"
            result += f"{indent}   Condição: {tree[1]}\n"
            result += f"{indent}   ↓\n"
            result += self._tree_to_text(tree[2], level + 1)
            
        elif operator == 'ρ':
            result = f"{indent}🏷️ ρ (Renomeação)\n"
            result += f"{indent}   Alias: {tree[1]}\n"
            result += f"{indent}   ↓\n"
            result += self._tree_to_text(tree[2], level + 1)
            
        elif operator == '⨝':
            result = f"{indent}🔗 ⨝ (Junção)\n"
            result += f"{indent}   Condição: {tree[1]}\n"
            result += f"{indent}   ↙️     ↘️\n"
            result += self._tree_to_text(tree[2], level + 1) + "\n"
            result += self._tree_to_text(tree[3], level + 1)
        
        return result
                                   
    def _generate_execution_plan(self, sql_query):

        try:
            plan = f"PLANO DE EXECUÇÃO PARA: {sql_query}\n"
            plan += "=" * 60 + "\n\n"
            
            parsed = self.converter._parse_sql(sql_query)
            if not parsed:
                return "Erro: Não foi possível gerar o plano de execução."
                
            step = 1
            plan += "ETAPAS DE EXECUÇÃO (Ordem Bottom-Up):\n\n"
            
            from_clause = parsed.get('from_clause', '')
            base_table_info, joins = self.converter._parse_from_clause(from_clause)
            
            if base_table_info:
                plan += f"{step}. SCAN da tabela base: {base_table_info.get('table')}\n"
                plan += f"   → Operação: Leitura sequencial da tabela\n"
                plan += f"   → Resultado: Todas as tuplas de {base_table_info.get('table')}\n\n"
                step += 1
            
            for join in joins:
                join_table = join.get('join_table')
                join_condition = join.get('join_on')
                plan += f"{step}. SCAN da tabela: {join_table}\n"
                plan += f"   → Operação: Leitura sequencial da tabela\n"
                plan += f"   → Resultado: Todas as tuplas de {join_table}\n\n"
                step += 1
                
                plan += f"{step}. JOIN (⨝) - Junção Natural\n"
                plan += f"   → Condição: {join_condition}\n"
                plan += f"   → Algoritmo: Nested Loop Join (não otimizado)\n"
                plan += f"   → Resultado: Tuplas que satisfazem a condição de join\n\n"
                step += 1
            
            where_clause = parsed.get('where')
            if where_clause:
                plan += f"{step}. SELEÇÃO (σ) - Filtro WHERE\n"
                plan += f"   → Condição: {where_clause}\n"
                plan += f"   → Operação: Aplicar predicados de seleção\n"
                plan += f"   → Resultado: Tuplas que satisfazem WHERE\n\n"
                step += 1
            
            columns = parsed.get('columns', '*')
            if columns and columns.strip() != '*':
                plan += f"{step}. PROJEÇÃO (π) - Seleção de colunas\n"
                plan += f"   → Colunas: {columns}\n"
                plan += f"   → Operação: Eliminar colunas não solicitadas\n"
                plan += f"   → Resultado: Apenas as colunas especificadas\n\n"
                step += 1
            
            plan += "=" * 60 + "\n"
            plan += "CARACTERÍSTICAS DO PLANO (NÃO OTIMIZADO):\n\n"
            plan += "• Ordem de execução: Bottom-up (das folhas para a raiz)\n"
            plan += "• JOINs executados na ordem que aparecem na consulta\n"
            plan += "• Seleções (WHERE) aplicadas após os JOINs\n"
            plan += "• Projeções aplicadas no final\n"
            plan += "• Sem otimizações de push-down de predicados\n"
            plan += "• Algoritmo de JOIN: Nested Loop (força bruta)\n\n"
            
            plan += "HEURÍSTICAS NÃO APLICADAS (seria necessário para otimizar):\n"
            plan += "• Push-down de seleções (aplicar WHERE mais cedo)\n"
            plan += "• Push-down de projeções (eliminar colunas cedo)\n"
            plan += "• Reordenação de JOINs para minimizar resultados intermediários\n"
            plan += "• Escolha de algoritmos de JOIN mais eficientes\n"
            
            return plan
            
        except Exception as e:
            return f"Erro ao gerar plano de execução: {str(e)}"
    
    def atualizar_grafo_visual(self):

        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        
        if not sql_query:
            messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL primeiro.")
            return
        
        try:
            self.graph_ax.clear()
            self.graph_ax.set_facecolor('#f8f9fa')
            self.graph_ax.axis('off')
            
            relational_tree = self.converter.convert_to_tree(sql_query)
            
            if isinstance(relational_tree, str) and relational_tree.startswith("Erro"):
                self.graph_ax.text(0.5, 0.5, f'Erro ao processar consulta:\n{relational_tree}',
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
            
            self._desenhar_grafo_integrado(G, pos, node_colors, node_labels, node_shapes, sql_query)
            
            self.graph_canvas.draw()
            
        except Exception as e:
            self.graph_ax.text(0.5, 0.5, f'Erro ao gerar grafo:\n{str(e)}',
                              ha='center', va='center', transform=self.graph_ax.transAxes,
                              fontsize=12, color='red')
            self.graph_canvas.draw()
            print(f"Erro detalhado: {e}")
    
    def _desenhar_grafo_integrado(self, G, pos, node_colors, node_labels, node_shapes, sql_query):

        color_styles = {
            'projection': {'color': '#9c27b0', 'shape': 'circle', 'icon': 'π', 'text_color': 'white'},
            'selection': {'color': '#4caf50', 'shape': 'rect', 'icon': 'σ', 'text_color': 'white'},
            'join': {'color': '#f44336', 'shape': 'diamond', 'icon': '⋈', 'text_color': 'white'},
            'rename': {'color': '#ff9800', 'shape': 'rect', 'icon': 'ρ', 'text_color': 'white'},
            'table': {'color': '#2196f3', 'shape': 'rect', 'icon': '📊', 'text_color': 'white'}
        }
        
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
            
            arrow_highlight = patches.FancyArrowPatch(start_pos, end_pos,
                                                    connectionstyle="arc3,rad=0.1",
                                                    arrowstyle="->", 
                                                    mutation_scale=20,
                                                    color='#5dade2',
                                                    linewidth=1.5,
                                                    alpha=0.6,
                                                    zorder=3)
            self.graph_ax.add_patch(arrow_highlight)
        
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_colors[node]
            label = node_labels[node]
            style = color_styles[node_type]
            
            if style['shape'] == 'circle':
                circle = patches.Circle((x, y), 0.35, facecolor=style['color'], 
                                      edgecolor='white', linewidth=3, alpha=0.95, zorder=4)
                self.graph_ax.add_patch(circle)
                
                inner_circle = patches.Circle((x - 0.05, y + 0.05), 0.32, 
                                            facecolor='white', alpha=0.2, zorder=5)
                self.graph_ax.add_patch(inner_circle)
                
            elif style['shape'] == 'diamond':
                diamond_points = [[x, y + 0.45], [x + 0.35, y], [x, y - 0.45], [x - 0.35, y]]
                diamond = patches.Polygon(diamond_points, facecolor=style['color'], 
                                        edgecolor='white', linewidth=3, alpha=0.95, zorder=4)
                self.graph_ax.add_patch(diamond)
                
                inner_diamond_points = [[x - 0.05, y + 0.4], [x + 0.3, y + 0.05], 
                                      [x - 0.05, y - 0.4], [x - 0.3, y + 0.05]]
                inner_diamond = patches.Polygon(inner_diamond_points, facecolor='white', 
                                              alpha=0.2, zorder=5)
                self.graph_ax.add_patch(inner_diamond)
                
            else:
                rect = patches.FancyBboxPatch((x - 0.45, y - 0.3), 0.9, 0.6,
                                            boxstyle="round,pad=0.05",
                                            facecolor=style['color'],
                                            edgecolor='white',
                                            linewidth=3,
                                            alpha=0.95,
                                            zorder=4)
                self.graph_ax.add_patch(rect)
                
                inner_rect = patches.FancyBboxPatch((x - 0.4, y - 0.25), 0.8, 0.5,
                                                  boxstyle="round,pad=0.02",
                                                  facecolor='white',
                                                  alpha=0.2,
                                                  zorder=5)
                self.graph_ax.add_patch(inner_rect)
            
            self.graph_ax.text(x + 0.02, y + 0.08, style['icon'], ha='center', va='center', 
                              fontsize=16, fontweight='bold', color='black', alpha=0.3, zorder=6)
            self.graph_ax.text(x, y + 0.1, style['icon'], ha='center', va='center', 
                              fontsize=16, fontweight='bold', color=style['text_color'], zorder=7)
            
            wrapped_label = self._wrap_label(label, 15)
            self.graph_ax.text(x + 0.02, y - 0.18, wrapped_label, ha='center', va='center', 
                              fontsize=9, fontweight='bold', color='black', alpha=0.3, zorder=6)
            self.graph_ax.text(x, y - 0.15, wrapped_label, ha='center', va='center', 
                              fontsize=9, fontweight='bold', color=style['text_color'], zorder=7)
        
        title = f'Grafo de Álgebra Relacional'
        subtitle = f'{sql_query[:60]}{"..." if len(sql_query) > 60 else ""}'
        
        self.graph_ax.text(0.5, 0.97, title, transform=self.graph_ax.transAxes, 
                          fontsize=16, fontweight='bold', ha='center', va='top',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#ecf0f1', alpha=0.9))
        
        self.graph_ax.text(0.5, 0.92, subtitle, transform=self.graph_ax.transAxes, 
                          fontsize=10, ha='center', va='top', style='italic',
                          color='#7f8c8d')
        
        self._add_compact_legend()
        
        if pos:
            x_coords = [x for x, y in pos.values()]
            y_coords = [y for x, y in pos.values()]
            margin = 1.2
            self.graph_ax.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
            self.graph_ax.set_ylim(min(y_coords) - margin, max(y_coords) + margin)
    
    def _add_compact_legend(self):

        legend_items = [
            {'icon': 'π', 'color': '#9c27b0', 'text': 'Projeção'},
            {'icon': 'σ', 'color': '#4caf50', 'text': 'Seleção'},
            {'icon': '⋈', 'color': '#f44336', 'text': 'Junção'},
            {'icon': 'ρ', 'color': '#ff9800', 'text': 'Renomeação'},
            {'icon': '📊', 'color': '#2196f3', 'text': 'Tabela'}
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
        self.graph_ax.text(0.5, 0.5, 'Digite uma consulta SQL e clique em "Processar Consulta"\npara visualizar o grafo de álgebra relacional',
                          ha='center', va='center', transform=self.graph_ax.transAxes,
                          fontsize=14, style='italic', color='gray')
        self.graph_canvas.draw()


def main():
    root = tk.Tk()
    app = ProcessadorConsultasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()