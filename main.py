import query_processor


def main():
    process = query_processor.QueryProcessor()

    
    test_queries = [
    # Categoria 1: Repetição Direta de Palavras-Chave
    # Objetivo: Verificar se o parser rejeita a duplicação de cláusulas estruturais.
    'SELECT SELECT Nome, Email FROM cliente;',        # "SELECT" duplicado
    'SELECT * FROM FROM cliente;',                    # "FROM" duplicado
    'SELECT * FROM cliente WHERE WHERE Nome = "A";',    # "WHERE" duplicado
    'SELECT * FROM cliente INNER JOIN INNER JOIN produto ON cliente.id = produto.id;', # "INNER JOIN" duplicado
    'SELECT * FROM cliente INNER JOIN produto ON ON cliente.id = produto.id;',       # "ON" duplicado

    # Categoria 2: Palavras-Chave Usadas como Nomes (Identificadores)
    # Objetivo: Garantir que o parser não confunda uma palavra-chave com um nome de coluna ou tabela.
    'SELECT Nome, FROM, Email FROM cliente;',        # "FROM" como se fosse uma coluna
    'SELECT WHERE FROM cliente;',                    # "WHERE" como se fosse uma coluna
    'SELECT * FROM SELECT;',                         # "SELECT" como se fosse uma tabela
    'SELECT * FROM cliente INNER JOIN WHERE ON cliente.id = WHERE.id;', # "WHERE" como se fosse uma tabela de join
    'SELECT * FROM cliente WHERE Nome = SELECT;',      # "SELECT" como se fosse um valor na cláusula WHERE

    # Categoria 3: Ordem e Estrutura Completamente Quebradas
    # Objetivo: Testar a rigidez da regex principal contra uma ordem ilógica de palavras-chave.
    'SELECT FROM WHERE;',                            # Cláusulas sem conteúdo entre elas
    'FROM cliente SELECT *;',                        # Ordem das cláusulas invertida
    'SELECT * cliente FROM;',                        # Ordem de tabela e FROM invertida
    'SELECT Nome FROM cliente ON idCliente = 1;',    # Cláusula ON sem um INNER JOIN
    'SELECT * FROM cliente WHERE INNER JOIN produto ON cliente.id = produto.id;', # Cláusula JOIN dentro da WHERE

    # Categoria 4: Operadores e Estruturas Malformadas
    # Objetivo: Testar a validação de tokens e a lógica interna das cláusulas.
    'SELECT * FROM cliente WHERE Nome >> "A";',       # Operador totalmente inválido
    'SELECT * FROM cliente WHERE Preco > > 50;',     # Operador duplicado
    'SELECT Nome, (Email) FROM cliente;',            # Parênteses em volta de uma coluna (seu parser pode ou não aceitar)
    'SELECT * FROM cliente WHERE Nome = "A" AND OR Email = "B";', # Operadores lógicos conflitantes
]

    # Itera sobre cada consulta da lista de testes
    for query in test_queries:
        print(f"Consulta SQL: {query}")
        is_valid = process.validate_query(query)
        print(f"  -> Consulta válida: {is_valid}\n")


if __name__ == "__main__":
    main()