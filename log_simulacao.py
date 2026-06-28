class LogSimulacao:
    def __init__(self, ativo=False):
        self.ativo = ativo

    def mostrar(self, mensagem):
        # Mostra logs apenas quando verbose está ativo.
        if self.ativo:
            print(f"[VERBOSE] {mensagem}")
