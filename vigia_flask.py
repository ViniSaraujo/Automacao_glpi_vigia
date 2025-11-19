import requests
import webbrowser
from threading import Timer
from bs4 import BeautifulSoup
import time
from datetime import datetime
from flask import Flask, render_template
import configparser

# --- Bloco 2: Configurações ATUALIZADO ---
# --- PREENCHA SUAS INFORMAÇÕES AQUI ---
GLPI_URL_BASE = 'https://chamados.slmandic.edu.br'
URL_FORMULARIO_LOGIN = f'{GLPI_URL_BASE}/glpi/index.php?noAUTO=1'
URL_POST_LOGIN = f'{GLPI_URL_BASE}/glpi/front/login.php' 
GLPI_USER= ""
GLPI_PASSWORD = ""

config= configparser.ConfigParser()
config.read('config.ini')

try:
    GLPI_USER = config['GLPI']['USUARIO']
    GLPI_PASSWORD = config['GLPI']['SENHA']
except KeyError:
    print("Erro: Arquivo 'config.ini' não encontrado ou incompleto.")
    print("Verifique se 'config.ini' existe e tem as seções [GLPI], USUARIO e SENHA.")


# --- NOSSAS 3 URLs DE ALVO (sem o _glpi_csrf_token) ---

# 1. A sua URL original (Pesquisa Salva 613) que mostra o TOTAL
URL_N1 = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=notold&criteria%5B1%5D%5Blink%5D=AND&criteria%5B1%5D%5Bfield%5D=8&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=74&search=Pesquisar&itemtype=Ticket&start=0"""
# 2. A URL "Vigia - Novo" (Status=1)
URL_N2 = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&search=Pesquisar&itemtype=Ticket&savedsearches_id=765&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=notold&criteria%5B1%5D%5Blink%5D=AND&criteria%5B1%5D%5Bfield%5D=8&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=75&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=6&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&reset=reset"""

# 3. A URL "Vigia - Pendente" (Status=4)
URL_N3 = """https://chamados.slmandic.edu.br/glpi/front/ticket.php?is_deleted=0&as_map=0&search=Pesquisar&itemtype=Ticket&savedsearches_id=778&criteria%5B0%5D%5Blink%5D=AND&criteria%5B0%5D%5Bfield%5D=12&criteria%5B0%5D%5Bsearchtype%5D=equals&criteria%5B0%5D%5Bvalue%5D=notold&criteria%5B1%5D%5Blink%5D=AND&criteria%5B1%5D%5Bfield%5D=8&criteria%5B1%5D%5Bsearchtype%5D=equals&criteria%5B1%5D%5Bvalue%5D=76&criteria%5B2%5D%5Blink%5D=AND&criteria%5B2%5D%5Bfield%5D=6&criteria%5B2%5D%5Bsearchtype%5D=equals&criteria%5B2%5D%5Bvalue%5D=0&reset=reset"""

INDICE_COLUNA_DATA = 9
def fazer_login(session):
        
        print("Iniciando missão: Fazer Login...")
        try:
             resposta_get = session.get(URL_FORMULARIO_LOGIN, timeout=10)
             soup= BeautifulSoup(resposta_get.text, 'html.parser')

             campo_usuario = soup.find('input', {'id': 'login_name'})
             nome_campo_usuario = campo_usuario['name'] if campo_usuario else 'login_name'
             campo_senha = soup.find('input', {'id': 'login_password'})
             nome_campo_senha = campo_senha['name'] if campo_senha else 'login_password'
             token_input = soup.find('input', {'name': '_glpi_csrf_token'})
             csrf_token = token_input['value'] if token_input else None

             payload = {
                  nome_campo_usuario: GLPI_USER,
                  nome_campo_senha: GLPI_PASSWORD,
                  '_glpi_csrf_token': csrf_token,
                  'submit': 'Enviar',
                  'noAUTO': '1'
             }

             resposta_post = session.post(URL_POST_LOGIN, data=payload, timeout=10)

             if "Sair" in resposta_post.text:
                  print("Sucesso! Login realizado.")
                  return True
             else:
                  print("Falha no login.")
                  return False
        except Exception as e:
             print(f"Erro no login: {e}")
             return False
        
