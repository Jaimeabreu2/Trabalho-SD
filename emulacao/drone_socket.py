import argparse
import json
import random
import socket
import time


def criar_mensagem(
    tipo,
    origem,
    destino,
    candidato,
    algoritmo,
    **campos_extras,
):
    mensagem = {
        "tipo": tipo,
        "origem": origem,
        "destino": destino,
        "candidato": candidato,
        "algoritmo": algoritmo,
    }
    mensagem.update(campos_extras)
    return mensagem


def deve_omitir(taxa_omissao, gerador):
    return gerador.random() < taxa_omissao


def alterar_candidato(candidato, destino, quantidade_drones):
    if quantidade_drones <= 1:
        return candidato

    novo = (destino + 1) % quantidade_drones
    if novo == candidato:
        novo = (novo + 1) % quantidade_drones
    return novo


def processar_mensagem(mensagem, configuracao, gerador):
    tipo = mensagem.get("tipo")
    comportamento = configuracao["comportamento"]

    if tipo == "ENCERRAR":
        return {"tipo": "ENCERRADO"}, True

    # Se o drone estiver em crash, ele não responde.
    if comportamento == "crash":
        return None, False

    if comportamento == "omissao" and deve_omitir(
        configuracao["taxa_omissao"],
        gerador,
    ):
        return None, False

    if comportamento == "temporizacao":
        atraso = gerador.uniform(0, configuracao["atraso_max"])
        time.sleep(atraso)

    configuracao.setdefault("maior_proposta_prometida", -1)
    configuracao.setdefault("proposta_aceita", None)
    configuracao.setdefault("valor_aceito", None)
    configuracao.setdefault("decisao_final", None)

    if tipo == "PREPARE":
        numero = mensagem.get("numero_proposta", 1)
        if numero <= configuracao["maior_proposta_prometida"]:
            return criar_mensagem(
                "REJECTED",
                configuracao["id"],
                mensagem.get("origem"),
                None,
                "paxos",
                numero_proposta=numero,
            ), False

        configuracao["maior_proposta_prometida"] = numero
        return criar_mensagem(
            "PROMISE",
            configuracao["id"],
            mensagem.get("origem"),
            configuracao["valor_aceito"],
            "paxos",
            numero_proposta=numero,
            proposta_aceita=configuracao["proposta_aceita"],
            valor_aceito=configuracao["valor_aceito"],
        ), False

    if tipo == "ACCEPT_REQUEST":
        numero = mensagem.get("numero_proposta", 1)
        if numero < configuracao["maior_proposta_prometida"]:
            return criar_mensagem(
                "REJECTED",
                configuracao["id"],
                mensagem.get("origem"),
                None,
                "paxos",
                numero_proposta=numero,
            ), False

        configuracao["maior_proposta_prometida"] = numero
        configuracao["proposta_aceita"] = numero
        configuracao["valor_aceito"] = mensagem.get("candidato")
        return criar_mensagem(
            "ACCEPTED",
            configuracao["id"],
            mensagem.get("origem"),
            configuracao["valor_aceito"],
            "paxos",
            numero_proposta=numero,
        ), False

    if tipo == "DECIDE":
        valor = mensagem.get("candidato")
        decisao_atual = configuracao["decisao_final"]
        if decisao_atual is None or decisao_atual == valor:
            configuracao["decisao_final"] = valor
        return criar_mensagem(
            "DECIDE_ACK",
            configuracao["id"],
            mensagem.get("origem"),
            configuracao["decisao_final"],
            "paxos",
        ), False

    respostas = {
        "ORDER": "ORDER_ACK",
        "FORWARD": "FORWARD_RESPONSE",
    }
    tipo_resposta = respostas.get(tipo, "ACK")
    candidato = mensagem.get("candidato")

    if comportamento == "bizantina" and tipo in ("ORDER", "FORWARD"):
        candidato = alterar_candidato(
            candidato,
            mensagem["destino"],
            configuracao["quantidade_drones"],
        )

    resposta = criar_mensagem(
        tipo_resposta,
        configuracao["id"],
        mensagem.get("origem"),
        candidato,
        mensagem.get("algoritmo"),
    )
    return resposta, False


class ServidorDrone:
    def __init__(self, configuracao, host="0.0.0.0", porta=5000):
        self.configuracao = configuracao
        self.gerador = random.Random(configuracao["seed"])
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, porta))
        self.socket.listen()
        self.porta = self.socket.getsockname()[1]
        self.ativo = True

    def servir(self):
        drone_id = self.configuracao["id"]
        print(f"Drone {drone_id} escutando na porta {self.porta}.", flush=True)

        while self.ativo:
            conexao, _ = self.socket.accept()
            with conexao:
                dados = conexao.recv(65536)
                if not dados:
                    continue

                mensagem = json.loads(dados.decode("utf-8"))
                print(
                    f"Drone {drone_id} recebeu {mensagem.get('tipo')}.",
                    flush=True,
                )
                resposta, encerrar = processar_mensagem(
                    mensagem,
                    self.configuracao,
                    self.gerador,
                )

                if resposta is not None:
                    conexao.sendall(json.dumps(resposta).encode("utf-8"))

                if encerrar:
                    self.ativo = False

        self.socket.close()


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Drone emulado por socket")
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--porta", type=int, default=5000)
    parser.add_argument(
        "--comportamento",
        choices=[
            "nenhuma",
            "crash",
            "omissao",
            "temporizacao",
            "bizantina",
        ],
        default="nenhuma",
    )
    parser.add_argument("--taxa-omissao", type=float, default=0)
    parser.add_argument("--atraso-max", type=float, default=0)
    parser.add_argument("--drones", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = ler_argumentos()
    configuracao = {
        "id": args.id,
        "comportamento": args.comportamento,
        "taxa_omissao": args.taxa_omissao,
        "atraso_max": args.atraso_max,
        "quantidade_drones": args.drones,
        "seed": args.seed,
        "maior_proposta_prometida": -1,
        "proposta_aceita": None,
        "valor_aceito": None,
        "decisao_final": None,
    }
    ServidorDrone(configuracao, porta=args.porta).servir()


if __name__ == "__main__":
    main()
