# Botlogger

Biblioteca Python para registrar execucoes de automacoes no Botlogger, incluindo:

- abertura e fechamento de execucao
- abertura e fechamento de etapas
- registro de logs
- marcacao de alerta e erro
- busca de empresa por CNPJ
- troca automatica de certificado no Windows quando a automacao exigir
- envio de alerta para Bitrix24 quando a execucao falha fora de manutencao

O projeto hoje e composto por uma unica classe, `Botlogger`, definida em `botlogger.py`.

## Requisitos

- Python 3.10 ou superior
- Windows, se voce usar a troca automatica de certificado via registro do Chrome
- acesso HTTP ao servidor do Botlogger configurado nas variaveis de ambiente

## Dependencias

O codigo depende destes pacotes:

- requests
- python-dotenv

Instalacao sugerida:

```bash
pip install requests python-dotenv
```

## Variaveis de ambiente

O construtor carrega um arquivo `.env` automaticamente com `load_dotenv()`.

Configure as variaveis abaixo:

```env
TOKEN_BOTLOGGER_OFICIAL=seu_token
HOST_BOTLOGGER_OFICIAL=https://seu-servidor
AUTOMACAO_ID_PARA_EXECUCAO=123
URL_BITRIX=https://empresa.bitrix24.com.br/rest/1/sdeq1s8d181q/im.message.add.json/
```

### Significado

- `TOKEN_BOTLOGGER_OFICIAL`: token usado no header `Authorization: Token ...`
- `HOST_BOTLOGGER_OFICIAL`: URL base da API do Botlogger
- `AUTOMACAO_ID_PARA_EXECUCAO`: ID numerico da automacao que sera executada

Se qualquer uma dessas configuracoes estiver ausente, a classe dispara `ValueError` durante a inicializacao.

## Como funciona

Ao instanciar `Botlogger`, o fluxo inicial faz o seguinte:

1. carrega as variaveis de ambiente
2. valida token, host e ID da automacao
3. busca a empresa pelo CNPJ informado no construtor
4. busca os dados da automacao
5. identifica se a automacao esta em manutencao
6. se `auth_certificate` estiver habilitado, atualiza a politica do Chrome no registro do Windows

## Exemplo de uso

### Uso padrao

```python
from botlogger import Botlogger


botlogger = Botlogger(empresa="12345678000199")
botlogger.inicio_execucao()
try:
    itens_automacao['1','2','3']
    for item in itens_automacao:
        try:
        botlogger.inicio_etapa("login")

        # Execução da Automação 

        botlogger.fim_etapa() ou botlogger.alerta_etapa("Etapa com algum alerta")
        except Exception as error:
        botlogger.erro_etapa(f"Etapa com erro: {error}")

    # Execução finalizada com sucesso ou alerta
    botlogger.fim_execucao() ou botlogger.alerta_execucao("Execução finalizada com algum alerta")

except Exception as error:
		botlogger.erro_execucao(f"Execução com erro: {error}")
		raise
```

### Uso com envio manual

Use `envio_manual=True` para registrar execucoes e etapas que ja ocorreram, informando datas e status manualmente:

```python
from botlogger import Botlogger

botlogger = Botlogger(empresa="12345678000199", envio_manual=True)
botlogger.inicio_execucao(
    date_start="2026-04-24T08:00:00",
    date_end="2026-04-24T08:05:00",
    status="concluido"
)

botlogger.inicio_etapa(
    "login",
    status="concluido",
    date_start="2026-04-24T08:00:00",
    date_end="2026-04-24T08:01:00"
)
```

## API disponivel

### Criacao

```python
botlogger = Botlogger("12345678000199")
# ou em modo de envio manual:
botlogger = Botlogger("12345678000199", envio_manual=True)
```

Parametros:

- `empresa`: CNPJ usado para consultar o business na API `/api/business/`
- `envio_manual` (opcional, padrao `False`): quando `True`, habilita o modo de envio manual, que exige `date_start`, `date_end` e `status` nos metodos `inicio_execucao()` e `inicio_etapa()`

