"""Teste da ferramenta remover_tarefa com um Trello simulado (não usa chaves).

Rode na raiz do projeto:  python tests/test_remover_tarefa.py
"""
import importlib.util
import os
import sys
import types

# --- módulos falsos, só para importar o agent.py sem as bibliotecas reais ---
class FakeAgent:
    def __init__(self, **kw):
        self.tools = kw["tools"]
        self.instruction = kw["instruction"]

google = types.ModuleType("google")
adk = types.ModuleType("google.adk")
agents = types.ModuleType("google.adk.agents")
llm_agent = types.ModuleType("google.adk.agents.llm_agent")
llm_agent.Agent = FakeAgent
sys.modules.update({
    "google": google, "google.adk": adk,
    "google.adk.agents": agents, "google.adk.agents.llm_agent": llm_agent,
})

dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda *a, **k: None
sys.modules["dotenv"] = dotenv


class Card:
    def __init__(self, name, lista):
        self.name, self.lista, self.deleted = name, lista, False
        self.desc, self.due, self.id = "", None, name

    def delete(self):
        self.deleted = True
        self.lista.cards.remove(self)


class Lista:
    def __init__(self, name):
        self.name, self.cards = name, []

    def list_cards(self):
        return list(self.cards)


class Board:
    name = "DIO"

    def __init__(self, listas):
        self.listas = listas

    def list_lists(self):
        return self.listas


class Client:
    board = None
    quebrar = False

    def __init__(self, **kw):
        if Client.quebrar:
            raise RuntimeError("falha de rede")

    def list_boards(self):
        return [Client.board]


trello = types.ModuleType("trello")
trello.TrelloClient = Client
sys.modules["trello"] = trello

CAMINHO_AGENT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "agenttaskmanager", "agent.py")
spec = importlib.util.spec_from_file_location("agent", CAMINHO_AGENT)
agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


def novo_quadro():
    a, e, c = Lista("A FAZER"), Lista("EM ANDAMENTO"), Lista("CONCLUÍDO")
    Client.board = Board([a, e, c])
    return a, e, c


# 1) remove um card existente (ignorando maiúsculas)
a, e, c = novo_quadro()
a.cards.append(Card("Pagar conta", a))
r = agent.remover_tarefa("pagar CONTA")
print("1:", r)
assert "removido" in r and "A FAZER" in r and a.cards == []

# 2) card inexistente
a, e, c = novo_quadro()
a.cards.append(Card("Estudar", a))
r = agent.remover_tarefa("Dormir")
print("2:", r)
assert "não encontrado" in r and len(a.cards) == 1

# 3) nome duplicado: não apaga nada
a, e, c = novo_quadro()
a.cards.append(Card("Reunião", a)); e.cards.append(Card("Reunião", e))
r = agent.remover_tarefa("Reunião")
print("3:", r)
assert "Nada foi removido" in r and len(a.cards) == 1 and len(e.cards) == 1

# 4) erro de conexão vira mensagem, não exceção
Client.quebrar = True
r = agent.remover_tarefa("X")
print("4:", r)
assert r.startswith("❌ Erro")
Client.quebrar = False

# 5) está registrada no agente e tem docstring/type hints (o ADK usa isso)
assert agent.remover_tarefa in agent.root_agent.tools
assert agent.remover_tarefa.__doc__ and agent.remover_tarefa.__annotations__["nome_da_task"] is str
assert "remover_tarefa" in agent.root_agent.instruction
print("OK: todos os testes passaram")
