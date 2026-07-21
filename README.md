# worker_automations

Framework para hospedar as automações não assistidas da empresa, cada uma rodando isolada em seu próprio worker Celery.

## Ideia geral

Cada automação vive em `app/automacoes/<nome_da_automacao>/` e é empacotada como **uma imagem Docker dedicada**, que sobe **um container só pra ela**, consumindo **uma fila só dela** no RabbitMQ. Isso garante que:

- o código e as dependências de uma automação nunca interferem nas outras;
- cada worker só carrega (e só precisa instalar) o que a sua automação específica usa;
- é possível escalar, reiniciar ou atualizar uma automação sem tocar nas demais.

O transporte de mensagens é RabbitMQ (broker) e o resultado das tasks é armazenado no Redis (result backend), ambos via [Celery](https://docs.celeryq.dev/).

## Estrutura do projeto

```
app/
  core/
    celery_worker.py   # cria a app Celery e descobre a task da automação do container
    config.py          # le configuracao (.env / variaveis de ambiente)
  shared/
    schemas/
      envelope.py       # payload base (Envelope) que toda automacao estende
  automacoes/
    modelo_padrao/      # exemplo de automacao, use como referencia para criar novas
      __init__.py
      schema.py          # Envelope especifico da automacao (campos extras do payload)
      main.py            # classe com a logica de negocio da automacao
      tasks.py           # registro da task Celery (nome, fila, parsing do payload)
      requirements.txt   # dependencias EXTRAS dessa automacao (alem do framework)
Dockerfile               # builda a imagem de UMA automacao por vez (via build args)
docker-compose.yml       # sobe o worker de uma automacao
worker-requirements.txt  # dependencias do framework (celery, pydantic, redis, etc)
```

## Como funciona uma automação

Toda automação segue o mesmo padrão de 4 arquivos, usando `modelo_padrao` como referência:

**`schema.py`** — define os campos extras que o payload dessa automação precisa, estendendo o `Envelope` base (que já traz `automacao_id`, `empresa_id`, `usuario_id`, `criado_em`, `origem`, `ip`):

```python
from app.shared.schemas import Envelope

class EnvelopePadrao(Envelope):
    cnpj: str
```

**`main.py`** — a lógica de negócio em si, isolada de qualquer detalhe de fila/Celery:

```python
class ModeloPadrao:
    def __init__(self, payload: EnvelopePadrao):
        self.payload = payload

    def execucao(self):
        print(f"Consultando CNPJ: {self.payload.cnpj}")
```

**`tasks.py`** — registra a task no Celery e faz o parsing do payload recebido. O arquivo **precisa se chamar `tasks.py`** (plural) — é a convenção que o `autodiscover_tasks` do Celery usa para encontrar as tasks de cada pacote:

```python
from app.core.celery_worker import celery
from app.automacoes.modelo_padrao.schema import EnvelopePadrao
from app.automacoes.modelo_padrao.main import ModeloPadrao

@celery.task(name="modelo_padrao.execucao", queue="modelo_padrao")
def padrao_task(payload: dict):
    envelope = EnvelopePadrao.model_validate(payload)
    padrao = ModeloPadrao(envelope)
    padrao.execucao()
```

O Celery entrega o payload como `dict` puro (ele não converte pelo type hint automaticamente) — por isso o `model_validate` explícito é obrigatório antes de instanciar a classe da automação.

**`requirements.txt`** — só as dependências **extras** dessa automação específica (ex: `psycopg2-binary`, `requests`). As dependências do framework (`celery`, `pydantic`, `redis` etc.) já estão em `worker-requirements.txt` na raiz e são instaladas automaticamente para todas as automações — não duplique elas aqui.

## Criando uma nova automação

1. Crie a pasta `app/automacoes/<nome_da_automacao>/` com `__init__.py` vazio.
2. Copie o padrão de `modelo_padrao/schema.py`, `main.py` e `tasks.py`, ajustando para a lógica da nova automação.
3. Use um `name` de task e uma `queue` únicos, seguindo o padrão `<nome_da_automacao>.<acao>` para o nome da task.
4. Crie `requirements.txt` na pasta da automação com as dependências extras (ou deixe só um comentário se não precisar de nenhuma).

## Configuração (variáveis de ambiente)

Lidas de um arquivo `.env` (dev local) ou injetadas diretamente no container (`stack.env`, gerado pelo Portainer em produção):

| Variável | Uso |
|---|---|
| `BROKER_URL` | URL de conexão do RabbitMQ (broker), ex: `amqp://user:senha@host:5672//` |
| `RESULT_BACKEND` | URL de conexão do Redis (result backend), ex: `redis://:senha@host:6379/0` |
| `AUTOMACAO` | Nome da pasta em `app/automacoes/` que este worker vai carregar |
| `CELERY_QUEUE` | Nome da fila que este worker vai consumir |
| `PYTHON_VERSION` | Versão da imagem base `python:${PYTHON_VERSION}-slim` |

> Se a senha do RabbitMQ/Redis tiver caracteres especiais (`@`, `#`, `:` etc.), ela precisa estar [percent-encoded](https://pt.wikipedia.org/wiki/Percent-encoding) dentro de `BROKER_URL`/`RESULT_BACKEND`.

`RABBITMQ_HOST`/`PORT`/`USER`/`PASSWORD` e `REDIS_HOST`/`PORT`/`PASSWORD` também podem estar presentes no `.env` como referência legível, mas quem a aplicação de fato lê é `BROKER_URL`/`RESULT_BACKEND` — mantenha os dois em sincronia se editar um deles.

## Build e execução

Cada build gera a imagem de **uma automação por vez**:

```bash
docker build \
  --build-arg AUTOMACAO=modelo_padrao \
  --build-arg CELERY_QUEUE=modelo_padrao \
  --build-arg PYTHON_VERSION=3.12 \
  -t worker_modelo_padrao .
```

Ou via `docker-compose.yml` (usa as mesmas variáveis, lidas de `stack.env`):

```bash
docker compose up --build
```

Para rodar N automações ao mesmo tempo, é preciso um `stack.env`/deploy por automação (cada um com seu próprio `AUTOMACAO`/`CELERY_QUEUE`) — hoje o `docker-compose.yml` builda e sobe uma automação por vez.

## Rodando localmente sem Docker

```bash
python -m venv .venv
.venv/Scripts/activate  # ou source .venv/bin/activate no Linux/Mac
pip install -r worker-requirements.txt -r app/automacoes/<automacao>/requirements.txt
celery -A app.core.celery_worker worker --loglevel=INFO --queues=<nome_da_fila>
```

Nesse caso, crie um `.env` na raiz do projeto (não versionado) com as variáveis da tabela acima.
