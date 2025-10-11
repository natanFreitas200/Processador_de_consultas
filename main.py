# main.py
import query_processor 

def main():
    process = query_processor.QueryProcessor()
    
    test_queries = [
        # Queries básicas com as tabelas que existem no banco real
        "SELECT * FROM cliente;",
        "SELECT Nome, Email FROM cliente;", 
        "SELECT * FROM produto;",
        "SELECT Nome, Preco FROM produto;",
        
        # Queries com WHERE
        "SELECT Nome, Preco FROM produto WHERE Preco > 50;",
        "SELECT Nome, QuantEstoque FROM produto WHERE QuantEstoque < 100;",
        "SELECT * FROM pedido WHERE Status_idStatus = 1;",
        
        # Queries com INNER JOIN
        "SELECT produto.Nome, categoria.Descricao FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria;",
        "SELECT pedido.idPedido, cliente.Nome FROM pedido INNER JOIN cliente ON pedido.Cliente_idCliente = cliente.idCliente;",
        "SELECT produto.Nome, pedido_has_produto.Quantidade FROM pedido_has_produto INNER JOIN produto ON pedido_has_produto.Produto_idProduto = produto.idProduto;",
        
        # Queries com INNER JOIN e WHERE
        "SELECT produto.Nome, produto.Preco FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria WHERE categoria.Descricao = 'Eletrônicos';",
        "SELECT pedido.idPedido, pedido.ValorTotalPedido FROM pedido INNER JOIN cliente ON pedido.Cliente_idCliente = cliente.idCliente WHERE cliente.Nome = 'João Silva';",
        
        # Queries para testar erros
        "SELECT * FROM tabela_inexistente;",
        "SELECT nome clientes;",  # Sintaxe incorreta
        "SELECT * FROM cliente INNER JOIN inexistente ON cliente.idCliente = inexistente.id;"
    ]

    for query in test_queries:
        process.validate_query(query)
        

if __name__ == "__main__":
    main()
