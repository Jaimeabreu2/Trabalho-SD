import unittest

from drone import Drone
from mensagem import Mensagem
from rede import Rede


def criar_mensagem(origem, destino):
    return Mensagem("TESTE", origem, destino, 1, 0, "nenhum")


class TestFalhas(unittest.TestCase):
    def test_drone_em_crash_nao_envia(self):
        rede = Rede()
        origem = Drone(0, comportamento="crash")
        destino = Drone(1)
        rede.registrar_drone(origem)
        rede.registrar_drone(destino)

        entregue = rede.enviar(criar_mensagem(0, 1))

        self.assertFalse(entregue)
        self.assertEqual(len(destino.listar_mensagens()), 0)

    def test_drone_em_crash_nao_recebe(self):
        rede = Rede()
        origem = Drone(0)
        destino = Drone(1, comportamento="crash")
        rede.registrar_drone(origem)
        rede.registrar_drone(destino)

        entregue = rede.enviar(criar_mensagem(0, 1))

        self.assertFalse(entregue)
        self.assertEqual(len(destino.listar_mensagens()), 0)

    def test_omissao_com_taxa_total(self):
        rede = Rede()
        origem = Drone(0, comportamento="omissao", taxa_omissao=1.0)
        destino = Drone(1)
        rede.registrar_drone(origem)
        rede.registrar_drone(destino)

        entregue = rede.enviar(criar_mensagem(0, 1))

        self.assertFalse(entregue)
        self.assertEqual(origem.mensagens_omitidas, 1)
        self.assertEqual(rede.mensagens_recebidas, 0)

    def test_temporizacao_registra_atraso(self):
        rede = Rede(seed=5)
        origem = Drone(0, comportamento="temporizacao", atraso_max=0.001)
        destino = Drone(1)
        rede.registrar_drone(origem)
        rede.registrar_drone(destino)

        entregue = rede.enviar(criar_mensagem(0, 1))

        self.assertTrue(entregue)
        self.assertEqual(origem.mensagens_atrasadas, 1)
        self.assertEqual(len(destino.listar_mensagens()), 1)

    def test_seed_repete_resultado_de_omissao(self):
        def executar(seed):
            rede = Rede(seed=seed)
            origem = Drone(0, comportamento="omissao", taxa_omissao=0.5)
            destino = Drone(1)
            rede.registrar_drone(origem)
            rede.registrar_drone(destino)
            return [rede.enviar(criar_mensagem(0, 1)) for _ in range(10)]

        self.assertEqual(executar(20), executar(20))


if __name__ == "__main__":
    unittest.main()
