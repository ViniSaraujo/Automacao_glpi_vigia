import requests
from bs4 import BeautifulSoup import time
import time

GLPI_URL_BASE= 'https://chamados.slmandic.edu.br/glpi'
LOGIN_URL:'https://chamados.slmandic.edu.br/glpi/front/login.php'
GLPI_USER:
GLPI_PASSWORD:
PAGINA_ALVO_URL = f""
def fazer_login(session):
    """
    Faz o login em duas etapas: 
    1. Visita a página para pegar um CSRF token válido.
    2. Envia o formulário de login com o token.
    """
    print("Iniciando missão: Fazer Login (com coleta de token)...")
    
    try:
        # --- ETAPA 1: VISITAR A PÁGINA E PEGAR O TOKEN (o "ingresso") ---
        print("  - Acessando a página de login para pegar o token de segurança...")
        # Primeiro, fazemos uma requisição GET para a página de login
        resposta_get = session.get(LOGIN_URL)
        
        # Usamos o BeautifulSoup para "ler" o HTML e encontrar o token
        soup = BeautifulSoup(resposta_get.text, 'html.parser')
        
        # O token geralmente está em um campo <input> escondido (hidden)
        token_input = soup.find('input', {'name': '_glpi_csrf_token'})
        
        if token_input:
            csrf_token = token_input['value']
            print(f"  - Token CSRF encontrado: {csrf_token[:10]}...") # Mostra só o começo do token
        else:
            print("  - ATENÇÃO: Campo _glpi_csrf_token não encontrado. Tentando logar sem ele.")
            csrf_token = None # Se não encontrar, tentamos logar sem

        # --- ETAPA 2: MONTAR O PAYLOAD E FAZER O LOGIN ---
        # Agora montamos o payload com o token FRESCO que acabamos de pegar
        payload = {
            'login_name': GLPI_USER,
            'login_password': GLPI_PASSWORD,
            'submit': 'Conectar',
            '_glpi_csrf_token': csrf_token # AQUI ELE ENTRA!
            # Adicione aqui qualquer outro campo que você viu, como 'no_csrftoken': '1'
        }
        
        print("  - Enviando credenciais e token para o servidor...")
        resposta_post = session.post(LOGIN_URL, data=payload)
        
        if "Desconectar" in resposta_post.text or "Logout" in resposta_post.text:
            print("Sucesso! Login realizado.")
            return True
        else:
            print("Falha no login. Verifique as credenciais, URL e payload.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão durante o login: {e}")
        return False

if __name__: "__main__"
    print(f"---Vigia do GLPI iniciando em {date.time.now().strftime('%d/%m/%Y %H%M%S')}---")
    sessãp_http = requests.session()

    if fazer_login(sessão_http):
    time_sleep(2)
    total_chamados=buscar_dados_da_pagina(sessão_http)

    if total_chamados is not None:
        if total_chamados > 20:
            print("\n[Alert!]O número de chamados ultrapassou o limite de 20!")
        else:
            print(f"\n[Status OK]total de chamados {total_chamados}dentro do limite.")
        print("-----Vigia finalizado----")




