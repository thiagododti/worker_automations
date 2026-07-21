from app.shared.schemas import Envelope


class EnvelopePadrao(Envelope):
    """Modelo para payload de automação padrão.

    atributo adicional: cnpj (str): CNPJ a ser consultado.
    """

    cnpj: str
