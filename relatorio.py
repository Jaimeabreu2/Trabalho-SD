from datetime import datetime
from pathlib import Path


def formatar_booleano(valor):
    if valor is None:
        return "Não aplicável"
    return "Sim" if valor else "Não"


def gerar_relatorio(
    resultados,
    caminho_saida,
    arquivos_csv=None,
    arquivos_graficos=None,
):
    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    arquivos_csv = arquivos_csv or []
    arquivos_graficos = arquivos_graficos or []

    algoritmos = sorted(
        {
            resultado.get("algoritmo", "-")
            for resultado in resultados
            if resultado.get("algoritmo") != "-"
        }
    )
    falhas = sorted(
        {
            resultado.get("tipo_falha", "nenhuma")
            for resultado in resultados
            if resultado.get("tipo_falha") != "-"
        }
    )

    linhas = [
        "Escolha de Comandante em uma Frota de Drones",
        "=" * 48,
        f"Data e hora: {datetime.now():%d/%m/%Y %H:%M:%S}",
        f"Total de cenários executados: {len(resultados)}",
        f"Algoritmos utilizados: {', '.join(algoritmos) or 'Nenhum'}",
        f"Falhas simuladas: {', '.join(falhas) or 'Nenhuma'}",
        "",
        "Resumo dos cenários",
        "-" * 20,
    ]

    # Registra os principais dados de cada cenário.
    for resultado in resultados:
        comandante = resultado.get("comandante_escolhido")
        comandante_texto = (
            f"Drone {comandante}" if comandante is not None else "Nenhum"
        )
        linhas.extend(
            [
                "",
                f"Cenário: {resultado.get('cenario', 'manual')}",
                f"Algoritmo: {resultado.get('algoritmo', '-')}",
                f"Drones: {resultado.get('quantidade_drones', '-')}",
                f"Falha: {resultado.get('tipo_falha', '-')}",
                f"Falhos: {resultado.get('quantidade_falhos', '-')}",
                f"Comandante escolhido: {comandante_texto}",
                "Decisão alcançada: "
                f"{formatar_booleano(resultado.get('decisao_alcancada'))}",
                f"Acordo: {formatar_booleano(resultado.get('acordo'))}",
                f"Validade: {formatar_booleano(resultado.get('validade'))}",
                f"Terminação: {formatar_booleano(resultado.get('terminacao'))}",
                "Mensagens enviadas: "
                f"{resultado.get('mensagens_enviadas', 0)}",
                "Mensagens recebidas: "
                f"{resultado.get('mensagens_recebidas', 0)}",
                "Mensagens omitidas: "
                f"{resultado.get('mensagens_omitidas', 0)}",
                "Mensagens atrasadas: "
                f"{resultado.get('mensagens_atrasadas', 0)}",
                "Mensagens contraditórias: "
                f"{resultado.get('mensagens_contraditorias', 0)}",
                "Tempo de execução: "
                f"{resultado.get('tempo_execucao', 0):.6f} s",
            ]
        )

        limite = resultado.get("status_limite_teorico")
        if limite is not None:
            linhas.append(f"Status do limite teórico: {limite}")

        if "erro" in resultado:
            linhas.append(f"Erro: {resultado['erro']}")

    linhas.extend(["", "Arquivos CSV gerados", "-" * 21])
    if arquivos_csv:
        linhas.extend(f"- {arquivo}" for arquivo in arquivos_csv)
    else:
        linhas.append("Nenhum arquivo CSV foi gerado.")

    linhas.extend(["", "Gráficos gerados", "-" * 17])
    if arquivos_graficos:
        linhas.extend(f"- {arquivo}" for arquivo in arquivos_graficos)
    else:
        linhas.append("Nenhum gráfico foi gerado.")

    fora_limite = any(
        resultado.get("status_limite_teorico") == "Fora"
        for resultado in resultados
    )
    if fora_limite:
        # Cenários fora do limite bizantino recebem observação.
        linhas.extend(
            [
                "",
                "Observação:",
                "Alguns cenários bizantinos foram executados fora da condição "
                "n >= 3f + 1. Nesses casos, a simulação é executada, mas não "
                "há garantia teórica clássica de consenso.",
            ]
        )

    nomes_algoritmos = ", ".join(algoritmos) or "nenhum algoritmo"
    linhas.extend(
        [
            "",
            "Conclusão:",
            f"A execução utilizou: {nomes_algoritmos}. "
            "Os resultados indicam, em cada caso, se houve decisão, acordo, "
            "validade e terminação.",
        ]
    )

    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8-sig")
    return caminho
