import query_processor


def main():
    process = query_processor.QueryProcessor()

    
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
        is_valid = process.validate_query(query)
        print(f"  -> Consulta válida: {is_valid}\n")


if __name__ == "__main__":
    main()