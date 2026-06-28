import argparse
from pathlib import Path

from drone import Drone
from exportador import salvar_resultados_csv
from graficos import gerar_graficos_resultados
from lsp import LamportShostakPease
from mensagem import Mensagem
from paxos import PaxosBasico
from rede import Rede
from relatorio import gerar_relatorio
from simulador import ARQUIVOS_CENARIOS, carregar_cenario


def ler_argumentos():
    parser = argparse.ArgumentParser(
        description="Simulador de escolha de comandante",
    )
    parser.add_argument("--algoritmo", choices=["paxos", "lsp"], default="paxos")
    parser.add_argument("--drones", type=int, default=5)
    parser.add_argument(
        "--falha",
        choices=["nenhuma", "crash", "omissao", "temporizacao", "bizantina"],
        default="nenhuma",
    )
    parser.add_argument("--falhos", type=int, default=0)
    parser.add_argument("--taxa-omissao", type=float, default=0.3)
    parser.add_argument("--atraso-max", type=float, default=0)
    parser.add_argument(
        "--valor-padrao",
        type=int,
        default=0,
        help="Valor padrão usado pelo OM(m)",
    )
    parser.add_argument(
        "--nivel-om",
        type=int,
        default=None,
        help="Nível m do OM(m); por padrão usa a quantidade de bizantinos",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--cenario", help="Caminho de um cenário JSON")
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Executa todos os cenários JSON",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Salva os resultados em CSV",
    )
    parser.add_argument(
        "--graficos",
        action="store_true",
        help="Gera gráficos dos resultados",
    )
    parser.add_argument(
        "--relatorio",
        action="store_true",
        help="Gera um relatório textual",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostra os passos da simulação",
    )
    return parser.parse_args()


def aplicar_cenario(args):
    if not args.cenario:
        return None

    cenario = carregar_cenario(args.cenario)

    # Campos do cenário substituem os argumentos manuais.
    args.algoritmo = cenario["algoritmo"]
    args.drones = cenario["drones"]
    args.falha = cenario["falha"]
    args.falhos = cenario["falhos"]
    args.seed = cenario["seed"]
    args.taxa_omissao = cenario["taxa_omissao"]
    args.atraso_max = cenario["atraso_max"]
    args.valor_padrao = cenario.get("valor_padrao", 0)
    args.nivel_om = cenario.get("nivel_om")
    return cenario["nome"]


def criar_drones(quantidade, falha, quantidade_falhos, taxa_omissao, atraso_max):
    if quantidade < 1:
        raise ValueError("A quantidade de drones deve ser maior que zero.")

    if quantidade_falhos < 0 or quantidade_falhos > quantidade:
        raise ValueError("A quantidade de falhos é inválida.")

    inicio_falhos = quantidade - quantidade_falhos
    drones = []

    for drone_id in range(quantidade):
        comportamento = falha if drone_id >= inicio_falhos else "nenhuma"
        drones.append(
            Drone(
                drone_id,
                comportamento=comportamento,
                taxa_omissao=taxa_omissao if comportamento == "omissao" else 0,
                atraso_max=atraso_max if comportamento == "temporizacao" else 0,
            )
        )

    return drones


def demonstrar_falha_bizantina(rede, drones):
    bizantinos = [drone for drone in drones if drone.bizantino]
    print(f"Simulando falha bizantina com {len(drones)} drones...\n")

    if not bizantinos:
        print("Nenhum drone foi configurado como bizantino.")
        return

    for bizantino in bizantinos:
        print(f"Drone bizantino: Drone {bizantino.id}")

        # Cada destino pode receber um valor diferente.
        for destino in drones:
            if destino.id == bizantino.id:
                continue

            mensagem = Mensagem(
                "VALOR",
                bizantino.id,
                destino.id,
                1,
                bizantino.id,
                "DEMONSTRACAO",
            )
            rede.enviar(mensagem)

        print(f"\nMensagens enviadas pelo Drone {bizantino.id}:")
        for destino, candidato in bizantino.historico_valores_enviados:
            print(f"Para Drone {destino}: candidato {candidato}")
        print(
            "\nMensagens contraditórias: "
            f"{bizantino.mensagens_contraditorias}"
        )


def texto_booleano(valor):
    if valor is None:
        return "Não aplicável"
    return "Sim" if valor else "Não"


