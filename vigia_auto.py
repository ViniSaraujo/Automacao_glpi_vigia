import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from flask import Flask, render_template

# --- Bloco 2: Configurações ATUALIZADO ---
# --- PREENCHA SUAS INFORMAÇÕES AQUI ---
GLPI_URL_BASE = 'https://chamados.slmandic.edu.br'
URL_FORMULARIO_LOGIN = f'{GLPI_URL_BASE}/glpi/front/login.php' 
URL_POST_LOGIN = f'{GLPI_URL_BASE}/glpi/front/login.php' 

# PREENCHA SUA SENHA AQUI
GLPI_USER = "01992005"
GLPI_PASSWORD = "SUA_SENHA_AQUI" # <--- COLOQUE SUA SENHA

# --- NOSSAS 3 URLs DE ALVO (sem o _glpi_csrf_token) ---

# 1. A sua URL original (Pesquisa Salva 613) que mostra o TOTAL
URL_TOTAL = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&search=Pesquisar&itemtype=Ticket&savedsearches_id=613&reset=reset&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=1&criteria%5B1%5D%5Blink%5D=OR&criteria%5B1%5D%5Bfield%5D=12&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=4&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=5&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&criteria%5B3%5D%5Blink%5D=AND&criteria%5B3%5D%5Bfield%5D=8&criteria%5B3%5D%5Bsearchtype%5D=equals&criteria%5B3%5D%5Bvalue%5D=0"""

# 2. A URL "Vigia - Novo" (Status=1)
URL_NOVOS = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=1&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=5&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&criteria%5B3%5D%5Blink%5D=AND&criteria%5B3%5D%5Bfield%5D=8&criteria%5B3%5D%5Bsearchtype%5D=equals&criteria%5B3%5D%5Bvalue%5D=0&search=Pesquisar&itemtype=Ticket&start=0"""

# 3. A URL "Vigia - Pendente" (Status=4)
URL_PENDENTES = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?criteria%5B1%5D%5Blink%5D=OR&criteria%5B1%5D%5Bfield%5D=12&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=4&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=5&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&criteria%5B3%5D%5Blink%5D=AND&criteria%5B3%5D%5Bfield%5D=8&criteria%5B3%5D%5Bsearchtype%5D=equals&criteria%5B3%5D%5Bvalue%5D=0&search=Pesquisar&itemtype=Ticket&start=0"""


# --- Bloco 3: Funções do Robô Vigia ---

# A função fazer_login continua EXATAMENTE IGUAL. Não mexa nela.
def fazer_login(session):
    print("Iniciando missão: Fazer Login...")
    try:
        print("  - Acessando a página de login para espionar os campos...")
        resposta_get = session.get(URL_FORMULARIO_LOGIN, timeout=10)
        resposta_get.raise_for_status()
        soup = BeautifulSoup(resposta_get.text, 'html.parser')
        
        campo_usuario = soup.find('input', {'id': 'login_name'})
        nome_campo_usuario = campo_usuario['name'] if campo_usuario else 'login_name'
        campo_senha = soup.find('input', {'id': 'login_password'})
        nome_campo_senha = campo_senha['name'] if campo_senha else 'login_password'
        token_input = soup.find('input', {'name': '_glpi_csrf_token'})
        csrf_token = token_input['value'] if token_input else None
        
        print(f"  - Campo de usuário dinâmico: {nome_campo_usuario}")
        print(f"  - Campo de senha dinâmico: {nome_campo_senha}")
        
        payload = {
            nome_campo_usuario: GLPI_USER,
            nome_campo_senha: GLPI_PASSWORD,
            '_glpi_csrf_token': csrf_token,
            'submit': 'Enviar',
            'noAUTO': '1'
        }
        
        print("  - Enviando credenciais...")
        resposta_post = session.post(URL_POST_LOGIN, data=payload, timeout=10)
        resposta_post.raise_for_status()
        
        if "Sair" in resposta_post.text:
            print("Sucesso! Login realizado.")
            return True
        else:
            print("Falha no login. Verifique as credenciais ou a palavra 'Sair'.")
            return False
    except Exception as e:
        print(f"Ocorreu um erro durante o processo de login: {e}")
        return False

# ✅ FUNÇÃO REFATORADA: Agora ela é reutilizável
def buscar_contagem(session, url_alvo, nome_do_filtro):
    """
    Navega até uma URL específica e extrai o número total de chamados
    daquele filtro específico.
    Retorna o número (int) ou None.
    """
    print(f"Iniciando missão: Buscar Contagem de '{nome_do_filtro}'...")
    texto_completo = "Erro: elemento não encontrado"
    try:
        print(f"  - Acessando {url_alvo[:70]}...") # Mostra só o começo da URL longa
        resposta = session.get(url_alvo, timeout=15)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # Usamos o seletor <td> que você descobriu
        elemento = soup.find('td', class_='tab_bg_2 b')
        
        if elemento:
            texto_completo = elemento.text.strip()
            palavras = texto_completo.split()
            if palavras:
                valor_texto = palavras[-1] # Pega o último número
                print(f"  - Texto: '{texto_completo}', Número: '{valor_texto}'")
                return int(valor_texto)
            else:
                print(f"  - Erro: lista de palavras vazia para '{texto_completo}'")
                return 0 # Se não achou nada, retorna 0
        else:
            print("  - Elemento <td> não encontrado. Retornando 0.")
            # Se o elemento não existe, significa que a contagem é 0
            return 0 
            
    except Exception as e:
        print(f"  - Ocorreu um erro ao buscar contagem de '{nome_do_filtro}': {e}")
        return None

# --- Bloco 4: A Aplicação Web Flask ---
app = Flask(__name__)

# ✅ ROTA ATUALIZADA: Agora ela faz 3 buscas
@app.route('/')
def mostrar_status():
    """
    Rota principal. Loga, busca as 3 contagens (Total, Novos, Pendentes)
    e renderiza o template HTML.
    """
    print("Requisição recebida na rota '/'. Iniciando processo...")
    dados = {} # Dicionário para guardar todos os nossos números
    erro = None
    
    sessao_http = requests.Session()
    
    if fazer_login(sessao_http):
        time.sleep(1) 
        
        # Chama a função de busca 3 vezes, uma para cada URL
        dados['total'] = buscar_contagem(sessao_http, URL_TOTAL, "Total")
        dados['novos'] = buscar_contagem(sessao_http, URL_NOVOS, "Novos")
        dados['pendentes'] = buscar_contagem(sessao_http, URL_PENDENTES, "Pendentes")
        
        if dados['total'] is None or dados['novos'] is None or dados['pendentes'] is None:
            status_mensagem = "Login OK, mas falha ao buscar/processar dados da página."
            erro = "Pelo menos uma das contagens falhou."
        else:
            status_mensagem = "Dados obtidos com sucesso!"
    else:
        status_mensagem = "Falha no login."
        erro = "Verifique as credenciais, URL de login ou payload."

    contexto = {
        'dados': dados, # Envia o dicionário inteiro (ex: {'total': 10, 'novos': 1, 'pendentes': 9})
        'mensagem': status_mensagem,
        'erro_msg': erro,
        'agora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return render_template('vigia.html', **contexto) # Vamos ATUALIZAR o vigia.html

# --- Bloco 5: Ponto de Partida do Servidor ---
if __name__ == "__main__":
    print(f"--- Servidor Flask Vigia GLPI (versão DETALHADA) iniciado ---")
    print(f"Acesse em seu navegador: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)