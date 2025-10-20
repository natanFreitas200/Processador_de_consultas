from conversor import RelationalAlgebraConverter
from query_processor import QueryProcessor


def test_query_processor():
    """Mantém o teste original que valida várias consultas (possíveis inválidas)
    usando a classe QueryProcessor do módulo `query_processor.py`.
    """
    process = QueryProcessor()

    test_queries = [
        'SELECT SELECT Nome, Email FROM Cliente;',
        'SELECT * FROM FROM Cliente;',
        'SELECT * FROM Cliente WHERE WHERE Nome = "A";',
        'SELECT * FROM Cliente INNER JOIN INNER JOIN Produto ON Cliente.id = Produto.id;',
        'SELECT * FROM Cliente INNER JOIN Produto ON ON Cliente.id = Produto.id;',

        'SELECT Nome, FROM, Email FROM Cliente;',
        'SELECT WHERE FROM Cliente;',
        'SELECT * FROM SELECT;',
        'SELECT * FROM Cliente INNER JOIN WHERE ON Cliente.id = WHERE.id;',
        'SELECT * FROM Cliente WHERE Nome = SELECT;',

        'SELECT FROM WHERE;',
        'FROM Cliente SELECT *;',
        'SELECT * Cliente FROM;',
        'SELECT Nome FROM Cliente ON idCliente = 1;',
        'SELECT * FROM Cliente WHERE INNER JOIN Produto ON Cliente.id = Produto.id;',

        'SELECT * FROM Cliente WHERE Nome >> "A";',
        'SELECT * FROM Cliente WHERE Preco > > 50;',
        'SELECT Nome, (Email) FROM Cliente;',
        'SELECT * FROM Cliente WHERE Nome = "A" AND OR Email = "B";',
    ]

    for query in test_queries:
        print(f"Consulta SQL: {query}")
        result = process.validate_query(query)

        # A API de validate_query pode retornar bool ou (bool, message)
        if isinstance(result, tuple):
            is_valid, msg = result
        else:
            is_valid = bool(result)
            msg = "Consulta válida" if is_valid else "Consulta inválida"

        print(f"  -> Consulta válida: {is_valid} {msg}\n")


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
    # Primeiro mantém os testes de validação originais
    test_query_processor()

    # Em seguida executa os testes do conversor
    test_converter()


if __name__ == "__main__":
    main()