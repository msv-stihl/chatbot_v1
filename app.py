from flask import Flask, jsonify
import sqlite3
from flask_cors import CORS
from datetime import datetime, date, timedelta  # Importamos tudo que precisamos para datas
import random

app = Flask(__name__)
CORS(app)

DB_FILE = "chamados.db"


# As funções contar_chamados_abertos, formatar_data_br, gerar_mensagem_explicativa e buscar_os_no_banco
# continuam exatamente as mesmas de antes, sem nenhuma alteração.
# Vou omiti-las aqui para focar na mudança principal, mas elas devem permanecer no seu arquivo.

# ... (cole aqui as funções contar_chamados_abertos, formatar_data_br, gerar_mensagem_explicativa e buscar_os_no_banco da resposta anterior) ...
def contar_chamados_abertos():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = "SELECT prioridade, COUNT(*) FROM chamados WHERE CAST(status AS INTEGER) < 96 AND LOWER(TRIM(prioridade)) != 'prioridade' GROUP BY prioridade;"
        cursor.execute(query)
        resultados = cursor.fetchall()
        conn.close()
        contagem_dict = {str(prioridade): contagem for prioridade, contagem in resultados}
        return contagem_dict
    except Exception as e:
        print(f"Erro ao contar chamados: {e}")
        return {}


def formatar_data_br(data_obj):
    if not isinstance(data_obj, date):
        return "não definida"
    return data_obj.strftime('%d/%m/%Y')


def gerar_mensagem_explicativa(dados_os):
    if not dados_os: return ""
    status_code_bruto = dados_os.get('status', '')
    status_code_limpo = ""
    if status_code_bruto:
        try:
            status_code_limpo = str(int(float(status_code_bruto)))
        except (ValueError, TypeError):
            status_code_limpo = str(status_code_bruto).strip()
    prioridade_code = dados_os.get('prioridade', '')
    data_prevista_db = dados_os.get('data_prevista_formatada', '')  # Usamos a data já formatada
    mapa_prioridade = {'1': 'ZU', '2': 'Alta', '3': 'Média', '4': 'Baixa', '5': 'Parada Programada', '6': 'Visita'}
    prioTxt = mapa_prioridade.get(str(prioridade_code), 'não definida')
    mapa_prazo_ava = {'2': '15 dias', '3': '30 dias', '4': '45 dias'}
    prazoAva = mapa_prazo_ava.get(str(prioridade_code), 'não definido')
    prazo = prazoAva
    dataPrev = data_prevista_db
    strDatePreview = dataPrev
    dias_a_somar = {'1': 7, '2': 15, '3': 30, '4': 45, '5': 90, '6': 10}.get(str(prioridade_code), 30)
    data_futura = date.today() + timedelta(days=dias_a_somar)
    strDatePlusPrio = data_futura.strftime('%d/%m/%Y')
    mapa_mensagens = {
        '0': [
            f"Seu chamado foi aberto como prioridade {prioTxt} e está aguardando avaliação da equipe responsável. Um de nossos técnicos irá te procurar em breve, o prazo de avaliação é de {prazoAva} 😉"],
        '00': [
            f"Seu chamado foi aberto como prioridade {prioTxt} e está aguardando avaliação da equipe responsável. Um de nossos técnicos irá te procurar em breve, o prazo de avaliação é de {prazoAva} 😉"],
        '39': [
            "Estamos buscando um fornecedor no mercado para que possamos adquirir os materiais necessários para atender seu chamado. Peço que consulte novamente dentro de alguns dias 🫡"],
        '40': [
            "Seu chamado está aguardando compra de material. Assim que o material estiver disponível, entrará na programação 🫡"],
        '41': [
            "Seu chamado está aguardando algum de nossos recursos estar disponível para ser programado. Aguarde alguns dias e verifique novamente para uma atualização do status 😁"],
        '42': [
            "Tentamos executar o seu chamado, porém a área não foi liberada 🥺. Favor enviar e-mail para manserv@stihl.com.br com uma data onde a área estará disponível, com pelo menos uma semana de antecedência"],
        '43': [
            f"Seu chamado está aguardando reposição de material no estoque 🙂. Assim que o material estiver disponível, entrará na programação. A previsão máxima é de {strDatePreview}"],
        '44': [
            "Recebemos a informação que seu chamado precisa ser executado durante a próxima parada de manutenção, e ele foi programado para esta data 😀. Caso essa informação esteja incorreta, favor informar através do e-mail manserv@stihl.com.br"],
        '45': [
            "Para realizar seu chamado, precisamos de uma verba que o setor de Infraestrutura não possui no momento 🫤. No próximo mês, faremos uma nova avaliação de custos, portanto peço que consulte novamente seu chamado, tá bom? Caso seja algo muito importante para o setor, e vocês possuam a verba para disponibilizar, favor entrar em contato com o setor de Infraestrutura"],
        '46': [
            f"Seu chamado necessitará de atendimento de uma empresa externa e está em processo de cotação e programação, conforme prioridades definidas pelo setor de Infraestrutura. A previsão máxima, até o momento, é de {strDatePreview} 😉"],
        '47': [
            f"Seu chamado foi definido como prioridade {prioTxt} e tem o prazo de {prazo}. Até o momento, a previsão máxima de execução é {strDatePlusPrio} ☺️"],
        '48': [
            "Vi aqui que seu chamado foi avaliado e está em processo de cotação, a requisição de compra deve ser criada logo mais. Sugiro que verifique novamente dentro de alguns dias para que eu possa te atualizar melhor 😉"],
        '49': [
            f"Já criamos a requisição de compra para poder atender seu chamado e estamos aguardando a entrega do material. Até o momento, a previsão é para {strDatePreview} 😄"],
        '50': [f"Uhuu! Seu chamado está programado para o dia {dataPrev} 🥰"],
        '55': ["Seu chamado está em execução 🫡", "Nossa equipe já está trabalhando na sua solicitação. 👨‍🔧",
               "Boas notícias! A execução do seu chamado já foi iniciada. 🫡"],
        '77': ["Trago ótimas notícias, seu chamado foi executado 🤗",
               "Missão cumprida! Sua solicitação foi atendida com sucesso. ✅",
               "Finalizamos o serviço do seu chamado. Tudo pronto! 🤗"],
        '95': ["Seu chamado está aguardando atualização de status, favor consultar novamente dentro de algumas horas"],
        '96': ["Seu chamado foi cancelado 😞"],
        '97': ["Seu chamado está aguardando atualização de status, favor consultar novamente dentro de algumas horas"],
        '99': ["Eba!! Seu chamado foi resolvido 🤩", "Problema solucionado! Seu chamado foi concluído com sucesso. ✨",
               "Pode comemorar! Seu chamado consta como resolvido em nosso sistema. 🤩"]
    }
    lista_de_mensagens = mapa_mensagens.get(status_code_limpo)
    if lista_de_mensagens:
        return random.choice(lista_de_mensagens)
    else:
        return "Status não reconhecido, favor contatar o suporte."


