from time import perf_counter

from mensagem import Mensagem
from metricas import criar_resultado


class PaxosBasico:
    def __init__(self, rede):
        self.rede = rede
        self.maioria = (len(rede.drones) // 2) + 1
        self.votos_promise = 0
        self.votos_accepted = 0
        self.comandante_escolhido = None
        self.decisao_alcancada = False
        self.maioria_promise = False
        self.maioria_accepted = False
        self.resultado_metricas = None
        self.tempo_execucao = 0
        self.valor_escolhido = None
        self.promessas_recebidas = []

    def executar(self, proponente_id, candidato, numero_proposta=1):
        inicio = perf_counter()
        if proponente_id not in self.rede.drones:
            raise ValueError("O proponente não está registrado na rede.")

        self.rede.drones[proponente_id].candidato_proposto = candidato
        self.rede.log("Iniciando Paxos.")
        self.rede.log(f"Proponente: Drone {proponente_id}.")
        self.rede.log(f"Candidato proposto: Drone {candidato}.")
        self.rede.log(f"Número da proposta: {numero_proposta}.")
        self.votos_promise = 0
        self.votos_accepted = 0
        self.comandante_escolhido = None
        self.decisao_alcancada = False
        self.maioria_promise = False
        self.maioria_accepted = False
        self.valor_escolhido = candidato
        self.promessas_recebidas = []

        # Envia PREPARE para pedir promessa dos drones.
        for drone_id in self.rede.drones:
            prepare = Mensagem(
                "PREPARE",
                proponente_id,
                drone_id,
                numero_proposta,
                candidato,
                "PAXOS",
                numero_proposta=numero_proposta,
            )
            if self.rede.enviar(prepare):
                promessa = self._responder_prepare(
                    drone_id,
                    proponente_id,
                    numero_proposta,
                )
                if promessa is not None:
                    self.promessas_recebidas.append(promessa)

        self.maioria_promise = self.votos_promise >= self.maioria
        self.rede.log(f"PROMISE recebidos: {self.votos_promise}.")
        if not self.maioria_promise:
            # Sem maioria, o Paxos não decide.
            self.rede.log("Sem maioria de PROMISE. O Paxos não decidiu.")
            self._finalizar_metricas(candidato, inicio)
            return None

        aceites_anteriores = [
            promessa
            for promessa in self.promessas_recebidas
            if promessa.proposta_aceita is not None
        ]
        if aceites_anteriores:
            maior_aceite = max(
                aceites_anteriores,
                key=lambda promessa: promessa.proposta_aceita,
            )
            self.valor_escolhido = maior_aceite.valor_aceito

        # Uma proposta maior preserva o valor aceito de maior número.
        self.rede.drones[proponente_id].candidato_proposto = (
            self.valor_escolhido
        )
        self.rede.log("Maioria de PROMISE alcançada.")
        self.rede.log(
            "Valor escolhido após PROMISE: "
            f"Drone {self.valor_escolhido}."
        )
        self.rede.log("Enviando ACCEPT_REQUEST.")

        for drone_id in self.rede.drones:
            pedido = Mensagem(
                "ACCEPT_REQUEST",
                proponente_id,
                drone_id,
                numero_proposta,
                self.valor_escolhido,
                "PAXOS",
                numero_proposta=numero_proposta,
            )
            if self.rede.enviar(pedido):
                self._responder_accept_request(
                    drone_id,
                    proponente_id,
                    numero_proposta,
                    self.valor_escolhido,
                )

        self.maioria_accepted = self.votos_accepted >= self.maioria
        self.rede.log(f"ACCEPTED recebidos: {self.votos_accepted}.")

        # A decisão só acontece se houver maioria.
        if self.maioria_accepted:
            self.comandante_escolhido = self.valor_escolhido
            self.decisao_alcancada = True
            self._enviar_decisao(
                proponente_id,
                self.valor_escolhido,
                numero_proposta,
            )
            self.rede.log("Maioria de ACCEPTED alcançada.")
            self.rede.log(
                f"Decisão final: Drone {self.valor_escolhido} "
                "será o comandante."
            )
            self.rede.log("Decisão enviada aos drones corretos.")
        else:
            self.rede.log("Sem maioria de ACCEPTED. O Paxos não decidiu.")

        self._finalizar_metricas(self.valor_escolhido, inicio)
        return self.comandante_escolhido

    def _finalizar_metricas(self, candidato, inicio):
        self.tempo_execucao = perf_counter() - inicio
        self.resultado_metricas = criar_resultado(
            algoritmo="Paxos",
            drones=list(self.rede.drones.values()),
            rede=self.rede,
            candidato_esperado=candidato,
            comandante_escolhido=self.comandante_escolhido,
            decisao_alcancada=self.decisao_alcancada,
            tempo_execucao=self.tempo_execucao,
        )

    def _responder_prepare(self, drone_id, proponente_id, numero_proposta):
        drone = self.rede.drones[drone_id]
        if numero_proposta <= drone.maior_proposta_prometida:
            self.rede.log(
                f"Drone {drone_id} rejeitou PREPARE antigo "
                f"{numero_proposta}."
            )
            return None

        drone.maior_proposta_prometida = numero_proposta
        resposta = Mensagem(
            "PROMISE",
            drone_id,
            proponente_id,
            numero_proposta,
            drone.valor_aceito,
            "PAXOS",
            numero_proposta=numero_proposta,
            proposta_aceita=drone.proposta_aceita,
            valor_aceito=drone.valor_aceito,
        )
        if self.rede.enviar(resposta):
            self.votos_promise += 1
            return resposta
        return None

    def _responder_accept_request(
        self,
        drone_id,
        proponente_id,
        numero_proposta,
        candidato,
    ):
        drone = self.rede.drones[drone_id]
        if numero_proposta < drone.maior_proposta_prometida:
            self.rede.log(
                f"Drone {drone_id} rejeitou ACCEPT_REQUEST antigo "
                f"{numero_proposta}."
            )
            return None

        # O valor aceito representa o comandante escolhido.
        drone.maior_proposta_prometida = numero_proposta
        drone.proposta_aceita = numero_proposta
        drone.valor_aceito = candidato

        resposta = Mensagem(
            "ACCEPTED",
            drone_id,
            proponente_id,
            numero_proposta,
            candidato,
            "PAXOS",
            numero_proposta=numero_proposta,
            proposta_aceita=numero_proposta,
            valor_aceito=candidato,
        )
        if self.rede.enviar(resposta):
            self.votos_accepted += 1
            return resposta
        return None

    def _enviar_decisao(self, proponente_id, candidato, numero_proposta):
        for drone_id, drone in self.rede.drones.items():
            decisao = Mensagem(
                "DECIDE",
                proponente_id,
                drone_id,
                numero_proposta,
                candidato,
                "PAXOS",
                numero_proposta=numero_proposta,
            )
            if self.rede.enviar(decisao):
                if (
                    drone.decisao_final is None
                    or drone.decisao_final == candidato
                ):
                    drone.decisao_final = candidato
