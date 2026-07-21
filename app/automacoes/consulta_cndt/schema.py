from app.shared.schemas import Envelope


class EnvelopeConsultaCNDT(Envelope):
    """Modelo para payload de automação padrão.

    atributos adicionais:
        cnpj (str | None): CNPJ a ser consultado.
        cpf (str | None): CPF a ser consultado.
    """

    cnpj: str | None
    cpf: str | None


class EnvelopeRetornoConsultaCNDT(EnvelopeConsultaCNDT):
    """Modelo para payload de retorno de automação padrão.

    atributos adicionais:
        resultado (dict): Resultado da execução da automação.
    """

    resultado: dict
