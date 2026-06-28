import unittest

from drone import Drone
from lsp import LamportShostakPease
from metricas import (
    verificar_acordo,
    verificar_terminacao,
    verificar_validade,
)
from paxos import PaxosBasico
from rede import Rede


class TestMetricas(unittest.TestCase):
    def test_acordo_verdadeiro_com_mesma_decisao(self):
        drones = [Drone(0), Drone(1), Drone(2)]
        for drone in drones:
            drone.decisao_final = 2

        self.assertTrue(verificar_acordo(drones))

    def test_acordo_falso_com_decisoes_diferentes(self):
        drones = [Drone(0), Drone(1)]
        drones[0].decisao_final = 1
        drones[1].decisao_final = 2

        self.assertFalse(verificar_acordo(drones))

    def test_terminacao_verdadeira_quando_todos_decidem(self):
        drones = [Drone(0), Drone(1)]
        for drone in drones:
            drone.decisao_final = 1

        self.assertTrue(verificar_terminacao(drones))

    def test_terminacao_falsa_quando_um_nao_decide(self):
        drones = [Drone(0), Drone(1)]
        drones[0].decisao_final = 1

        self.assertFalse(verificar_terminacao(drones))

    def test_validade_com_proposta_comum(self):
        drones = [Drone(0, candidato_proposto=2), Drone(1, candidato_proposto=2)]
        for drone in drones:
            drone.decisao_final = 2

        self.assertTrue(verificar_validade(drones, 2))

    def test_paxos_preenche_metricas_padronizadas(self):
        rede = Rede()
        for drone_id in range(5):
            rede.registrar_drone(Drone(drone_id))

        paxos = PaxosBasico(rede)
        paxos.executar(0, 2)

        self.assertEqual(paxos.resultado_metricas["algoritmo"], "Paxos")
        self.assertTrue(paxos.resultado_metricas["acordo"])
        self.assertTrue(paxos.resultado_metricas["terminacao"])

    def test_lsp_preenche_metricas_padronizadas(self):
        rede = Rede(seed=42)
        for drone_id in range(4):
            rede.registrar_drone(Drone(drone_id))
        rede.registrar_drone(Drone(4, comportamento="bizantina"))

        lsp = LamportShostakPease(rede)
        lsp.executar(0, 2)

        self.assertEqual(
            lsp.resultado_metricas["algoritmo"],
            "Lamport-Shostak-Pease",
        )
        self.assertTrue(lsp.resultado_metricas["acordo"])
        self.assertEqual(
            lsp.resultado_metricas["status_limite_teorico"],
            "Dentro",
        )


if __name__ == "__main__":
    unittest.main()
