import random
import time

from falhas import deve_omitir, gerar_candidato_falso, sortear_atraso
from log_simulacao import LogSimulacao
from mensagem import Mensagem


class Rede:
    def __init__(self, seed=None, verbose=False):
        self.drones = {}
        self.mensagens_enviadas = 0
        self.mensagens_recebidas = 0
        self.gerador = random.Random(seed)
        self.logger = LogSimulacao(verbose)

    def log(self, mensagem):
        self.logger.mostrar(mensagem)

    def registrar_drone(self, drone):
        self.drones[drone.id] = drone

    def enviar(self, mensagem):
        if mensagem.origem not in self.drones:
            raise ValueError("Drone de origem não está registrado.")

        if mensagem.destino not in self.drones:
            raise ValueError("Drone de destino não está registrado.")

        origem = self.drones[mensagem.origem]
        destino = self.drones[mensagem.destino]

        # Drone em crash não participa da comunicação.
        if not origem.ativo:
            self.log(
                f"Drone {origem.id} está em crash e não enviou "
                f"{mensagem.tipo}."
            )
            return False

        self.mensagens_enviadas += 1
        self.log(
            f"Drone {origem.id} enviou {mensagem.tipo} "
            f"para Drone {destino.id}."
        )

        if origem.bizantino:
            mensagem = self._alterar_mensagem_bizantina(origem, mensagem)

        if not destino.ativo:
            self.log(
                f"Drone {destino.id} está em crash e não recebeu "
                f"{mensagem.tipo}."
            )
            return False

        # A omissão descarta algumas mensagens.
        for drone in (origem, destino):
            if deve_omitir(drone, self.gerador):
                drone.mensagens_omitidas += 1
                self.log(
                    f"Mensagem omitida entre Drone {origem.id} "
                    f"e Drone {destino.id}."
                )
                return False

        atrasos = []
        for drone in (origem, destino):
            atraso = sortear_atraso(drone, self.gerador)
            if atraso > 0:
                drone.mensagens_atrasadas += 1
                atrasos.append(atraso)
                self.log(
                    f"Mensagem atrasada para Drone {destino.id}."
                )

        # A temporização simula atraso na entrega.
        if atrasos:
            time.sleep(max(atrasos))

        destino.receber_mensagem(mensagem)
        self.mensagens_recebidas += 1
        return True

    def _alterar_mensagem_bizantina(self, drone, mensagem):
        valores_usados = {
            valor for _, valor in drone.historico_valores_enviados
        }
        candidato_falso = gerar_candidato_falso(
            mensagem.candidato,
            list(self.drones),
            valores_usados,
            self.gerador,
        )

        # Drone bizantino pode trocar o candidato enviado.
        copia = Mensagem(
            tipo=mensagem.tipo,
            origem=mensagem.origem,
            destino=mensagem.destino,
            rodada=mensagem.rodada,
            candidato=candidato_falso,
            algoritmo=mensagem.algoritmo,
            timestamp=mensagem.timestamp,
            numero_proposta=mensagem.numero_proposta,
            proposta_aceita=mensagem.proposta_aceita,
            valor_aceito=mensagem.valor_aceito,
            caminho=mensagem.caminho,
        )
        drone.mensagens_contraditorias += 1
        drone.historico_valores_enviados.append(
            (mensagem.destino, candidato_falso)
        )
        self.log(
            f"Drone bizantino {drone.id} alterou candidato enviado "
            f"para Drone {mensagem.destino}: {candidato_falso}."
        )
        return copia

    def enviar_para_todos(self, mensagem):
        if mensagem.origem not in self.drones:
            raise ValueError("Drone de origem não está registrado.")

        # Envia a mesma mensagem para todos os drones, exceto a origem.
        for drone_id in self.drones:
            if drone_id == mensagem.origem:
                continue

            copia = Mensagem(
                tipo=mensagem.tipo,
                origem=mensagem.origem,
                destino=drone_id,
                rodada=mensagem.rodada,
                candidato=mensagem.candidato,
                algoritmo=mensagem.algoritmo,
                timestamp=mensagem.timestamp,
                numero_proposta=mensagem.numero_proposta,
                proposta_aceita=mensagem.proposta_aceita,
                valor_aceito=mensagem.valor_aceito,
                caminho=mensagem.caminho,
            )
            self.enviar(copia)
