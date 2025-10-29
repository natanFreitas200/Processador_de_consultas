# Processador de Consultas SQL (Álgebra Relacional)

Breve: este projeto é uma implementação educativa em Python que faz parsing de consultas SQL limitadas, converte para álgebra relacional, aplica heurísticas simples de otimização, gera um grafo de operadores e exibe tudo isso em uma interface gráfica.

Este README foi melhorado para ser mais direto: contém uma seção "Try it" (teste rápido), comandos práticos, descrição das partes principais e sugestões de extensão.

## Try it — executar rápido

1. Abra PowerShell na pasta do projeto:

```powershell
cd 'C:\Users\Bene\Desktop\Codes\Processador_de_consultas'
```

2. (Opcional) ative o venv do projeto:

```powershell
.\venv\Scripts\Activate.ps1
```

3. Instale dependências (somente se ainda não instalou):

```powershell
pip install -r requirements.txt
```

4. (Opcional) configurar validação com MySQL:

```powershell
copy .env.example .env
# editar .env e preencher DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_DATABASE
```

5. Abrir a interface gráfica:

```powershell
python interface_grafica.py
```

Exemplo de consulta para colar na GUI (testado pelos exemplos do projeto):

```sql
SELECT c.nome, p.valor
FROM cliente c
INNER JOIN pedidos p ON c.id = p.cliente_id
WHERE p.valor > 500;
```

Ao clicar em "Processar Consulta" você verá:
- Validação (sintaxe; se o DB estiver configurado, também valida nomes de tabelas/colunas)
- A expressão em Álgebra Relacional (string)
- O grafo de operadores (visual)
- Um plano de execução textual mostrando as etapas otimizadas

## O que há aqui (visão rápida dos arquivos)

- `interface_grafica.py`: GUI (Tkinter) — entrada de SQL, botões, abas e visualização com matplotlib + networkx.
- `conversor.py`: parser e conversor SQL → árvore/álgebra; funções para gerar o grafo em memória.
- `optimizer.py`: heurísticas implementadas (push-down de seleção/projeção, reordenação básica de joins, anotação de algoritmo de junção no log).
- `query_processor.py`: validação contra esquema (usa `db.py` para recolher esquema via information_schema).
- `db.py`: conexão com MySQL (usa variáveis de ambiente lidas por `python-dotenv`).
- `test.py`: testes e exemplos rápidos.

## Principais comportamentos implementados

- Parsing limitado a: SELECT, FROM, WHERE, INNER JOIN (com alias simples).
- Operadores suportados nas expressões/condições: `=`, `>`, `<`, `<=`, `>=`, `<>`, `AND`, parênteses.
- Otimizações aplicadas (documentadas no `optimization_log`):
  - Push-down de seleções (σ) — evita processamento desnecessário em níveis superiores
  - Push-down de projeções (π) — reduz número de atributos o mais cedo possível
  - Reordenação básica de joins (prioriza joins com seleções locais)
  - Marcação/registro de algoritmo preferido (Hash Join) no log — não altera o motor de execução (não há execução física de joins)

## Sugestões de melhoria (próximos passos)

1. Integrar `QueryProcessor` na GUI para que o botão "Validar" faça checagem completa contra o esquema (atualmente a validação de sintaxe usa `converter.validate_sql_syntax`).
2. Gerar o plano de execução diretamente a partir da árvore otimizada (pós-ordem) e numerar as operações exatamente na ordem que o executor hipotético seguiria.
3. Implementar estimativas simples de custo (`cardinality` heurística) para reordenar joins de forma mais precisa.
4. (Opcional) Adicionar um modo "offline" onde o esquema pode ser carregado de um arquivo JSON para evitar necessidade de MySQL em demonstrações.

## Problemas comuns e soluções rápidas

- Erro ao conectar ao MySQL: verifique `.env` e se o serviço MySQL está rodando. Enquanto o MySQL estiver indisponível, parsing e visualização continuarão funcionando.
- Erros com matplotlib/Tkinter: verifique se o ambiente tem suporte gráfico (no Windows, TkAgg costuma funcionar). Se executar em ambiente headless, o grafo não será exibido.

## Comandos úteis

Ativar venv e instalar dependências (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Criar arquivo `.env` a partir do exemplo:

```powershell
copy .env.example .env
notepad .env
```

## Licença

Este projeto é fornecido como material de estudo; inclua um arquivo `LICENSE` se quiser publicar com uma licença específica (MIT, Apache-2.0, etc.).

---

Se quiser, faço uma das seguintes melhorias automaticamente:

- Integrar validação completa (`QueryProcessor`) na GUI (botão "Validar").
- Substituir o gerador de plano textual para percorrer a árvore otimizada e listar as etapas reais de execução.
- Melhorar a reordenação de joins com uma heurística simples de seletividade.

Diga qual prefere que eu implemente que eu aplico as mudanças no código e testo localmente.
