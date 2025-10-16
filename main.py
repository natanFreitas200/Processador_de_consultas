import query_processor


def main():
    process = query_processor.QueryProcessor()

    
    test_queries = [
        "SELECT * FROM cliente;",
        "SELECT Nome, Email FROM cliente;",
        "SELECT * FROM produto;",
        "SELECT Nome, Preco FROM produto;",

        "SELECT Nome, Preco FROM produto WHERE Preco > 50;",
        "SELECT Nome, QuantEstoque FROM produto WHERE QuantEstoque < 100;",
        "SELECT * FROM pedido WHERE Status_idStatus = 1;",

        "SELECT produto.Nome, categoria.Descricao FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria;",
        "SELECT pedido.idPedido, cliente.Nome FROM pedido INNER JOIN cliente ON pedido.Cliente_idCliente = cliente.idCliente;",
        "SELECT produto.Nome, pedido_has_produto.Quantidade FROM pedido_has_produto INNER JOIN produto ON pedido_has_produto.Produto_idProduto = produto.idProduto;",

        "SELECT produto.Nome, produto.Preco FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria WHERE categoria.Descricao = 'Eletrônicos';",
        "SELECT pedido.idPedido, pedido.ValorTotalPedido FROM pedido INNER JOIN cliente ON pedido.Cliente_idCliente = cliente.idCliente WHERE cliente.Nome = 'João Silva';",

        "SELECT cliente.Nome, produto.Nome, pedido.DataPedido FROM pedido INNER JOIN cliente ON pedido.Cliente_idCliente = cliente.idCliente INNER JOIN pedido_has_produto ON pedido.idPedido = pedido_has_produto.Pedido_idPedido INNER JOIN produto ON pedido_has_produto.Produto_idProduto = produto.idProduto;",

        "SELECT c.Nome, p.ValorTotalPedido FROM cliente AS c INNER JOIN pedido AS p ON c.idCliente = p.Cliente_idCliente;",
        "SELECT prod.Nome FROM produto prod WHERE prod.Preco > 100;",

        "SELECT * FROM produto WHERE (Preco > 100 AND QuantEstoque < 50) OR (Preco < 20);",

        "SELECT Categoria_idCategoria, COUNT(*) FROM produto GROUP BY Categoria_idCategoria;",
        "SELECT Categoria_idCategoria, AVG(Preco) FROM produto GROUP BY Categoria_idCategoria HAVING AVG(Preco) > 200;",

        "SELECT Nome FROM produto WHERE Categoria_idCategoria IN (SELECT idCategoria FROM categoria WHERE Descricao = 'Importados');",
        "SELECT * FROM pedido WHERE Cliente_idCliente = (SELECT idCliente FROM cliente WHERE Nome = 'Maria Souza');",

        "SELECT Nome, Preco FROM produto ORDER BY Preco DESC;",
        "SELECT * FROM cliente ORDER BY Nome ASC LIMIT 10;",

        "SELECT Nome, Email, FROM cliente;",
        "SELECT Nome FROM produto WHERE Preco > 50 AND;",

        "SELECT c.Nome FROM cliente AS c WHERE cliente.Nome = 'José';",

        "SELECT * FROM produto INNER JOIN categoria;",

        "SELECT Nome, COUNT(*) FROM produto GROUP BY Categoria_idCategoria;",

        "SELECT * FROM produto HAVING AVG(Preco) > 100;",

        "SELECT * FROM produto WHERE Preco =< 100;",

        "SELECT Nome, -- Comentário ignorado\n Preco FROM produto;",

        "SELECT Nome FROM cliente UNION SELECT Nome FROM produto;",

        "SELECT id FROM cliente INNER JOIN pedido ON cliente.idCliente = pedido.Cliente_idCliente;",

        "SELECT cliente.Nome, pedido.idPedido FROM cliente, pedido WHERE cliente.idCliente = pedido.Cliente_idCliente;",

        "SELECT Preco * 2 AS PrecoDobrado FROM produto WHERE PrecoDobrado > 100;",
        "SELECT * FROM produto WHERE COUNT(*) > 10;",
    ]

    # Itera sobre cada consulta da lista de testes
    for query in test_queries:
        print(f"Consulta SQL: {query}")
        is_valid = process.validate_query(query)
        print(f"  -> Consulta válida: {is_valid}\n")


if __name__ == "__main__":
    main()