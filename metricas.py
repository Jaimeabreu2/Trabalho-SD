def verificar_acordo(drones_corretos):
    # Acordo considera apenas drones corretos.
    decisoes = [
        drone.decisao_final
        for drone in drones_corretos
        if drone.decisao_final is not None
    ]
    return bool(decisoes) and len(set(decisoes)) == 1


def verificar_validade(drones_corretos, candidato_esperado):
    propostas = {
        drone.candidato_proposto
        for drone in drones_corretos
        if drone.candidato_proposto is not None
    }

    # Validade é verificada quando existe proposta comum.
    if len(propostas) != 1:
        return None

    proposta_comum = next(iter(propostas))
    decisoes = [
        drone.decisao_final
        for drone in drones_corretos
        if drone.decisao_final is not None
    ]
    return (
        proposta_comum == candidato_esperado
        and bool(decisoes)
        and all(decisao == proposta_comum for decisao in decisoes)
    )


def verificar_terminacao(drones_corretos):
    # Terminação falha se algum drone correto não decidiu.
    return bool(drones_corretos) and all(
        drone.decisao_final is not None for drone in drones_corretos
    )


def criar_resultado(
    algoritmo,
    drones,
    rede,
    candidato_esperado,
    comandante_escolhido,
    decisao_alcancada,
    tempo_execucao,
    limite_bizantino=None,
):
    drones_corretos = [
        drone for drone in drones if drone.comportamento == "nenhuma"
    ]
    falhos = [
        drone for drone in drones if drone.comportamento != "nenhuma"
    ]
    tipos_falha = sorted(
        {drone.comportamento for drone in falhos}
    )

    if not tipos_falha:
        tipo_falha = "nenhuma"
    else:
        tipo_falha = ", ".join(tipos_falha)

    status_limite = None
    if limite_bizantino is not None:
        status_limite = (
            "Dentro"
            if limite_bizantino["dentro_limite"]
            else "Fora"
        )

    return {
        "algoritmo": algoritmo,
        "quantidade_drones": len(drones),
        "tipo_falha": tipo_falha,
        "quantidade_falhos": len(falhos),
        "comandante_escolhido": comandante_escolhido,
        "decisao_alcancada": decisao_alcancada,
        "acordo": verificar_acordo(drones_corretos),
        "validade": verificar_validade(
            drones_corretos,
            candidato_esperado,
        ),
        "terminacao": verificar_terminacao(drones_corretos),
        "mensagens_enviadas": rede.mensagens_enviadas,
        "mensagens_recebidas": rede.mensagens_recebidas,
        "mensagens_omitidas": sum(
            drone.mensagens_omitidas for drone in drones
        ),
        "mensagens_atrasadas": sum(
            drone.mensagens_atrasadas for drone in drones
        ),
        "mensagens_contraditorias": sum(
            drone.mensagens_contraditorias for drone in drones
        ),
        "status_limite_teorico": status_limite,
        "tempo_execucao": tempo_execucao,
    }
