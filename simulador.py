import json
from pathlib import Path


CAMPOS_OBRIGATORIOS = {
    "nome",
    "algoritmo",
    "drones",
    "falha",
    "falhos",
    "seed",
    "taxa_omissao",
    "atraso_max",
}

ARQUIVOS_CENARIOS = [
    "paxos_5_crash.json",
    "paxos_5_omissao.json",
    "paxos_5_temporizacao.json",
    "paxos_10_crash.json",
    "paxos_10_omissao.json",
    "paxos_10_temporizacao.json",
    "lsp_5_bizantina_1.json",
    "lsp_5_bizantina_2.json",
    "lsp_10_bizantina_1.json",
    "lsp_10_bizantina_3.json",
    "lsp_10_bizantina_4.json",
]


def carregar_cenario(caminho):
    # Carrega os dados do cenário a partir do JSON.
    arquivo = Path(caminho)
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo de cenário não encontrado: {caminho}")

    try:
        with arquivo.open(encoding="utf-8") as entrada:
            cenario = json.load(entrada)
    except json.JSONDecodeError as erro:
        raise ValueError(f"JSON inválido: {erro.msg}") from erro

    if not isinstance(cenario, dict):
        raise ValueError("O cenário deve ser um objeto JSON.")

    ausentes = CAMPOS_OBRIGATORIOS - cenario.keys()
    if ausentes:
        campos = ", ".join(sorted(ausentes))
        raise ValueError(f"Campos obrigatórios ausentes: {campos}")

    if cenario["algoritmo"] not in ("paxos", "lsp"):
        raise ValueError("O algoritmo deve ser paxos ou lsp.")

    if cenario["falha"] not in (
        "nenhuma",
        "crash",
        "omissao",
        "temporizacao",
        "bizantina",
    ):
        raise ValueError("Tipo de falha inválido no cenário.")

    if not isinstance(cenario["drones"], int) or cenario["drones"] < 1:
        raise ValueError("A quantidade de drones deve ser maior que zero.")

    if (
        not isinstance(cenario["falhos"], int)
        or cenario["falhos"] < 0
        or cenario["falhos"] > cenario["drones"]
    ):
        raise ValueError("A quantidade de falhos é inválida.")

    if not isinstance(cenario["nome"], str) or not cenario["nome"].strip():
        raise ValueError("O cenário deve possuir um nome.")

    if cenario["seed"] is not None and not isinstance(cenario["seed"], int):
        raise ValueError("A seed deve ser um número inteiro.")

    taxa = cenario["taxa_omissao"]
    if not isinstance(taxa, (int, float)) or not 0 <= taxa <= 1:
        raise ValueError("A taxa de omissão deve estar entre 0 e 1.")

    atraso = cenario["atraso_max"]
    if not isinstance(atraso, (int, float)) or atraso < 0:
        raise ValueError("O atraso máximo não pode ser negativo.")

    nivel_om = cenario.get("nivel_om")
    if nivel_om is not None and (
        not isinstance(nivel_om, int) or nivel_om < 0
    ):
        raise ValueError("O nível OM(m) deve ser um inteiro não negativo.")

    return cenario
