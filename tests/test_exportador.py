import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from exportador import COLUNAS_CSV, salvar_resultados_csv


PASTA_PROJETO = Path(__file__).resolve().parent.parent


def criar_resultado(nome):
    return {
        "cenario": nome,
        "algoritmo": "Paxos",
        "quantidade_drones": 5,
        "tipo_falha": "crash",
        "quantidade_falhos": 1,
        "comandante_escolhido": 2,
        "decisao_alcancada": True,
        "acordo": True,
        "validade": True,
        "terminacao": True,
        "mensagens_enviadas": 23,
        "mensagens_recebidas": 20,
        "mensagens_omitidas": 0,
        "mensagens_atrasadas": 0,
        "mensagens_contraditorias": 0,
        "status_limite_teorico": None,
        "tempo_execucao": 0.001,
    }


class TestExportadorCSV(unittest.TestCase):
    def test_salva_csv_com_um_resultado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultado.csv"
            salvar_resultados_csv([criar_resultado("teste")], caminho)

            with caminho.open(encoding="utf-8", newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo))

            self.assertEqual(len(linhas), 1)
            self.assertEqual(linhas[0]["cenario"], "teste")

    def test_salva_csv_com_varios_resultados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultados.csv"
            resultados = [criar_resultado("um"), criar_resultado("dois")]
            salvar_resultados_csv(resultados, caminho)

            with caminho.open(encoding="utf-8", newline="") as arquivo:
                linhas = list(csv.DictReader(arquivo))

            self.assertEqual(len(linhas), 2)

    def test_cabecalho_csv_esta_correto(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultado.csv"
            salvar_resultados_csv([criar_resultado("teste")], caminho)

            with caminho.open(encoding="utf-8", newline="") as arquivo:
                leitor = csv.reader(arquivo)
                cabecalho = next(leitor)

            self.assertEqual(cabecalho, [nome for nome, _ in COLUNAS_CSV])

    def test_cria_pasta_de_resultados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultados" / "resultado.csv"
            salvar_resultados_csv([criar_resultado("teste")], caminho)

            self.assertTrue(caminho.is_file())

    def test_todos_com_csv_gera_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = subprocess.run(
                [
                    sys.executable,
                    str(PASTA_PROJETO / "main.py"),
                    "--todos",
                    "--seed",
                    "42",
                    "--csv",
                ],
                cwd=pasta,
                capture_output=True,
                text=True,
                check=True,
            )
            caminho = Path(pasta) / "resultados" / "resultados_todos.csv"

            self.assertTrue(caminho.is_file())
            self.assertIn("Arquivo CSV gerado em:", resultado.stdout)

    def test_cenario_com_csv_gera_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            cenario = PASTA_PROJETO / "cenarios" / "paxos_5_crash.json"
            subprocess.run(
                [
                    sys.executable,
                    str(PASTA_PROJETO / "main.py"),
                    "--cenario",
                    str(cenario),
                    "--csv",
                ],
                cwd=pasta,
                capture_output=True,
                text=True,
                check=True,
            )
            caminho = (
                Path(pasta)
                / "resultados"
                / "resultado_paxos_5_crash.csv"
            )

            self.assertTrue(caminho.is_file())


if __name__ == "__main__":
    unittest.main()
