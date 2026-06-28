import unittest

from drone import Drone
from lsp import LamportShostakPease
from rede import Rede


class TestLamportShostakPease(unittest.TestCase):
    def setUp(self):
        self.rede = Rede(seed=42)
        self.drones = [Drone(i) for i in range(4)]
        self.bizantino = Drone(4, comportamento="bizantina")
        self.drones.append(self.bizantino)

        for drone in self.drones:
            self.rede.registrar_drone(drone)

        self.lsp = LamportShostakPease(self.rede)
        self.resultado = self.lsp.executar(comandante_id=0, candidato=2)

    def test_lsp_produz_decisao(self):
        self.assertTrue(self.lsp.decisao_alcancada)
        self.assertEqual(self.resultado, 2)

    def test_drones_corretos_decidem_o_mesmo_comandante(self):
        decisoes = {drone.decisao_final for drone in self.drones[:4]}
        self.assertEqual(decisoes, {2})
        self.assertTrue(self.lsp.acordo)

    def test_drone_bizantino_gera_mensagens_contraditorias(self):
        self.assertGreater(self.bizantino.mensagens_contraditorias, 0)
        valores = [
            valor
            for _, valor in self.bizantino.historico_valores_enviados
        ]
        self.assertGreater(len(set(valores)), 1)

    def test_decisao_usa_valor_mais_frequente(self):
        for valores in self.lsp.valores_recebidos.values():
            self.assertEqual(
                LamportShostakPease.decidir_por_maioria(valores),
                2,
            )

    def test_empate_nao_produz_decisao(self):
        decisao = LamportShostakPease.decidir_por_maioria([1, 1, 2, 2])
        self.assertEqual(decisao, 0)

    def test_ausencia_de_maioria_nao_produz_decisao(self):
        decisao = LamportShostakPease.decidir_por_maioria([1, 2, 3, 4])
        self.assertEqual(decisao, 0)

    def test_om_zero_com_comandante_correto(self):
        rede = Rede(seed=42)
        drones = [Drone(i) for i in range(4)]
        for drone in drones:
            rede.registrar_drone(drone)

        lsp = LamportShostakPease(rede)
        resultado = lsp.executar(0, 2, m=0)

        self.assertEqual(resultado, 2)
        self.assertEqual({drone.decisao_final for drone in drones}, {2})

    def test_om_um_termina_com_comandante_bizantino(self):
        rede = Rede(seed=42)
        drones = [Drone(0, comportamento="bizantina")]
        drones.extend(Drone(i) for i in range(1, 5))
        for drone in drones:
            rede.registrar_drone(drone)

        lsp = LamportShostakPease(rede, valor_padrao=0)
        resultado = lsp.executar(0, 2, m=1)

        decisoes_corretas = {drone.decisao_final for drone in drones[1:]}
        self.assertIsNotNone(resultado)
        self.assertEqual(len(decisoes_corretas), 1)
        self.assertTrue(lsp.resultado_metricas["terminacao"])
        self.assertTrue(lsp.limite_bizantino["dentro_limite"])

    def test_om_usa_valor_padrao_quando_mensagem_ausente(self):
        rede = Rede(seed=42)
        rede.registrar_drone(Drone(0))
        rede.registrar_drone(Drone(1, comportamento="crash"))
        lsp = LamportShostakPease(rede, valor_padrao=7)

        decisoes, _ = lsp._om(0, 0, 2, [0, 1], [0])

        self.assertEqual(decisoes[1], 7)

    def test_empate_usa_valor_padrao_configurado(self):
        decisao = LamportShostakPease.decidir_por_maioria(
            [1, 1, 2, 2],
            valor_padrao=9,
        )
        self.assertEqual(decisao, 9)


if __name__ == "__main__":
    unittest.main()
