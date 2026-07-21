import os
from pathlib import Path
from typing import List, Tuple


def limpar_requirements(caminho_requirements_automacao):
    """
    Remove do requirements.txt da automação todas as dependências que existem
    no worker-requirements.txt da raiz, mantendo apenas as dependências exclusivas.

    Args:
        caminho_requirements_automacao (str): Caminho para o requirements.txt da automação
    """
    # Encontrar o worker-requirements.txt na raiz
    raiz = Path(caminho_requirements_automacao).drive + "\\"

    # Procurar worker-requirements.txt na raiz do projeto
    worker_req_path = None
    for item in Path(caminho_requirements_automacao).parents:
        potencial_path = item / "worker-requirements.txt"
        if potencial_path.exists():
            worker_req_path = potencial_path
            break

    if not worker_req_path:
        print("❌ worker-requirements.txt não encontrado")
        return

    # Ler dependências do worker-requirements.txt
    def read_lines_with_fallback(filepath) -> Tuple[List[str], str]:
        """
        Tenta ler um arquivo usando várias codificações e retorna (linhas, encoding_usada).
        Se todas falharem, lê em 'utf-8' com errors='replace'.
        """
        encodings = ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1"]
        for enc in encodings:
            try:
                with open(filepath, "r", encoding=enc) as f:
                    return f.readlines(), enc
            except FileNotFoundError:
                raise
            except Exception:
                continue

        # fallback: read binary and decode replacing errors
        try:
            with open(filepath, "rb") as f:
                data = f.read()
                text = data.decode("utf-8", errors="replace")
                return text.splitlines(keepends=True), "utf-8-replace"
        except FileNotFoundError:
            raise

    def extrair_packages(filepath):
        packages = set()
        try:
            linhas, used_enc = read_lines_with_fallback(filepath)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {filepath}")
            return packages

        for linha in linhas:
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                # Extrair apenas o nome do pacote (antes de ==, >=, <=, etc)
                package_name = (
                    linha.split("==")[0]
                    .split(">=")[0]
                    .split("<=")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .split("!=")[0]
                    .strip()
                )
                packages.add(package_name.lower())

        return packages

    # Ler o requirements.txt da automação
    try:
        linhas_automacao, enc_auto = read_lines_with_fallback(
            caminho_requirements_automacao
        )
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {caminho_requirements_automacao}")
        return

    # Extrair packages do worker-requirements.txt
    packages_worker = extrair_packages(str(worker_req_path))

    # Filtrar linhas do requirements da automação
    linhas_filtradas = []
    for linha in linhas_automacao:
        linha_strip = linha.strip()

        # Manter linhas vazias e comentários
        if not linha_strip or linha_strip.startswith("#"):
            linhas_filtradas.append(linha)
        else:
            # Extrair nome do pacote
            package_name = (
                linha_strip.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
                .split("!=")[0]
                .strip()
                .lower()
            )

            # Manter apenas se não estiver no worker-requirements.txt
            if package_name not in packages_worker:
                linhas_filtradas.append(linha)

    # Escrever o requirements.txt limpo (salva em utf-8)
    with open(caminho_requirements_automacao, "w", encoding="utf-8") as f:
        f.writelines(linhas_filtradas)

    print("✅ requirements.txt limpo com sucesso!")
    print(f"📍 Arquivo: {caminho_requirements_automacao}")
    print(f"📍 Worker requirements removidas: {len(packages_worker)}")
    print(
        f"📍 Dependências mantidas: {len([l for l in linhas_filtradas if l.strip() and not l.strip().startswith('#')])}"
    )


if __name__ == "__main__":
    # Exemplo de uso
    limpar_requirements(r"app\automacoes\consulta_cnpj\requirements.txt")
