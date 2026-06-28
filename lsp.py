from collections import Counter
from time import perf_counter

from mensagem import Mensagem
from metricas import criar_resultado


def verificar_limite_bizantino(n, f):
    if n < 1:
        raise ValueError("A quantidade de drones deve ser maior que zero.")

    if f < 0 or f > n:
        raise ValueError("A quantidade de falhas bizantinas é inválida.")

    dentro_limite = n >= (3 * f) + 1
    maximo_tolerado = (n - 1) // 3

    if dentro_limite:
        mensagem = (
            "Limite teórico bizantino: dentro da garantia clássica."
        )
    else:
        mensagem = (
            "Atenção: este cenário está acima do limite teórico clássico "
            "de tolerância bizantina. O algoritmo será executado, mas o "
            "consenso não possui garantia teórica."
        )

    return {
        "dentro_limite": dentro_limite,
        "maximo_tolerado": maximo_tolerado,
        "mensagem": mensagem,
    }


class LamportShostakPease:
    def __init__(self, rede, valor_padrao=0):
        self.rede = rede
        self.valor_padrao = valor_padrao
        self.valores_recebidos = {}
        self.comandante_escolhido = None
        self.acordo = False
        self.decisao_alcancada = False
        self.limite_bizantino = None
        self.resultado_metricas = None
        self.tempo_execucao = 0
        self.nivel_om = 0

    def executar(self, comandante_id, candidato, m=None):
        inicio = perf_counter()
        if comandante_id not in self.rede.drones:
            raise ValueError("O comandante inicial não está registrado.")

        drones = list(self.rede.drones.values())
        corretos = [drone for drone in drones if not drone.bizantino]
        quantidade_bizantinos = len(drones) - len(corretos)
        self.nivel_om = quantidade_bizantinos if m is None else m

        if self.nivel_om < 0:
            raise ValueError("O nível OM(m) não pode ser negativo.")

        self.rede.drones[comandante_id].candidato_proposto = candidato
        self.rede.log(
            f"Iniciando Lamport-Shostak-Pease OM({self.nivel_om})."
        )
        self.rede.log(f"Comandante inicial: Drone {comandante_id}.")
        self.rede.log(f"Candidato proposto: Drone {candidato}.")
        self.rede.log(f"Valor padrão: Drone {self.valor_padrao}.")

        ids_bizantinos = [
            str(drone.id) for drone in drones if drone.bizantino
        ]
        self.rede.log(
            "Drones bizantinos: "
            f"{', '.join(ids_bizantinos) if ids_bizantinos else 'nenhum'}."
        )

        self.limite_bizantino = verificar_limite_bizantino(
            len(drones),
            quantidade_bizantinos,
        )
        self.rede.log(self.limite_bizantino["mensagem"])

        participantes = [drone.id for drone in drones]
        decisoes_tenentes, votos_tenentes = self._om(
            self.nivel_om,
            comandante_id,
            candidato,
            participantes,
            [comandante_id],
        )

        self.valores_recebidos = {}
        decisoes_corretas = []
        for drone in corretos:
            if drone.id == comandante_id:
                decisao = candidato
                votos = [candidato]
            else:
                decisao = decisoes_tenentes.get(
                    drone.id,
                    self.valor_padrao,
                )
                votos = votos_tenentes.get(
                    drone.id,
                    [self.valor_padrao],
                )

            drone.decisao_final = decisao
            self.valores_recebidos[drone.id] = votos
            decisoes_corretas.append(decisao)
            self.rede.log(
                f"Drone {drone.id} recebeu valores {votos} "
                f"e decidiu pelo Drone {decisao}."
            )
            drone.receber_mensagem(
                Mensagem(
                    "DECISION",
                    drone.id,
                    drone.id,
                    self.nivel_om + 2,
                    decisao,
                    "LSP",
                    caminho=[drone.id],
                )
            )

        self.acordo = (
            bool(decisoes_corretas)
            and len(set(decisoes_corretas)) == 1
        )
        self.decisao_alcancada = self.acordo
        self.comandante_escolhido = (
            decisoes_corretas[0] if self.acordo else None
        )
        self.rede.log(
            "Acordo entre drones corretos: "
            f"{'Sim' if self.acordo else 'Não'}."
        )

        self.tempo_execucao = perf_counter() - inicio
        self.resultado_metricas = criar_resultado(
            algoritmo="Lamport-Shostak-Pease",
            drones=drones,
            rede=self.rede,
            candidato_esperado=candidato,
            comandante_escolhido=self.comandante_escolhido,
            decisao_alcancada=self.decisao_alcancada,
            tempo_execucao=self.tempo_execucao,
            limite_bizantino=self.limite_bizantino,
        )
        return self.comandante_escolhido

    def _om(self, nivel, comandante_id, valor, participantes, caminho):
        tenentes = [
            drone_id
            for drone_id in participantes
            if drone_id != comandante_id
        ]
        recebidos_diretos = {}

        self.rede.log(
            f"OM({nivel}) comandante Drone {comandante_id}, "
            f"caminho {caminho}."
        )

        for destino_id in tenentes:
            tipo = "ORDER" if len(caminho) == 1 else "FORWARD"
            mensagem = Mensagem(
                tipo,
                comandante_id,
                destino_id,
                len(caminho),
                valor,
                "LSP",
                caminho=caminho,
            )
            if self.rede.enviar(mensagem):
                recebida = self.rede.drones[
                    destino_id
                ].listar_mensagens()[-1]
                valor_recebido = recebida.candidato
            else:
                valor_recebido = self.valor_padrao
                self.rede.log(
                    f"Drone {destino_id} não recebeu pelo caminho "
                    f"{caminho}; usando valor padrão "
                    f"{self.valor_padrao}."
                )
            recebidos_diretos[destino_id] = valor_recebido

        if nivel == 0 or len(tenentes) <= 1:
            votos = {
                drone_id: [valor_recebido]
                for drone_id, valor_recebido in recebidos_diretos.items()
            }
            return recebidos_diretos, votos

        resultados_repassados = {}
        proximos_participantes = tenentes
        for novo_comandante in tenentes:
            resultado, _ = self._om(
                nivel - 1,
                novo_comandante,
                recebidos_diretos[novo_comandante],
                proximos_participantes,
                caminho + [novo_comandante],
            )
            resultados_repassados[novo_comandante] = resultado

        decisoes = {}
        votos_finais = {}
        for receptor in tenentes:
            valores = [recebidos_diretos[receptor]]
            for novo_comandante in tenentes:
                if novo_comandante == receptor:
                    continue
                valores.append(
                    resultados_repassados[novo_comandante].get(
                        receptor,
                        self.valor_padrao,
                    )
                )

            votos_finais[receptor] = valores
            decisoes[receptor] = self.decidir_por_maioria(
                valores,
                self.valor_padrao,
            )
            self.rede.log(
                f"Maioria no caminho {caminho} para Drone {receptor}: "
                f"{valores} -> {decisoes[receptor]}."
            )

        return decisoes, votos_finais

    @staticmethod
    def decidir_por_maioria(valores, valor_padrao=0):
        if not valores:
            return valor_padrao

        contagem = Counter(valores)
        maior_quantidade = max(contagem.values())
        mais_frequentes = [
            valor
            for valor, quantidade in contagem.items()
            if quantidade == maior_quantidade
        ]

        if len(mais_frequentes) != 1:
            return valor_padrao
        return mais_frequentes[0]
