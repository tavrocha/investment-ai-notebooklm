# ==============================
# Dashboard de Investimentos v2
# Layout profissional + gráfico otimizado
# Vinícius Tavares Rocha
# ==============================

import tkinter as tk
from tkinter import ttk
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

# ==============================
# CONFIGURAÇÃO DE CORES
# ==============================
BG = "#0f1115"
CARD = "#171a21"
TXT = "#ffffff"
BTN = "#2a2f3a"

CORES_ATIVOS = [
    "#00E5FF", "#FF9100", "#FF1744", "#76FF03", "#D500F9",
    "#FFD600", "#00BFA5", "#FF6D00", "#64DD17", "#2979FF", "#FF4081"
]

ativos = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA",
    "BBAS3.SA", "WEGE3.SA", "SUZB3.SA", "CPFE3.SA",
    "TAEE11.SA", "PRIO3.SA", "MGLU3.SA"
]

# ==============================
# FUNÇÃO DATA
# ==============================
# ==============================
# FUNÇÃO DATA (VALIDAÇÃO REAL)
# ==============================
def formatar_data(valor):
    if len(valor) != 8 or not valor.isdigit():
        return None

    try:
        data = datetime.strptime(valor, "%d%m%Y")

        # bloqueia datas futuras
        if data > datetime.now():
            return None

        return data.strftime("%Y-%m-%d")

    except ValueError:
        # pega datas inexistentes tipo 31/02
        return None

# ==============================
# FUNÇÃO GERAR GRÁFICO
# ==============================
def gerar_grafico():
    for widget in frame_grafico.winfo_children():
        widget.destroy()

    start = formatar_data(entry_inicio.get())
    end = formatar_data(entry_fim.get())
    if start >= end:
        erro = tk.Label(  
            frame_grafico,
            text="Data final deve ser maior que a data inicial.",
            fg="#FF5252",
            bg=CARD
            )
        erro.pack(pady=20)
        return

    if not start or not end:
        erro = tk.Label(frame_grafico, text="Data inválida. Use DDMMAAAA real.", fg="#FF5252", bg=CARD)
        erro.pack(pady=20)
        return

    dados = yf.download(ativos, start=start, end=end)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, ativo in enumerate(ativos):
        try:
            serie = dados["Close"][ativo].dropna()
            ax.plot(
                serie.index,
                serie.values,
                linewidth=3,
                color=CORES_ATIVOS[i],
                label=ativo.replace(".SA", "")
            )
        except:
            pass

    ax.set_title("Evolução dos Ativos", color=TXT, fontsize=14, fontweight="bold")
    ax.set_ylabel("Preço (R$)", color=TXT)

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"R$ {x:,.0f}")
    )

    ax.tick_params(colors=TXT)
    ax.legend(frameon=False, ncol=2, fontsize=8)

    for spine in ax.spines.values():
        spine.set_color("#444")

    fig.tight_layout(pad=2)
    fig.subplots_adjust(bottom=0.20)

    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ==============================
# FUNÇÃO CDB
# ==============================
def simular_cdb():
    texto_valor = entry_valor.get().strip()
    texto_cdi = entry_cdi.get().strip()
    texto_dias = entry_dias.get().strip()

    try:
        valor = float(texto_valor)
        percentual = float(texto_cdi)
        dias = int(texto_dias)

        if valor <= 0 or percentual <= 0 or dias <= 0:
            raise ValueError

        taxa_cdi = 0.105
        taxa = taxa_cdi * (percentual / 100)

        final = valor * (1 + taxa) ** (dias / 365)
        rendimento = final - valor

        resultado_cdb.config(
            text=f"Valor final: R$ {final:.2f} | Lucro: R$ {rendimento:.2f}",
            fg="#00E676"
        )

    except:
        resultado_cdb.config(
            text="Digite valores numéricos válidos",
            fg="#FF5252"
        )

# ==============================
# JANELA PRINCIPAL
# ==============================
root = tk.Tk()
root.title("Dashboard de Investimentos")
root.geometry("1100x650")
root.configure(bg=BG)

# ==============================
# TOPO
# ==============================
frame_topo = tk.Frame(root, bg=BG)
frame_topo.pack(fill="x", pady=10)

tk.Label(frame_topo, text="Data início (DDMMAAAA)", bg=BG, fg=TXT).pack(side="left", padx=5)
entry_inicio = tk.Entry(frame_topo, width=12)
entry_inicio.pack(side="left")

tk.Label(frame_topo, text="Data fim (DDMMAAAA)", bg=BG, fg=TXT).pack(side="left", padx=5)
entry_fim = tk.Entry(frame_topo, width=12)
entry_fim.pack(side="left")

tk.Button(frame_topo, text="Gerar Gráfico", bg=BTN, fg=TXT, command=gerar_grafico).pack(side="left", padx=10)

# ==============================
# ÁREA DO GRÁFICO
# ==============================
frame_grafico = tk.Frame(root, bg=CARD)
frame_grafico.pack(fill="both", expand=True, padx=15, pady=(5, 0))

# ==============================
# CARD CDB
# ==============================
frame_cdb = tk.Frame(root, bg=CARD)
frame_cdb.pack(fill="x", padx=15, pady=15)

tk.Label(frame_cdb, text="Simulador de CDB", bg=CARD, fg=TXT, font=("Arial", 11, "bold")).pack(pady=5)

linha_inputs = tk.Frame(frame_cdb, bg=CARD)
linha_inputs.pack()

entry_valor = tk.Entry(linha_inputs, width=12)
entry_valor.insert(0, "Valor R$")
entry_valor.pack(side="left", padx=5)

entry_cdi = tk.Entry(linha_inputs, width=12)
entry_cdi.insert(0, "% CDI")
entry_cdi.pack(side="left", padx=5)

entry_dias = tk.Entry(linha_inputs, width=12)
entry_dias.insert(0, "Dias")
entry_dias.pack(side="left", padx=5)

tk.Button(linha_inputs, text="Simular", bg=BTN, fg=TXT, command=simular_cdb).pack(side="left", padx=10)

resultado_cdb = tk.Label(frame_cdb, text="", bg=CARD, fg="#00E676", font=("Arial", 10))
resultado_cdb.pack(pady=5)

root.mainloop()