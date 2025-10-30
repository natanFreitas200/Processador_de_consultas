import query_processor


def main():
    process = query_processor.QueryProcessor()

    test_queries = [
        "SELECT SELECT Nome FROM Cliente;",
        "SELECT * FROM FROM Cliente;",
        "SELECT * FROM Cliente WHERE WHERE Nome = 'A';",
        "FROM Cliente SELECT *;",
        "SELECT Nome Cliente;",
        "SELECT * FROM Cliente Nome = 'A';",
        "SELECT FROM WHERE;",
        "SELECT * FROM;",

        "SELECT Nome, , Email FROM Cliente;",
        "SELECT Nome Email FROM Cliente;",
        "SELECT FROM Cliente;",
        "SELECT Nome, FROM FROM Cliente;",

        "SELECT * FROM Cliente INNER JOIN INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente;",
        "SELECT * FROM Cliente INNER JOIN Pedido ON ON Cliente.idCliente = Pedido.Cliente_idCliente;",
        "SELECT * FROM Cliente INNER JOIN Pedido;",
        "SELECT * FROM Cliente ON idCliente = 1;",
        "SELECT * FROM Cliente WHERE INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente;",

        "SELECT * FROM Cliente WHERE Nome >> 'A';",
        "SELECT * FROM Cliente WHERE Preco > > 50;",
        "SELECT * FROM Cliente WHERE Nome = 'A' AND;",
        "SELECT * FROM Cliente WHERE Nome = 'A' AND OR Email = 'B';",
        "SELECT * FROM Cliente WHERE (Nome = 'A';",

        "SELECT WHERE FROM Cliente;",
        "SELECT * FROM SELECT;",
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