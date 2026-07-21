from app.shared.schemas import Envelope


class EnvelopeConsultaCnpj(Envelope):
    """Modelo para payload de automação padrão.

    atributo adicional: cnpj (str): CNPJ a ser consultado.
    """

    cnpj: str


class EnvelopeRetornoConsultaCnpj(EnvelopeConsultaCnpj):
    """Modelo para payload de retorno de automação padrão.

    atributos adicionais:
        resultado (dict): Resultado da execução da automação.
    """

    resultado: dict