def exibir_resultado(resultado):
    comandante = resultado["comandante_escolhido"]
    nome_comandante = (
        f"Drone {comandante}" if comandante is not None else "Nenhum"
    )

    print("\nResultado do consenso:")
    print(f"Comandante escolhido: {nome_comandante}")
    print(
        "Decisão alcançada: "
        f"{texto_booleano(resultado['decisao_alcancada'])}"
    )
    print(f"Acordo: {texto_booleano(resultado['acordo'])}")
    print(f"Validade: {texto_booleano(resultado['validade'])}")
    print(f"Terminação: {texto_booleano(resultado['terminacao'])}")
    print(f"Mensagens enviadas: {resultado['mensagens_enviadas']}")
    print(f"Mensagens recebidas: {resultado['mensagens_recebidas']}")
    print(f"Mensagens omitidas: {resultado['mensagens_omitidas']}")
    print(f"Mensagens atrasadas: {resultado['mensagens_atrasadas']}")
    print(
        "Mensagens contraditórias: "
        f"{resultado['mensagens_contraditorias']}"
    )
    if resultado["status_limite_teorico"] is not None:
        print(
            "Status do limite teórico: "
            f"{resultado['status_limite_teorico']}"
        )
    print(f"Tempo de execução: {resultado['tempo_execucao']:.6f} s")


def executar_dados_cenario(cenario, seed=None, verbose=False):
    seed_usada = cenario["seed"] if seed is None else seed
    drones = criar_drones(
        cenario["drones"],
        cenario["falha"],
        cenario["falhos"],
        cenario["taxa_omissao"],
        cenario["atraso_max"],
    )
    rede = Rede(seed=seed_usada, verbose=verbose)

    for drone in drones:
        rede.registrar_drone(drone)

    candidato = min(2, len(drones) - 1)
    if cenario["algoritmo"] == "paxos":
        algoritmo = PaxosBasico(rede)
        algoritmo.executar(0, candidato)
    else:
        algoritmo = LamportShostakPease(
            rede,
            valor_padrao=cenario.get("valor_padrao", 0),
        )
        algoritmo.executar(
            0,
            candidato,
            m=cenario.get("nivel_om", cenario["falhos"]),
        )

    resultado = dict(algoritmo.resultado_metricas)
    resultado["cenario"] = cenario["nome"]
    return resultado


def resultado_com_erro(nome, erro):
    return {
        "cenario": nome,
        "algoritmo": "-",
        "quantidade_drones": "-",
        "tipo_falha": "-",
        "quantidade_falhos": "-",
        "comandante_escolhido": None,
        "decisao_alcancada": False,
        "acordo": False,
        "validade": None,
        "terminacao": False,
        "mensagens_enviadas": 0,
        "mensagens_recebidas": 0,
        "mensagens_omitidas": 0,
        "mensagens_atrasadas": 0,
        "mensagens_contraditorias": 0,
        "status_limite_teorico": None,
        "tempo_execucao": 0,
        "erro": str(erro),
    }


def executar_todos_cenarios(caminhos=None, seed=None, verbose=False):
    if caminhos is None:
        pasta = Path(__file__).resolve().parent / "cenarios"
        caminhos = [pasta / nome for nome in ARQUIVOS_CENARIOS]

    resultados = []

    # Executa todos os cenários JSON em sequência.
    for caminho in caminhos:
        try:
            cenario = carregar_cenario(caminho)
            if verbose:
                print(
                    f"\n[VERBOSE] ===== Cenário: "
                    f"{cenario['nome']} ====="
                )
            resultados.append(
                executar_dados_cenario(cenario, seed, verbose)
            )
        except Exception as erro:
            # Mesmo se um cenário falhar, os próximos continuam.
            nome = Path(caminho).stem
            resultados.append(resultado_com_erro(nome, erro))

    return resultados


def valor_tabela(valor):
    if isinstance(valor, bool) or valor is None:
        return texto_booleano(valor)
    return str(valor)


def exibir_tabela_geral(resultados):
    colunas = [
        ("Cenário", "cenario"),
        ("Algoritmo", "algoritmo"),
        ("Drones", "quantidade_drones"),
        ("Falha", "tipo_falha"),
        ("Falhos", "quantidade_falhos"),
        ("Comandante", "comandante_escolhido"),
        ("Decisão", "decisao_alcancada"),
        ("Acordo", "acordo"),
        ("Validade", "validade"),
        ("Terminação", "terminacao"),
        ("Enviadas", "mensagens_enviadas"),
        ("Recebidas", "mensagens_recebidas"),
        ("Omitidas", "mensagens_omitidas"),
        ("Atrasadas", "mensagens_atrasadas"),
        ("Contraditórias", "mensagens_contraditorias"),
        ("Limite", "status_limite_teorico"),
        ("Tempo (s)", "tempo_execucao"),
    ]

    linhas = []
    for resultado in resultados:
        linha = []
        for _, chave in colunas:
            valor = resultado[chave]
            if chave == "algoritmo":
                valor = "LSP" if str(valor).startswith("Lamport") else str(valor).upper()
            elif chave == "comandante_escolhido":
                valor = f"Drone {valor}" if valor is not None else "-"
            elif chave == "tempo_execucao":
                valor = f"{valor:.6f}"
            linha.append(valor_tabela(valor))
        linhas.append(linha)

    larguras = []
    for indice, (titulo, _) in enumerate(colunas):
        larguras.append(
            max(len(titulo), *(len(linha[indice]) for linha in linhas))
        )

    # A tabela final resume os resultados principais.
    print("Resumo geral dos cenários:\n")
    print(
        "  ".join(
            titulo.ljust(larguras[indice])
            for indice, (titulo, _) in enumerate(colunas)
        )
    )
    print(
        "  ".join("-" * largura for largura in larguras)
    )
    for linha in linhas:
        print(
            "  ".join(
                valor.ljust(larguras[indice])
                for indice, valor in enumerate(linha)
            )
        )

    erros = [resultado for resultado in resultados if "erro" in resultado]
    if erros:
        print("\nErros encontrados:")
        for resultado in erros:
            print(f"- {resultado['cenario']}: {resultado['erro']}")


