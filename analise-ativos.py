# ==============================
# Projeto DIO - Análise de Ativo Financeiro
# ==============================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ------------------------------
# Função para ler e validar data
# Entrada do usuário: DDMMAAAA (apenas números)
# Saída: YYYY-MM-DD (formato aceito pelo yfinance)
# ------------------------------
def ler_data(mensagem):
    while True:
        entrada = input(mensagem).strip()

        # valida tamanho e se são números
        if len(entrada) != 8 or not entrada.isdigit():
            print("❌ Digite a data com 8 números no formato DDMMAAAA. Ex: 25022025")
            continue

        dia = entrada[0:2]
        mes = entrada[2:4]
        ano = entrada[4:8]

        try:
            data_obj = datetime.strptime(f"{dia}-{mes}-{ano}", "%d-%m-%Y")

            if data_obj > datetime.now():
                print("❌ A data não pode estar no futuro.")
                continue

            # retorna no formato que a API entende
            return data_obj.strftime("%Y-%m-%d")

        except ValueError:
            print("❌ Data inválida no calendário. Tente novamente.")


# ------------------------------
# Definição dos ativos
# ------------------------------
ativos = ["PETR4.SA", "BBDC4.SA"]

# ------------------------------
# Entrada de datas validada
# ------------------------------
start = ler_data("Digite a data de início (DDMMAAAA): ")
end = ler_data("Digite a data de término (DDMMAAAA): ")

# ------------------------------
# Download dos dados históricos
# ------------------------------
dados = yf.download(ativos, start=start, end=end)

# verifica se veio dado
if dados.empty:
    print("⚠ Nenhum dado retornado. Verifique o período ou os ativos.")
    exit()

print(dados.head())

# ------------------------------
# Cálculo simples de análise
# ------------------------------
media_petr = dados["Close"]["PETR4.SA"].mean()
media_bbdc = dados["Close"]["BBDC4.SA"].mean()

print(f"Média de fechamento PETR4: {media_petr:.2f}")
print(f"Média de fechamento BBDC4: {media_bbdc:.2f}")