import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
import networkx as nx
import re
from conversor import RelationalAlgebraConverter

# --- Verificação de Dependências ---
try:
    from query_processor import QueryProcessor
except ImportError:
    print("Aviso: Módulo 'query_processor' não encontrado. A validação com o banco de dados será desativada.")
    QueryProcessor = None
except Exception as e:
    print(f"Aviso: Não foi possível inicializar QueryProcessor: {e}")
    QueryProcessor = None
# --- Fim da Verificação ---


class ProcessadorConsultasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Consultas SQL - Álgebra Relacional (OTIMIZADO)")
        self.root.geometry("1200x850")
        self.root.configure(bg='#f0f0f0')

        self.query_processor = QueryProcessor() if QueryProcessor else None
        
        self.converter = RelationalAlgebraConverter()
        self.current_unoptimized_tree = None
        self.current_optimized_tree = None
        self.current_sql = None
        
        self.node_styles = {
            'projection': {'c': '#8e44ad', 'ico': 'π', 'label': 'Projeção'},
            'selection':  {'c': '#27ae60', 'ico': 'σ', 'label': 'Seleção'},
            'join':       {'c': '#c0392b', 'ico': '|X|', 'label': 'Junção'},
            'rename':     {'c': '#f39c12', 'ico': 'ρ', 'label': 'Renomeação'},
            'table':      {'c': '#2980b9', 'ico': 'T', 'label': 'Tabela'}
        }
        
        self.graph_view_var = tk.StringVar(value="optimized")
        
        self.setup_interface()
    
    def setup_interface(self):
        main_frame = ttk.Frame(self.root, padding="10"); main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1); self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1); main_frame.rowconfigure(2, weight=1)
        style = ttk.Style(); style.configure('TButton', font=('Arial', 10)); style.configure('TRadiobutton', background='#f0f0f0', font=('Arial', 10))
        ttk.Label(main_frame, text="Processador de Consultas SQL com Otimização", font=('Arial', 16, 'bold'), background='#f0f0f0').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        input_frame = ttk.LabelFrame(main_frame, text="Entrada da Consulta SQL", padding="10"); input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        self.sql_entry = scrolledtext.ScrolledText(input_frame, height=5, width=70, wrap=tk.WORD, font=('Courier New', 10), relief=tk.SOLID, borderwidth=1); self.sql_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        button_frame = ttk.Frame(input_frame); button_frame.grid(row=2, column=0, pady=(0, 5))
        ttk.Button(button_frame, text="Validar Consulta", command=self.validar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Processar Consulta", command=self.processar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Limpar", command=self.limpar_campos).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Próximo Exemplo", command=self.next_example_query).pack(side=tk.LEFT, padx=(0, 5))
        self.notebook = ttk.Notebook(main_frame); self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        self.setup_tabs(); self.add_example_queries()

    def setup_tabs(self):
        tab_names = ["Validação SQL", "Álgebra Relacional", "Grafo Visual", "Plano de Execução"]
        for name in tab_names:
            frame = ttk.Frame(self.notebook, padding="10"); self.notebook.add(frame, text=name)
            if name == "Grafo Visual": self.setup_graph_tab(frame)
            else:
                frame.columnconfigure(0, weight=1); frame.rowconfigure(1, weight=1)
                title_map = { "Validação SQL": "Resultado da Validação:", "Álgebra Relacional": "Expressão em Álgebra Relacional:", "Plano de Execução": "Ordem de Execução da Consulta (OTIMIZADO):" }
                ttk.Label(frame, text=title_map[name], font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
                text_widget = scrolledtext.ScrolledText(frame, height=15, font=('Courier New', 10), relief=tk.SOLID, borderwidth=1)
                text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
                setattr(self, f"{name.lower().replace(' ', '_')}_text", text_widget)

    def setup_graph_tab(self, graph_frame):
        graph_frame.columnconfigure(0, weight=1); graph_frame.rowconfigure(1, weight=1)
        
        # Controles do grafo
        graph_controls = ttk.Frame(graph_frame); graph_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        graph_controls.columnconfigure(1, weight=1)
        
        ttk.Label(graph_controls, text="Visualização do Grafo:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Botões de controle
        control_buttons = ttk.Frame(graph_controls)
        control_buttons.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(control_buttons, text="🔍 Zoom In", command=self._zoom_in, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_buttons, text="🔍 Zoom Out", command=self._zoom_out, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_buttons, text="🔄 Resetar", command=self._reset_zoom, width=12).pack(side=tk.LEFT, padx=2)
        
        # Radio buttons para alternar visualização
        radio_frame = ttk.Frame(graph_controls)
        radio_frame.grid(row=0, column=2, sticky=tk.E, padx=(10, 0))
        ttk.Radiobutton(radio_frame, text="Otimizado", variable=self.graph_view_var, value="optimized", command=self.atualizar_grafo_visual).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Radiobutton(radio_frame, text="Não Otimizado", variable=self.graph_view_var, value="unoptimized", command=self.atualizar_grafo_visual).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Canvas frame
        canvas_frame = ttk.Frame(graph_frame, style='TFrame')
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1); canvas_frame.rowconfigure(0, weight=1)
        
        # Criar figura matplotlib
        self.graph_fig = plt.Figure(figsize=(12, 9), facecolor='#f0f0f0', dpi=100)
        self.graph_ax = self.graph_fig.add_subplot(111, facecolor='#f0f0f0')
        self.graph_ax.axis('off')
        
        # Canvas com toolbar de navegação
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=canvas_frame)
        self.graph_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Variáveis para interatividade
        self.current_node_annotations = []
        self.zoom_level = 1.0
        self.pan_start = None
        self.current_xlim = None
        self.current_ylim = None
        
        # Conectar eventos de mouse
        self.graph_canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.graph_canvas.mpl_connect('button_press_event', self._on_press)
        self.graph_canvas.mpl_connect('button_release_event', self._on_release)
        self.graph_canvas.mpl_connect('scroll_event', self._on_scroll)
        
        # Mensagem inicial
        self.graph_ax.text(0.5, 0.5, 'Processar uma consulta para visualizar o grafo interativo.\n\n💡 Use scroll do mouse para zoom\n💡 Arraste para mover o grafo\n💡 Passe o mouse sobre os nós para detalhes', 
                          ha='center', va='center', transform=self.graph_ax.transAxes, 
                          fontsize=12, color='gray', style='italic')
        self.graph_canvas.draw()
        
    def add_example_queries(self):
        complex_queries = [
            "SELECT c.Nome, prod.Nome AS Produto, ped.ValorTotalPedido FROM Cliente AS c INNER JOIN Pedido AS ped ON c.idCliente = ped.Cliente_idCliente INNER JOIN Pedido_has_Produto AS pp ON ped.idPedido = pp.Pedido_idPedido INNER JOIN Produto AS prod ON pp.Produto_idProduto = prod.idProduto WHERE (c.TipoCliente_idTipoCliente = 1 AND ped.ValorTotalPedido > 500) OR prod.Preco < 20;",
            "SELECT tc.Descricao, c.Nome, ped.idPedido, prod.Nome, pp.Quantidade FROM TipoCliente tc INNER JOIN Cliente c ON tc.idTipoCliente = c.TipoCliente_idTipoCliente INNER JOIN Pedido ped ON c.idCliente = ped.Cliente_idCliente INNER JOIN Pedido_has_Produto pp ON ped.idPedido = pp.Pedido_idPedido INNER JOIN Produto prod ON pp.Produto_idProduto = prod.idProduto WHERE tc.idTipoCliente = 1 AND prod.Preco > 500;",
            "SELECT * FROM Cliente c INNER JOIN Pedido p ON c.idCliente = p.Cliente_idCliente INNER JOIN Status s ON p.Status_idStatus = s.idStatus WHERE s.idStatus = 3;",
            "SELECT c.Nome, e.Cidade, t.Numero AS Telefone, tc.Descricao AS Tipo FROM Cliente c INNER JOIN Endereco e ON c.idCliente = e.Cliente_idCliente INNER JOIN Telefone t ON c.idCliente = t.Cliente_idCliente INNER JOIN TipoCliente tc ON c.TipoCliente_idTipoCliente = tc.idTipoCliente WHERE e.UF = 'SP';",
        ]
        self.example_queries = complex_queries
        self.example_index = 0
        self.sql_entry.delete("1.0", tk.END); self.sql_entry.insert(tk.END, self.example_queries[0])

    def next_example_query(self):
        self.example_index = (self.example_index + 1) % len(self.example_queries)
        self.sql_entry.delete("1.0", tk.END); self.sql_entry.insert(tk.END, self.example_queries[self.example_index])

    def validar_consulta(self):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        if not sql_query: messagebox.showwarning("Aviso", "Digite uma consulta SQL."); return
        self.validação_sql_text.delete("1.0", tk.END); self.validação_sql_text.insert(tk.END, "Validando...")
        self.notebook.select(0)
        threading.Thread(target=self._validar_consulta_thread, args=(sql_query,), daemon=True).start()

    def _validar_consulta_thread(self, sql_query):
        final_msg = f"Consulta SQL:\n{sql_query}\n\n=== RESULTADO DA VALIDAÇÃO ===\n"
        if self.query_processor:
            is_valid, msg = self.query_processor.validate_query(sql_query)
            validator_used = "QueryProcessor (validador com schema)"
            if not self.query_processor.schema: msg += "\n\nAviso: Conexão com o BD indisponível, validação de nomes ignorada."
        else:
            is_valid, msg = self.converter.validate_sql_syntax(sql_query)
            validator_used = "Conversor (sintaxe básica)"
        final_msg += f"Validador: {validator_used}\nResultado: {msg}\n\n{'✅ CONSULTA VÁLIDA!' if is_valid else '❌ CONSULTA INVÁLIDA!'}"
        self.root.after(0, lambda: (self.validação_sql_text.delete("1.0", tk.END), self.validação_sql_text.insert(tk.END, final_msg)))

    def processar_consulta(self):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        if not sql_query: messagebox.showwarning("Aviso", "Digite uma consulta SQL."); return
        is_valid, msg = self.query_processor.validate_query(sql_query) if self.query_processor else self.converter.validate_sql_syntax(sql_query)
        if not is_valid: messagebox.showerror("Consulta Inválida", f"A consulta não pode ser processada.\n\nMotivo: {msg}"); return
        self.limpar_resultados(); self.álgebra_relacional_text.insert(tk.END, "Processando...")
        threading.Thread(target=self._processar_consulta_thread, args=(sql_query,), daemon=True).start()

    def _processar_consulta_thread(self, sql_query):
        try:
            self.current_unoptimized_tree, self.current_optimized_tree = self.converter.convert_to_optimized_tree(sql_query)
            self.current_sql = sql_query; self.root.after(0, self.update_ui_after_processing)
        except Exception as e: self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha ao processar a consulta:\n{e}"))

    def update_ui_after_processing(self):
        self.álgebra_relacional_text.delete("1.0", tk.END)
        self.álgebra_relacional_text.insert(tk.END, f"SQL Original:\n{self.current_sql}\n\nExpressão (Não Otimizada):\n{self.converter.convert(self.current_sql)}\n\n{'='*70}\nOTIMIZAÇÕES:\n{self.converter.get_optimization_log()}")
        self.plano_de_execução_text.delete("1.0", tk.END); self.plano_de_execução_text.insert(tk.END, self._generate_optimized_execution_plan())
        self.atualizar_grafo_visual(); self.notebook.select(2)

    def atualizar_grafo_visual(self):
        if not self.current_sql: return
        try:
            self.graph_ax.clear()
            self.graph_ax.axis('off')
            self.current_node_annotations = []
            
            is_opt = self.graph_view_var.get() == "optimized"
            tree = self.current_optimized_tree if is_opt else self.current_unoptimized_tree
            title_suffix, badge_color = ("OTIMIZADA", self.node_styles['selection']['c']) if is_opt else ("NÃO OTIMIZADA", self.node_styles['join']['c'])
            
            # Construir grafo
            G = nx.DiGraph()
            self.converter.node_counter = 0
            pos_dict, colors, labels, shapes = {}, {}, {}, {}
            root_id = self.converter._add_nodes_to_graph(tree, G, pos_dict, colors, labels, shapes)
            
            # Calcular posições melhoradas com mais espaçamento
            pos = self._calculate_hierarchical_layout(G, root_id)
            
            # Armazenar dados do grafo para interatividade
            self.current_graph_data = {
                'G': G,
                'pos': pos,
                'colors': colors,
                'labels': labels,
                'shapes': shapes
            }
            
            # Desenhar grafo
            self._desenhar_grafo_integrado(G, pos, colors, labels, self.current_sql, title_suffix, badge_color)
            
            # Resetar zoom
            self._reset_zoom()
            
            self.graph_canvas.draw()
        except Exception as e:
            self.graph_ax.clear()
            self.graph_ax.text(0.5, 0.5, f'Erro ao gerar grafo:\n{str(e)}', 
                             ha='center', va='center', color='red', fontsize=12)
            self.graph_ax.axis('off')
            self.graph_canvas.draw()

    def _darken_color(self, hex_color, factor=0.7):
        hex_color = hex_color.lstrip('#'); rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"#{''.join([f'{int(c*factor):02x}' for c in rgb])}"

    def _desenhar_texto_com_sombra(self, x, y, text, **kwargs):
        props = kwargs.copy(); zorder = props.pop('zorder', 5); self.graph_ax.text(x+0.008, y-0.008, text, **props, color='#2c3e50', zorder=zorder-1); self.graph_ax.text(x, y, text, **props, color='white', zorder=zorder)

    def _desenhar_grafo_integrado(self, G, pos, node_colors, node_labels, sql_query, title_suffix, badge_color):
        """Desenha o grafo com visual moderno e interativo"""
        
        # Desenhar arestas primeiro (fundo)
        for u, v in G.edges():
            start, end = pos[u], pos[v]
            
            # Sombra da aresta
            shadow = patches.FancyArrowPatch(
                (start[0] + 0.08, start[1] - 0.08),
                (end[0] + 0.08, end[1] - 0.08),
                connectionstyle="arc3,rad=0.15",
                arrowstyle="-|>",
                mutation_scale=30,
                color='black',
                alpha=0.15,
                lw=3,
                zorder=1
            )
            self.graph_ax.add_patch(shadow)
            
            # Aresta principal com gradiente visual
            arrow = patches.FancyArrowPatch(
                start, end,
                connectionstyle="arc3,rad=0.15",
                arrowstyle="-|>",
                mutation_scale=30,
                color='#34495e',
                lw=2.5,
                zorder=2,
                linestyle='-',
                capstyle='round'
            )
            self.graph_ax.add_patch(arrow)
        
        # Desenhar nós
        for node in G.nodes():
            x, y = pos[node]
            node_type = node_colors.get(node, 'table')
            style = self.node_styles[node_type]
            label = node_labels.get(node, '')
            edge_color = self._darken_color(style['c'], 0.6)
            
            shape = {'projection': 'circle', 'join': 'diamond'}.get(node_type, 'rect')
            
            # Desenhar formas com sombra e borda destacada
            shadow_offset = (0.1, -0.1)
            
            if shape == 'circle':
                r = 0.7
                # Sombra
                self.graph_ax.add_patch(patches.Circle(
                    (x + shadow_offset[0], y + shadow_offset[1]),
                    r, fc='black', alpha=0.2, zorder=2
                ))
                # Círculo principal
                self.graph_ax.add_patch(patches.Circle(
                    (x, y), r,
                    fc=style['c'],
                    ec=edge_color,
                    lw=3,
                    zorder=3
                ))
                # Brilho interno
                self.graph_ax.add_patch(patches.Circle(
                    (x - 0.15, y + 0.15), r * 0.3,
                    fc='white',
                    alpha=0.3,
                    zorder=4
                ))
                
            elif shape == 'diamond':
                h, w = 0.9, 0.9
                points = [[x, y + h], [x + w, y], [x, y - h], [x - w, y]]
                # Sombra
                shadow_points = [[p[0] + shadow_offset[0], p[1] + shadow_offset[1]] for p in points]
                self.graph_ax.add_patch(patches.Polygon(
                    shadow_points, fc='black', alpha=0.2, zorder=2
                ))
                # Diamante principal
                self.graph_ax.add_patch(patches.Polygon(
                    points,
                    fc=style['c'],
                    ec=edge_color,
                    lw=3,
                    zorder=3
                ))
                
            else:  # Retângulo
                w, h = 2.0, 1.2
                # Sombra
                self.graph_ax.add_patch(patches.FancyBboxPatch(
                    (x - w/2 + shadow_offset[0], y - h/2 + shadow_offset[1]),
                    w, h,
                    boxstyle="round,pad=0.15",
                    fc='black',
                    alpha=0.2,
                    zorder=2
                ))
                # Retângulo principal
                self.graph_ax.add_patch(patches.FancyBboxPatch(
                    (x - w/2, y - h/2),
                    w, h,
                    boxstyle="round,pad=0.15",
                    fc=style['c'],
                    ec=edge_color,
                    lw=3,
                    zorder=3
                ))
            
            # Desenhar texto dos nós
            icon = style['ico']
            details = '\n'.join(label.split('\n')[1:])
            
            if node_type == 'table':
                # Texto para tabelas
                self._desenhar_texto_com_sombra(
                    x, y,
                    self._wrap_label(label, 18),
                    ha='center', va='center',
                    fontsize=12,
                    fontweight='bold',
                    zorder=5
                )
            else:
                # Ícone + detalhes para operadores
                icon_size = 16 if node_type == 'join' else 20
                self._desenhar_texto_com_sombra(
                    x, y + 0.2,
                    icon,
                    ha='center', va='center',
                    fontsize=icon_size,
                    fontweight='bold',
                    zorder=5
                )
                self._desenhar_texto_com_sombra(
                    x, y - 0.15,
                    self._wrap_label(details, 25),
                    ha='center', va='top',
                    fontsize=9,
                    fontweight='normal',
                    zorder=5
                )
        
        # Título e subtítulo
        subtitle = f'{sql_query[:80]}{"..." if len(sql_query) > 80 else ""}'
        
        self.graph_ax.text(
            0.5, 0.98,
            f'Grafo de Álgebra Relacional - {title_suffix}',
            ha='center', va='top',
            transform=self.graph_ax.transAxes,
            fontsize=18,
            fontweight='bold',
            color='white',
            bbox=dict(
                boxstyle="round,pad=0.5",
                fc=badge_color,
                ec='white',
                lw=3,
                alpha=0.95
            ),
            zorder=100
        )
        
        self.graph_ax.text(
            0.5, 0.93,
            subtitle,
            ha='center', va='top',
            transform=self.graph_ax.transAxes,
            fontsize=10,
            style='italic',
            color='#2c3e50',
            zorder=100
        )
        
        # Legenda
        self._add_legend()
        
        # Ajustar limites
        if pos:
            x_coords = [c[0] for c in pos.values()]
            y_coords = [c[1] for c in pos.values()]
            margin = 2.5
            self.graph_ax.set_xlim(min(x_coords) - margin, max(x_coords) + margin)
            self.graph_ax.set_ylim(min(y_coords) - margin, max(y_coords) + margin)

    def _add_legend(self):
        """Adiciona legenda moderna e interativa"""
        items = [{'icon': v['ico'], 'c': v['c'], 't': v['label']} for k, v in self.node_styles.items()]
        
        lx, ly = 0.02, 0.88
        height = (len(items) + 1) * 0.055
        width = 0.16
        
        # Sombra da legenda
        shadow_patch = patches.FancyBboxPatch(
            (lx + 0.003, ly - height - 0.003),
            width, height,
            boxstyle="round,pad=0.015",
            fc='black',
            ec=None,
            alpha=0.15,
            transform=self.graph_ax.transAxes,
            zorder=98
        )
        self.graph_ax.add_patch(shadow_patch)
        
        # Fundo da legenda com gradiente visual
        bg_patch = patches.FancyBboxPatch(
            (lx, ly - height),
            width, height,
            boxstyle="round,pad=0.015",
            fc='white',
            ec='#34495e',
            linewidth=2,
            alpha=0.98,
            transform=self.graph_ax.transAxes,
            zorder=99
        )
        self.graph_ax.add_patch(bg_patch)
        
        # Título da legenda
        title_x = lx + width / 2
        self.graph_ax.text(
            title_x, ly - 0.015,
            'Operadores',
            transform=self.graph_ax.transAxes,
            fontsize=12,
            fontweight='bold',
            ha='center',
            va='top',
            color='#2c3e50',
            zorder=100
        )
        
        # Itens da legenda
        icon_x = lx + 0.025
        text_x = lx + 0.055
        
        for i, item in enumerate(items):
            y_pos = ly - (i + 1.7) * 0.052
            
            # Círculo de fundo para o ícone
            circle = patches.Circle(
                (icon_x, y_pos),
                0.012,
                fc=item['c'],
                ec=self._darken_color(item['c'], 0.7),
                linewidth=1.5,
                transform=self.graph_ax.transAxes,
                zorder=100,
                alpha=0.9
            )
            self.graph_ax.add_patch(circle)
            
            # Ícone
            icon_fs = 10 if item['icon'] in ['|X|', 'JOIN'] else 12
            self.graph_ax.text(
                icon_x, y_pos,
                item['icon'],
                transform=self.graph_ax.transAxes,
                fontsize=icon_fs,
                color='white',
                ha='center',
                va='center',
                fontweight='bold',
                zorder=101
            )
            
            # Texto
            self.graph_ax.text(
                text_x, y_pos,
                item['t'],
                transform=self.graph_ax.transAxes,
                fontsize=10,
                ha='left',
                va='center',
                color='#34495e',
                zorder=100
            )

    def _wrap_label(self,text,width):
        words=text.split(); lines,current_line=[],[];
        for word in words:
            if len(' '.join(current_line+[word]))<=width: current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line=[word]
        if current_line: lines.append(' '.join(current_line))
        return '\n'.join(lines[:3])

    def _calculate_hierarchical_layout(self, G, root_id):
        """Calcula layout hierárquico melhorado com mais espaçamento"""
        pos = {}
        levels = {}
        queue = [(root_id, 0)]
        visited = set()
        
        # BFS para determinar níveis
        while queue:
            node, level = queue.pop(0)
            if node in visited: continue
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
        
        # Posicionar nós com espaçamento otimizado
        for level, nodes in level_nodes.items():
            y = (max_level - level) * 3.5  # Espaçamento vertical maior
            num_nodes = len(nodes)
            
            if num_nodes == 1:
                x_positions = [0]
            else:
                # Espaçamento horizontal adaptativo
                width = max(6, num_nodes * 3)
                x_positions = [(i - (num_nodes - 1) / 2) * (width / num_nodes) for i in range(num_nodes)]
            
            for i, node in enumerate(nodes):
                pos[node] = (x_positions[i], y)
        
        return pos
    
    def _zoom_in(self):
        """Zoom in no grafo"""
        self.zoom_level *= 1.2
        self._apply_zoom()
    
    def _zoom_out(self):
        """Zoom out no grafo"""
        self.zoom_level /= 1.2
        self._apply_zoom()
    
    def _reset_zoom(self):
        """Reseta o zoom para visualização padrão"""
        self.zoom_level = 1.0
        if hasattr(self, 'current_graph_data') and self.current_graph_data:
            pos = self.current_graph_data['pos']
            if pos:
                x_coords = [c[0] for c in pos.values()]
                y_coords = [c[1] for c in pos.values()]
                margin = 2
                self.current_xlim = (min(x_coords) - margin, max(x_coords) + margin)
                self.current_ylim = (min(y_coords) - margin, max(y_coords) + margin)
                self.graph_ax.set_xlim(self.current_xlim)
                self.graph_ax.set_ylim(self.current_ylim)
                self.graph_canvas.draw()
    
    def _apply_zoom(self):
        """Aplica o nível de zoom atual"""
        if not hasattr(self, 'current_xlim') or not self.current_xlim:
            return
        
        center_x = (self.current_xlim[0] + self.current_xlim[1]) / 2
        center_y = (self.current_ylim[0] + self.current_ylim[1]) / 2
        
        width = (self.current_xlim[1] - self.current_xlim[0]) / self.zoom_level
        height = (self.current_ylim[1] - self.current_ylim[0]) / self.zoom_level
        
        self.graph_ax.set_xlim(center_x - width/2, center_x + width/2)
        self.graph_ax.set_ylim(center_y - height/2, center_y + height/2)
        self.graph_canvas.draw()
    
    def _on_scroll(self, event):
        """Handler para scroll do mouse (zoom)"""
        if event.inaxes != self.graph_ax:
            return
        
        if event.button == 'up':
            self.zoom_level *= 1.1
        elif event.button == 'down':
            self.zoom_level /= 1.1
        
        self._apply_zoom()
    
    def _on_press(self, event):
        """Handler para botão do mouse pressionado (iniciar pan)"""
        if event.inaxes != self.graph_ax or event.button != 1:
            return
        self.pan_start = (event.xdata, event.ydata)
    
    def _on_release(self, event):
        """Handler para botão do mouse solto (finalizar pan)"""
        self.pan_start = None
    
    def _on_hover(self, event):
        """Handler para movimento do mouse (mostrar tooltips)"""
        if not hasattr(self, 'current_graph_data') or not self.current_graph_data:
            return
        
        # Pan se estiver arrastando
        if self.pan_start and event.xdata and event.ydata:
            dx = event.xdata - self.pan_start[0]
            dy = event.ydata - self.pan_start[1]
            
            xlim = self.graph_ax.get_xlim()
            ylim = self.graph_ax.get_ylim()
            
            self.graph_ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
            self.graph_ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
            
            self.current_xlim = self.graph_ax.get_xlim()
            self.current_ylim = self.graph_ax.get_ylim()
            
            self.graph_canvas.draw()
            return
        
        # Tooltip ao passar o mouse
        if event.inaxes != self.graph_ax or not event.xdata or not event.ydata:
            self._clear_tooltips()
            return
        
        pos = self.current_graph_data['pos']
        labels = self.current_graph_data['labels']
        colors = self.current_graph_data['colors']
        
        # Encontrar nó mais próximo
        min_dist = float('inf')
        closest_node = None
        
        for node, (x, y) in pos.items():
            dist = ((event.xdata - x)**2 + (event.ydata - y)**2)**0.5
            if dist < min_dist and dist < 1.0:  # Threshold de proximidade
                min_dist = dist
                closest_node = node
        
        if closest_node:
            self._show_tooltip(closest_node, pos[closest_node], labels[closest_node], colors[closest_node])
        else:
            self._clear_tooltips()
    
    def _show_tooltip(self, node, pos, label, node_type):
        """Mostra tooltip com informações do nó"""
        self._clear_tooltips()
        
        x, y = pos
        style = self.node_styles.get(node_type, self.node_styles['table'])
        
        # Criar tooltip estilizado
        tooltip_text = f"{style['label']}\n{label}"
        
        bbox_props = dict(
            boxstyle='round,pad=0.5',
            facecolor='#2c3e50',
            edgecolor=style['c'],
            alpha=0.95,
            linewidth=2
        )
        
        annotation = self.graph_ax.annotate(
            tooltip_text,
            xy=(x, y),
            xytext=(15, 15),
            textcoords='offset points',
            fontsize=10,
            color='white',
            fontweight='bold',
            bbox=bbox_props,
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0.3',
                color=style['c'],
                linewidth=2
            ),
            zorder=1000
        )
        
        self.current_node_annotations.append(annotation)
        self.graph_canvas.draw_idle()
    
    def _clear_tooltips(self):
        """Remove todos os tooltips ativos"""
        for annotation in self.current_node_annotations:
            annotation.remove()
        self.current_node_annotations = []
        self.graph_canvas.draw_idle()
    
    def limpar_campos(self): 
        self.sql_entry.delete("1.0", tk.END)
        self.limpar_resultados()
    
    def limpar_resultados(self):
        for widget in [self.validação_sql_text, self.álgebra_relacional_text, self.plano_de_execução_text]:
            widget.delete("1.0", tk.END)
        self.current_sql = None
        self.current_graph_data = None
        self.graph_ax.clear()
        self.graph_ax.axis('off')
        self.graph_ax.text(0.5, 0.5, 'Interface limpa. Aguardando nova consulta.\n\n💡 Use os controles acima para interagir com o grafo', 
                          ha='center', va='center', fontsize=12, color='gray', style='italic')
        self.graph_canvas.draw()
        
    def _generate_optimized_execution_plan(self):
        """
        Gera um plano de execução textual FIEL à árvore otimizada,
        percorrendo-a em pós-ordem.
        """
        plan = f"PLANO DE EXECUÇÃO OTIMIZADO PARA:\n{self.current_sql}\n{'='*80}\n\n"
        
        steps = []
        node_results = {}
        
        def post_order_traversal(tree_node):
            if isinstance(tree_node, str):
                node_id = f"Tabela_{tree_node}"
                steps.append(f"Acessar a tabela base '{tree_node}'.")
                node_results[id(tree_node)] = node_id
                return node_id
            
            op = tree_node[0]
            
            if op in ['π', 'σ', 'ρ']:
                child_result = post_order_traversal(tree_node[2])
                step_num = len(steps) + 1
                
                if op == 'π':
                    desc = f"PROJEÇÃO (π): Selecionar as colunas: {self._wrap_label(tree_node[1], 50)}"
                    steps.append(f"{step_num}. {desc} do resultado de [{child_result}].")
                elif op == 'σ':
                    desc = f"SELEÇÃO (σ): Aplicar o filtro: {self._wrap_label(tree_node[1], 50)}"
                    steps.append(f"{step_num}. {desc} sobre o resultado de [{child_result}].")
                elif op == 'ρ':
                    desc = f"RENOMEAR (ρ): Acessar '{tree_node[2]}' e apelidar como '{tree_node[1]}'"
                    steps.append(f"{step_num}. {desc}.")
                    child_result = f"Tabela_{tree_node[2]}"
                
                result_id = f"Passo_{step_num}"
                node_results[id(tree_node)] = result_id
                return result_id
            
            elif op == '⨝':
                left_result = post_order_traversal(tree_node[2])
                right_result = post_order_traversal(tree_node[3])
                step_num = len(steps) + 1
                
                desc = f"JUNÇÃO (JOIN): Unir os resultados de [{left_result}] e [{right_result}]"
                cond = f"   - Condição: {tree_node[1]}"
                algo = "   - Algoritmo: Hash Join (preferencial)"
                steps.append(f"{step_num}. {desc}\n{cond}\n{algo}")

                result_id = f"Passo_{step_num}"
                node_results[id(tree_node)] = result_id
                return result_id
            return "Nó desconhecido"

        post_order_traversal(self.current_optimized_tree)
        plan += "\n".join(steps)
        plan += f"\n\n{len(steps) + 1}. RESULTADO FINAL: Retornar o resultado do último passo."
        return plan

def main():
    root = tk.Tk()
    app = ProcessadorConsultasGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()