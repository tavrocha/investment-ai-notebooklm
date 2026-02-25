# ==============================
# Projeto DIO - Análise de Ativos Financeiros Brasileiros
# ==============================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# ------------------------------
# Função para ler e validar data
# Entrada do usuário: DDMMAAAA
# Saída: YYYY-MM-DD
# ------------------------------
def ler_data(mensagem):
    while True:
        entrada = input(mensagem).strip()

        if len(entrada) != 8 or not entrada.isdigit():
            print("❌ Digite a data com 8 números no formato DDMMAAAA")
            continue

        dia = entrada[0:2]
        mes = entrada[2:4]
        ano = entrada[4:8]

        try:
            data_obj = datetime.strptime(f"{dia}-{mes}-{ano}", "%d-%m-%Y")

            if data_obj > datetime.now():
                print("❌ A data não pode estar no futuro.")
                continue

            return data_obj.strftime("%Y-%m-%d")

        except ValueError:
            print("❌ Data inválida no calendário.")


# ------------------------------
# Principais ativos do mercado brasileiro
# ------------------------------
ativos = [
    "PETR4.SA",  # petróleo
    "VALE3.SA",  # mineração
    "ITUB4.SA",  # banco
    "BBDC4.SA",  # banco
    "BBAS3.SA",  # banco
    "WEGE3.SA",  # indústria
    "SUZB3.SA",  # papel e celulose
    "CPFE3.SA",  # CPFL Energia
    "TAEE11.SA", # energia
    "PRIO3.SA",  # petróleo
    "MGLU3.SA"   # varejo
]

# ------------------------------
# Entrada de datas
# ------------------------------
start = ler_data("Digite a data de início (DDMMAAAA): ")
end = ler_data("Digite a data de término (DDMMAAAA): ")

# ------------------------------
# Download dos dados históricos
# ------------------------------
dados = yf.download(ativos, start=start, end=end)

if dados.empty:
    print("⚠ Nenhum dado retornado.")
    exit()
    
# ------------------------------
# Visualização gráfica dos ativos
# ------------------------------

plt.figure(figsize=(12, 6))

for ativo in ativos:
    try:
        plt.plot(dados["Close"][ativo], label=ativo)
    except:
        print(f"⚠ Não foi possível plotar {ativo}")

plt.title("Evolução do preço de fechamento")
plt.xlabel("Data")
plt.ylabel("Preço (R$)")
plt.legend()
plt.grid(True)

plt.show()

# ------------------------------
# Função de análise por ativo
# ------------------------------
def analisar_ativo(df, ticker):
    fechamento = df["Close"][ticker].dropna()

    preco_medio = fechamento.mean()
    preco_inicial = fechamento.iloc[0]
    preco_final = fechamento.iloc[-1]
    retorno = ((preco_final - preco_inicial) / preco_inicial) * 100
    volatilidade = fechamento.pct_change().std() * 100
    maximo = fechamento.max()
    minimo = fechamento.min()

    return {
        "Ativo": ticker.replace(".SA", ""),
        "Preço Médio": preco_medio,
        "Retorno %": retorno,
        "Volatilidade %": volatilidade,
        "Máximo": maximo,
        "Mínimo": minimo
    }


# ------------------------------
# Construção da tabela comparativa
# ------------------------------
analises = []

for ativo in ativos:
    try:
        resultado = analisar_ativo(dados, ativo)
        analises.append(resultado)
    except:
        print(f"⚠ Falha ao analisar {ativo}")

tabela = pd.DataFrame(analises)

# ------------------------------
# Formatação visual da tabela
# ------------------------------
tabela = tabela.sort_values(by="Retorno %", ascending=False)

tabela["Preço Médio"] = tabela["Preço Médio"].round(2)
tabela["Retorno %"] = tabela["Retorno %"].round(2)
tabela["Volatilidade %"] = tabela["Volatilidade %"].round(2)
tabela["Máximo"] = tabela["Máximo"].round(2)
tabela["Mínimo"] = tabela["Mínimo"].round(2)

print("\n📊 Ranking de desempenho no período:\n")
print(tabela.to_string(index=False))

# ------------------------------
# Simulação de investimento em CDB
# ------------------------------

print("\n💰 Simulador de CDB")

try:
    valor_cdb = float(input("Digite o valor investido (R$): "))
    percentual_cdi = float(input("Percentual do CDI (ex: 110 para 110%): "))
    dias = int(input("Período do investimento em dias: "))

    # taxa média anual do CDI (pode virar variável dinâmica no futuro)
    taxa_cdi_anual = 0.105  # 10.5% ao ano (exemplo realista)

    taxa_anual_cdb = taxa_cdi_anual * (percentual_cdi / 100)

    valor_final = valor_cdb * (1 + taxa_anual_cdb) ** (dias / 365)
    rendimento = valor_final - valor_cdb

    print("\n📈 Resultado da simulação:")
    print(f"Valor inicial: R$ {valor_cdb:.2f}")
    print(f"Valor final estimado: R$ {valor_final:.2f}")
    print(f"Rendimento bruto: R$ {rendimento:.2f}")

except:
    print("⚠ Entrada inválida na simulação do CDB.")