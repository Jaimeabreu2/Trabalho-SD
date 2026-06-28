from pathlib import Path


def _carregar_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _salvar_barras(plt, nomes, valores, titulo, eixo_y, caminho):
    plt.figure(figsize=(11, 6))
    plt.bar(nomes, valores, color="#4472C4")
    plt.title(titulo)
    plt.ylabel(eixo_y)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()


def gerar_graficos_resultados(resultados, pasta_saida):
    # Se não houver dados, não gera gráfico.
    if not resultados:
        return []

    plt = _carregar_matplotlib()
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)

    nomes = [resultado.get("cenario", "manual") for resultado in resultados]
    arquivos = []

    graficos = [
        (
            "grafico_mensagens_enviadas.png",
            [resultado.get("mensagens_enviadas", 0) for resultado in resultados],
            "Mensagens enviadas por cenário",
            "Mensagens",
        ),
        (
            "grafico_tempo_execucao.png",
            [resultado.get("tempo_execucao", 0) for resultado in resultados],
            "Tempo de execução por cenário",
            "Tempo (segundos)",
        ),
        (
            "grafico_decisoes.png",
            [
                1 if resultado.get("decisao_alcancada") else 0
                for resultado in resultados
            ],
            "Decisões alcançadas por cenário",
            "Decisão (1 = Sim, 0 = Não)",
        ),
    ]

    for nome_arquivo, valores, titulo, eixo_y in graficos:
        caminho = pasta / nome_arquivo
        _salvar_barras(plt, nomes, valores, titulo, eixo_y, caminho)
        arquivos.append(caminho)

    bizantinos = [
        resultado
        for resultado in resultados
        if resultado.get("mensagens_contraditorias", 0) > 0
    ]
    if bizantinos:
        caminho = pasta / "grafico_mensagens_contraditorias.png"
        _salvar_barras(
            plt,
            [resultado["cenario"] for resultado in bizantinos],
            [
                resultado["mensagens_contraditorias"]
                for resultado in bizantinos
            ],
            "Mensagens contraditórias nos cenários bizantinos",
            "Mensagens",
            caminho,
        )
        arquivos.append(caminho)

    grupos = {}
    for resultado in resultados:
        algoritmo = resultado.get("algoritmo", "-")
        grupos.setdefault(algoritmo, []).append(
            resultado.get("mensagens_enviadas", 0)
        )

    if len(grupos) > 1:
        caminho = pasta / "grafico_comparacao_algoritmos.png"
        medias = [
            sum(valores) / len(valores) for valores in grupos.values()
        ]
        _salvar_barras(
            plt,
            list(grupos),
            medias,
            "Média de mensagens enviadas por algoritmo",
            "Média de mensagens",
            caminho,
        )
        arquivos.append(caminho)

    return arquivos
