# main.py
from query_processor import QueryProcessor

def main():
    print("=== Demo: Query Processor ===")
    print("Digite uma query SQL simples (ou 'exit' para sair).")
    print("Exemplo: SELECT nome, preco FROM produtos WHERE preco > 100;\n")

    qp = QueryProcessor()

    while True:
        query = input("SQL> ").lower().strip()
        if query in ("exit", "quit"):
            print("Encerrando demo.")
            break

        if not query:
            continue

        valid = qp.validate_query(query)
        if isinstance(valid, tuple):  # retorna (False, mensagem)
            ok, msg = valid
            print(msg)
        elif valid:
            print("✅ Query válida e tabelas encontradas no banco.")
        else:
            print("❌ Query inválida ou erro de sintaxe.")

if __name__ == "__main__":
    main()
