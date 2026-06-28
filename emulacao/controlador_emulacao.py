import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import socket
import time

try:
    from emulacao.drone_socket import criar_mensagem
except ModuleNotFoundError:
    from drone_socket import criar_mensagem


def enviar_mensagem(ip, porta, mensagem, timeout=3):
    try:
        with socket.create_connection((ip, porta), timeout=timeout) as conexao:
            conexao.sendall(json.dumps(mensagem).encode("utf-8"))
            dados = conexao.recv(65536)
            if not dados:
                return None
            return json.loads(dados.decode("utf-8"))
    except (ConnectionError, OSError, socket.timeout):
        return None


def aguardar_drones(enderecos, tentativas=20, intervalo=0.2):
    pendentes = {(drone_id, ip, porta) for drone_id, ip, porta in enderecos}

    for _ in range(tentativas):
        prontos = set()
        for endereco in pendentes:
            _, ip, porta = endereco
            try:
                with socket.create_connection((ip, porta), timeout=0.2):
                    prontos.add(endereco)
            except (ConnectionError, OSError, socket.timeout):
                pass

        pendentes -= prontos
        if not pendentes:
            return True
        time.sleep(intervalo)

    ids = ", ".join(str(drone_id) for drone_id, _, _ in sorted(pendentes))
    raise RuntimeError(f"Drones não ficaram prontos: {ids}")


def maioria(valores):
    if not valores:
        return None
    valor, quantidade = Counter(valores).most_common(1)[0]
    if quantidade > len(valores) // 2:
        return valor
    return None


