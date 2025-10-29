Processador de Consultas SQL (Álgebra Relacional)

Projeto educativo para implementar um processador de consultas SQL com parser, conversão para álgebra relacional, otimizações heurísticas, geração de grafo de operadores e uma interface gráfica para visualização.

Este repositório contém uma implementação em Python de um processador de consultas simplificado, desenvolvido para fins acadêmicos (trabalho de disciplina). O projeto oferece:

- Parser simples para consultas SQL com suporte a: `SELECT`, `FROM`, `WHERE`, `INNER JOIN`.
- Conversor para uma representação de Álgebra Relacional (string e árvore).
- Otimizações heurísticas (push-down de seleções e projeções, reordenação básica de joins, escolha documentada de algoritmo de junção).
- Construção de um grafo de operadores (nós: π, σ, ρ, ⨝ e tabelas) e visualização via GUI (Tkinter + matplotlib + networkx).
- Validação básica de sintaxe e (opcional) validação de nomes de tabelas/colunas consultando um banco MySQL.

## Estrutura do projeto

- `interface_grafica.py` — Interface gráfica (Tkinter) que recebe a consulta, mostra validação, álgebra relacional, grafo e plano de execução.
- `conversor.py` — Conversor SQL → Álgebra Relacional e geração de árvores/graph nodes.
- `optimizer.py` — Implementação das heurísticas de otimização (logs e transformações básicas na árvore).
- `query_processor.py` — Validação de consultas contra o esquema do banco (usa `db.py`).
- `db.py` — Código para ler o esquema do MySQL (usa `python-dotenv` e `mysql-connector-python`).
- `test.py` — Testes e exemplos rápidos para o conversor / processador.
- `requirements.txt` — Dependências do projeto.
- `.env` — (não comitado) arquivo com credenciais do banco; veja `.env.example`.

## Requisitos

- Python 3.8+ (testado com Python 3.13 neste ambiente)
- MySQL (opcional — apenas se desejar validação contra esquema real)
- Dependências Python (listadas em `requirements.txt`):
  - matplotlib
  - networkx
  - mysql-connector-python
  - python-dotenv

## Instalação e uso (Windows PowerShell)

1. Abra o PowerShell na pasta do projeto:

```powershell
cd 'C:\Users\Bene\Desktop\Codes\Processador_de_consultas'
```

2. Ative o ambiente virtual (se existir `venv` na raiz):

```powershell
# Ativa o venv existente
.\venv\Scripts\Activate.ps1
```

Se ainda não tiver criado um `venv` local, crie e ative:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

4. Configure as credenciais do banco (opcional, só necessário para validação com MySQL):

- Copie `.env.example` para `.env` e preencha com suas credenciais MySQL.

```powershell
copy .env.example .env
# editar .env com um editor de texto e fornecer DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE
```

5. Execute a interface gráfica:

```powershell
python interface_grafica.py
```

ou (se preferir) execute `main.py` se este arquivo estiver configurado para iniciar a GUI.

## Como usar a GUI

- Cole ou escreva uma consulta SQL no campo de entrada (ex.: `SELECT c.nome, p.valor FROM cliente c INNER JOIN pedidos p ON c.id = p.cliente_id WHERE p.valor > 500;`).
- Clique em `Validar Consulta` para checar sintaxe (e — se configurado e com o BD disponível — nomes de tabela/coluna).
- Clique em `Processar Consulta` para:
  - Converter para álgebra relacional (string e árvore)
  - Aplicar otimizações heurísticas
  - Exibir grafo de operadores (versão otimizada e não otimizada)
  - Gerar um plano de execução textual (ordem de execução) — atualmente gerado a partir do parse e das heurísticas aplicadas

## Arquitetura e pontos importantes

- O parser suporta a maioria dos exemplos do trabalho (SELECT, FROM, WHERE, INNER JOIN). Operadores suportados: `=, >, <, <=, >=, <>, AND, ( , )`.
- O otimizador aplica push-down de seleção/projeção e registra ações no `optimization_log`. A reordenação de joins tem uma implementação básica que percorre e prioriza joins com seleções locais. A seleção de algoritmo (ex: Hash Join) é documentada no log; se desejar marcar explicitamente nos nós do grafo, adapte `optimizer.py` para apontar a estratégia escolhida no nó correspondente.
- Validação de nomes de tabelas/colunas: `query_processor.py` usa `db.get_db_schema` (em `db.py`) para recuperar o esquema via `information_schema` do MySQL. Se o MySQL não estiver disponível ou as credenciais estiverem ausentes, `DB_SCHEMA` será `None` e a validação completa ficará desabilitada — o projeto continuará a funcionar localmente para parsing e visualização.

## Testes e verificação

- Para rodar os testes/exemplos rápidos incluídos:

```powershell
python test.py
```

## Arquivos para editar / estender

- `interface_grafica.py`: GUI e integração. Aqui você pode integrar totalmente `QueryProcessor` (validação completa) ou melhorar o plano textual para percorrer a árvore otimizada.
- `conversor.py`: conversão SQL → árvore/algebra; altera o modo como o grafo é gerado.
- `optimizer.py`: heurísticas; é o local para melhorar reordenação de joins com estimativas de custo e marcar algoritmos de execução.

## Erros comuns / solução rápida

- Se ao iniciar a GUI ocorrer erro de conexão com MySQL: verifique o `.env`, se o servidor MySQL está em execução e as credenciais estão corretas. Enquanto isso, o parsing e a visualização funcionarão sem a validação do esquema.
- Se o matplotlib reclamar do backend em ambiente headless, garanta que a execução seja em ambiente com display X (no Windows o TkAgg é padrão). O arquivo `interface_grafica.py` já define `matplotlib.use('TkAgg')`.

## Licença

Este projeto é fornecido apenas como material de estudo. Sinta-se livre para adaptar. Caso deseje uma licença permissiva, adicione um arquivo `LICENSE` (por exemplo MIT).

---

Se quiser, posso: integrar a validação completa na GUI (usar `QueryProcessor` para validar nomes de tabela/coluna), gerar um plano de execução diretamente a partir da árvore otimizada, ou melhorar a reordenação de joins — diga qual dessas melhorias prefere que eu implemente.
