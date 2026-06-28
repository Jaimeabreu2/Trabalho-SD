import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from main import executar_dados_cenario
from simulador import carregar_cenario

PASTA_PROJETO = Path(__file__).resolve().parent.parent
MAIN = str(PASTA_PROJETO / "main.py")


def executar(*argumentos):
    return subprocess.run(
        [sys.executable, MAIN, *argumentos],
        cwd=PASTA_PROJETO,
        capture_output=True,
        text=True,
        check=True,
    )


class TestVerbose(unittest.TestCase):
    def test_sem_verbose_mantem_saida_resumida(self):
        resultado = executar("--algoritmo", "paxos", "--drones", "3")
        self.assertNotIn("[VERBOSE]", resultado.stdout)

    def test_verbose_funciona_com_paxos(self):
        resultado = executar(
            "--algoritmo",
            "paxos",
            "--drones",
            "5",
            "--falha",
            "crash",
            "--falhos",
            "1",
            "--verbose",
        )

        self.assertIn("[VERBOSE] Iniciando Paxos.", resultado.stdout)
        self.assertIn("Número da proposta: 1", resultado.stdout)
        self.assertIn("Maioria de PROMISE alcançada", resultado.stdout)
        self.assertIn("Valor escolhido após PROMISE", resultado.stdout)
        self.assertIn("Decisão alcançada: Sim", resultado.stdout)

    def test_verbose_funciona_com_lsp(self):
        resultado = executar(
            "--algoritmo",
            "lsp",
            "--drones",
            "5",
            "--falha",
            "bizantina",
            "--falhos",
            "1",
            "--seed",
            "42",
            "--verbose",
        )

        self.assertIn(
            "[VERBOSE] Iniciando Lamport-Shostak-Pease OM(1).",
            resultado.stdout,
        )
        self.assertIn("OM(1) comandante", resultado.stdout)
        self.assertIn("Drone bizantino", resultado.stdout)
        self.assertIn("Acordo entre drones corretos: Sim", resultado.stdout)

    def test_cenario_funciona_com_verbose(self):
        resultado = executar(
            "--cenario",
            "cenarios/lsp_5_bizantina_1.json",
            "--verbose",
        )

        self.assertIn("[VERBOSE]", resultado.stdout)
        self.assertIn("Cenário: lsp_5_bizantina_1", resultado.stdout)

    def test_todos_funciona_com_verbose(self):
        resultado = executar("--todos", "--seed", "42", "--verbose")

        self.assertIn(
            "[VERBOSE] ===== Cenário: paxos_5_crash =====",
            resultado.stdout,
        )
        self.assertIn(
            "[VERBOSE] ===== Cenário: lsp_10_bizantina_4 =====",
            resultado.stdout,
        )
        self.assertIn("Resumo geral dos cenários:", resultado.stdout)

    def test_verbose_nao_altera_resultado(self):
        cenario = carregar_cenario(
            PASTA_PROJETO / "cenarios" / "lsp_5_bizantina_1.json"
        )
        sem_verbose = executar_dados_cenario(
            cenario,
            seed=42,
            verbose=False,
        )
        with redirect_stdout(StringIO()):
            com_verbose = executar_dados_cenario(
                cenario,
                seed=42,
                verbose=True,
            )

        sem_verbose.pop("tempo_execucao")
        com_verbose.pop("tempo_execucao")
        self.assertEqual(sem_verbose, com_verbose)


if __name__ == "__main__":
    unittest.main()
