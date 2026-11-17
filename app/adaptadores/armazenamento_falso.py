class ArmazenamentoFalso:
    def __init__(self, disponivel: bool = True) -> None:
        self.disponivel = disponivel

    def verificar(self) -> bool:
        return self.disponivel
