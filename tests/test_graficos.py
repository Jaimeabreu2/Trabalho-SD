import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from graficos import gerar_graficos_resultados
from main import gerar_graficos_execucao


PASTA_PROJETO = Path(__file__).resolve().parent.parent
MATPLOTLIB_INSTALADO = importlib.util.find_spec("matplotlib") is not None


def resultado_teste():
    return {
        "cenario": "teste",
        "algoritmo": "Paxos",
        "mensagens_enviadas": 10,
        "tempo_execucao": 0.01,
        "decisao_alcancada": True,
        "mensagens_contraditorias": 0,
    }


class TestGraficos(unittest.TestCase):
    def test_funcao_de_graficos_e_chamada(self):
        with patch("main.gerar_graficos_resultados", return_value=[]) as funcao:
            gerar_graficos_execucao([resultado_teste()])

        funcao.assert_called_once()

    def test_sem_resultados_nao_gera_grafico(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivos = gerar_graficos_resultados([], pasta)

        self.assertEqual(arquivos, [])

    @unittest.skipUnless(MATPLOTLIB_INSTALADO, "matplotlib não instalado")
    def test_cria_pasta_e_arquivo_png(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "graficos"
            arquivos = gerar_graficos_resultados(
                [resultado_teste()],
                saida,
            )

            self.assertTrue(saida.is_dir())
            self.assertTrue(arquivos)
            self.assertTrue(all(caminho.is_file() for caminho in arquivos))

    def test_todos_csv_graficos_nao_quebra(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = subprocess.run(
                [
                    sys.executable,
                    str(PASTA_PROJETO / "main.py"),
                    "--todos",
                    "--seed",
                    "42",
                    "--csv",
                    "--graficos",
                ],
                cwd=pasta,
                capture_output=True,
                text=True,
            )

            self.assertEqual(resultado.returncode, 0)
            self.assertIn("Resumo geral dos cenários:", resultado.stdout)
            self.assertTrue(
                "Gráficos gerados na pasta:" in resultado.stdout
                or "Não foi possível gerar gráficos." in resultado.stdout
            )


if __name__ == "__main__":
    unittest.main()
