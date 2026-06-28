import subprocess
import sys
import unittest
from pathlib import Path

from main import executar_todos_cenarios
from simulador import ARQUIVOS_CENARIOS


PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_CENARIOS = PASTA_PROJETO / "cenarios"


class TestModoTodos(unittest.TestCase):
    def test_executa_todos_os_cenarios_esperados(self):
        resultados = executar_todos_cenarios(seed=42)

        self.assertEqual(len(resultados), len(ARQUIVOS_CENARIOS))
        self.assertEqual(
            [resultado["cenario"] for resultado in resultados],
            [Path(nome).stem for nome in ARQUIVOS_CENARIOS],
        )

    def test_resultados_sao_retornados_em_lista(self):
        caminhos = [
            PASTA_CENARIOS / "paxos_5_crash.json",
            PASTA_CENARIOS / "lsp_5_bizantina_1.json",
        ]
        resultados = executar_todos_cenarios(caminhos, seed=42)

        self.assertIsInstance(resultados, list)
        self.assertEqual(len(resultados), 2)
        self.assertIn("decisao_alcancada", resultados[0])

    def test_falha_em_um_cenario_nao_interrompe_os_demais(self):
        caminhos = [
            PASTA_CENARIOS / "paxos_5_crash.json",
            PASTA_CENARIOS / "arquivo_inexistente.json",
            PASTA_CENARIOS / "lsp_5_bizantina_1.json",
        ]
        resultados = executar_todos_cenarios(caminhos, seed=42)

        self.assertEqual(len(resultados), 3)
        self.assertIn("erro", resultados[1])
        self.assertEqual(resultados[2]["cenario"], "lsp_5_bizantina_1")

    def test_seed_e_aceita_com_modo_todos(self):
        caminho = [PASTA_CENARIOS / "paxos_5_omissao.json"]
        primeira = executar_todos_cenarios(caminho, seed=15)
        segunda = executar_todos_cenarios(caminho, seed=15)

        self.assertEqual(
            primeira[0]["mensagens_omitidas"],
            segunda[0]["mensagens_omitidas"],
        )

    def test_comando_todos_mostra_resumo(self):
        resultado = subprocess.run(
            [sys.executable, str(PASTA_PROJETO / "main.py"), "--todos", "--seed", "42"],
            cwd=PASTA_PROJETO,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertIn("Resumo geral dos cenários:", resultado.stdout)
        self.assertIn("paxos_5_crash", resultado.stdout)
        self.assertIn("lsp_10_bizantina_4", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
