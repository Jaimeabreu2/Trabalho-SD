import csv
from pathlib import Path


COLUNAS_CSV = [
    ("cenario", "cenario"),
    ("algoritmo", "algoritmo"),
    ("drones", "quantidade_drones"),
    ("falha", "tipo_falha"),
    ("falhos", "quantidade_falhos"),
    ("comandante_escolhido", "comandante_escolhido"),
    ("decisao_alcancada", "decisao_alcancada"),
    ("acordo", "acordo"),
    ("validade", "validade"),
    ("terminacao", "terminacao"),
    ("mensagens_enviadas", "mensagens_enviadas"),
    ("mensagens_recebidas", "mensagens_recebidas"),
    ("mensagens_omitidas", "mensagens_omitidas"),
    ("mensagens_atrasadas", "mensagens_atrasadas"),
    ("mensagens_contraditorias", "mensagens_contraditorias"),
    ("status_limite_teorico", "status_limite_teorico"),
    ("tempo_execucao", "tempo_execucao"),
]


def preparar_valor(valor):
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    return valor


def salvar_resultados_csv(resultados, caminho_saida):
    caminho = Path(caminho_saida)

    # Cria a pasta de resultados se ela não existir.
    caminho.parent.mkdir(parents=True, exist_ok=True)

    # Cada linha representa um cenário executado.
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=[nome for nome, _ in COLUNAS_CSV],
        )
        escritor.writeheader()

        for resultado in resultados:
            linha = {
                nome: preparar_valor(resultado.get(chave))
                for nome, chave in COLUNAS_CSV
            }
            escritor.writerow(linha)

    return caminho
