import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from relatorio import gerar_relatorio


PASTA_PROJETO = Path(__file__).resolve().parent.parent


def criar_resultado(nome="teste", limite=None):
    return {
        "cenario": nome,
        "algoritmo": "Lamport-Shostak-Pease",
        "quantidade_drones": 5,
        "tipo_falha": "bizantina",
        "quantidade_falhos": 1,
        "comandante_escolhido": 2,
        "decisao_alcancada": True,
        "acordo": True,
        "validade": True,
        "terminacao": True,
        "mensagens_enviadas": 20,
        "mensagens_recebidas": 20,
        "mensagens_omitidas": 0,
        "mensagens_atrasadas": 0,
        "mensagens_contraditorias": 4,
        "status_limite_teorico": limite,
        "tempo_execucao": 0.001,
    }


class TestRelatorio(unittest.TestCase):
    def test_gera_relatorio_com_um_resultado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio.txt"
            gerar_relatorio([criar_resultado()], caminho)
            texto = caminho.read_text(encoding="utf-8")

            self.assertIn("Total de cenários executados: 1", texto)

    def test_gera_relatorio_com_varios_resultados(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio.txt"
            gerar_relatorio(
                [criar_resultado("um"), criar_resultado("dois")],
                caminho,
            )
            texto = caminho.read_text(encoding="utf-8")

            self.assertIn("Total de cenários executados: 2", texto)
            self.assertIn("Cenário: dois", texto)

    def test_cria_pasta_e_arquivo_txt(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "resultados" / "relatorio.txt"
            gerar_relatorio([criar_resultado()], caminho)

            self.assertTrue(caminho.is_file())

    def test_relatorio_contem_metricas_de_consenso(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio.txt"
            gerar_relatorio([criar_resultado()], caminho)
            texto = caminho.read_text(encoding="utf-8")

            self.assertIn("Acordo: Sim", texto)
            self.assertIn("Validade: Sim", texto)
            self.assertIn("Terminação: Sim", texto)

    def test_registra_cenario_fora_do_limite(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio.txt"
            gerar_relatorio([criar_resultado(limite="Fora")], caminho)
            texto = caminho.read_text(encoding="utf-8")

            self.assertIn("Observação:", texto)
            self.assertIn("n >= 3f + 1", texto)

    def test_integracao_todos_relatorio(self):
        with tempfile.TemporaryDirectory() as pasta:
            resultado = subprocess.run(
                [
                    sys.executable,
                    str(PASTA_PROJETO / "main.py"),
                    "--todos",
                    "--seed",
                    "42",
                    "--relatorio",
                ],
                cwd=pasta,
                capture_output=True,
                text=True,
                check=True,
            )
            caminho = Path(pasta) / "resultados" / "relatorio_todos.txt"

            self.assertTrue(caminho.is_file())
            self.assertIn("Relatório gerado em:", resultado.stdout)

    def test_conclusao_individual_cita_apenas_algoritmo_usado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "relatorio.txt"
            resultado = criar_resultado()
            resultado["algoritmo"] = "Paxos"
            gerar_relatorio([resultado], caminho)
            texto = caminho.read_text(encoding="utf-8-sig")

            self.assertIn("A execução utilizou: Paxos.", texto)
            self.assertNotIn(
                "A execução utilizou: Lamport-Shostak-Pease, Paxos.",
                texto,
            )


if __name__ == "__main__":
    unittest.main()
