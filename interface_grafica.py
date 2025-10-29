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
            'join':       {'c': '#c0392b', 'ico': 'JOIN', 'label': 'Junção'},
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
        graph_controls = ttk.Frame(graph_frame); graph_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        graph_controls.columnconfigure(0, weight=1)
        ttk.Label(graph_controls, text="Visualização do Grafo:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        radio_frame = ttk.Frame(graph_controls); radio_frame.grid(row=0, column=1, sticky=tk.E)
        ttk.Radiobutton(radio_frame, text="Otimizado", variable=self.graph_view_var, value="optimized", command=self.atualizar_grafo_visual).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Radiobutton(radio_frame, text="Não Otimizado", variable=self.graph_view_var, value="unoptimized", command=self.atualizar_grafo_visual).pack(side=tk.RIGHT, padx=(5, 0))
        canvas_frame = ttk.Frame(graph_frame, style='TFrame'); canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1); canvas_frame.rowconfigure(0, weight=1)
        self.graph_fig = plt.Figure(figsize=(10, 8), facecolor='#f0f0f0'); self.graph_ax = self.graph_fig.add_subplot(111, facecolor='#f0f0f0'); self.graph_ax.axis('off')
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=canvas_frame); self.graph_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.graph_ax.text(0.5, 0.5, 'Processar uma consulta para visualizar o grafo.', ha='center', va='center', transform=self.graph_ax.transAxes, fontsize=14, color='gray')
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
            self.graph_ax.clear(); self.graph_ax.axis('off')
            is_opt = self.graph_view_var.get() == "optimized"; tree = self.current_optimized_tree if is_opt else self.current_unoptimized_tree
            title_suffix, badge_color = ("OTIMIZADA", self.node_styles['selection']['c']) if is_opt else ("NÃO OTIMIZADA", self.node_styles['join']['c'])
            G = nx.DiGraph(); self.converter.node_counter = 0; pos_dict, colors, labels, shapes = {}, {}, {}, {}
            root_id = self.converter._add_nodes_to_graph(tree, G, pos_dict, colors, labels, shapes)
            pos = self.converter._calculate_improved_positions(G, root_id)
            self._desenhar_grafo_integrado(G, pos, colors, labels, self.current_sql, title_suffix, badge_color)
            self.graph_canvas.draw()
        except Exception as e: self.graph_ax.clear(); self.graph_ax.text(0.5, 0.5, f'Erro ao gerar grafo:\n{e}', ha='center', va='center', color='red'); self.graph_ax.axis('off'); self.graph_canvas.draw()

    def _darken_color(self, hex_color, factor=0.7):
        hex_color = hex_color.lstrip('#'); rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"#{''.join([f'{int(c*factor):02x}' for c in rgb])}"

    def _desenhar_texto_com_sombra(self, x, y, text, **kwargs):
        props = kwargs.copy(); zorder = props.pop('zorder', 5); self.graph_ax.text(x+0.008, y-0.008, text, **props, color='#2c3e50', zorder=zorder-1); self.graph_ax.text(x, y, text, **props, color='white', zorder=zorder)

    def _desenhar_grafo_integrado(self, G, pos, node_colors, node_labels, sql_query, title_suffix, badge_color):
        for node in G.nodes():
            x, y = pos[node]; node_type = node_colors.get(node, 'table'); style = self.node_styles[node_type]; label = node_labels.get(node, ''); edge_color = self._darken_color(style['c'])
            shape = {'projection': 'circle', 'join': 'diamond'}.get(node_type, 'rect')
            if shape == 'circle':
                r=0.55; self.graph_ax.add_patch(patches.Circle((x+0.07, y-0.07), r, fc='black', alpha=0.15)); self.graph_ax.add_patch(patches.Circle((x,y), r, fc=style['c'], ec=edge_color, lw=2, zorder=3))
            elif shape == 'diamond':
                h, w = 0.75, 0.75; points = [[x,y+h],[x+w,y],[x,y-h],[x-w,y]]; self.graph_ax.add_patch(patches.Polygon([[p[0]+0.07, p[1]-0.07] for p in points], fc='black', alpha=0.15)); self.graph_ax.add_patch(patches.Polygon(points, fc=style['c'], ec=edge_color, lw=2, zorder=3))
            else:
                w,h=1.6,1.0; self.graph_ax.add_patch(patches.FancyBboxPatch((x-w/2+0.07,y-h/2-0.07), w,h, boxstyle="round,pad=0.1", fc='black', alpha=0.15)); self.graph_ax.add_patch(patches.FancyBboxPatch((x-w/2, y-h/2), w,h, boxstyle="round,pad=0.1", fc=style['c'], ec=edge_color, lw=2, zorder=3))
            props={'ha':'center','fontweight':'bold','zorder':5}; icon, details=style['ico'],'\n'.join(label.split('\n')[1:])
            if node_type=='table': self._desenhar_texto_com_sombra(x,y, self._wrap_label(label,15), **{**props,'va':'center','fontsize':11})
            else: self._desenhar_texto_com_sombra(x,y+0.15, icon, **{**props,'va':'center','fontsize':14 if node_type=='join' else 18}); self._desenhar_texto_com_sombra(x,y-0.1, self._wrap_label(details,22), **{**props,'va':'top','fontsize':9,'fontweight':'normal'})
        for u, v in G.edges():
            start, end = pos[u], pos[v]; arrow=patches.FancyArrowPatch(start, end, connectionstyle="arc3,rad=0.2", arrowstyle="-|>", mutation_scale=25, color='#34495e', lw=2, zorder=2); self.graph_ax.add_patch(arrow)
        subtitle=f'{sql_query[:70]}{"..."if len(sql_query)>70 else ""}'; self.graph_ax.text(0.5,0.97,f'Grafo de Álgebra Relacional - {title_suffix}',ha='center',va='top',transform=self.graph_ax.transAxes,fontsize=16,fontweight='bold',color='white',bbox=dict(boxstyle="round,pad=0.3",fc=badge_color,ec='white',lw=2))
        self.graph_ax.text(0.5,0.92,subtitle,ha='center',va='top',transform=self.graph_ax.transAxes,fontsize=11,style='italic',color='#34495e'); self._add_legend()
        if pos: x_coords,y_coords=[c[0] for c in pos.values()],[c[1] for c in pos.values()]; self.graph_ax.set_xlim(min(x_coords)-2,max(x_coords)+2); self.graph_ax.set_ylim(min(y_coords)-2,max(y_coords)+2)

    def _add_legend(self):
        items=[{'icon':v['ico'],'c':v['c'],'t':v['label']} for k,v in self.node_styles.items()]; lx,ly=-0.12,0.98; height,width=(len(items)+1)*0.05,0.2
        bg_patch=patches.FancyBboxPatch((lx-0.01,ly-height-0.03),width,height,boxstyle="round,pad=0.02",fc='#fdfefd',ec='#bdc3c7',alpha=0.95,transform=self.graph_ax.transAxes,zorder=10); self.graph_ax.add_patch(bg_patch)
        title_x,icon_x,text_x=lx+(width/2)-0.01,lx+0.03,lx+0.07; self.graph_ax.text(title_x,ly-0.02,'Operadores',transform=self.graph_ax.transAxes,fontsize=11,fontweight='bold',ha='center',va='top',zorder=11)
        for i,item in enumerate(items):
            y_pos=ly-(i+1.5)*0.048; icon_fs=11 if item['icon']=='JOIN' else 14
            self.graph_ax.text(icon_x,y_pos,item['icon'],transform=self.graph_ax.transAxes,fontsize=icon_fs,color=item['c'],ha='center',va='center',fontweight='bold',zorder=11)
            self.graph_ax.text(text_x,y_pos,item['t'],transform=self.graph_ax.transAxes,fontsize=10,ha='left',va='center',zorder=11)

    def _wrap_label(self,text,width):
        words=text.split(); lines,current_line=[],[];
        for word in words:
            if len(' '.join(current_line+[word]))<=width: current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line=[word]
        if current_line: lines.append(' '.join(current_line))
        return '\n'.join(lines[:3])

    def limpar_campos(self): self.sql_entry.delete("1.0", tk.END); self.limpar_resultados()
    def limpar_resultados(self):
        for widget in [self.validação_sql_text, self.álgebra_relacional_text, self.plano_de_execução_text]: widget.delete("1.0", tk.END)
        self.current_sql=None; self.graph_ax.clear(); self.graph_ax.axis('off'); self.graph_ax.text(0.5,0.5,'Interface limpa.',ha='center',va='center',fontsize=14,color='gray'); self.graph_canvas.draw()
        
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