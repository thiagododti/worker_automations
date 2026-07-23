class ConsultaCNDTInfoSimples:
    from app.automacoes.consulta_cndt.schema import EnvelopeConsultaCNDT
    from app.shared.botlogger import Botlogger
    import os
    import time
    import requests

    def __init__(self, payload: EnvelopeConsultaCNDT):
        # Configurações de retry inforsimples
        self.retry_count = 0
        self.max_retries = 3
        self.code = None
        self.retry_sleep = 5
        ######################################

        # Configurações de consulta CNDT
        self.payload = payload
        self.url = "https://api.infosimples.com/api/v2/consultas/tribunal/tst/cndt"
        self.params = {
            "token": self.os.getenv("INFOSIMPLES_TOKEN"),
            "timeout": 600,
            "ignore_site_receipt": 0,
        }
        if self.payload.cnpj:
            self.params["cnpj"] = self.payload.cnpj
        elif self.payload.cpf:
            self.params["cpf"] = self.payload.cpf
        else:
            raise ValueError("É necessário fornecer um CNPJ ou CPF para a consulta.")
        ######################################

    def execucao(self):

        try:
            # Iiniciando o botlogger para registrar a execução da consulta
            botlogger = self.Botlogger(
                empresa=self.payload.empresa_cnpj,
                automacao_id=27,
            )
            botlogger.inicio_execucao()
            botlogger.inicio_etapa(
                identificacao=self.payload.cnpj or self.payload.cpf or "desconhecido",
            )

            # Loop de tentativas de consulta com retry
            while self.retry_count < self.max_retries:
                response = self.requests.get(self.url, params=self.params, timeout=30)
                dados = response.json()
                self.code = dados.get("code")

                if self.code == 200:
                    # Consulta realizada com sucesso, sai do loop
                    botlogger.fim_etapa()
                    botlogger.fim_execucao()
                    break
                elif self.code == 605:
                    # Inforsimples orienta a dar retry quando o código 605 é retornado.
                    # https://api.infosimples.com/consultas/docs#boas-praticas
                    self.retry_count += 1
                    self.time.sleep(self.retry_sleep)
                    self.retry_sleep *= 2  # Aumenta o tempo de espera exponencialmente
                else:
                    # Qualquer outro código de erro, sai do loop e não tenta novamente
                    botlogger.alerta_etapa(
                        f"Consulta retornou código {self.code} Consulta não foi realizada com sucesso."
                    )
                    botlogger.alerta_execucao(
                        f"Consulta retornou código {self.code} Consulta não foi realizada com sucesso."
                    )
                    break

            return dados

        except self.requests.RequestException as e:
            tipo = (
                "cnpj"
                if self.payload.cnpj
                else "cpf"
                if self.payload.cpf
                else "desconhecido"
            )

            botlogger.erro_etapa(
                f"Erro ao consultar cnd tst {getattr(self.payload, tipo)}: {e}"
            )

            botlogger.erro_execucao(f"Execução com erro: {e}")
            return {"error": "Erro ao conectar com a API.", "data": str(e)}
