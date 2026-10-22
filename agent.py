from google.adk.agents.llm_agent import Agent
from trello import TrelloClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

# Credenciais do Trello (vêm do arquivo .env)
API_KEY = os.getenv('TRELLO_API_KEY')
API_SECRET = os.getenv('TRELLO_API_SECRET')
TOKEN = os.getenv('TRELLO_TOKEN')

# Nome do quadro no Trello. Se o seu quadro tiver outro nome, mude aqui.
NOME_DO_QUADRO = 'DIO'


def get_temporal_context():
    now = datetime.now()
    return now.strftime('%Y/%m/%d %H:%M:%S')


def adicionar_tarefa(nome_da_task: str, descricao_da_task: str, due_date: str):

    client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )

    client.list_boards()
    # Obter o board (você precisa do ID ou nome do board)
    boards = client.list_boards()
    meu_board = [b for b in boards if b.name == NOME_DO_QUADRO][0]

    # Obter a lista onde quer adicionar o card
    listas = meu_board.list_lists()

    minha_lista = [l for l in listas if l.name.upper() == 'TO DO' or l.name.upper() == 'A FAZER'][0]

    # Criar o card (task)
    minha_lista.add_card(
        name=nome_da_task,
        desc=descricao_da_task,
        due=due_date
    )


def listar_tarefas(status: str = "todas"):
    client = TrelloClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        token=TOKEN
    )

    boards = client.list_boards()
    meu_board = [b for b in boards if b.name == NOME_DO_QUADRO][0]
    listas = meu_board.list_lists()

    if status.lower() == "todas":
        listas_filtradas = listas
    elif status.lower() == "a fazer":
        listas_filtradas = [l for l in listas if l.name.upper() in ['A FAZER', 'TO DO', 'TODO']]
    elif status.lower() == "em andamento":
        listas_filtradas = [l for l in listas if l.name.upper() in ['EM ANDAMENTO', 'DOING']]
    elif status.lower() == "concluido":
        listas_filtradas = [l for l in listas if l.name.upper() in ['CONCLUÍDO', 'CONCLUIDO', 'DONE']]
    else:
        listas_filtradas = listas

    tarefas = []

    for lista in listas_filtradas:
        cards = lista.list_cards()
        for card in cards:
            tarefas.append({
                "nome": card.name,
                "descricao": card.desc,
                "vencimento": card.due,
                "status": lista.name,
                "id": card.id
            })

    return tarefas


def mudar_status_tarefa(nome_da_task: str, novo_status: str) -> str:
    try:
        client = TrelloClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            token=TOKEN
        )

        boards = client.list_boards()
        meu_board = [b for b in boards if b.name == NOME_DO_QUADRO][0]
        listas = meu_board.list_lists()

        # Mapear status para listas
        status_map = {
            "a fazer": "A FAZER",
            "em andamento": "EM ANDAMENTO",
            "concluido": "CONCLUÍDO"
        }

        nome_lista_destino = status_map.get(novo_status.lower())

        if not nome_lista_destino:
            return "❌ Status inválido. Use: 'a fazer', 'em andamento' ou 'concluido'"

        # Encontrar lista de destino
        lista_destino = next(
            (l for l in listas if l.name.upper() == nome_lista_destino.upper()),
            None
        )

        if not lista_destino:
            return f"❌ Lista '{nome_lista_destino}' não encontrada no board"

        # Buscar card em todas as listas
        card_encontrado = None
        lista_origem = None

        for lista in listas:
            cards = lista.list_cards()
            card_encontrado = next(
                (c for c in cards if c.name.lower() == nome_da_task.lower()),
                None
            )
            if card_encontrado:
                lista_origem = lista
                break

        if not card_encontrado:
            return f"❌ Card '{nome_da_task}' não encontrado"

        # Mover
        card_encontrado.change_list(lista_destino.id)
        return f"✅ '{nome_da_task}': {lista_origem.name} → {lista_destino.name}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


def remover_tarefa(nome_da_task: str) -> str:
    """Remove (apaga de vez) o card de uma tarefa do quadro do Trello.

    Só chame esta ferramenta depois que o usuário confirmar que quer remover
    a tarefa, porque o card é excluído de forma permanente.

    Args:
        nome_da_task: nome do card que será removido (maiúsculas e minúsculas
            não importam).

    Returns:
        Mensagem dizendo se a tarefa foi removida ou o que deu errado.
    """
    try:
        client = TrelloClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            token=TOKEN
        )

        boards = client.list_boards()
        meu_board = [b for b in boards if b.name == NOME_DO_QUADRO][0]
        listas = meu_board.list_lists()

        # Procurar o nome em todas as listas. Guardamos todos os achados
        # para não apagar o card errado quando houver nomes repetidos.
        encontrados = []
        for lista in listas:
            for card in lista.list_cards():
                if card.name.lower() == nome_da_task.lower():
                    encontrados.append((card, lista))

        if not encontrados:
            return f"❌ Card '{nome_da_task}' não encontrado"

        if len(encontrados) > 1:
            onde = ", ".join(l.name for _, l in encontrados)
            return (f"❌ Existem {len(encontrados)} cards chamados '{nome_da_task}' "
                    f"(nas listas: {onde}). Nada foi removido; peça ao usuário "
                    f"para renomear ou remover manualmente no Trello.")

        card, lista = encontrados[0]
        card.delete()
        return f"🗑️ '{card.name}' removido da lista {lista.name}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"


root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Agente de Organização de Tarefas',
    instruction="""
        Você é um agente de organização de tarefas.
        Sua função é receber uma tarefa e criar um card no Trello com o nome e descrição da tarefa.
        Você deve me perguntar as atividas que tenho no dia e criar um card para cada uma delas.
        Você inicia a conversa assim que for ativado, perguntando quais são as tarefas do dia.
        Sempre inicie a conversa perguntando quais são as tarefas do dia informando a data com pela tool get_temporal_context,
        e depois vá perguntando se tem mais alguma tarefa, até que o usuário diga que não tem mais tarefas.
        Suas funções:
          1. Adicionar novas tarefas com nome e descrição (tool adicionar_tarefa)
          2. Listar todas as tarefas ou filtrar por status (tool listar_tarefas)
          3. Marcar tarefas como concluídas (tool mudar_status_tarefa)
          4. Remover tarefas da lista (tool remover_tarefa)
          5. Mudar o status da tarefa (ex: de "A Fazer" para "Em Andamento" e de "Em Andamento" para "Concluído") (tool mudar_status_tarefa)
          6. Gerar contexto temporal (data e hora atual) para organizar as tarefas do dia (tool get_temporal_context)

        Ao remover uma tarefa: a remoção apaga o card de forma permanente. Antes de chamar remover_tarefa,
        confirme com o usuário o nome exato da tarefa. Só chame a tool depois de ele confirmar.
        Se a tool disser que não achou o card, ofereça listar as tarefas para o usuário conferir o nome.
""",
    tools=[get_temporal_context, adicionar_tarefa, listar_tarefas, mudar_status_tarefa, remover_tarefa],
)
