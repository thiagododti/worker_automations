import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import os


class Botlogger:
    def __init__(self, empresa: str, envio_manual=False, automacao_id=None):
        self.envio_manual = envio_manual
        self.botlogger_version = self._get_botlogger_version()
        self._env_check()
        # Recebimento de parametros
        automation_id_env = automacao_id or os.getenv("AUTOMACAO_ID_PARA_EXECUCAO", 0)
        self.automation_id = int(automation_id_env) if automation_id_env else 0
        self.empresa = empresa
        # URL base e headers comuns para todas as requisições
        self.token = os.getenv("TOKEN_BOTLOGGER_OFICIAL", None)
        self.url = os.getenv("HOST_BOTLOGGER_OFICIAL", "")
        self.headers = {"Authorization": f"Token {self.token}"}

        self.automation_url = f"{self.url}/api/automations/{{id}}/"
        self.execution_url = f"{self.url}/api/executions/"
        self.patch_execution_url = f"{self.url}/api/executions/{{id}}/"
        self.step_url = f"{self.url}/api/executions/steps/"
        self.patch_step_url = f"{self.url}/api/executions/steps/{{id}}/"
        self.log_url = f"{self.url}/api/executions/logs/"
        self.business_url = f"{self.url}/api/business/"
        self.url_bitrix = os.getenv("URL_BITRIX", "")

        self.status_aceitos = ["concluido", "erro", "alerta", "teste"]

        # Em ambiente de desenvolvimento, evita enviar mensagens para o Bitrix24

        self.business = None
        self.business_id = None
        # Dados essenciais para o funcionamento do Botlogger

        self.automation = None

        self.execution = None
        self.execution_id = None
        self.etapa = None
        self.etapa_id = None

        # Verifica se token foi carregado
        if not self.token:
            raise ValueError(
                "Token do Botlogger não encontrado. Verifique o arquivo .env o token foi carregado na variavel TOKEN_BOTLOGGER_OFICIAL."
            )
        if automacao_id is None and self.automation_id == 0:
            raise ValueError(
                "ID da automação não encontrado. Verifique o arquivo .env o token foi carregado na variavel AUTOMACAO_ID_PARA_EXECUCAO."
            )

        if not self.url:
            raise ValueError(
                "URL do Botlogger não encontrada. Verifique o arquivo .env o token foi carregado na variavel HOST_BOTLOGGER_OFICIAL."
            )
        if not self.url_bitrix:
            raise ValueError(
                "URL do Bitrix24 não encontrada. Verifique o arquivo .env o token foi carregado na variavel URL_BITRIX."
            )

        # busca e empresa
        self.get_empresa()
        self.get_automation()
        if self.automation and self.automation["in_manutention"]:
            self.em_implementacao = True
        else:
            self.em_implementacao = False

        if self.automation and self.automation["auth_certificate"]:
            self.troca_certificado()

    def _get_botlogger_version(self):
        import ast
        import hashlib
        from pathlib import Path

        file_path = Path(__file__).resolve()

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        normalized = ast.dump(tree)

        return hashlib.sha256(normalized.encode()).hexdigest()

    def _env_check(self):
        from pathlib import Path
        # Verifica se existe um arquivo .env na raiz do projeto e retorna true ou false

        if Path(".env").exists():
            # Carrega as variáveis de ambiente do arquivo .env
            load_dotenv()

        envs_necessarias = [
            "TOKEN_BOTLOGGER_OFICIAL",
            "HOST_BOTLOGGER_OFICIAL",
            "URL_BITRIX",
        ]
        if not self.automation_id:
            envs_necessarias.append("AUTOMACAO_ID_PARA_EXECUCAO")

        for env in envs_necessarias:
            if not os.getenv(env):
                raise EnvironmentError(f"Variável obrigatória '{env}' não encontrada!")

            value = os.getenv(env)
            if value is None or value.strip() == "":
                raise ValueError(f"Variável de ambiente '{env}' está vazia.")

    def _safe_request(self, method, url, retries=3, backoff=1, **kwargs):
        for attempt in range(retries):
            try:
                response = requests.request(
                    method, url, timeout=5, verify=False, **kwargs
                )
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                if attempt < retries - 1:
                    wait = backoff * (2**attempt)
                    print(
                        f"[BOTLOGGER RETRY] tentativa {attempt + 1} falhou: {e} | retry em {wait}s"
                    )
                    time.sleep(wait)
                else:
                    print(f"[BOTLOGGER ERROR] falha definitiva: {e}")
                    return None

    def _safe_json(self, response):
        try:
            return response.json() if response else {}
        except Exception:
            return {}

    def send_bitrix_message(self, erro):
        automacao = (
            self.execution.get("automation_data", {}).get("name", "N/A")
            if self.execution
            else "N/A"
        )
        inicio = self.execution.get("date_start", "N/A") if self.execution else "N/A"
        if inicio != "N/A":
            inicio = datetime.strptime(
                inicio.rstrip("Z"), "%Y-%m-%dT%H:%M:%S.%f"
            ).strftime("%d/%m/%Y %H:%M:%S")

        fim = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        url = f"{self.url_bitrix}"

        # Validação: verifica se a mensagem está vazia
        if not automacao or not erro or not inicio or not fim:
            print(f"⚠️ AVISO: Campos obrigatórios faltando")
            return False

        message = f"🤖 Automação - {automacao}\n🆘 erro: {erro}\n▶️ Data Inicio: {inicio} | ⏸️ Data Fim: {fim}"
        params = {"DIALOG_ID": "chat184838", "MESSAGE": message}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins
            print(f"✅ Mensagem enviada com sucesso")
            return True
        except requests.exceptions.RequestException as e:
            # Substitua por logger.
            print(f"❌ Erro ao enviar mensagem: {e}")

    def log(self, mensagem):
        if not self.execution_id:
            return

        data = {"description": mensagem, "execution": self.execution_id}

        response = self._safe_request(
            "POST", self.log_url, json=data, headers=self.headers
        )

        log = self._safe_json(response)
        print(f"Log registrado: {log.get('id')}")

    def get_empresa(self):
        params = {"cnpj": self.empresa}
        response = self._safe_request(
            "GET", self.business_url, headers=self.headers, params=params
        )

        results = self._safe_json(response)

        self.business = results.get("results")

        if not results:
            raise ValueError("Nenhum business encontrado para os parâmetros informados")

        self.business_id = int(self.business[0].get("id"))

        if not self.business_id:
            raise ValueError("Business encontrado, mas sem ID válido")

    def get_automation(self):

        response = self._safe_request(
            "GET",
            self.automation_url.format(id=self.automation_id),
            headers=self.headers,
        )

        self.automation = self._safe_json(response)

        if not self.automation:
            raise ValueError(
                "Nenhuma automação encontrada para os parâmetros informados"
            )

    def update_string_value(self, name: str, value: str, path: str):
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

        except PermissionError:
            raise PermissionError(
                "Permissão negada ao acessar o registro. Execute como administrador."
            )

        except FileNotFoundError:
            raise FileNotFoundError(f"Caminho do registro não encontrado: {path}")

        except Exception as e:
            raise RuntimeError(f"Erro ao atualizar registro: {str(e)}")

    def troca_certificado(self):
        path = r"SOFTWARE\Policies\Google\Chrome\AutoSelectCertificateForUrls"
        name = "1"

        # URL vem da automação
        url = self.automation.get("url_certificate")

        if not url:
            raise ValueError("A automação não possui 'url_certificate'.")

        # Considerando que você vai usar o primeiro business
        if not self.business or not isinstance(self.business, list):
            raise ValueError("Nenhum business informado.")

        business = self.business[0]

        # Validação dos campos obrigatórios
        required_fields = [
            "subject_cn",
            "subject_c",
            "subject_o",
            "issuer_cn",
            "issuer_c",
            "issuer_o",
        ]

        for field in required_fields:
            if not business.get(field):
                raise ValueError(f"Campo obrigatório ausente no business: {field}")

        json_data = {
            "pattern": url,
            "filter": {
                "ISSUER": {
                    "CN": business["issuer_cn"],
                    "C": business["issuer_c"],
                    "O": business["issuer_o"],
                },
                "SUBJECT": {
                    "CN": business["subject_cn"],
                    "C": business["subject_c"],
                    "O": business["subject_o"],
                },
            },
        }

        import json

        self.update_string_value(name, json.dumps(json_data), path)

    def inicio_execucao(self, date_start=None, date_end=None, status=None):

        data = {
            "status": "iniciado",
            "automation": self.automation_id,
            "business": self.business_id,
        }
        if self.envio_manual:
            if not date_start or not date_end or not status:
                raise ValueError(
                    "Para envio manual, date_start, date_end e status são obrigatórios."
                )

            if status not in self.status_aceitos:
                raise ValueError(
                    f"Status '{status}' não é válido. Status aceitos: {self.status_aceitos}"
                )

            data["date_start"] = date_start
            data["date_end"] = date_end
            data["status"] = status
            data["envio_manual"] = self.envio_manual

        print(data)
        response = self._safe_request(
            "POST", self.execution_url, json=data, headers=self.headers
        )

        execution = self._safe_json(response)

        self.execution = execution
        self.execution_id = execution.get("id")

        if not self.execution_id:
            raise ValueError("Falha ao iniciar execução: ID não retornado")

        print(f"Execução iniciada: {self.execution_id}")

    def fim_execucao(self, mensagem=None):
        if not self.execution_id:
            return

        response = self._safe_request(
            "PATCH",
            self.patch_execution_url.format(id=self.execution_id),
            json={"status": "concluido"},
            headers=self.headers,
        )

        execution = self._safe_json(response)

        if mensagem:
            self.log(mensagem)
        print(f"Execução finalizada: {execution.get('id')}")

    def erro_execucao(self, mensagem):
        if not self.execution_id:
            return

        response = self._safe_request(
            "PATCH",
            self.patch_execution_url.format(id=self.execution_id),
            json={"status": "erro"},
            headers=self.headers,
        )

        self.log(mensagem)
        if not self.em_implementacao:
            self.send_bitrix_message(erro=mensagem)

        execution = self._safe_json(response)
        print(f"Execução com erro: {execution.get('id')}")

    def alerta_execucao(self, mensagem):
        if not self.execution_id:
            return

        response = self._safe_request(
            "PATCH",
            self.patch_execution_url.format(id=self.execution_id),
            json={"status": "alerta"},
            headers=self.headers,
        )

        self.log(mensagem)

        execution = self._safe_json(response)
        print(f"Execução com alerta: {execution.get('id')}")

    def inicio_etapa(self, identificacao, status=None, date_start=None, date_end=None):
        if not self.execution_id:
            return

        data = {
            "identification": identificacao,
            "status": "iniciado",
            "execution": self.execution_id,
        }

        if self.envio_manual:
            # Validações para envio manual
            if status != "erro" and (not date_start or not date_end):
                raise ValueError(
                    "Para envio manual, date_start e date_end são obrigatórios, exceto para status 'erro'."
                )
            # Em status 'erro', date_end deve ser None
            if status not in self.status_aceitos:
                raise ValueError(
                    f"Status '{status}' não é válido. Status aceitos: {self.status_aceitos}"
                )

            data["date_start"] = date_start
            data["status"] = status
            data["envio_manual"] = self.envio_manual

            if status != "erro":
                data["date_end"] = date_end
            elif status == "erro":
                data["date_end"] = None

        print(data)
        response = self._safe_request(
            "POST", self.step_url, json=data, headers=self.headers
        )

        step = self._safe_json(response)

        self.etapa = step
        self.etapa_id = step.get("id")

        print(f"Etapa iniciada: {self.etapa_id}")

    def fim_etapa(self, mensagem=None):
        if not self.etapa_id:
            return

        self._safe_request(
            "PATCH",
            self.patch_step_url.format(id=self.etapa_id),
            json={"status": "concluido"},
            headers=self.headers,
        )

        if mensagem:
            self.log(mensagem)

        print(f"Etapa finalizada: {self.etapa_id}")

    def erro_etapa(self, mensagem):
        if not self.etapa_id:
            return

        self._safe_request(
            "PATCH",
            self.patch_step_url.format(id=self.etapa_id),
            json={"status": "erro"},
            headers=self.headers,
        )

        self.log(mensagem)

        print(f"Etapa com erro: {self.etapa_id}")

    def alerta_etapa(self, mensagem):
        if not self.etapa_id:
            return

        self._safe_request(
            "PATCH",
            self.patch_step_url.format(id=self.etapa_id),
            json={"status": "alerta"},
            headers=self.headers,
        )

        self.log(mensagem)

        print(f"Etapa com alerta: {self.etapa_id}")
