# ==============================
# Dashboard de Investimentos v2
# Layout profissional + gráfico otimizado
# Vinícius Tavares Rocha
# ==============================

import tkinter as tk
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

# ==============================
# CONFIGURAÇÃO DE CORES
# ==============================
BG = "#0f1115"
CARD = "#08080a"
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
# FUNÇÃO DATA COM VALIDAÇÃO REAL
# ==============================
def formatar_data(valor):
    if len(valor) != 8 or not valor.isdigit():
        return None
    try:
        data = datetime.strptime(valor, "%d%m%Y")
        if data > datetime.now():
            return None
        return data.strftime("%Y-%m-%d")
    except ValueError:
        return None

# ==============================
# FUNÇÃO GERAR GRÁFICO (CORRIGIDA)
# ==============================
def gerar_grafico():

    for widget in frame_grafico.winfo_children():
        widget.destroy()

    start = formatar_data(entry_inicio.get())
    end = formatar_data(entry_fim.get())

    if not start or not end:
        erro = tk.Label(frame_grafico, text="Data inválida. Use DDMMAAAA real.", fg="#FF5252", bg=CARD)
        erro.pack(pady=20)
        return

    if start >= end:
        erro = tk.Label(frame_grafico, text="Data final deve ser maior que a inicial.", fg="#FF5252", bg=CARD)
        erro.pack(pady=20)
        return

    dados = yf.download(ativos, start=start, end=end)

    if dados.empty:
        erro = tk.Label(frame_grafico, text="Nenhum dado retornado.", fg="#FF5252", bg=CARD)
        erro.pack(pady=20)
        return

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
                color=CORES_ATIVOS[i % len(CORES_ATIVOS)],
                label=ativo.replace(".SA", "")
            )
        except:
            pass

    ax.set_title("Evolução dos Ativos", color=TXT, fontsize=14, fontweight="bold")
    ax.set_ylabel("Preço (R$)", color=TXT)

    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda x, _: f"R$ {x:,.0f}")
    )

    leg = ax.legend(frameon=False, ncol=2, fontsize=9)
    for text in leg.get_texts():
        text.set_color("#FFFFFF")

    ax.tick_params(axis="x", colors="#FFFFFF")
    ax.tick_params(axis="y", colors="#FFFFFF")

    for spine in ax.spines.values():
        spine.set_color("#444")

    fig.tight_layout(pad=2)
    fig.subplots_adjust(bottom=0.20)

    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ==============================
# FUNÇÃO CDB (100% FUNCIONAL)
# ==============================
def simular_cdb():
    try:
        valor = float(entry_valor.get())
        percentual = float(entry_cdi.get())
        dias = int(entry_dias.get())

        if valor <= 0 or percentual <= 0 or dias <= 0:
            raise ValueError

        taxa_cdi = 0.105
        taxa = taxa_cdi * (percentual / 100)

        final = valor * (1 + taxa) ** (dias / 365)
        rendimento = final - valor

        resultado_cdb.config(
            text=f"Valor final: R$ {final:,.2f} | Lucro: R$ {rendimento:,.2f}",
            fg="#00E676"
        )

    except:
        resultado_cdb.config(
            text="Preencha os campos com números válidos",
            fg="#FF5252"
        )

# ==============================
# REMOVE TEXTO PADRÃO AO CLICAR
# ==============================
def limpar_placeholder(entry, texto):
    if entry.get() == texto:
        entry.delete(0, tk.END)

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
entry_valor.insert(0, "Valor")
entry_valor.bind("<FocusIn>", lambda e: limpar_placeholder(entry_valor, "Valor"))
entry_valor.pack(side="left", padx=5)

entry_cdi = tk.Entry(linha_inputs, width=12)
entry_cdi.insert(0, "%CDI")
entry_cdi.bind("<FocusIn>", lambda e: limpar_placeholder(entry_cdi, "%CDI"))
entry_cdi.pack(side="left", padx=5)

entry_dias = tk.Entry(linha_inputs, width=12)
entry_dias.insert(0, "Dias")
entry_dias.bind("<FocusIn>", lambda e: limpar_placeholder(entry_dias, "Dias"))
entry_dias.pack(side="left", padx=5)

tk.Button(linha_inputs, text="Simular", bg=BTN, fg=TXT, command=simular_cdb).pack(side="left", padx=10)

resultado_cdb = tk.Label(frame_cdb, text="", bg=CARD, fg="#00E676", font=("Arial", 10))
resultado_cdb.pack(pady=5)

root.mainloop()