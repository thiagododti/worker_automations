from pydantic import BaseModel
from datetime import datetime


class Envelope(BaseModel):
    """Modelo base para payload de automações.

    Atributos:
        automacao_id: Identificador único da automação.
        empresa_id: Identificador único da empresa.
        usuario_id: Identificador único do usuário. Opcional.
        criado_em: Data e hora de criação do payload.
        origem: Origem da requisição.
        ip_origem: Endereço IP da requisição.
    """

    execucao_id: str
    automacao_id: int
    empresa_id: int | None = None
    usuario_id: int | None = None
    criado_em: datetime
    origem: str
    ip_origem: str
