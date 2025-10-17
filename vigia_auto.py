#
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# --- Bloco 2: Configurações ---
GLPI_URL_BASE = 'https://chamados.slmandic.edu.br/glpi'
LOGIN_URL = 'https://chamados.slmandic.edu.br/glpi/index.php?noAUTO=1'


GLPI_USER = "01992005"
GLPI_PASSWORD = "Maequeridas2"

PAGINA_ALVO_URL = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&search=Pesquisar&itemtype=Ticket&savedsearches_id=613&reset=reset&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=1&criteria%5B1%5D%5Blink%5D=OR&criteria%5B1%5D%5Bfield%5D=12&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=4&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=5&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&criteria%5B3%5D%5Blink%5D=AND&criteria%5B3%5D%5Bfield%5D=8&criteria%5B3%5D%5Bsearchtype%5D=equals&criteria%5B3%5D%5Bvalue%5D=0"""

# --- Bloco 3: Funções ---

def fazer_login(session):
    """
    Faz o login em duas etapas: 
    1. Visita a página para pegar os nomes dinâmicos dos campos e o token.
    2. Envia o formulário de login com todos os dados corretos.
    """
    print("Iniciando missão: Fazer Login (com coleta de campos dinâmicos)...")
    
    try:
        print("  - Acessando a página de login para espionar os campos...")
        # A URL de login é a correta para pegar o formulário
        resposta_get = session.get(LOGIN_URL)
        soup = BeautifulSoup(resposta_get.text, 'html.parser')
        
        # Encontra o NOME do campo de usuário procurando pelo seu ID fixo 'login_name'
        campo_usuario = soup.find('input', {'id': 'login_name'})
        nome_campo_usuario = campo_usuario['name'] if campo_usuario else 'login_name'
        
        # Encontra o NOME do campo de senha procurando pelo seu ID fixo 'login_password'
        campo_senha = soup.find('input', {'id': 'login_password'})
        nome_campo_senha = campo_senha['name'] if campo_senha else 'login_password'
        
        # Encontra o token CSRF (esta parte já estava funcionando)
        token_input = soup.find('input', {'name': '_glpi_csrf_token'})
        csrf_token = token_input['value'] if token_input else None
        # =========================================================================
        
        print(f"  - Campo de usuário dinâmico encontrado: {nome_campo_usuario}")
        print(f"  - Campo de senha dinâmico encontrado: {nome_campo_senha}")
        
        # Agora, ao montar o payload, as variáveis 'nome_campo_usuario' e 'nome_campo_senha' já existem!
        payload = {
            nome_campo_usuario: GLPI_USER,
            nome_campo_senha: GLPI_PASSWORD,
            '_glpi_csrf_token': csrf_token,
            'submit': 'Conectar', # Verifique se o valor do seu botão é 'Conectar' ou 'Enviar'
            'noAUTO': '1'
        }
        
        print("  - Enviando credenciais com os nomes de campo corretos...")
        # A URL para o POST é a do action do formulário
        url_post = f"https://chamados.slmandic.edu.br/glpi/front/login.php"
        resposta_post = session.post(url_post, data=payload)
        
        if "Desconectar" in resposta_post.text or "Logout" in resposta_post.text:
            print("Sucesso! Login realizado.")
            return True
        else:
            print("Falha no login. A resposta do servidor não indicou sucesso.")
            return False
            
    except Exception as e:
        print(f"Ocorreu um erro durante o processo de login: {e}")
        return False

def buscar_dados_da_pagina(session):
    """Navega até a página alvo (já logado) e extrai a informação desejada."""
    print("Iniciando missão: Buscar Dados na Página...")
    try:
        resposta = session.get(PAGINA_ALVO_URL, timeout=15)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # 1. Encontra o elemento <td> com a classe "tab_bg_2 b"
        elemento = soup.find('td', class_='tab_bg_2 b')
        
        if elemento:
            # 2. Pega o texto completo. Ex: "De 1 para 7 de 7"
            texto_completo = elemento.text.strip()
            print(f"Texto do elemento encontrado: '{texto_completo}'")
            
            # 3. "Quebra" o texto em uma lista de palavras. Ex: ['De', '1', 'para', '7', 'de', '7']
            palavras = texto_completo.split()
            
            # 4. Pega a última palavra da lista, que é o número total. Ex: '7'
            valor_texto = palavras[-1]
            
            print(f"Número total extraído: '{valor_texto}'")
            # 5. Converte o texto para um número inteiro e o retorna
            return int(valor_texto)
        else:
            print("Elemento com a contagem total não foi encontrado. Verifique a tag e a classe.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao buscar dados: {e}")
        return None
    except (IndexError, ValueError) as e:
        print(f"Erro ao processar o texto do elemento. O formato pode ter mudado. Erro: {e}")
        return None

# --- Bloco 4: Ponto de Partida ---
if __name__ == "__main__":
    print(f"--- Vigia do GLPI iniciando em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ---")
    
    sessao_http = requests.Session()

    if fazer_login(sessao_http):
        time.sleep(2)
        total_chamados = buscar_dados_da_pagina(sessao_http)

        if total_chamados is not None:
            if total_chamados > 20:
                print("\n[ALERTA!] O número de chamados ultrapassou o limite de 20!")
                # Futuramente, aqui entrará a chamada para enviar_alerta_por_email(total_chamados)
            else:
                print(f"\n[Status OK] Total de chamados ({total_chamados}) dentro do limite.")
    
    print("--- Vigia finalizado ---")