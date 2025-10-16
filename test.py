from conversor import RelationalAlgebraConverter

def main():
    converter = RelationalAlgebraConverter()

    test_queries = [
        "SELECT Nome, Email FROM cliente;",
        "SELECT * FROM produto;",
        "SELECT Nome, Preco FROM produto WHERE Preco > 50;",
        "SELECT produto.Nome, categoria.Descricao FROM produto INNER JOIN categoria ON produto.Categoria_id = categoria.id WHERE produto.Preco > 100 AND categoria.Nome = 'Tech';",
        "SELECT * FROM funcionarios WHERE (Salario > 5000 AND Depto = 'TI') OR Cargo = 'Gerente';",
    ]

    print("--- Iniciando Teste Isolado do Conversor (Sem Banco de Dados) ---\n")

    for query in test_queries:
        print(f"SQL Original: {query}")
        
        resultado_algebra = converter.convert(query)
        
        print(f"Álgebra Rel.: {resultado_algebra}")
        print("-" * 60)

if __name__ == "__main__":
    main()