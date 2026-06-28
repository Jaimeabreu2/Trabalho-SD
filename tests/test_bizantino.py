import unittest

from drone import Drone
from mensagem import Mensagem
from rede import Rede


class TestFalhaBizantina(unittest.TestCase):
    def test_drone_correto_nao_altera_candidato(self):
        rede = Rede(seed=42)
        origem = Drone(0)
        destino = Drone(1)
        rede.registrar_drone(origem)
        rede.registrar_drone(destino)

        rede.enviar(Mensagem("VALOR", 0, 1, 1, 7, "TESTE"))

        recebida = destino.listar_mensagens()[0]
        self.assertEqual(recebida.candidato, 7)
        self.assertEqual(origem.mensagens_contraditorias, 0)

    def test_drone_bizantino_envia_candidatos_diferentes(self):
        _, destinos, valores = self._executar_cenario(seed=42)

        self.assertEqual(len(destinos), 4)
        self.assertEqual(len(set(valores)), 4)

    def test_contador_de_mensagens_contraditorias(self):
        bizantino, _, _ = self._executar_cenario(seed=42)

        self.assertEqual(bizantino.mensagens_contraditorias, 4)
        self.assertEqual(len(bizantino.historico_valores_enviados), 4)

    def test_seed_repete_comportamento_bizantino(self):
        _, _, valores_1 = self._executar_cenario(seed=15)
        _, _, valores_2 = self._executar_cenario(seed=15)

        self.assertEqual(valores_1, valores_2)

    def _executar_cenario(self, seed):
        rede = Rede(seed=seed)
        drones = [Drone(i) for i in range(4)]
        bizantino = Drone(4, comportamento="bizantina")
        todos = drones + [bizantino]

        for drone in todos:
            rede.registrar_drone(drone)

        for destino in drones:
            rede.enviar(
                Mensagem("VALOR", 4, destino.id, 1, 4, "TESTE")
            )

        valores = [
            drone.listar_mensagens()[0].candidato for drone in drones
        ]
        return bizantino, drones, valores


if __name__ == "__main__":
    unittest.main()