def salvar_csv_execucao(resultado, nome_cenario=None):
    resultado_csv = dict(resultado)
    resultado_csv["cenario"] = nome_cenario or "manual"

    if nome_cenario:
        nome_arquivo = f"resultado_{nome_cenario}.csv"
    else:
        nome_arquivo = "resultado_manual.csv"

    caminho = Path("resultados") / nome_arquivo
    caminho_gerado = salvar_resultados_csv([resultado_csv], caminho)
    print(f"\nArquivo CSV gerado em: {caminho_gerado}")
    return caminho_gerado


def gerar_graficos_execucao(resultados):
    try:
        arquivos = gerar_graficos_resultados(resultados, "resultados")
    except ImportError:
        print(
            "\nNão foi possível gerar gráficos. "
            "Instale as dependências com:\n"
            "pip install -r requirements.txt"
        )
        return []

    if arquivos:
        print("\nGráficos gerados na pasta: resultados/")
    else:
        print("\nNão há resultados para gerar gráficos.")
    return arquivos


def gerar_relatorio_execucao(
    resultado,
    nome_cenario=None,
    arquivos_csv=None,
    arquivos_graficos=None,
):
    resultado_relatorio = dict(resultado)
    resultado_relatorio["cenario"] = nome_cenario or "manual"
    nome = nome_cenario or "manual"
    caminho = Path("resultados") / f"relatorio_{nome}.txt"
    caminho_gerado = gerar_relatorio(
        [resultado_relatorio],
        caminho,
        arquivos_csv,
        arquivos_graficos,
    )
    print(f"\nRelatório gerado em: {caminho_gerado}")
    return caminho_gerado


def executar_lsp(rede, drones, valor_padrao=0, nivel_om=None):
    comandante = 0
    candidato = min(2, len(drones) - 1)
    bizantinos = [drone.id for drone in drones if drone.bizantino]
    lsp = LamportShostakPease(rede, valor_padrao=valor_padrao)
    lsp.executar(comandante, candidato, m=nivel_om)

    print("Algoritmo: Lamport-Shostak-Pease")
    print(f"Drones: {len(drones)}")
    print(f"Falhas bizantinas: {len(bizantinos)}")
    print(lsp.limite_bizantino["mensagem"])
    print()
    print(f"Comandante inicial: Drone {comandante}")
    nomes_bizantinos = ", ".join(f"Drone {drone_id}" for drone_id in bizantinos)
    print(f"Drones bizantinos: {nomes_bizantinos or 'Nenhum'}")
    print(f"Candidato proposto: Drone {candidato}\n")
    print(f"Execução OM({lsp.nivel_om})")
    print(f"Valor padrão: Drone {lsp.valor_padrao}\n")
    print("Valores recebidos pelos drones corretos:")

    for drone_id, valores in lsp.valores_recebidos.items():
        print(f"Drone {drone_id}: {valores}")

    contraditorias = sum(
        drone.mensagens_contraditorias for drone in drones
    )
    comandante_escolhido = (
        f"Drone {lsp.comandante_escolhido}"
        if lsp.decisao_alcancada
        else "Nenhum"
    )
    print(f"\nComandante escolhido: {comandante_escolhido}")
    print(f"Acordo entre drones corretos: {'Sim' if lsp.acordo else 'Não'}")
    print(f"Decisão alcançada: {'Sim' if lsp.decisao_alcancada else 'Não'}")
    print(f"Mensagens contraditórias: {contraditorias}")
    print(f"Mensagens enviadas: {rede.mensagens_enviadas}")
    status_limite = (
        "Dentro"
        if lsp.limite_bizantino["dentro_limite"]
        else "Fora"
    )
    print(f"Status do limite teórico: {status_limite}")
    exibir_resultado(lsp.resultado_metricas)
    return lsp.resultado_metricas


