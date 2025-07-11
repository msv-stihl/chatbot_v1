import os
import re
import time
import sqlite3
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURAÇÃO E SEGURANÇA ---
# TODO: Substitua pelos seus dados. NUNCA deixe senhas diretamente no código em produção.
# Considere usar variáveis de ambiente ou um cofre de segredos no futuro.
PRISMA_URL = "https://prisma4.manserv.com.br/Prisma4/"
PRISMA_USER = "028885"  # SEU USUÁRIO
PRISMA_PASS = "Wb230818#" # !! USE A NOVA SENHA QUE VOCÊ CRIOU !!

# Define o diretório de trabalho e a pasta de downloads
# Isso garante que o script funcione, não importa de onde ele seja chamado.
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_DOWNLOAD = os.path.abspath(os.path.join(DIRETORIO_ATUAL, "downloads"))
ARQUIVO_DESTINO = os.path.join(DIRETORIO_ATUAL, "exportacao.xlsx")

# Garante que a pasta de downloads exista
if not os.path.exists(PASTA_DOWNLOAD):
    os.makedirs(PASTA_DOWNLOAD)

def coletar_e_salvar_dados():
    """
    Função principal que executa toda a automação: login, download e processamento do Excel.
    """
    print("Iniciando o robô de coleta de dados...")

    # --- Configuração do Selenium (Headless e Pasta de Download) ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("window-size=1920,1080")
    # Configura o Chrome para baixar arquivos na nossa pasta 'downloads' sem perguntar
    prefs = {
        "download.default_directory": PASTA_DOWNLOAD,
        "download.prompt_for_download": False,         # Não pedir local para salvar
        "directory_upgrade": True,                     # Atualiza pasta automaticamente
        "safebrowsing.enabled": True                   # Evita bloqueio por segurança
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    # Define um tempo de espera máximo de 30 segundos para os elementos aparecerem
    wait = WebDriverWait(driver, 30)

    try:
        # --- ETAPA 1: LOGIN ---
        print(f"Acessando {PRISMA_URL}...")
        driver.get(PRISMA_URL)

        # TODO: SUA TAREFA É ENCONTRAR OS SELETORES CORRETOS NO SITE DO PRISMA4
        # Use o "Inspecionar" do seu navegador para encontrar o 'id' ou 'name' dos campos.
        print("Realizando login...")
        wait.until(EC.presence_of_element_located((By.ID, 'UserName'))).send_keys(PRISMA_USER)
        wait.until(EC.presence_of_element_located((By.ID, 'Password'))).send_keys(PRISMA_PASS)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))).click()
        print("Login realizado com sucesso!")

        # --- ETAPA 2: NAVEGAÇÃO E EXPORTAÇÃO ---
        # TODO: ESTA PARTE É UM EXEMPLO. VOCÊ PRECISA ADAPTAR COM OS CLICKS REAIS.
        # Encontre os seletores dos menus e do botão de exportar.
        print("Navegando até o relatório...")
        elemento = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='nav-label' and contains(text(), 'Ordens de Serviço')]")))
        driver.execute_script("arguments[0].click();", elemento)
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//span[@class='nav-label' and contains(text(), 'OS Completa')]"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//div[contains(@class, 'sp-input-button') and contains(@class, 'sp-search-button')]"))).click()
        # Aguarda o select aparecer
        select_element = wait.until(EC.presence_of_element_located((By.XPATH, 
            "//select[contains(@class, 'searches-combo')]")))
        # Cria o objeto Select e seleciona pelo valor
        wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@class, 'searches-combo')]/option[@value='119']")))
        select_box = Select(select_element)
        select_box.select_by_value("119")  # valor do Chatbot_v2

        print("Exportando o arquivo Excel...")
        # Aguarda o botão "Passar para Excel" se tornar clicável (até 30s)
        botao_excel = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,
            "//button[contains(@class, 'search-window-excel') and contains(., 'Passar para Excel')]")))
        # Clica no botão
        botao_excel.click()

        # --- ETAPA 3: AGUARDAR O DOWNLOAD ---
        print("Aguardando o download do arquivo...")
        tempo_espera = 0
        arquivo_baixado = None
        while tempo_espera < 60: # Espera por no máximo 60 segundos
            lista_arquivos = [f for f in os.listdir(PASTA_DOWNLOAD) if f.endswith(('.xlsx', '.xls'))]
            if lista_arquivos:
                arquivo_baixado = os.path.join(PASTA_DOWNLOAD, lista_arquivos[0])
                print(f"Download concluído: {arquivo_baixado}")
                break
            time.sleep(1)
            tempo_espera += 1
        
        if not arquivo_baixado:
            raise Exception("O download do arquivo demorou muito ou falhou.")

        # --- ETAPA 4: PROCESSAR O EXCEL COM PANDAS ---
        print("Processando a planilha...")
        # Lê o arquivo baixado, pulando as 5 primeiras linhas (dados começam na linha 6)
        df_novo = pd.read_excel(arquivo_baixado, skiprows=5)
        
        # Carrega o arquivo de destino existente para manter a formatação
        with pd.ExcelWriter(ARQUIVO_DESTINO, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            # Escreve os novos dados na planilha, começando na linha 2 (índice 1)
            # header=False e index=False garantem que só os dados sejam escritos, preservando seu cabeçalho original.
            df_novo.to_excel(writer, sheet_name='sisteplant', startrow=1, header=False, index=False)
        
        print(f"Arquivo {os.path.basename(ARQUIVO_DESTINO)} atualizado com {len(df_novo)} registros.")

        # --- ETAPA 5: LIMPEZA ---
        print(f"Limpando o arquivo baixado: {os.path.basename(arquivo_baixado)}")
        os.remove(arquivo_baixado)
        # Releitura do arquivo final consolidado para garantir fidelidade
        df_final = pd.read_excel(ARQUIVO_DESTINO, sheet_name='sisteplant')
        # Remove registros inválidos que tenham 'numero_os' como o texto do cabeçalho
        print(df_final.columns.tolist())
        print(f"Tentando salvar {len(df_final)} registros no banco.")
        print(df_final.head(3))
        salvar_dados_no_banco(df_final)
        exportar_para_json(df_final)


    except Exception as e:
        print(f"\nOcorreu um erro durante a automação: {e}")
        # Tira um screenshot da tela no momento do erro para ajudar a depurar
        driver.save_screenshot("erro_screenshot.png")
        print("Um screenshot do erro foi salvo como 'erro_screenshot.png'.")
        raise

    finally:
        # Garante que o navegador seja sempre fechado no final
        print("Fechando o navegador.")
        driver.quit()

def limpar_descricao(descricao):
    """
    Se a descrição contiver 'Solicitante Nome Sobrenome.', retorna tudo até esse ponto.
    Caso contrário, retorna a descrição original.
    """
    match = re.search(r"(.*?Solicitante\s+[A-ZÀ-ÿa-z\s]+?\.)", descricao, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return descricao.strip()

def salvar_dados_no_banco(df):
    conn = sqlite3.connect("chamados.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            numero_os TEXT PRIMARY KEY,
            os_prisma TEXT,
            prioridade TEXT,
            oficina TEXT,
            ativo TEXT,
            denominacao TEXT,
            descricao TEXT,
            status TEXT,
            data_prevista TEXT,
            tipo_servico TEXT
        )
    """)

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO chamados (
                numero_os, os_prisma, prioridade, oficina, ativo,
                denominacao, descricao, status, data_prevista, tipo_servico
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(row.get('numero_os', '')),
            str(row.get('os_prisma', '')),
            str(row.get('prioridade', '')),
            str(row.get('oficina', '')),
            str(row.get('ativo', '')),
            str(row.get('denominacao', '')),
            limpar_descricao(str(row.get('descricao', ''))),
            str(row.get('status', '')),
            str(row.get('data_prevista', '')),
            str(row.get('tipo_servico', ''))
        ))

    conn.commit()
    conn.close()
    print("✅ Dados salvos no banco chamados.db com sucesso!")

def exportar_para_json(df, caminho_json="dados.json"):
    campos_necessarios = [
        'numero_os', 'prioridade', 'descricao', 'status', 'data_prevista'
    ]
    df_filtrado = df[campos_necessarios].copy()
    df_filtrado.to_json(caminho_json, orient='records', force_ascii=False, indent=2)
    print(f"📁 Arquivo {caminho_json} exportado com sucesso.")

# Bloco principal para executar o script
if __name__ == '__main__':
    max_tentativas = 3
    for tentativa in range(1, max_tentativas + 1):
        print(f"\n🔄 Tentativa {tentativa} de {max_tentativas}...\n")
        try:
            coletar_e_salvar_dados()
            print("✅ Execução concluída com sucesso.")
            break  # Sai do loop se der certo
        except Exception as e:
            print(f"❌ Erro na tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                print("⏳ Aguardando 30 segundos antes de tentar novamente...")
                time.sleep(30)
            else:
                print("🚫 Todas as tentativas falharam. Encerrando.")