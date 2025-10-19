import query_processor


def main():
    process = query_processor.QueryProcessor()

    
    test_queries = [
    'SELECT SELECT Nome, Email FROM cliente;',
    'SELECT * FROM FROM cliente;',
    'SELECT * FROM cliente WHERE WHERE Nome = "A";',
    'SELECT * FROM cliente INNER JOIN INNER JOIN produto ON cliente.id = produto.id;',
    'SELECT * FROM cliente INNER JOIN produto ON ON cliente.id = produto.id;',

    'SELECT Nome, FROM, Email FROM cliente;',
    'SELECT WHERE FROM cliente;',
    'SELECT * FROM SELECT;',
    'SELECT * FROM cliente INNER JOIN WHERE ON cliente.id = WHERE.id;',
    'SELECT * FROM cliente WHERE Nome = SELECT;',

    'SELECT FROM WHERE;',
    'FROM cliente SELECT *;',
    'SELECT * cliente FROM;',
    'SELECT Nome FROM cliente ON idCliente = 1;',
    'SELECT * FROM cliente WHERE INNER JOIN produto ON cliente.id = produto.id;',

    'SELECT * FROM cliente WHERE Nome >> "A";',
    'SELECT * FROM cliente WHERE Preco > > 50;',
    'SELECT Nome, (Email) FROM cliente;',
    'SELECT * FROM cliente WHERE Nome = "A" AND OR Email = "B";',
]

    for query in test_queries:
        print(f"Consulta SQL: {query}")
        is_valid = process.validate_query(query)
        print(f"  -> Consulta válida: {is_valid}\n")


if __name__ == "__main__":
    main()