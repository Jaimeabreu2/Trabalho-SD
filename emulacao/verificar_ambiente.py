import importlib.util
import os
import platform
import shutil
import sys


def verificar_dependencias():
    return {
        "python3": shutil.which("python3") is not None,
        "linux": platform.system() == "Linux",
        "mininet": (
            shutil.which("mn") is not None
            and importlib.util.find_spec("mininet") is not None
        ),
        "openvswitch": shutil.which("ovs-vsctl") is not None,
        "root": os.geteuid() == 0 if hasattr(os, "geteuid") else None,
    }


def main():
    resultado = verificar_dependencias()
    print("Verificando ambiente para Mininet...\n")
    print(f"Python: {'OK' if resultado['python3'] else 'NÃO ENCONTRADO'}")
    print(f"Versão atual: {sys.version.split()[0]}")
    print(f"Sistema operacional: {platform.system()}")
    print(f"Linux: {'OK' if resultado['linux'] else 'NÃO'}")
    print(f"Mininet: {'OK' if resultado['mininet'] else 'NÃO ENCONTRADO'}")
    print(
        "Open vSwitch: "
        f"{'OK' if resultado['openvswitch'] else 'NÃO ENCONTRADO'}"
    )
    if resultado["root"] is None:
        print("Executando como root: Não aplicável neste sistema")
    else:
        print(f"Executando como root: {'Sim' if resultado['root'] else 'Não'}")

    if not all(
        (
            resultado["python3"],
            resultado["linux"],
            resultado["mininet"],
            resultado["openvswitch"],
        )
    ):
        print(
            "\nMininet não encontrado ou ambiente incompatível.\n"
            "Execute esta etapa em uma VM Linux com Mininet instalado.\n"
            "A versão principal do projeto continua funcionando pelo main.py."
        )
        return 1

    print("\nAmbiente aparentemente pronto para executar a emulação.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
