
ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim

ARG AUTOMACAO
ARG CELERY_QUEUE
ARG CONCORRENCIA


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# RUN apt-get update \
#     && rm -rf /var/lib/apt/lists/*

COPY worker-requirements.txt .
COPY app/automacoes/${AUTOMACAO}/requirements.txt app/automacoes/${AUTOMACAO}/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r worker-requirements.txt \
    && pip install --no-cache-dir -r app/automacoes/${AUTOMACAO}/requirements.txt

COPY . .

CMD ["sh","-c","celery -A app.core.celery_worker worker --loglevel=INFO --queues=${CELERY_QUEUE} --concurrency=${CONCORRENCIA}"]