def executar_paxos(
    enderecos,
    candidato,
    falha="nenhuma",
    falhos=0,
    numero_proposta=1,
):
    total = len(enderecos)
    quorum = (total // 2) + 1
    mensagens = 0
    promises = 0
    respostas_promise = []
    accepted = 0
    confirmacoes_decisao = 0
    inicio_falhos = total - falhos

    print("Executando eleição de comandante...")
    print("Proponente: Drone 0")
    print(f"Número da proposta: {numero_proposta}")
    print(f"Candidato proposto: Drone {candidato}\n")
    print("Fase PREPARE:")

    for drone_id, ip, porta in enderecos:
        print(f"Drone 0 -> Drone {drone_id}: PREPARE")
        mensagem = criar_mensagem(
            "PREPARE",
            0,
            drone_id,
            candidato,
            "paxos",
            numero_proposta=numero_proposta,
        )
        resposta = enviar_mensagem(ip, porta, mensagem)
        mensagens += 1 + (1 if resposta else 0)
        if resposta and resposta["tipo"] == "PROMISE":
            promises += 1
            respostas_promise.append(resposta)
            print(f"Drone {drone_id} -> Drone 0: PROMISE")
        elif falha == "crash" and drone_id >= inicio_falhos:
            print(f"Drone {drone_id} está em crash e não respondeu.")
        else:
            print(f"Drone {drone_id} não respondeu ao PREPARE.")

    print(f"\nPROMISE recebidos: {promises}")
    print(f"Maioria necessária: {quorum}")
    print(f"Maioria alcançada: {'Sim' if promises >= quorum else 'Não'}")

    valor_escolhido = candidato
    aceites_anteriores = [
        resposta
        for resposta in respostas_promise
        if resposta.get("proposta_aceita") is not None
    ]
    if aceites_anteriores:
        maior_aceite = max(
            aceites_anteriores,
            key=lambda resposta: resposta["proposta_aceita"],
        )
        valor_escolhido = maior_aceite["valor_aceito"]
    print(
        "Valor escolhido após PROMISE: "
        f"Drone {valor_escolhido}"
    )

    print("\nFase ACCEPT:")
    if promises >= quorum:
        for drone_id, ip, porta in enderecos:
            print(f"Drone 0 -> Drone {drone_id}: ACCEPT_REQUEST")
            mensagem = criar_mensagem(
                "ACCEPT_REQUEST",
                0,
                drone_id,
                valor_escolhido,
                "paxos",
                numero_proposta=numero_proposta,
            )
            resposta = enviar_mensagem(ip, porta, mensagem)
            mensagens += 1 + (1 if resposta else 0)
            if resposta and resposta["tipo"] == "ACCEPTED":
                accepted += 1
                print(f"Drone {drone_id} -> Drone 0: ACCEPTED")
            else:
                print(f"Drone {drone_id} não respondeu ao ACCEPT_REQUEST.")

    decidiu = accepted >= quorum
    print(f"\nACCEPTED recebidos: {accepted}")
    print(f"Maioria necessária: {quorum}")
    print(f"Maioria alcançada: {'Sim' if decidiu else 'Não'}")

    if decidiu:
        print("\nFase DECIDE:")
        for drone_id, ip, porta in enderecos:
            mensagem = criar_mensagem(
                "DECIDE",
                0,
                drone_id,
                valor_escolhido,
                "paxos",
                numero_proposta=numero_proposta,
            )
            resposta = enviar_mensagem(ip, porta, mensagem)
            mensagens += 1 + (1 if resposta else 0)
            if resposta:
                confirmacoes_decisao += 1

    terminacao = decidiu and confirmacoes_decisao >= total - falhos
    print("\nResultado:")
    print(
        f"Comandante escolhido: "
        f"{f'Drone {valor_escolhido}' if decidiu else 'Nenhum'}"
    )
    print(f"Decisão alcançada: {'Sim' if decidiu else 'Não'}")
    print(f"Acordo: {'Sim' if decidiu else 'Não'}")
    print(f"Validade: {'Sim' if decidiu else 'Não'}")
    print(f"Terminação: {'Sim' if terminacao else 'Não'}")
    print(f"Mensagens trocadas: {mensagens}")

    return {
        "comandante_escolhido": valor_escolhido if decidiu else None,
        "decisao_alcancada": decidiu,
        "mensagens_trocadas": mensagens,
        "mensagens_contraditorias": 0,
        "acordo": decidiu,
        "validade": decidiu,
        "terminacao": terminacao,
        "numero_proposta": numero_proposta,
        "valor_escolhido": valor_escolhido,
    }


def decidir_maioria(valores, valor_padrao):
    if not valores:
        return valor_padrao
    contagem = Counter(valores)
    maior_quantidade = max(contagem.values())
    candidatos = [
        valor
        for valor, quantidade in contagem.items()
        if quantidade == maior_quantidade
    ]
    return candidatos[0] if len(candidatos) == 1 else valor_padrao


def executar_om_socket(
    nivel,
    comandante,
    valor,
    participantes,
    caminho,
    mapa_enderecos,
    valor_padrao,
    estatisticas,
):
    tenentes = [drone for drone in participantes if drone != comandante]
    recebidos = {}

    print(f"OM({nivel}) - comandante Drone {comandante}, caminho {caminho}")
    ip, porta = mapa_enderecos[comandante]
    for destino in tenentes:
        tipo = "ORDER" if len(caminho) == 1 else "FORWARD"
        mensagem = criar_mensagem(
            tipo,
            comandante,
            destino,
            valor,
            "lsp",
            caminho=caminho,
            nivel_om=nivel,
        )
        resposta = enviar_mensagem(ip, porta, mensagem)
        estatisticas["mensagens"] += 1 + (1 if resposta else 0)
        if resposta:
            recebido = resposta["candidato"]
            if recebido != valor:
                estatisticas["contraditorias"] += 1
        else:
            recebido = valor_padrao
        recebidos[destino] = recebido

    if nivel == 0 or len(tenentes) <= 1:
        votos = {drone: [valor] for drone, valor in recebidos.items()}
        return recebidos, votos

    repasses = {}
    for novo_comandante in tenentes:
        resultado, _ = executar_om_socket(
            nivel - 1,
            novo_comandante,
            recebidos[novo_comandante],
            tenentes,
            caminho + [novo_comandante],
            mapa_enderecos,
            valor_padrao,
            estatisticas,
        )
        repasses[novo_comandante] = resultado

    decisoes = {}
    votos = {}
    for receptor in tenentes:
        valores = [recebidos[receptor]]
        for novo_comandante in tenentes:
            if novo_comandante != receptor:
                valores.append(
                    repasses[novo_comandante].get(
                        receptor,
                        valor_padrao,
                    )
                )
        votos[receptor] = valores
        decisoes[receptor] = decidir_maioria(valores, valor_padrao)
    return decisoes, votos


def executar_lsp(enderecos, candidato, falhos, m=None, valor_padrao=0):
    total = len(enderecos)
    nivel_om = falhos if m is None else m
    ids_bizantinos = set(range(total - falhos, total))
    corretos = set(range(total)) - ids_bizantinos
    mapa_enderecos = {
        drone_id: (ip, porta) for drone_id, ip, porta in enderecos
    }
    estatisticas = {"mensagens": 0, "contraditorias": 0}

    print(f"Executando Lamport-Shostak-Pease OM({nivel_om}) emulado...")
    print("Comandante inicial: Drone 0")
    print(
        "Drones bizantinos: "
        + (", ".join(f"Drone {i}" for i in sorted(ids_bizantinos)) or "Nenhum")
    )
    print(f"Candidato proposto: Drone {candidato}")
    print(f"Valor padrão: Drone {valor_padrao}\n")

    decisoes_tenentes, votos = executar_om_socket(
        nivel_om,
        0,
        candidato,
        list(range(total)),
        [0],
        mapa_enderecos,
        valor_padrao,
        estatisticas,
    )

    decisoes = {}
    valores_corretos = {}
    for drone_id in corretos:
        if drone_id == 0:
            decisoes[drone_id] = candidato
            valores_corretos[drone_id] = [candidato]
        else:
            decisoes[drone_id] = decisoes_tenentes.get(
                drone_id,
                valor_padrao,
            )
            valores_corretos[drone_id] = votos.get(
                drone_id,
                [valor_padrao],
            )

    acordo = bool(decisoes) and len(set(decisoes.values())) == 1
    escolhido = next(iter(decisoes.values())) if acordo else None
    dentro_limite = total >= (3 * falhos) + 1
    terminacao = len(decisoes) == len(corretos)

    print("\nMensagens recebidas pelos drones corretos:")
    for drone_id in sorted(valores_corretos):
        print(f"Drone {drone_id}: {valores_corretos[drone_id]}")

    print("\nResultado:")
    print(
        f"Comandante escolhido: "
        f"{f'Drone {escolhido}' if escolhido is not None else 'Nenhum'}"
    )
    print(f"Acordo entre drones corretos: {'Sim' if acordo else 'Não'}")
    print(f"Decisão alcançada: {'Sim' if acordo else 'Não'}")
    print(f"Validade: {'Sim' if escolhido == candidato else 'Não aplicável'}")
    print(f"Terminação: {'Sim' if terminacao else 'Não'}")
    print(
        "Mensagens contraditórias: "
        f"{estatisticas['contraditorias']}"
    )
    print(
        "Status do limite teórico n >= 3f + 1: "
        f"{'Dentro' if dentro_limite else 'Fora'}"
    )
    print(f"Mensagens trocadas: {estatisticas['mensagens']}")

    return {
        "comandante_escolhido": escolhido,
        "decisao_alcancada": acordo,
        "mensagens_trocadas": estatisticas["mensagens"],
        "mensagens_contraditorias": estatisticas["contraditorias"],
        "acordo": acordo,
        "validade": escolhido == candidato if 0 in corretos else None,
        "terminacao": terminacao,
        "status_limite_teorico": (
            "Dentro" if dentro_limite else "Fora"
        ),
        "nivel_om": nivel_om,
        "valor_padrao": valor_padrao,
    }


def salvar_resultado_emulacao(resultado, configuracao, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    comandante = resultado["comandante_escolhido"]
    linhas = [
        "Resultado da emulação Mininet",
        "=" * 31,
        f"Data e hora: {datetime.now():%d/%m/%Y %H:%M:%S}",
        "Ambiente: Mininet",
        f"Algoritmo: {configuracao['algoritmo']}",
        f"Quantidade de drones: {configuracao['drones']}",
        f"Tipo de falha: {configuracao['falha']}",
        f"Quantidade de falhos: {configuracao['falhos']}",
        "Comandante escolhido: "
        f"{f'Drone {comandante}' if comandante is not None else 'Nenhum'}",
        "Decisão alcançada: "
        f"{'Sim' if resultado['decisao_alcancada'] else 'Não'}",
        f"Acordo: {'Sim' if resultado.get('acordo') else 'Não'}",
        "Validade: "
        f"{'Sim' if resultado.get('validade') else 'Não'}",
        "Terminação: "
        f"{'Sim' if resultado.get('terminacao') else 'Não'}",
        f"Mensagens trocadas: {resultado['mensagens_trocadas']}",
        "Mensagens contraditórias: "
        f"{resultado.get('mensagens_contraditorias', 0)}",
    ]
    if resultado.get("status_limite_teorico") is not None:
        linhas.append(
            "Status do limite teórico: "
            f"{resultado['status_limite_teorico']}"
        )
    if resultado.get("numero_proposta") is not None:
        linhas.append(
            f"Número da proposta: {resultado['numero_proposta']}"
        )
    if resultado.get("nivel_om") is not None:
        linhas.append(f"Nível OM(m): {resultado['nivel_om']}")
    linhas.extend(
        [
            "Observação: os drones foram executados como hosts emulados.",
            "Comunicação: sockets TCP com mensagens JSON.",
            "Validação do ambiente: "
            f"{configuracao.get('ambiente_execucao', 'não informado')}.",
        ]
    )
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8-sig")
    return caminho


def encerrar_drones(enderecos):
    for drone_id, ip, porta in enderecos:
        mensagem = criar_mensagem("ENCERRAR", -1, drone_id, None, "controle")
        enviar_mensagem(ip, porta, mensagem, timeout=1)


def ler_endereco(valor):
    drone_id, ip, porta = valor.split(",")
    return int(drone_id), ip, int(porta)


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Controlador da emulação")
    parser.add_argument("--algoritmo", choices=["paxos", "lsp"], required=True)
    parser.add_argument("--drones", type=int, required=True)
    parser.add_argument("--falha", required=True)
    parser.add_argument("--falhos", type=int, required=True)
    parser.add_argument("--candidato", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--numero-proposta", type=int, default=1)
    parser.add_argument("--nivel-om", type=int, default=None)
    parser.add_argument("--valor-padrao", type=int, default=0)
    parser.add_argument(
        "--ambiente-execucao",
        default="Mininet real",
    )
    parser.add_argument("--nome", default="manual")
    parser.add_argument("--saida", required=True)
    parser.add_argument("--endereco", action="append", required=True)
    return parser.parse_args()


def main():
    args = ler_argumentos()
    enderecos = [ler_endereco(valor) for valor in args.endereco]
    configuracao = vars(args)

    try:
        aguardar_drones(enderecos)
        if args.algoritmo == "paxos":
            resultado = executar_paxos(
                enderecos,
                args.candidato,
                args.falha,
                args.falhos,
                args.numero_proposta,
            )
        else:
            resultado = executar_lsp(
                enderecos,
                args.candidato,
                args.falhos,
                m=args.nivel_om,
                valor_padrao=args.valor_padrao,
            )

        caminho = salvar_resultado_emulacao(
            resultado,
            configuracao,
            args.saida,
        )
        print(f"\nResultado salvo em:\n{caminho}")
    finally:
        encerrar_drones(enderecos)


if __name__ == "__main__":
    main()
