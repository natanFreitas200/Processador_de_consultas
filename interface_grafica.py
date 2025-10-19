import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import filedialog
import threading
import os

from query_processor import QueryProcessor
from conversor import RelationalAlgebraConverter


class ProcessadorConsultasGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Consultas SQL - Álgebra Relacional")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar processadores
        try:
            self.query_processor = QueryProcessor()
        except Exception as e:
            self.query_processor = None
            print(f"Aviso: QueryProcessor não pôde ser inicializado: {e}")
            
        self.converter = RelationalAlgebraConverter()
        
        self.setup_interface()
        
    def setup_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Processador de Consultas SQL", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame de entrada
        input_frame = ttk.LabelFrame(main_frame, text="Entrada da Consulta SQL", padding="10")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        # Campo de entrada SQL
        ttk.Label(input_frame, text="Digite sua consulta SQL:").grid(row=0, column=0, sticky=tk.W)
        
        self.sql_entry = scrolledtext.ScrolledText(input_frame, height=4, width=70, 
                                                  wrap=tk.WORD, font=('Courier New', 10))
        self.sql_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Frame de botões
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, pady=(0, 5))
        
        # Botões
        ttk.Button(button_frame, text="Validar Consulta", 
                  command=self.validar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Processar Consulta", 
                  command=self.processar_consulta).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Limpar", 
                  command=self.limpar_campos).pack(side=tk.LEFT, padx=(0, 5))
        
        # Notebook para abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Aba 1: Resultados de Validação
        self.setup_validation_tab()
        
        # Aba 2: Álgebra Relacional
        self.setup_algebra_tab()
        
        # Aba 3: Grafo Visual
        self.setup_graph_tab()
        
        # Aba 4: Plano de Execução
        self.setup_execution_tab()
        
        # Consultas de exemplo
        self.add_example_queries()
        
    def setup_validation_tab(self):
        # Frame de validação
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
        # Frame de álgebra relacional
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
        # Frame do grafo
        graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(graph_frame, text="Grafo de Operadores")
        
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(1, weight=1)
        
        # Frame superior com botões
        graph_controls = ttk.Frame(graph_frame)
        graph_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(graph_controls, text="Grafo de Operadores (Não Otimizado):", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(graph_controls, text="Gerar Imagem PNG", 
                  command=self.gerar_imagem_grafo).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(graph_controls, text="Abrir Pasta", 
                  command=self.abrir_pasta_imagens).pack(side=tk.RIGHT)
        
        # Área de texto para mostrar a representação textual do grafo
        self.graph_text = scrolledtext.ScrolledText(graph_frame, height=20, 
                                                   font=('Courier New', 10))
        self.graph_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), 
                            padx=10, pady=(0, 10))
        
    def setup_execution_tab(self):
        # Frame do plano de execução
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
        # Adicionar alguns exemplos no campo SQL
        example_sql = """SELECT c.Nome, p.Nome, cat.Descricao
FROM Cliente c
INNER JOIN Pedido ped ON c.idCliente = ped.Cliente_idCliente
INNER JOIN Pedido_has_Produto pp ON ped.idPedido = pp.Pedido_idPedido
INNER JOIN Produto p ON pp.Produto_idProduto = p.idProduto
INNER JOIN Categoria cat ON p.Categoria_idCategoria = cat.idCategoria
WHERE p.Preco > 50 AND cat.Descricao = 'Eletrônicos'"""
        
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
                
                # Validação básica de sintaxe
                if self._basic_syntax_check(sql_query):
                    self.validation_text.insert(tk.END, "✅ Sintaxe básica parece válida.\n")
                    self.validation_text.insert(tk.END, "⚠️ Nota: Validação completa requer conexão com banco de dados.\n")
                else:
                    self.validation_text.insert(tk.END, "❌ Problema de sintaxe detectado.\n")
                return
            
            # Capturar output da validação
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
        """Validação básica de sintaxe SQL"""
        sql_upper = sql_query.upper().strip()
        
        # Verificar se começa com SELECT
        if not sql_upper.startswith("SELECT"):
            return False
            
        # Verificar se tem FROM
        if "FROM" not in sql_upper:
            return False
            
        # Verificar estrutura básica com regex
        import re
        pattern = r"^\s*SELECT\s+.+\s+FROM\s+\w+.*$"
        return bool(re.match(pattern, sql_query, re.IGNORECASE | re.DOTALL))
            
    def processar_consulta(self):
        sql_query = self.sql_entry.get("1.0", tk.END).strip()
        
        if not sql_query:
            messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL.")
            return
            
        # Executar processamento em thread separada para não travar a GUI
        threading.Thread(target=self._processar_consulta_thread, args=(sql_query,), daemon=True).start()
        
    def _processar_consulta_thread(self, sql_query):
        try:
            # 1. Converter para álgebra relacional
            self.root.after(0, lambda: self.algebra_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "Processando consulta...\n"))
            
            algebra_expression = self.converter.convert(sql_query)
            
            self.root.after(0, lambda: self.algebra_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"Consulta SQL Original:\n{sql_query}\n\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, "=== ÁLGEBRA RELACIONAL (NÃO OTIMIZADA) ===\n"))
            self.root.after(0, lambda: self.algebra_text.insert(tk.END, f"{algebra_expression}\n\n"))
            
            # 2. Gerar representação textual do grafo
            tree_representation = self._generate_tree_text(sql_query)
            self.root.after(0, lambda: self.graph_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.graph_text.insert(tk.END, tree_representation))
            
            # 4. Gerar plano de execução
            execution_plan = self._generate_execution_plan(sql_query)
            self.root.after(0, lambda: self.execution_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.execution_text.insert(tk.END, execution_plan))
            
            # 5. Mudar para a aba do grafo
            self.root.after(0, lambda: self.notebook.select(2))
            
        except Exception as e:
            error_msg = f"Erro durante o processamento: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
            
    def _generate_tree_text(self, sql_query):
        """Gera uma representação textual da árvore de álgebra relacional"""
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
        """Converte árvore em representação textual indentada"""
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
        """Gera um plano de execução baseado na consulta"""
        try:
            plan = f"PLANO DE EXECUÇÃO PARA: {sql_query}\n"
            plan += "=" * 60 + "\n\n"
            
            # Parse da consulta para extrair componentes
            parsed = self.converter._parse_sql(sql_query)
            if not parsed:
                return "Erro: Não foi possível gerar o plano de execução."
                
            step = 1
            plan += "ETAPAS DE EXECUÇÃO (Ordem Bottom-Up):\n\n"
            
            # Identificar tabelas
            from_clause = parsed.get('from_clause', '')
            base_table_info, joins = self.converter._parse_from_clause(from_clause)
            
            if base_table_info:
                plan += f"{step}. SCAN da tabela base: {base_table_info.get('table')}\n"
                plan += f"   → Operação: Leitura sequencial da tabela\n"
                plan += f"   → Resultado: Todas as tuplas de {base_table_info.get('table')}\n\n"
                step += 1
            
            # JOINs
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
            
            # WHERE clause
            where_clause = parsed.get('where')
            if where_clause:
                plan += f"{step}. SELEÇÃO (σ) - Filtro WHERE\n"
                plan += f"   → Condição: {where_clause}\n"
                plan += f"   → Operação: Aplicar predicados de seleção\n"
                plan += f"   → Resultado: Tuplas que satisfazem WHERE\n\n"
                step += 1
            
            # SELECT clause
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
    
    def gerar_imagem_grafo(self):
        """Gera uma imagem PNG do grafo usando o conversor"""
        try:
            sql_query = self.sql_entry.get("1.0", tk.END).strip()
            
            if not sql_query:
                messagebox.showwarning("Aviso", "Por favor, digite uma consulta SQL primeiro.")
                return
            
            # Gerar imagem
            timestamp = str(int(threading.current_thread().ident))
            filename = f"grafo_consulta_{timestamp}.png"
            
            self.converter.generate_image_graph(sql_query, filename)
            
            messagebox.showinfo("Sucesso", f"Imagem do grafo gerada: {filename}\n\nA imagem foi salva na pasta do projeto.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar imagem: {str(e)}")
    
    def abrir_pasta_imagens(self):
        """Abre a pasta atual onde estão as imagens geradas"""
        try:
            current_dir = os.getcwd()
            os.startfile(current_dir)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir pasta: {str(e)}")
    
    def limpar_campos(self):
        self.sql_entry.delete("1.0", tk.END)
        self.validation_text.delete("1.0", tk.END)
        self.algebra_text.delete("1.0", tk.END)
        self.execution_text.delete("1.0", tk.END)
        self.graph_text.delete("1.0", tk.END)


def main():
    root = tk.Tk()
    app = ProcessadorConsultasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()