def calcular_tempo_aberto(texto_data):
     
     try:
          data_chamado = datetime.strptime(texto_data.strip(), "%d-%m-%Y %H:%M")
          agora = datetime.now()
          diference = agora - data_chamado

          dias = diference.days
          horas = diference.seconds 

          return f"{dias}d {horas}h", dias
     except Exception as e:
          print(f"- Erro ao calcular data para '{texto_data}': {e}...")
          return "--", 0        

def analisar_fila(session, url, nome_fila):
    """Busca total e dados do mais antigo."""
    print(f"  - Analisando fila '{nome_fila}'...")
    info = {
        'total': 0, 
        'mais_antigo_tempo': '--', 
        'mais_antigo_dias': 0,
        'tem_chamados': False
    }
    
    try:
        resposta = session.get(url, timeout=15)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # 1. PEGAR O TOTAL (Lógica antiga)
        elemento_total = soup.find('td', class_='tab_bg_2 b')
        if elemento_total:
            texto = elemento_total.text.strip() 
            total = int(texto.split()[-1])
            info['total'] = total
            if total > 0:
                info['tem_chamados'] = True
        
        # 2. PEGAR O MAIS ANTIGO (Nova Lógica)
        if info['tem_chamados']:
            # Encontra a tabela principal de tickets (geralmente tem classe 'tab_cadre_fixehov')
            tabela = soup.find('table', class_='tab_cadre_fixehov')
            
            if tabela:
                # Pega todas as linhas (tr), ignorando o cabeçalho
                linhas = tabela.find_all('tr')
                # A linha 0 geralmente é cabeçalho. Vamos tentar a linha 1 (o primeiro chamado).
                # (Dependendo do GLPI, pode ter mais linhas de cabeçalho, talvez precise ser linhas[2])
                primeiro_chamado = None
                
                # Procura a primeira linha que tenha dados (classe tab_bg_...)
                for linha in linhas:
                    if 'tab_bg_' in str(linha.get('class', [])):
                        primeiro_chamado = linha
                        break
                
                if primeiro_chamado:
                    colunas = primeiro_chamado.find_all('td')
                    # Pega a coluna da data
                    if len(colunas) > INDICE_COLUNA_DATA:
                        data_texto = colunas[INDICE_COLUNA_DATA].text.strip()
                        print(f"    > Data encontrada na col {INDICE_COLUNA_DATA}: {data_texto}")
                        
                        tempo_texto, dias = calcular_tempo_aberto(data_texto)
                        info['mais_antigo_tempo'] = tempo_texto
                        info['mais_antigo_dias'] = dias
                    else:
                        print(f"    > Erro: Tabela tem menos colunas ({len(colunas)}) que o índice pedido ({INDICE_COLUNA_DATA}).")

        return info

    except Exception as e:
        print(f"Erro ao analisar {nome_fila}: {e}")
        return info

# --- Bloco 4: Flask ---
app = Flask(__name__)

@app.route('/')
def mostrar_status():
    sessao = requests.Session()
    dados = {}
    msg = "Iniciando..."
    erro = None

    if fazer_login(sessao):
        msg = "Login OK. Analisando filas..."
        
        dados['n1'] = analisar_fila(sessao, URL_N1, "N1")
        dados['n2'] = analisar_fila(sessao, URL_N2, "N2")
        dados['n3'] = analisar_fila(sessao, URL_N3, "N3")
        
        # Calcula total geral
        dados['total_geral'] = dados['n1']['total'] + dados['n2']['total'] + dados['n3']['total']
        
        msg = "Análise completa!"
    else:
        msg = "Falha no Login"
        erro = "Verifique credenciais."

    contexto = {
        'dados': dados,
        'mensagem': msg,
        'erro_msg': erro,
        'agora': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return render_template('vigia.html', **contexto)

def abrir_navegador():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Timer(1.5, abrir_navegador).start()
    app.run(host='127.0.0.1', port=5000, debug=True)