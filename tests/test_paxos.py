import unittest

from drone import Drone
from paxos import PaxosBasico
from rede import Rede


class TestPaxosBasico(unittest.TestCase):
    def setUp(self):
        self.rede = Rede()
        self.drones = [Drone(drone_id) for drone_id in range(5)]

        for drone in self.drones:
            self.rede.registrar_drone(drone)

        self.paxos = PaxosBasico(self.rede)
        self.resultado = self.paxos.executar(proponente_id=0, candidato=2)

    def test_paxos_decide_um_comandante(self):
        self.assertTrue(self.paxos.decisao_alcancada)
        self.assertEqual(self.resultado, 2)

    def test_todos_recebem_a_mesma_decisao(self):
        decisoes = {drone.decisao_final for drone in self.drones}
        self.assertEqual(decisoes, {2})

    def test_comandante_e_o_candidato_proposto(self):
        self.assertEqual(self.paxos.comandante_escolhido, 2)

    def test_consegue_maioria_de_promise(self):
        self.assertTrue(self.paxos.maioria_promise)
        self.assertGreaterEqual(self.paxos.votos_promise, self.paxos.maioria)

    def test_consegue_maioria_de_accepted(self):
        self.assertTrue(self.paxos.maioria_accepted)
        self.assertGreaterEqual(self.paxos.votos_accepted, self.paxos.maioria)


class TestPaxosComFalhas(unittest.TestCase):
    def executar(self, comportamentos, taxa_omissao=0, atraso_max=0):
        rede = Rede(seed=42)
        drones = []

        for drone_id, comportamento in enumerate(comportamentos):
            drone = Drone(
                drone_id,
                comportamento=comportamento,
                taxa_omissao=taxa_omissao if comportamento == "omissao" else 0,
                atraso_max=atraso_max if comportamento == "temporizacao" else 0,
            )
            drones.append(drone)
            rede.registrar_drone(drone)

        paxos = PaxosBasico(rede)
        paxos.executar(proponente_id=0, candidato=2)
        return paxos, drones

    def test_um_crash_ainda_permite_decisao(self):
        paxos, drones = self.executar(
            ["nenhuma", "nenhuma", "nenhuma", "nenhuma", "crash"]
        )

        self.assertTrue(paxos.decisao_alcancada)
        self.assertEqual(paxos.votos_promise, 4)
        self.assertTrue(all(drone.decisao_final == 2 for drone in drones[:4]))

    def test_crashes_demais_impedem_decisao(self):
        paxos, _ = self.executar(
            ["nenhuma", "nenhuma", "crash", "crash", "crash"]
        )

        self.assertFalse(paxos.decisao_alcancada)
        self.assertFalse(paxos.maioria_promise)
        self.assertEqual(paxos.votos_accepted, 0)

    def test_omissao_total_impede_decisao(self):
        paxos, drones = self.executar(
            ["omissao"] * 5,
            taxa_omissao=1.0,
        )

        self.assertFalse(paxos.decisao_alcancada)
        self.assertEqual(paxos.votos_promise, 0)
        self.assertGreater(sum(d.mensagens_omitidas for d in drones), 0)

    def test_temporizacao_registra_mensagens_atrasadas(self):
        paxos, drones = self.executar(
            ["nenhuma", "nenhuma", "nenhuma", "nenhuma", "temporizacao"],
            atraso_max=0.001,
        )

        self.assertTrue(paxos.decisao_alcancada)
        self.assertGreater(sum(d.mensagens_atrasadas for d in drones), 0)


class TestSegurancaPaxos(unittest.TestCase):
    def criar_rede(self):
        rede = Rede(seed=42)
        drones = [Drone(i) for i in range(5)]
        for drone in drones:
            rede.registrar_drone(drone)
        return rede, drones

    def test_proposta_maior_preserva_valor_ja_aceito(self):
        rede, drones = self.criar_rede()

        primeira = PaxosBasico(rede)
        primeira.executar(0, 1, numero_proposta=1)

        segunda = PaxosBasico(rede)
        resultado = segunda.executar(0, 2, numero_proposta=2)

        self.assertEqual(resultado, 1)
        self.assertEqual({drone.decisao_final for drone in drones}, {1})
        self.assertEqual(segunda.valor_escolhido, 1)
        self.assertTrue(segunda.resultado_metricas["validade"])

    def test_promise_informa_valor_aceito_anterior(self):
        rede, _ = self.criar_rede()
        primeira = PaxosBasico(rede)
        primeira.executar(0, 1, numero_proposta=1)

        segunda = PaxosBasico(rede)
        segunda.executar(0, 2, numero_proposta=2)

        self.assertTrue(segunda.promessas_recebidas)
        self.assertTrue(
            all(
                promessa.proposta_aceita == 1
                and promessa.valor_aceito == 1
                for promessa in segunda.promessas_recebidas
            )
        )

    def test_prepare_antigo_e_rejeitado(self):
        rede, _ = self.criar_rede()
        paxos = PaxosBasico(rede)
        paxos.executar(0, 2, numero_proposta=5)

        antigo = PaxosBasico(rede)
        resultado = antigo.executar(0, 3, numero_proposta=4)

        self.assertIsNone(resultado)
        self.assertEqual(antigo.votos_promise, 0)

    def test_accept_request_antigo_e_rejeitado(self):
        rede, drones = self.criar_rede()
        drones[1].maior_proposta_prometida = 5
        paxos = PaxosBasico(rede)

        resposta = paxos._responder_accept_request(1, 0, 4, 2)

        self.assertIsNone(resposta)
        self.assertIsNone(drones[1].proposta_aceita)
        self.assertIsNone(drones[1].valor_aceito)


if __name__ == "__main__":
    unittest.main()
