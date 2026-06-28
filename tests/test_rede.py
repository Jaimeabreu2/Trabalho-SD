import unittest

from drone import Drone
from mensagem import Mensagem
from rede import Rede


class TestRede(unittest.TestCase):
    def test_envio_direto_e_envio_para_todos(self):
        rede = Rede()
        drones = [Drone(0), Drone(1), Drone(2)]

        for drone in drones:
            rede.registrar_drone(drone)

        direta = Mensagem("PROPOSTA", 0, 1, 1, 0, "teste")
        rede.enviar(direta)

        geral = Mensagem("AVISO", 0, None, 1, 0, "teste")
        rede.enviar_para_todos(geral)

        self.assertEqual(len(drones[0].listar_mensagens()), 0)
        self.assertEqual(len(drones[1].listar_mensagens()), 2)
        self.assertEqual(len(drones[2].listar_mensagens()), 1)
        self.assertEqual(drones[1].listar_mensagens()[0].tipo, "PROPOSTA")
        self.assertEqual(drones[1].listar_mensagens()[1].tipo, "AVISO")
        self.assertEqual(drones[2].listar_mensagens()[0].tipo, "AVISO")
        self.assertEqual(rede.mensagens_enviadas, 3)
        self.assertEqual(rede.mensagens_recebidas, 3)


if __name__ == "__main__":
    unittest.main()
