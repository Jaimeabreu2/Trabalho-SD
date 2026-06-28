TIPOS_DE_FALHA = (
    "nenhuma",
    "crash",
    "omissao",
    "temporizacao",
    "bizantina",
)


def validar_falha(comportamento, taxa_omissao, atraso_max):
    if comportamento not in TIPOS_DE_FALHA:
        raise ValueError(f"Tipo de falha inválido: {comportamento}")

    if not 0 <= taxa_omissao <= 1:
        raise ValueError("A taxa de omissão deve estar entre 0 e 1.")

    if atraso_max < 0:
        raise ValueError("O atraso máximo não pode ser negativo.")


def deve_omitir(drone, gerador):
    return (
        drone.comportamento == "omissao"
        and gerador.random() < drone.taxa_omissao
    )


def sortear_atraso(drone, gerador):
    if drone.comportamento != "temporizacao":
        return 0

    return gerador.uniform(0, drone.atraso_max)


def gerar_candidato_falso(candidato, candidatos, valores_usados, gerador):
    opcoes = [
        valor
        for valor in candidatos
        if valor != candidato and valor not in valores_usados
    ]

    if not opcoes:
        opcoes = [valor for valor in candidatos if valor != candidato]

    if not opcoes:
        return candidato

    return gerador.choice(opcoes)
