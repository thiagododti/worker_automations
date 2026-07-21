from app.core.celery_worker import celery

from app.automacoes.modelo_padrao.schema import EnvelopePadrao
from app.automacoes.modelo_padrao.main import ModeloPadrao

# nome_fila: nome da fila que será criada no RabbitMQ
# nome_task: nome da task que será criada no RabbitMQ

# name: ModeloPadrao.execucao
# queue: ModeloPadrao


# estou fazendo a execucao do meu robo chamado ModeloPadrao.
# assim eu crio uma fila chamada modelo_padrao e uma task chamada execucao, que vai executar o robo ModeloPadrao.
@celery.task(
    name="modelo_padrao.execucao",
    queue="modelo_padrao",
)
def padrao_task(payload: dict):

    envelope = EnvelopePadrao.model_validate(payload)
    padrao = ModeloPadrao(envelope)

    padrao.execucao()
