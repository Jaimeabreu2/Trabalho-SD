import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from simulador import carregar_cenario


PASTA_PROJETO = Path(__file__).resolve().parent.parent


class TestCenarios(unittest.TestCase):
    def test_carrega_cenario_paxos_valido(self):
        cenario = carregar_cenario(
            PASTA_PROJETO / "cenarios" / "paxos_5_crash.json"
        )

        self.assertEqual(cenario["algoritmo"], "paxos")
        self.assertEqual(cenario["drones"], 5)

    def test_carrega_cenario_lsp_valido(self):
        cenario = carregar_cenario(
            PASTA_PROJETO / "cenarios" / "lsp_5_bizantina_1.json"
        )

        self.assertEqual(cenario["algoritmo"], "lsp")
        self.assertEqual(cenario["falha"], "bizantina")
        self.assertEqual(cenario["nivel_om"], 1)
        self.assertEqual(cenario["valor_padrao"], 0)

    def test_detecta_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            carregar_cenario(PASTA_PROJETO / "cenarios" / "inexistente.json")

    def test_detecta_campo_obrigatorio_ausente(self):
        dados = {
            "nome": "incompleto",
            "algoritmo": "paxos",
        }

        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "incompleto.json"
            caminho.write_text(json.dumps(dados), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Campos obrigatórios"):
                carregar_cenario(caminho)

    def test_executa_simulacao_usando_cenario(self):
        resultado = subprocess.run(
            [
                sys.executable,
                str(PASTA_PROJETO / "main.py"),
                "--cenario",
                str(PASTA_PROJETO / "cenarios" / "paxos_5_crash.json"),
            ],
            cwd=PASTA_PROJETO,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertIn("Cenário: paxos_5_crash", resultado.stdout)
        self.assertIn("Algoritmo: PAXOS", resultado.stdout)

    def test_comando_manual_continua_funcionando(self):
        resultado = subprocess.run(
            [
                sys.executable,
                str(PASTA_PROJETO / "main.py"),
                "--algoritmo",
                "paxos",
                "--drones",
                "3",
                "--falha",
                "nenhuma",
            ],
            cwd=PASTA_PROJETO,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertIn("Quantidade de drones: 3", resultado.stdout)
        self.assertIn("Decisão alcançada: Sim", resultado.stdout)

    def test_configuracao_manual_invalida_nao_mostra_traceback(self):
        resultado = subprocess.run(
            [
                sys.executable,
                str(PASTA_PROJETO / "main.py"),
                "--drones",
                "0",
            ],
            cwd=PASTA_PROJETO,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn("Configuração inválida:", resultado.stderr)
        self.assertNotIn("Traceback", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
