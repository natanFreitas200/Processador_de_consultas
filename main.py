import query_processor


def main():
    process = query_processor.QueryProcessor()

    
    test_queries = [
   "SELECT SELECT Nome FROM Cliente;",              # SELECT repetido
            "SELECT * FROM FROM Cliente;",                   # FROM repetido
            "SELECT * FROM Cliente WHERE WHERE Nome = 'A';", # WHERE repetido
            "FROM Cliente SELECT *;",                        # Ordem incorreta
            "SELECT Nome Cliente;",                          # Falta o FROM
            "SELECT * FROM Cliente Nome = 'A';",             # Falta o WHERE
            "SELECT FROM WHERE;",                            # Apenas palavras-chave
            "SELECT * FROM;",                                # Cláusula FROM vazia
            
            # --- Categoria 2: Erros na Cláusula SELECT ---
            "SELECT Nome, , Email FROM Cliente;",            # Vírgula dupla
            "SELECT Nome Email FROM Cliente;",               # Falta vírgula
            "SELECT FROM Cliente;",                          # Lista de colunas vazia
            "SELECT Nome, FROM FROM Cliente;",               # Palavra-chave no lugar de coluna
            
            # --- Categoria 3: Erros em JOINs ---
            "SELECT * FROM Cliente INNER JOIN INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente;", # JOIN repetido
            "SELECT * FROM Cliente INNER JOIN Pedido ON ON Cliente.idCliente = Pedido.Cliente_idCliente;",       # ON repetido
            "SELECT * FROM Cliente INNER JOIN Pedido;",      # JOIN sem ON
            "SELECT * FROM Cliente ON idCliente = 1;",       # ON sem JOIN
            "SELECT * FROM Cliente WHERE INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente;", # JOIN dentro do WHERE
            
            # --- Categoria 4: Erros na Cláusula WHERE ---
            "SELECT * FROM Cliente WHERE Nome >> 'A';",      # Operador inválido
            "SELECT * FROM Cliente WHERE Preco > > 50;",     # Operador repetido
            "SELECT * FROM Cliente WHERE Nome = 'A' AND;",   # Operador lógico incompleto
            "SELECT * FROM Cliente WHERE Nome = 'A' AND OR Email = 'B';", # Operadores lógicos misturados
            "SELECT * FROM Cliente WHERE (Nome = 'A';",      # Parênteses não fechado
            
            # --- Categoria 5: Uso de Palavras-Chave como Identificadores ---
            "SELECT WHERE FROM Cliente;",                    # Palavra-chave como coluna
            "SELECT * FROM SELECT;",                         # Palavra-chave como tabela
            "SELECT * FROM Cliente WHERE Nome = SELECT;", 
            "SELECT Nome, Email FROM Cliente WHERE TipoCliente_idTipoCliente = 1;",
            "SELECT Nome, Preco FROM Produto WHERE Preco > 50 AND QuantEstoque < 20;",
            "SELECT * FROM Pedido WHERE ValorTotalPedido > 100.00;",
            "SELECT c.Nome, e.Cidade, e.UF FROM Cliente c INNER JOIN Endereco e ON c.idCliente = e.Cliente_idCliente;",
            "SELECT p.Nome AS NomeProduto, cat.Descricao AS Categoria FROM Produto p INNER JOIN Categoria cat ON p.Categoria_idCategoria = cat.idCategoria WHERE p.Preco < 50;",
            "SELECT c.Nome, p.DataPedido FROM Cliente c INNER JOIN Pedido p ON c.idCliente = p.Cliente_idCliente WHERE p.Status_idStatus = 1;",
            "SELECT c.Nome, prod.Nome AS Produto, pp.Quantidade FROM Cliente c INNER JOIN Pedido ped ON c.idCliente = ped.Cliente_idCliente INNER JOIN Pedido_has_Produto pp ON ped.idPedido = pp.Pedido_idPedido INNER JOIN Produto prod ON pp.Produto_idProduto = prod.idProduto;"
]

    for query in test_queries:
        print(f"Consulta SQL: {query}")
        is_valid = process.validate_query(query)
        print(f"  -> Consulta válida: {is_valid}\n")


if __name__ == "__main__":
    main()