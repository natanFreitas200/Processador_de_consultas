"""
Script de teste para validação de consultas SQL inválidas.
Testa os validadores melhorados para garantir que consultas
incorretas sejam detectadas corretamente.
"""

from conversor import RelationalAlgebraConverter
from query_processor import QueryProcessor

def test_invalid_queries():
    """Testa consultas SQL inválidas para verificar se são detectadas."""
    
    converter = RelationalAlgebraConverter()
    query_processor = QueryProcessor() if QueryProcessor else None
    
    # Lista de consultas inválidas com descrição do erro esperado
    invalid_queries = [
        ("SELECT * FROM Cliente INNER JOIN INNER JOIN Produto ON Cliente.id = Produto.id;",
         "INNER JOIN duplicado"),
        
        ("SELECT * FROM Cliente INNER JOIN Produto ON ON Cliente.id = Produto.id;",
         "ON duplicado"),
        
        ("SELECT * FROM Cliente INNER JOIN WHERE ON Cliente.id = WHERE.id;",
         "WHERE usado como nome de tabela"),
        
        ("SELECT * FROM Cliente WHERE Nome = SELECT;",
         "SELECT usado como valor"),
        
        ("SELECT Nome FROM Cliente ON idCliente = 1;",
         "ON usado sem JOIN"),
        
        ("SELECT * FROM Cliente WHERE INNER JOIN Produto ON Cliente.id = Produto.id;",
         "WHERE antes de JOIN"),
        
        ("SELECT * FROM Cliente WHERE Nome >> \"A\";",
         "Operador inválido >>"),
        
        ("SELECT * FROM Cliente WHERE Preco > > 50;",
         "Operador duplicado > >"),
        
        ("SELECT Nome, (Email) FROM Cliente;",
         "Parênteses incorretos na lista de colunas"),
        
        ("SELECT * FROM Cliente WHERE Nome = \"A\" AND OR Email = \"B\";",
         "Operadores lógicos inválidos AND OR"),
    ]
    
    print("="*80)
    print("TESTE DE VALIDAÇÃO DE CONSULTAS INVÁLIDAS")
    print("="*80)
    print()
    
    passed = 0
    failed = 0
    
    for i, (query, description) in enumerate(invalid_queries, 1):
        print(f"\n{i}. Testando: {description}")
        print(f"   Query: {query}")
        print("-" * 80)
        
        # Testar com o conversor
        is_valid_conv, msg_conv = converter.validate_sql_syntax(query)
        print(f"   Conversor: {'❌ VÁLIDA (ERRO!)' if is_valid_conv else '✅ INVÁLIDA (correto)'}")
        print(f"   Mensagem: {msg_conv}")
        
        # Testar com o query processor (se disponível)
        if query_processor:
            is_valid_qp, msg_qp = query_processor.validate_query(query)
            print(f"   QueryProcessor: {'❌ VÁLIDA (ERRO!)' if is_valid_qp else '✅ INVÁLIDA (correto)'}")
            print(f"   Mensagem: {msg_qp}")
            
            # Considerar sucesso se ambos detectaram erro
            if not is_valid_conv and not is_valid_qp:
                passed += 1
                print("   RESULTADO: ✅ TESTE PASSOU")
            else:
                failed += 1
                print("   RESULTADO: ❌ TESTE FALHOU")
        else:
            # Se só temos o conversor, verificar apenas ele
            if not is_valid_conv:
                passed += 1
                print("   RESULTADO: ✅ TESTE PASSOU")
            else:
                failed += 1
                print("   RESULTADO: ❌ TESTE FALHOU")
    
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    print(f"Total de testes: {len(invalid_queries)}")
    print(f"Testes aprovados: {passed} ✅")
    print(f"Testes falhados: {failed} ❌")
    print(f"Taxa de sucesso: {(passed/len(invalid_queries)*100):.1f}%")
    print("="*80)
    
    # Testar algumas queries válidas para garantir que não rejeitamos queries corretas
    print("\n\nVERIFICANDO QUERIES VÁLIDAS (não devem ser rejeitadas):")
    print("="*80)
    
    valid_queries = [
        "SELECT Nome, Email FROM Cliente WHERE idade > 25;",
        "SELECT * FROM Cliente INNER JOIN Pedidos ON Cliente.id = Pedidos.cliente_id;",
        "SELECT c.nome, p.valor FROM cliente c INNER JOIN pedidos p ON c.id = p.cliente_id WHERE p.valor > 500;",
    ]
    
    valid_passed = 0
    for query in valid_queries:
        print(f"\nQuery: {query}")
        is_valid_conv, msg_conv = converter.validate_sql_syntax(query)
        print(f"Conversor: {'✅ VÁLIDA' if is_valid_conv else '❌ INVÁLIDA (ERRO!)'}")
        
        if query_processor:
            is_valid_qp, msg_qp = query_processor.validate_query(query)
            print(f"QueryProcessor: {'✅ VÁLIDA' if is_valid_qp else '❌ INVÁLIDA (ERRO!)'}")
            if is_valid_conv and is_valid_qp:
                valid_passed += 1
        elif is_valid_conv:
            valid_passed += 1
    
    print(f"\n✅ {valid_passed}/{len(valid_queries)} queries válidas aceitas corretamente")
    

if __name__ == "__main__":
    test_invalid_queries()
