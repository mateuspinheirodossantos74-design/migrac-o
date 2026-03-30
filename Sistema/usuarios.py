import mysql.connector
import bcrypt
from datetime import date

# ===============================
# CONFIGURAÇÃO DE CONEXÃO RAILWAY
# ===============================
RAILWAY_HOST = "gondola.proxy.rlwy.net"
RAILWAY_USER = "root"
RAILWAY_PASSWORD = "NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH"
RAILWAY_DB = "railway"
RAILWAY_PORT = 25644

# ===============================
# DADOS DO USUÁRIO
# ===============================
nome = "Mateus Pinheiro"
usuario = "2960007532"
senha = "cd@1200"              # senha em texto
cargo = "Analista"
funcao = "Desenvolvimento"
nivel_acesso = "admin"
data_criacao = date.today()   # pega a data atual automaticamente

# ===============================
# GERAR HASH DA SENHA
# ===============================
senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

# ===============================
# CONECTAR AO BANCO
# ===============================
conn = mysql.connector.connect(
    host=RAILWAY_HOST,
    user=RAILWAY_USER,
    password=RAILWAY_PASSWORD,
    database=RAILWAY_DB,
    port=RAILWAY_PORT
)
cursor = conn.cursor()

# ===============================
# INSERIR USUÁRIO
# ===============================
query = """
INSERT INTO usuarios (nome, usuario, senha, cargo, funcao, nivel_acesso, data_criacao)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
values = (nome, usuario, senha_hash.decode(), cargo, funcao, nivel_acesso, data_criacao)

cursor.execute(query, values)
conn.commit()

print(f"Usuário '{usuario}' criado com sucesso!")

# ===============================
# FECHAR CONEXÃO
# ===============================
cursor.close()
conn.close()