def main():
    args = ler_argumentos()

    if args.todos:
        resultados = executar_todos_cenarios(
            seed=args.seed,
            verbose=args.verbose,
        )
        exibir_tabela_geral(resultados)
        arquivos_csv = []
        arquivos_graficos = []
        if args.csv:
            caminho = salvar_resultados_csv(
                resultados,
                Path("resultados") / "resultados_todos.csv",
            )
            arquivos_csv.append(caminho)
            print(f"\nArquivo CSV gerado em: {caminho}")
        if args.graficos:
            arquivos_graficos = gerar_graficos_execucao(resultados)
        if args.relatorio:
            caminho = gerar_relatorio(
                resultados,
                Path("resultados") / "relatorio_todos.txt",
                arquivos_csv,
                arquivos_graficos,
            )
            print(f"\nRelatório gerado em: {caminho}")
        return

    try:
        nome_cenario = aplicar_cenario(args)
    except (FileNotFoundError, ValueError) as erro:
        raise SystemExit(f"Erro ao carregar cenário: {erro}") from erro

    try:
        drones = criar_drones(
            args.drones,
            args.falha,
            args.falhos,
            args.taxa_omissao,
            args.atraso_max,
        )
    except ValueError as erro:
        raise SystemExit(f"Configuração inválida: {erro}") from erro
    rede = Rede(seed=args.seed, verbose=args.verbose)

    for drone in drones:
        rede.registrar_drone(drone)

    if nome_cenario:
        print(f"Cenário: {nome_cenario}\n")

    if args.algoritmo == "lsp":
        resultado = executar_lsp(
            rede,
            drones,
            valor_padrao=args.valor_padrao,
            nivel_om=args.nivel_om,
        )
        arquivos_csv = []
        arquivos_graficos = []
        if args.csv:
            arquivos_csv.append(
                salvar_csv_execucao(resultado, nome_cenario)
            )
        if args.graficos:
            resultado_grafico = dict(resultado)
            resultado_grafico["cenario"] = nome_cenario or "manual"
            arquivos_graficos = gerar_graficos_execucao([resultado_grafico])
        if args.relatorio:
            gerar_relatorio_execucao(
                resultado,
                nome_cenario,
                arquivos_csv,
                arquivos_graficos,
            )
        return

    if args.falha == "bizantina":
        demonstrar_falha_bizantina(rede, drones)
        return

    proponente = 0
    candidato = min(2, args.drones - 1)
    paxos = PaxosBasico(rede)
    paxos.executar(proponente, candidato)

    omitidas = sum(drone.mensagens_omitidas for drone in drones)
    atrasadas = sum(drone.mensagens_atrasadas for drone in drones)
    comandante = (
        f"Drone {paxos.comandante_escolhido}"
        if paxos.decisao_alcancada
        else "Nenhum"
    )

    print("Simulador de escolha de comandante iniciado.\n")
    print(f"Algoritmo: {args.algoritmo.upper()}")
    print(f"Quantidade de drones: {args.drones}")
    print(f"Tipo de falha: {args.falha}")
    print(f"Quantidade de falhos: {args.falhos}")
    print(f"Proponente: Drone {proponente}")
    print(f"Candidato a comandante: Drone {candidato}")
    print(f"PROMISE recebidos: {paxos.votos_promise}")
    print(f"ACCEPTED recebidos: {paxos.votos_accepted}")
    print(f"Comandante escolhido: {comandante}")
    print(f"Decisão alcançada: {'Sim' if paxos.decisao_alcancada else 'Não'}")
    print(
        "Maioria suficiente: "
        f"{'Sim' if paxos.maioria_promise and paxos.maioria_accepted else 'Não'}"
    )
    print(f"Mensagens enviadas: {rede.mensagens_enviadas}")
    print(f"Mensagens recebidas: {rede.mensagens_recebidas}")
    print(f"Mensagens omitidas: {omitidas}")
    print(f"Mensagens atrasadas: {atrasadas}")
    exibir_resultado(paxos.resultado_metricas)
    arquivos_csv = []
    arquivos_graficos = []
    if args.csv:
        arquivos_csv.append(
            salvar_csv_execucao(paxos.resultado_metricas, nome_cenario)
        )
    if args.graficos:
        resultado_grafico = dict(paxos.resultado_metricas)
        resultado_grafico["cenario"] = nome_cenario or "manual"
        arquivos_graficos = gerar_graficos_execucao([resultado_grafico])
    if args.relatorio:
        gerar_relatorio_execucao(
            paxos.resultado_metricas,
            nome_cenario,
            arquivos_csv,
            arquivos_graficos,
        )


if __name__ == "__main__":
    main()
