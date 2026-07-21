from app.shared.schemas import Envelope


class EnvelopeConsultaFgts(Envelope):
    """Modelo para payload de automação padrão.

    atributo adicional: cnpj (str): CNPJ a ser consultado.
    """

    cnpj: str | None
    cpf: str | None


class EnvelopeRetornoConsultaFgts(EnvelopeConsultaFgts):
    """Modelo para payload de retorno de automação padrão.

    atributos adicionais:
        resultado (dict): Resultado da execução da automação.
    """

    resultado: dict
