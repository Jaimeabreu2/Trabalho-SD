from falhas import validar_falha


class Drone:
    def __init__(
        self,
        drone_id,
        candidato_proposto=None,
        comportamento="nenhuma",
        taxa_omissao=0,
        atraso_max=0,
    ):
        validar_falha(comportamento, taxa_omissao, atraso_max)

        self.id = drone_id
        self.candidato_proposto = candidato_proposto
        self.comportamento = comportamento
        self.ativo = comportamento != "crash"
        self.bizantino = comportamento == "bizantina"
        self.taxa_omissao = taxa_omissao
        self.atraso_max = atraso_max
        self.mensagens_omitidas = 0
        self.mensagens_atrasadas = 0
        self.mensagens_contraditorias = 0
        self.historico_valores_enviados = []
        self.decisao_final = None
        self.mensagens_recebidas = []
        self.maior_proposta_prometida = -1
        self.proposta_aceita = None
        self.valor_aceito = None

    @property
    def maior_numero_prometido(self):
        return self.maior_proposta_prometida

    @maior_numero_prometido.setter
    def maior_numero_prometido(self, valor):
        self.maior_proposta_prometida = valor

    @property
    def numero_aceito(self):
        return self.proposta_aceita

    @numero_aceito.setter
    def numero_aceito(self, valor):
        self.proposta_aceita = valor

    def receber_mensagem(self, mensagem):
        """Guarda uma mensagem recebida pelo drone."""
        self.mensagens_recebidas.append(mensagem)

    def listar_mensagens(self):
        return list(self.mensagens_recebidas)

    def limpar_mensagens(self):
        self.mensagens_recebidas.clear()
