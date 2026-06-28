import importlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import threading
import unittest

from emulacao.controlador_emulacao import (
    encerrar_drones,
    enviar_mensagem,
    executar_lsp,
    executar_paxos,
    salvar_resultado_emulacao,
)
from emulacao.drone_socket import (
    ServidorDrone,
    alterar_candidato,
    criar_mensagem,
    deve_omitir,
)
from emulacao.verificar_ambiente import verificar_dependencias


def configuracao_drone(comportamento="nenhuma"):
    return {
        "id": 1,
        "comportamento": comportamento,
        "taxa_omissao": 0,
        "atraso_max": 0,
        "quantidade_drones": 5,
        "seed": 42,
    }


class TestEmulacao(unittest.TestCase):
    def iniciar_drones(self, comportamentos):
        servidores = []
        threads = []
        enderecos = []

        for drone_id, comportamento in enumerate(comportamentos):
            configuracao = configuracao_drone(comportamento)
            configuracao["id"] = drone_id
            servidor = ServidorDrone(
                configuracao,
                host="127.0.0.1",
                porta=0,
            )
            thread = threading.Thread(target=servidor.servir, daemon=True)
            thread.start()
            servidores.append(servidor)
            threads.append(thread)
            enderecos.append((drone_id, "127.0.0.1", servidor.porta))

        return enderecos, threads

    def test_cria_mensagem_json(self):
        mensagem = criar_mensagem("PREPARE", 0, 1, 2, "paxos")
        texto = json.dumps(mensagem)

        self.assertEqual(json.loads(texto)["tipo"], "PREPARE")
        self.assertEqual(mensagem["candidato"], 2)

    def test_drone_socket_responde_em_localhost(self):
        servidor = ServidorDrone(
            configuracao_drone(),
            host="127.0.0.1",
            porta=0,
        )
        thread = threading.Thread(target=servidor.servir, daemon=True)
        thread.start()

        mensagem = criar_mensagem("PREPARE", 0, 1, 2, "paxos")
        resposta = enviar_mensagem("127.0.0.1", servidor.porta, mensagem)
        encerrar = criar_mensagem("ENCERRAR", -1, 1, None, "controle")
        enviar_mensagem("127.0.0.1", servidor.porta, encerrar)
        thread.join(timeout=2)

        self.assertEqual(resposta["tipo"], "PROMISE")
        self.assertFalse(thread.is_alive())

    def test_omissao_com_taxa_total(self):
        self.assertTrue(deve_omitir(1.0, random.Random(42)))

    def test_comportamento_bizantino_altera_candidato(self):
        alterado = alterar_candidato(2, destino=1, quantidade_drones=5)
        self.assertNotEqual(alterado, 2)

    def test_gera_arquivo_de_resultado(self):
        resultado = {
            "comandante_escolhido": 2,
            "decisao_alcancada": True,
            "mensagens_trocadas": 20,
        }
        configuracao = {
            "algoritmo": "paxos",
            "drones": 5,
            "falha": "crash",
            "falhos": 1,
        }

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultado.txt"
            salvar_resultado_emulacao(resultado, configuracao, caminho)
            texto = caminho.read_text(encoding="utf-8")

            self.assertIn("Resultado da emulação Mininet", texto)
            self.assertIn("Comandante escolhido: Drone 2", texto)

    def test_importa_topologia_sem_mininet(self):
        modulo = importlib.import_module("emulacao.mininet_topologia")
        self.assertTrue(callable(modulo.mininet_disponivel))

    def test_ajuda_da_topologia_funciona_sem_mininet(self):
        caminho = (
            Path(__file__).resolve().parent.parent
            / "emulacao"
            / "mininet_topologia.py"
        )
        resultado = subprocess.run(
            [sys.executable, str(caminho), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertIn("Topologia Mininet dos drones", resultado.stdout)

    def test_ausencia_do_mininet_retorna_erro_amigavel(self):
        modulo = importlib.import_module("emulacao.mininet_topologia")
        if modulo.mininet_disponivel():
            self.skipTest("Mininet está instalado neste ambiente")

        caminho = (
            Path(__file__).resolve().parent.parent
            / "emulacao"
            / "mininet_topologia.py"
        )
        resultado = subprocess.run(
            [sys.executable, str(caminho)],
            capture_output=True,
            text=True,
        )

        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Mininet não encontrado", resultado.stdout)
        self.assertNotIn("Traceback", resultado.stderr)

    def test_verificador_de_ambiente_nao_exige_mininet(self):
        resultado = verificar_dependencias()

        self.assertIn("python3", resultado)
        self.assertIn("mininet", resultado)
        self.assertIn("openvswitch", resultado)
        self.assertIn("linux", resultado)

    def test_controlador_paxos_com_sockets_locais(self):
        enderecos, threads = self.iniciar_drones(["nenhuma"] * 5)
        try:
            resultado = executar_paxos(enderecos, candidato=2)
        finally:
            encerrar_drones(enderecos)
            for thread in threads:
                thread.join(timeout=2)

        self.assertTrue(resultado["decisao_alcancada"])
        self.assertEqual(resultado["comandante_escolhido"], 2)

    def test_controlador_lsp_com_socket_bizantino(self):
        enderecos, threads = self.iniciar_drones(
            ["nenhuma", "nenhuma", "nenhuma", "nenhuma", "bizantina"]
        )
        try:
            resultado = executar_lsp(enderecos, candidato=2, falhos=1)
        finally:
            encerrar_drones(enderecos)
            for thread in threads:
                thread.join(timeout=2)

        self.assertTrue(resultado["decisao_alcancada"])
        self.assertEqual(resultado["comandante_escolhido"], 2)
        self.assertGreater(resultado["mensagens_contraditorias"], 0)

    def test_paxos_emulado_preserva_valor_aceito(self):
        enderecos, threads = self.iniciar_drones(["nenhuma"] * 5)
        try:
            primeira = executar_paxos(
                enderecos,
                candidato=1,
                numero_proposta=1,
            )
            segunda = executar_paxos(
                enderecos,
                candidato=2,
                numero_proposta=2,
            )
        finally:
            encerrar_drones(enderecos)
            for thread in threads:
                thread.join(timeout=2)

        self.assertEqual(primeira["comandante_escolhido"], 1)
        self.assertEqual(segunda["comandante_escolhido"], 1)


if __name__ == "__main__":
    unittest.main()
