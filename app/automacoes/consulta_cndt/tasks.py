from app.core.celery_worker import celery
from datetime import datetime
from app.automacoes.consulta_cndt.schema import (
    EnvelopeConsultaCNDT,
    EnvelopeRetornoConsultaCNDT,
)
from app.automacoes.consulta_cndt.main import ConsultaCNDTInfoSimples

# nome_fila: nome da fila que será criada no RabbitMQ
# nome_task: nome da task que será criada no RabbitMQ

# name: ModeloPadrao.execucao
# queue: ModeloPadrao

INTERVALO_ENTRE_CONSULTAS = 15


# estou fazendo a execucao do meu robo chamado ConsultaCnpjWs.
# assim eu crio uma fila chamada consulta_cnpj e uma task chamada execucao, que vai executar o robo ConsultaCnpjWs.
@celery.task(
    name="consulta_cndt.execucao",
    queue="consulta_cndt",
)
def consulta_cndt_task(payload: dict):
    import time

    envelope = EnvelopeConsultaCNDT.model_validate(payload)
    consulta_cndt_info_simples = ConsultaCNDTInfoSimples(envelope)

    resultado = consulta_cndt_info_simples.execucao()

    retorno = EnvelopeRetornoConsultaCNDT.model_validate(
        {
            "execucao_id": envelope.execucao_id,
            "automacao_id": envelope.automacao_id,
            "criado_em": datetime.now(),
            "origem": "worker_consulta_cndt",
            "ip_origem": "192.168.74.10",
            "cnpj": envelope.cnpj if envelope.cnpj else None,
            "cpf": envelope.cpf if envelope.cpf else None,
            "resultado": resultado,
        }
    )
    if envelope.origem == "automation_center":
        # Se a origem for "automation_center", envia o resultado para a fila de retorno
        celery.send_task(
            name="consulta_cndt.retorno_automation_center",
            queue="consulta_cndt_retorno_automation_center",
            args=[
                retorno.model_dump(mode="json")
            ],  # Converte o modelo para JSON antes de enviar
        )
    else:
        celery.send_task(
            name="consulta_cndt.retorno",
            queue="consulta_cndt_retorno",
            args=[
                retorno.model_dump(mode="json")
            ],  # Converte o modelo para JSON antes de enviar
        )
    time.sleep(INTERVALO_ENTRE_CONSULTAS)
    return resultado
