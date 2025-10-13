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
        
        # ===== QUERIES MAIS DIFÍCEIS E COMPLEXAS =====
        
        # Teste de ambiguidade de colunas (sem qualificar tabela)
        "SELECT Nome FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria;",  # Deve detectar ambiguidade se ambas tabelas tem 'Nome'
        
        # WHERE com múltiplas condições complexas
        "SELECT produto.Nome, produto.Preco FROM produto WHERE Preco > 50 AND QuantEstoque < 100 AND Preco < 500;",
        "SELECT cliente.Nome, cliente.Email FROM cliente WHERE Nome LIKE 'João' OR Email LIKE 'gmail.com';",
        
        # WHERE com strings contendo palavras-chave SQL
        "SELECT * FROM produto WHERE Nome = 'WHERE';",  # String contém palavra-chave
        "SELECT * FROM categoria WHERE Descricao = 'SELECT AND OR';",
        
        # JOIN com WHERE complexo usando colunas de ambas tabelas
        "SELECT produto.Nome, categoria.Descricao FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria WHERE produto.Preco > 100 AND categoria.Descricao = 'Eletrônicos';",
        
        # WHERE com operadores IN e NOT
        "SELECT Nome FROM produto WHERE QuantEstoque IN 10 OR QuantEstoque IN 20;",
        "SELECT * FROM cliente WHERE NOT Nome = 'João Silva';",
        
        # Colunas qualificadas desnecessariamente (mas válidas)
        "SELECT cliente.Nome, cliente.Email, cliente.Telefone FROM cliente;",
        
        # JOIN ON com expressões complexas
        "SELECT produto.Nome FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.idCategoria AND categoria.Descricao = 'Eletrônicos';",
        
        # Teste de espaços extras e formatação estranha
        "SELECT    Nome   ,   Email   FROM   cliente   WHERE   Nome   =   'João'  ;",
        "SELECT produto.Nome,produto.Preco,produto.QuantEstoque FROM produto WHERE Preco>50;",  # Sem espaços
        
        # ===== QUERIES COM ERROS PARA TESTAR VALIDAÇÃO =====
        
        # Coluna inexistente
        "SELECT Nome, ColunaInexistente FROM produto;",
        "SELECT * FROM cliente WHERE CampoInvalido = 'teste';",
        
        # Tabela qualificada incorretamente
        "SELECT tabela_errada.Nome FROM produto;",
        "SELECT produto.ColunaErrada FROM produto;",
        
        # Ambiguidade sem JOIN (deve funcionar se só uma tabela tem a coluna)
        "SELECT idCliente FROM cliente;",  # OK
        
        # JOIN com coluna errada no ON
        "SELECT produto.Nome FROM produto INNER JOIN categoria ON produto.ColunaErrada = categoria.idCategoria;",
        "SELECT produto.Nome FROM produto INNER JOIN categoria ON produto.Categoria_idCategoria = categoria.ColunaErrada;",
        
        # WHERE com coluna de tabela não incluída na query
        "SELECT Nome FROM produto WHERE categoria.Descricao = 'Eletrônicos';",  # categoria não está no FROM
        
        # Sintaxes totalmente erradas
        "SELECT * FROM tabela_inexistente;",
        "SELECT nome clientes;",  # Sem FROM
        "SELECT * FROM cliente INNER JOIN inexistente ON cliente.idCliente = inexistente.id;",
        "SELECT FROM cliente;",  # Sem colunas
        "SELECT * cliente;",  # Sem FROM
        "SELECIONAR * FROM cliente;",  # Palavra-chave errada
        
        # Edge cases com números e strings
        "SELECT Nome FROM produto WHERE Preco > 'texto';",  # Tipo errado mas sintaxe OK
        "SELECT * FROM produto WHERE QuantEstoque = 100;",  # OK
        "SELECT Nome FROM produto WHERE Nome = '123';",  # OK
    ]

    for query in test_queries:
        process.validate_query(query)
        

if __name__ == "__main__":
    main()
