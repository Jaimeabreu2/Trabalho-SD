from datetime import datetime


class Mensagem:
    def __init__(
        self,
        tipo,
        origem,
        destino,
        rodada,
        candidato,
        algoritmo,
        timestamp=None,
        numero_proposta=None,
        proposta_aceita=None,
        valor_aceito=None,
        caminho=None,
    ):
        self.tipo = tipo
        self.origem = origem
        self.destino = destino
        self.rodada = rodada
        self.candidato = candidato
        self.algoritmo = algoritmo
        self.timestamp = datetime.now() if timestamp is None else timestamp
        self.numero_proposta = (
            rodada if numero_proposta is None else numero_proposta
        )
        self.proposta_aceita = proposta_aceita
        self.valor_aceito = valor_aceito
        self.caminho = list(caminho or [])
