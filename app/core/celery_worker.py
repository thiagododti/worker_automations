from celery import Celery
from app.core.config import settings

celery = Celery(
    "worker",
    broker=settings.broker_url,
    backend=settings.result_backend,
)

# Cada container é dedicado a uma única automação (settings.automacao),
# então só descobrimos as tasks dela — nunca as das demais pastas em
# app/automacoes, que podem ter dependências não instaladas nesta imagem.
celery.autodiscover_tasks([f"app.automacoes.{settings.automacao}"])
