import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import time


PASTA_PROJETO = Path(__file__).resolve().parent.parent


def mininet_disponivel():
    return importlib.util.find_spec("mininet") is not None


def carregar_configuracao(args):
    if args.cenario:
        caminho = Path(args.cenario)
        with caminho.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados

    nome = f"{args.algoritmo}_{args.drones}_{args.falha}"
    if args.falha == "bizantina":
        nome = f"{nome}_{args.falhos}"

    return {
        "nome": nome,
        "algoritmo": args.algoritmo,
        "drones": args.drones,
        "falha": args.falha,
        "falhos": args.falhos,
        "seed": args.seed,
        "taxa_omissao": args.taxa_omissao,
        "atraso_max": args.atraso_max,
    }


def executar_mininet(configuracao):
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topo import Topo

    class TopologiaDrones(Topo):
        def build(self):
            switch = self.addSwitch("s1")
            self.addLink(self.addHost("coord"), switch)
            for drone_id in range(configuracao["drones"]):
                self.addLink(self.addHost(f"d{drone_id}"), switch)

    titulo_algoritmo = (
        "PAXOS"
        if configuracao["algoritmo"] == "paxos"
        else "LSP / OM(m)"
    )
    print("=" * 30)
    print(f"EMULAÇÃO MININET - {titulo_algoritmo}")
    print("=" * 30)
    print()
    rede = Mininet(
        topo=TopologiaDrones(),
        controller=None,
        switch=OVSBridge,
    )
    processos_drones = []

    try:
        rede.start()
        drones = [rede.get(f"d{i}") for i in range(configuracao["drones"])]
        controlador = rede.get("coord")
        print("Topologia criada:")
        print("- Switch: s1")
        print("- Controlador: coord")
        print("- Drones: " + ", ".join(host.name for host in drones))
        print("\nAmbiente:")
        print("- Comunicação: sockets TCP")
        print("- Mensagens: JSON")
        print(f"- Falha simulada: {configuracao['falha']}")
        rotulo_falhos = (
            "Drones bizantinos"
            if configuracao["falha"] == "bizantina"
            else "Drones falhos"
        )
        print(f"- {rotulo_falhos}: {configuracao['falhos']}")
        print(f"- Seed: {configuracao['seed']}\n")

        inicio_falhos = configuracao["drones"] - configuracao["falhos"]
        porta = 5000
        script_drone = PASTA_PROJETO / "emulacao" / "drone_socket.py"

        # Mininet cria hosts separados para representar drones.
        for drone_id, host in enumerate(drones):
            comportamento = (
                configuracao["falha"]
                if drone_id >= inicio_falhos
                else "nenhuma"
            )
            comando = [
                "python3",
                str(script_drone),
                "--id",
                str(drone_id),
                "--porta",
                str(porta),
                "--comportamento",
                comportamento,
                "--taxa-omissao",
                str(configuracao["taxa_omissao"]),
                "--atraso-max",
                str(configuracao["atraso_max"]),
                "--drones",
                str(configuracao["drones"]),
                "--seed",
                str(configuracao["seed"]),
            ]
            processos_drones.append(
                host.popen(
                    comando,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            )
            print(
                f"Drone {drone_id} iniciado em {host.name} "
                f"({host.IP()}:{porta}) - {comportamento}"
            )

        print()
        time.sleep(0.5)
        script_controlador = (
            PASTA_PROJETO / "emulacao" / "controlador_emulacao.py"
        )
        nome = configuracao["nome"]
        caminho_saida = (
            PASTA_PROJETO / "resultados" / f"emulacao_{nome}.txt"
        )
        comando = [
            "python3",
            str(script_controlador),
            "--algoritmo",
            configuracao["algoritmo"],
            "--drones",
            str(configuracao["drones"]),
            "--falha",
            configuracao["falha"],
            "--falhos",
            str(configuracao["falhos"]),
            "--candidato",
            str(min(2, configuracao["drones"] - 1)),
            "--nome",
            nome,
            "--seed",
            str(configuracao["seed"]),
            "--numero-proposta",
            "1",
            "--nivel-om",
            str(configuracao.get("nivel_om", configuracao["falhos"])),
            "--valor-padrao",
            str(configuracao.get("valor_padrao", 0)),
            "--ambiente-execucao",
            "Mininet real",
            "--saida",
            str(caminho_saida),
        ]

        for drone_id, host in enumerate(drones):
            comando.extend(
                [
                    "--endereco",
                    f"{drone_id},{host.IP()},{porta}",
                ]
            )

        processo_controlador = controlador.popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            saida, _ = processo_controlador.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            processo_controlador.terminate()
            saida, _ = processo_controlador.communicate()
            raise RuntimeError(
                "O controlador excedeu o tempo de execução. "
                "Execute 'sudo mn -c' antes de tentar novamente."
            )

        print(saida)
        if processo_controlador.returncode != 0:
            raise RuntimeError(
                "O controlador da emulação terminou com erro."
            )
        print("Emulação finalizada com sucesso.")
    finally:
        for processo in processos_drones:
            if processo.poll() is None:
                processo.terminate()
                try:
                    processo.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    processo.kill()
        rede.stop()


def ler_argumentos():
    parser = argparse.ArgumentParser(description="Topologia Mininet dos drones")
    parser.add_argument("--algoritmo", choices=["paxos", "lsp"], default="paxos")
    parser.add_argument("--drones", type=int, default=5)
    parser.add_argument(
        "--falha",
        choices=[
            "nenhuma",
            "crash",
            "omissao",
            "temporizacao",
            "bizantina",
        ],
        default="nenhuma",
    )
    parser.add_argument("--falhos", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--taxa-omissao", type=float, default=0.3)
    parser.add_argument("--atraso-max", type=float, default=0)
    parser.add_argument("--cenario")
    return parser.parse_args()


def main():
    args = ler_argumentos()

    if not mininet_disponivel():
        print(
            "Mininet não encontrado. Esta etapa precisa ser executada em "
            "Linux, WSL ou máquina virtual com Mininet instalado.\n"
            "A versão local do projeto continua disponível normalmente "
            "pelo main.py."
        )
        return 1

    configuracao = carregar_configuracao(args)
    executar_mininet(configuracao)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
