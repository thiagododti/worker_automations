from app.core.celery_worker import celery
from datetime import datetime
from app.automacoes.consulta_cnpj.schema import (
    EnvelopeConsultaCnpj,
    EnvelopeRetornoConsultaCnpj,
)
from app.automacoes.consulta_cnpj.main import ConsultaCnpjWs

# nome_fila: nome da fila que será criada no RabbitMQ
# nome_task: nome da task que será criada no RabbitMQ

# name: ModeloPadrao.execucao
# queue: ModeloPadrao

INTERVALO_ENTRE_CONSULTAS = 21


# estou fazendo a execucao do meu robo chamado ConsultaCnpjWs.
# assim eu crio uma fila chamada consulta_cnpj e uma task chamada execucao, que vai executar o robo ConsultaCnpjWs.
@celery.task(
    name="consulta_cnpj.execucao",
    queue="consulta_cnpj",
)
def consulta_cnpj_task(payload: dict):
    import time

    envelope = EnvelopeConsultaCnpj.model_validate(payload)
    consulta_cnpj_ws = ConsultaCnpjWs(envelope)

    resultado = consulta_cnpj_ws.execucao()

    retorno = EnvelopeRetornoConsultaCnpj.model_validate(
        {
            "execucao_id": envelope.execucao_id,
            "automacao_id": envelope.automacao_id,
            "criado_em": datetime.now(),
            "origem": "worker_consulta_cnpj",
            "ip_origem": "192.168.74.10",
            "cnpj": envelope.cnpj,
            "resultado": resultado,
        }
    )
    if envelope.origem == "automation_center":
        # Se a origem for "automation_center", envia o resultado para a fila de retorno
        celery.send_task(
            name="consulta_cnpj.retorno_automation_center",
            queue="consulta_cnpj_retorno_automation_center",
            args=[
                retorno.model_dump(mode="json")
            ],  # Converte o modelo para JSON antes de enviar
        )
    else:
        celery.send_task(
            name="consulta_cnpj.retorno",
            queue="consulta_cnpj_retorno",
            args=[
                retorno.model_dump(mode="json")
            ],  # Converte o modelo para JSON antes de enviar
        )
    time.sleep(INTERVALO_ENTRE_CONSULTAS)
    return resultado