def buscar_os_no_banco(numero_os):
    print("🔎 Buscando OS:", numero_os)
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chamados WHERE numero_os = ?", (numero_os,))
        chamado = cursor.fetchone()
        conn.close()
        if chamado: return dict(chamado)
        return None
    except sqlite3.OperationalError:
        print("AVISO: Tabela 'chamados' não encontrada. Execute o coletor.py primeiro.")
        return None


# --- ROTA DA API ATUALIZADA COM A NOVA LÓGICA DE DATAS ---
@app.route('/api/os/<string:numero_os>', methods=['GET'])
def get_os_status(numero_os):
    """Endpoint da API que o chatbot vai chamar."""
    dados_os = buscar_os_no_banco(numero_os)

    if dados_os:
        # --- INÍCIO DA NOVA LÓGICA DE CÁLCULO DE DATA ---

        hoje = date.today()
        data_final_formatada = "não definida"

        data_prevista_str = dados_os.get('data_prevista')
        prioridade_code = str(dados_os.get('prioridade', ''))

        data_a_usar = None

        if data_prevista_str:
            try:
                # Tenta converter a data do banco para um objeto de data
                data_prevista_obj = datetime.strptime(data_prevista_str.split(' ')[0], '%Y-%m-%d').date()

                # A CONDIÇÃO PRINCIPAL: a data prevista já passou?
                if data_prevista_obj < hoje:
                    print(
                        f"DEBUG: Data {data_prevista_obj} está no passado. Recalculando com base na prioridade {prioridade_code}.")
                    # Se passou, calcula a nova data com base na prioridade
                    if prioridade_code == '2':  # Alta
                        data_a_usar = hoje + timedelta(days=30)
                    elif prioridade_code == '3':  # Média
                        data_a_usar = hoje + timedelta(days=60)
                    elif prioridade_code == '4':  # Baixa
                        data_a_usar = hoje + timedelta(days=90)
                    elif prioridade_code == '5':  # Parada Programada
                        ano_seguinte = hoje.year + 1
                        data_a_usar = date(ano_seguinte, 1, 15)  # 15 de Janeiro do próximo ano
                    else:
                        # Para outras prioridades (1, 6, etc.), mantém a data original vencida
                        data_a_usar = data_prevista_obj
                else:
                    # Se a data prevista ainda está no futuro, usa ela mesma
                    data_a_usar = data_prevista_obj

            except (ValueError, TypeError):
                # Se a data do banco for inválida, não fazemos nada e resultará em "não definida"
                print(f"DEBUG: Formato de data inválido no banco: {data_prevista_str}")
                pass

        if data_a_usar:
            data_final_formatada = data_a_usar.strftime('%d/%m/%Y')

        # Adiciona a data final (original ou recalculada) à resposta
        dados_os['data_prevista_formatada'] = data_final_formatada

        # --- FIM DA NOVA LÓGICA DE CÁLCULO DE DATA ---

        # O resto da lógica continua igual
        descricao_status = gerar_mensagem_explicativa(dados_os)
        dados_os['descricao_status'] = descricao_status

        contagem_abertos = contar_chamados_abertos()
        dados_os['contagem_abertos'] = contagem_abertos

        return jsonify(dados_os)
    else:
        return jsonify({"erro": f"A OS {numero_os} não foi encontrada em nossa base."}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)