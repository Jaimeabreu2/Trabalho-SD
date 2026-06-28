import unittest

from drone import Drone
from lsp import LamportShostakPease, verificar_limite_bizantino
from rede import Rede


class TestLimiteBizantino(unittest.TestCase):
    def test_cinco_drones_e_um_bizantino_dentro_do_limite(self):
        resultado = verificar_limite_bizantino(5, 1)

        self.assertTrue(resultado["dentro_limite"])
        self.assertEqual(resultado["maximo_tolerado"], 1)

    def test_cinco_drones_e_dois_bizantinos_fora_do_limite(self):
        resultado = verificar_limite_bizantino(5, 2)

        self.assertFalse(resultado["dentro_limite"])
        self.assertEqual(resultado["maximo_tolerado"], 1)

    def test_dez_drones_e_tres_bizantinos_dentro_do_limite(self):
        resultado = verificar_limite_bizantino(10, 3)
        self.assertTrue(resultado["dentro_limite"])

    def test_dez_drones_e_quatro_bizantinos_fora_do_limite(self):
        resultado = verificar_limite_bizantino(10, 4)
        self.assertFalse(resultado["dentro_limite"])

    def test_lsp_executa_fora_do_limite(self):
        rede = Rede(seed=42)
        drones = [
            Drone(0),
            Drone(1),
            Drone(2),
            Drone(3, comportamento="bizantina"),
            Drone(4, comportamento="bizantina"),
        ]

        for drone in drones:
            rede.registrar_drone(drone)

        lsp = LamportShostakPease(rede)
        lsp.executar(comandante_id=0, candidato=2)

        self.assertIsNotNone(lsp.limite_bizantino)
        self.assertFalse(lsp.limite_bizantino["dentro_limite"])
        self.assertGreater(rede.mensagens_enviadas, 0)


if __name__ == "__main__":
    unittest.main()
