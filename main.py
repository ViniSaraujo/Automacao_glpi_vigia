import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

DB_HOST ="slm-sites-read-cluster.cluster-ro-c0appmybhqbr.us-east-1.rds.amazonaws.com"
DB_NAME ="slmglpi"#aqui o nome do banco glpi
DB_USER ="infra_monitor" #- lçeitura usuario
DB_PASS ="z%HnGqRg?s%@@+?7gF" #- leitura de senha
# -- CONFIGURAÇÕES DE BANCO DE DADOS
SMTP_SERVER= "smtp.office365.com"
SMTP_PORT = 587
SMTP_USER= "vinicius-araujo99@hotmail.com"
SMTP_PASS = "hjaizjeejcvxiwsh"
REMETENTE= "vinicius-araujo99@hotmail.com"
DESTINATARIO = "viniciussaraujo99@outlook.com"
NOME_GERENTE = "Ricardo"

QUERIES = {
    "pendentes": """
    SELECT COUNT(*) FROM glpi_tickets t
    INNER JOIN glpi_groups_tickets g ON g.tickets_id = t.id AND g.type = 2
    WHERE t.is_deleted = '0' AND t.status = '4' AND g.groups_id IN (74, 75, 76)
    """,

    "novos_hoje": """
        SELECT COUNT() FROM glpi_tickets t
        INNER JOIN glpi_groups_tickets g ON g.tickets_id = t.id AND g.type = 2
        WHERE CAST(t.date_creation AS DATE) = CAST(NOW() AS DATE) AND g.groups_id IN (74, 75 ,76)
        """,
    "resolvidos hoje": """
        SELECT COUNT(*) FROM glpi_tickets t
        INNER JOIN glpi_tickets g ON g.tickets_id = t.id AND g.type = 2
        """,

}

def buscar_dados_do_banco(): #-- conecta ao banco de dados, executa queries e retorna dicionario com os results
    print("Buscando dados no banco GLPI")
    dados = {}
    conn = None 
    try: 
        conn =mysql.connector.connecet(
            host= DB_HOST,
            database = DB_NAME,
            user = DB_USER,
            password = DB_PASS
        )
        cursor = conn.cursor()
        for metrica, sql in QUERIES.item():
            cursor.execute(sql)
            resultado = cursor.fetchone()
            dados[metrica] = resultado[0] if resultado else 0
            print("Dados coletados com sucesso")
            return dados
    except mysql.connector.Error as err:
        print(f"ERRO ao buscar dados: {err}!")
        return None # Retorna None em caso de falha
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def enviar_email(dados): """onde monta e envia o e-mail com dados coletados""" 
print("Montando e enviando o e-mail..")

    #monta a mensagem
data_hoje= datetime.now() . strftime('%d/%m/%y')
assunto = f"Relatório diário de Chamados - Infraestrutura - {data_hoje}"

corpo_html = f"""
    <html>
    <head></head>
    <body>
        <p>Bom dia, {NOME_GERENTE}.</p>
        <p>Segue o resumo dos chamados da equipe de Infra até o momento:</p>
        <ul>
            <li><b>Chamados Pendentes:</b> {dados['pendentes']}</li>
            <li><b>Novos chamados hoje:</b> {dados['novos_hoje']}</li>
            <li><b>Chamados resolvidos hoje:</b> {dados['resolvidos_hoje']}</li>
        </ul>
        <p>     
            Para uma visão completa com gráficos detalhados , acesse o dashboard completo no Grafana:<b>
            <a heref = "http://link.para.seu.dashboard/grafana">Dashboard de Chamados GLPI</a>
        </p>
        <p>Atenciosamente,</p>
        <p><i>(este e-mail foi enviado por um assistente automático)</i></p>
    </body> 
    </html>
    """

    #onde configura o e-mail
msg = MIMEMultipart()
msg['From'] = REMETENTE
msg['To']= DESTINATARIO
msg['Subject']= assunto
msg.attach(MIMEText(corpo_html, 'html'))

# onde o envio
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls() #onde ativa a segurança
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(REMETENTE, DESTINATARIO, msg.as_string())
    server.quit()
    print("E-mail enviado com sucesso")
except Exception as e:
    print(f"ERRO ao enviar e-mail: {e}")

# -- Parte principal para execução

if __name__ =="__main__":
    print("iniciando o assistente de relatório ...")
    dados_coletados = buscar_dados_do_banco()

    if dados_coletados is not None:
        enviar_email(dados_coletados)
    else:
        print("O programa não continuou devido algum erro na coleta de dados")

    print("Processo finalizado")
        