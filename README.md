# Agente de tarefas com Trello (Google ADK + Gemini)

Agente de IA em Python que organiza as tarefas do dia num quadro do Trello a partir de uma conversa. Cada função Python vira uma ferramenta (*tool*) que o Gemini decide chamar.

Projeto do desafio da DIO. O ponto de partida foi o agente `agents/agent04` do repositório [digitalinnovationone/agent-carbon-footprint](https://github.com/digitalinnovationone/agent-carbon-footprint), reproduzido aqui com o meu quadro e com uma melhoria.

## O que o agente faz

Ao ser ativado, ele pergunta quais são as tarefas do dia (informando a data de hoje) e continua perguntando se há mais, até você dizer que não. Ferramentas:

| Ferramenta | O que faz |
|---|---|
| `get_temporal_context` | Devolve a data e a hora atuais, usadas para abrir a conversa. |
| `adicionar_tarefa` | Cria um card na lista **A fazer** com nome, descrição e data de vencimento. |
| `listar_tarefas` | Lista os cards do quadro, todos ou só de um status (`a fazer`, `em andamento`, `concluido`). |
| `mudar_status_tarefa` | Move um card entre **A fazer**, **Em andamento** e **Concluído**. |
| `remover_tarefa` | **Nova (minha melhoria).** Apaga um card do quadro, depois de você confirmar. |

## Estrutura

```
.
├── agenttaskmanager/
│   ├── __init__.py
│   ├── agent.py          # ferramentas e definição do agente
│   └── .env.exemplo      # modelo das credenciais
├── tests/
│   └── test_remover_tarefa.py   # teste com Trello simulado
├── requirements.txt
├── .gitignore
└── README.md
```

## Como configurar e rodar

Requer **Python 3.10 ou superior** (mínimo do ADK).

### 1. Preparar o Trello

1. Crie um quadro chamado **DIO** com as listas **A fazer**, **Em andamento** e **Concluído**. Se o seu quadro tiver outro nome, mude a constante `NOME_DO_QUADRO` no topo do `agent.py`.
2. Acesse <https://trello.com/power-ups/admin/>, clique em **New** e crie um aplicativo (nome, workspace e e-mail; a URL do conector pode ficar em branco).
3. Na página do Power-Up, copie a **API Key** e o **Secret**.
4. Gere o token abrindo no navegador a URL abaixo, trocando `SUA_API_KEY_AQUI` pela sua chave, e clique em **Permitir**:

   ```
   https://trello.com/1/authorize?expiration=never&name=AppDio&scope=read,write&response_type=token&key=SUA_API_KEY_AQUI
   ```

   O `scope=read,write` é necessário, pois o agente cria, move e remove cards.

### 2. Preparar o ambiente

```bash
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Guardar as credenciais

Crie uma chave gratuita do Gemini no [Google AI Studio](https://aistudio.google.com/apikey), depois:

```bash
cp agenttaskmanager/.env.exemplo agenttaskmanager/.env
```

Edite o `agenttaskmanager/.env` e preencha `GOOGLE_API_KEY`, `TRELLO_API_KEY`, `TRELLO_API_SECRET` e `TRELLO_TOKEN`. O `.env` está no `.gitignore` e **não deve ser versionado**.

### 4. Rodar

Na raiz do projeto:

```bash
adk web
```

Abra o endereço mostrado no terminal (normalmente <http://localhost:8000>), escolha `agenttaskmanager` e converse com o agente. A chave gratuita do Gemini tem limite diário de uso, então evite repetir testes sem necessidade.

## Melhoria escolhida: ferramenta de remover tarefa

**Problema:** a instrução do agente prometia "Remover tarefas da lista", mas o código não tinha nenhuma ferramenta para isso. O modelo dizia que podia remover, mas não tinha como.

**O que mudei:**

- Criei `remover_tarefa(nome_da_task)` em `agent.py` e a registrei em `tools=[...]` do agente.
- A função procura o card pelo nome (sem diferenciar maiúsculas de minúsculas) em todas as listas do quadro e o apaga.
- **Nomes repetidos:** se houver mais de um card com o mesmo nome, ela **não apaga nada** e avisa em quais listas eles estão. Assim nunca remove o card errado.
- **Erros:** usa `try/except`, então falhas (rede, credencial inválida) voltam como mensagem de texto para o agente explicar ao usuário, em vez de quebrar a conversa.
- **Confirmação:** como a exclusão é permanente, a instrução do agente manda confirmar o nome da tarefa com você antes de chamar a ferramenta.
- Alinhei a instrução do agente às ferramentas reais (cada função agora cita a tool correspondente).
- Corrigi o `requirements.txt`: o original listava `datetime` e `dotenv`, que são outros pacotes do PyPI. O correto é `python-dotenv` (`datetime` já vem com o Python).

## Como testei

1. **Teste automatizado com Trello simulado** (sem usar chaves). Rode com `python tests/test_remover_tarefa.py`. Ele verifica que a função remove um card existente ignorando maiúsculas, informa quando o card não existe, recusa apagar quando há nomes duplicados, converte erro de conexão em mensagem e está registrada no agente.
2. **Teste real no `adk web`** (faça com o seu quadro e adicione os prints abaixo):
   1. Peça: *"Adicione a tarefa Teste de remoção, descrição qualquer, para hoje"*. O card aparece em **A fazer**.
   2. Peça: *"Remova a tarefa Teste de remoção"*. O agente deve pedir confirmação.
   3. Responda *"sim"*. O card some do quadro e o agente confirma.
   4. Peça: *"Remova a tarefa Inexistente"*. O agente informa que não encontrou.

### Evidências

_Adicione aqui um print da conversa no `adk web` ao lado do quadro do Trello, mostrando criar, listar, mover e remover um card._
