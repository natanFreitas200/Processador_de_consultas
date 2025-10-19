from conversor import RelationalAlgebraConverter

def test_converter():
    converter = RelationalAlgebraConverter()
    
    test_queries = [
        "SELECT Nome, Email FROM cliente;",
        "SELECT * FROM produto;",
        "SELECT Nome, Preco FROM produto WHERE Preco > 50;",
        "SELECT produto.Nome, categoria.Descricao FROM produto INNER JOIN categoria ON produto.Categoria_id = categoria.id WHERE produto.Preco > 100 AND categoria.Nome = 'Tech';",
        "SELECT * FROM funcionarios WHERE (Salario > 5000 AND Depto = 'TI') OR Cargo = 'Gerente';",
        "SELECT c.Nome, p.Preco FROM Cliente c INNER JOIN Pedido ped ON c.id = ped.cliente_id INNER JOIN Produto p ON ped.produto_id = p.id",
        "SELECT Nome FROM Cliente WHERE idade > 25 AND cidade = 'Sao Paulo'"
    ]
    
    print("=== TESTE DO CONVERSOR DE ALGEBRA RELACIONAL ===")
    print("--- Iniciando Teste Isolado do Conversor (Sem Banco de Dados) ---\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Teste {i}:")
        print(f"SQL Original: {query}")
        
        is_valid, message = converter.validate_sql_syntax(query)
        print(f"Validacao: {'OK' if is_valid else 'FALHA'} {message}")
        
        if is_valid:
            try:
                resultado_algebra = converter.convert(query)
                print(f"Algebra Rel.: {resultado_algebra}")
            except Exception as e:
                print(f"Erro na conversao: {e}")
        
        print("-" * 60)
        print()

def main():
    test_converter()

if __name__ == "__main__":
    main()