### Metodos de execucao

- `inicio_execucao(date_start=None, date_end=None, status=None)`: cria uma execucao com status `iniciado`; em modo `envio_manual`, os tres parametros sao obrigatorios
- `fim_execucao(mensagem=None)`: finaliza a execucao com status `concluido`
- `erro_execucao(mensagem)`: finaliza a execucao com status `erro`, registra log e pode notificar o Bitrix24
- `alerta_execucao(mensagem)`: atualiza a execucao com status `alerta` e registra log

### Metodos de etapa

- `inicio_etapa(identificacao, status=None, date_start=None, date_end=None)`: cria uma etapa vinculada a execucao atual; em modo `envio_manual`, `date_start` e `date_end` sao obrigatorios (exceto quando `status='erro'`)
- `fim_etapa(mensagem=None)`: finaliza a etapa atual com status `concluido`
- `erro_etapa(mensagem)`: marca a etapa atual como `erro` e registra log
- `alerta_etapa(mensagem)`: marca a etapa atual como `alerta` e registra log

### Status aceitos

Quando `envio_manual=True`, o parametro `status` deve ser um dos valores abaixo:

- `concluido`
- `erro`
- `alerta`
- `teste`

### Metodos auxiliares

- `log(mensagem)`: cria um log textual vinculado a execucao atual
- `get_empresa()`: consulta a empresa pelo CNPJ informado
- `get_automation()`: consulta a automacao configurada no `.env`
- `troca_certificado()`: atualiza a politica `AutoSelectCertificateForUrls` do Chrome no registro do Windows

## Fluxo recomendado

Para evitar inconsistencias, a sequencia mais segura de uso e:

1. instanciar a classe
2. chamar `inicio_execucao()`
3. registrar etapas com `inicio_etapa()` e `fim_etapa()`
4. usar `log()` para eventos importantes
5. encerrar com `fim_execucao()`
6. em caso de falha, chamar `erro_execucao()`

## Comportamento de rede e resiliencia

As chamadas HTTP passam pelo metodo interno `_safe_request()`, que:

- usa `requests.request(...)`
- define timeout de 5 segundos
- tenta novamente ate 3 vezes
- aplica backoff exponencial entre as tentativas
- retorna `None` em falha definitiva

O parse de JSON passa por `_safe_json()`, que devolve um dicionario vazio em caso de resposta invalida.

## Troca automatica de certificado

Quando a automacao retorna `auth_certificate = true`, a classe tenta escrever no registro do Windows em:

```text
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Google\Chrome\AutoSelectCertificateForUrls
```

Para isso funcionar, e necessario:

- executar no Windows
- ter permissao para escrever em `HKEY_LOCAL_MACHINE`
- a automacao possuir `url_certificate`
- o business conter os campos:
	- `subject_cn`
	- `subject_c`
	- `subject_o`
	- `issuer_cn`
	- `issuer_c`
	- `issuer_o`

Se algum desses dados estiver ausente, a inicializacao pode falhar com excecao.

## Integracao com Bitrix24

O metodo `erro_execucao()` envia mensagem para o Bitrix24 quando a automacao nao esta em manutencao. O texto inclui:

- nome da automacao
- descricao do erro
- data de inicio
- data de fim

Esse envio usa uma URL fixa embutida no codigo.

## Observacoes importantes

- O projeto desabilita verificacao SSL nas requisicoes internas da API do Botlogger com `verify=False`.
- `inicio_execucao()` precisa ser chamado antes de `log()`, `inicio_etapa()` e demais operacoes vinculadas a execucao.
- `inicio_etapa()` precisa ser chamado antes de `fim_etapa()`, `erro_etapa()` e `alerta_etapa()`.
- A classe usa o primeiro item retornado em `results` na consulta de business.

## Estrutura do projeto

```text
.
|-- botlogger.py
|-- README.md
|-- requirements.txt
|-- .env.example
```
