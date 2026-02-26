# ==============================
# Dashboard de Investimentos v3
# Seleção de ativos + adição dinâmica
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
BG      = "#0f1115"
CARD    = "#08080a"
TXT     = "#ffffff"
BTN     = "#2a2f3a"
ACCENT  = "#00E5FF"
CDB_BG  = "#0d1f2d"

CORES_ATIVOS = [
    "#00E5FF", "#FF9100", "#FF1744", "#76FF03", "#D500F9",
    "#FFD600", "#00BFA5", "#FF6D00", "#64DD17", "#2979FF",
    "#FF4081", "#F50057", "#69F0AE", "#EEFF41", "#FF6E40",
    "#40C4FF", "#B2FF59", "#EA80FC", "#FF80AB", "#CCFF90",
]

# Ativos padrão (lista fixa conhecida)
ATIVOS_PADRAO = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA",
    "BBAS3.SA", "WEGE3.SA", "SUZB3.SA", "CPFE3.SA",
    "TAEE11.SA", "PRIO3.SA", "MGLU3.SA",
]

# ==============================
# ESTADO DOS ATIVOS
# ==============================
ativos_vars = {}   # ticker -> BooleanVar
ativos_ordem = []  # mantém ordem de inserção

# ==============================
# HELPERS
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

def limpar_placeholder(entry, texto):
    if entry.get() == texto:
        entry.delete(0, tk.END)

def nome_exibicao(ticker):
    return ticker.replace(".SA", "").upper()

# ==============================
# ADICIONAR ATIVO DINAMICAMENTE
# ==============================
def adicionar_ativo():
    raw = entry_novo_ativo.get().strip().upper()
    if not raw or raw == "EX: EGIE3":
        return

    ticker = raw if raw.endswith(".SA") else raw + ".SA"

    if ticker in ativos_vars:
        label_status.config(text=f"{nome_exibicao(ticker)} já está na lista.", fg="#FFD600")
        return

    var = tk.BooleanVar(value=True)
    ativos_vars[ticker] = var
    ativos_ordem.append(ticker)
    _criar_checkbox(ticker, var)

    entry_novo_ativo.delete(0, tk.END)
    label_status.config(text=f"{nome_exibicao(ticker)} adicionado ✔", fg="#00E676")

def _criar_checkbox(ticker, var):
    idx = ativos_ordem.index(ticker)
    cor = CORES_ATIVOS[idx % len(CORES_ATIVOS)]

    row_frame = tk.Frame(frame_lista_ativos, bg=CARD)
    row_frame.pack(anchor="w", padx=6, pady=1)

    # quadradinho colorido = cor da linha no gráfico
    c = tk.Canvas(row_frame, width=12, height=12, bg=CARD, highlightthickness=0)
    c.create_rectangle(0, 0, 12, 12, fill=cor, outline="")
    c.pack(side="left", padx=(0, 4))

    cb = tk.Checkbutton(
        row_frame,
        text=nome_exibicao(ticker),
        variable=var,
        bg=CARD, fg=TXT,
        selectcolor="#1a2a3a",
        activebackground=CARD,
        activeforeground=TXT,
        font=("Arial", 9),
        cursor="hand2"
    )
    cb.pack(side="left")

# ==============================
# SELECIONAR / DESMARCAR TODOS
# ==============================
def selecionar_todos():
    for var in ativos_vars.values():
        var.set(True)

def desmarcar_todos():
    for var in ativos_vars.values():
        var.set(False)

# ==============================
# GERAR GRÁFICO
# ==============================
def gerar_grafico():
    for widget in frame_grafico.winfo_children():
        widget.destroy()

    start = formatar_data(entry_inicio.get())
    end   = formatar_data(entry_fim.get())

    if not start or not end:
        tk.Label(frame_grafico, text="Data inválida. Use DDMMAAAA real.",
                 fg="#FF5252", bg=CARD).pack(pady=20)
        return

    if start >= end:
        tk.Label(frame_grafico, text="Data final deve ser maior que a inicial.",
                 fg="#FF5252", bg=CARD).pack(pady=20)
        return

    selecionados = [t for t in ativos_ordem if ativos_vars[t].get()]

    if not selecionados:
        tk.Label(frame_grafico, text="Selecione ao menos um ativo.",
                 fg="#FFD600", bg=CARD).pack(pady=20)
        return

    dados = yf.download(selecionados, start=start, end=end, auto_adjust=True)

    if dados.empty:
        tk.Label(frame_grafico, text="Nenhum dado retornado.",
                 fg="#FF5252", bg=CARD).pack(pady=20)
        return

    fig = plt.figure(figsize=(11, 4.5))
    fig.patch.set_facecolor(BG)

    ax = fig.add_axes([0.07, 0.15, 0.68, 0.75])
    ax.set_facecolor(BG)

    ax_leg = fig.add_axes([0.77, 0.05, 0.22, 0.90])
    ax_leg.set_facecolor("#0d1a24")
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])
    for spine in ax_leg.spines.values():
        spine.set_edgecolor(ACCENT)
        spine.set_linewidth(1.2)

    linhas, nomes = [], []

    for ativo in selecionados:
        cor = CORES_ATIVOS[ativos_ordem.index(ativo) % len(CORES_ATIVOS)]
        try:
            if len(selecionados) == 1:
                serie = dados["Close"].dropna()
            else:
                serie = dados["Close"][ativo].dropna()

            linha, = ax.plot(
                serie.index, serie.values,
                linewidth=2.5, color=cor,
                label=nome_exibicao(ativo)
            )
            linhas.append(linha)
            nomes.append(nome_exibicao(ativo))
        except Exception:
            pass

    ax.set_title("Evolução dos Ativos", color=TXT, fontsize=13, fontweight="bold")
    ax.set_ylabel("Preço (R$)", color=TXT)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
    ax.tick_params(axis="x", colors="#FFFFFF")
    ax.tick_params(axis="y", colors="#FFFFFF")
    for spine in ax.spines.values():
        spine.set_color("#444")

    ax_leg.text(0.5, 0.97, "Ativos", transform=ax_leg.transAxes,
                color=ACCENT, fontsize=10, fontweight="bold", ha="center", va="top")

    leg = ax_leg.legend(
        handles=linhas, labels=nomes,
        loc="upper center", bbox_to_anchor=(0.5, 0.90),
        frameon=False, ncol=1, fontsize=9,
        handlelength=1.5, handleheight=0.8, labelspacing=0.5
    )
    for text in leg.get_texts():
        text.set_color("#FFFFFF")

    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ==============================
# SIMULADOR CDB
# ==============================
def simular_cdb():
    try:
        valor      = float(entry_valor.get())
        percentual = float(entry_cdi.get())
        dias       = int(entry_dias.get())

        if valor <= 0 or percentual <= 0 or dias <= 0:
            raise ValueError

        taxa_cdi = 0.105
        taxa     = taxa_cdi * (percentual / 100)
        final    = valor * (1 + taxa) ** (dias / 365)
        lucro    = final - valor

        resultado_cdb.config(
            text=f"💰  Valor final: R$ {final:,.2f}   |   Lucro: R$ {lucro:,.2f}",
            fg="#00E676"
        )
    except Exception:
        resultado_cdb.config(
            text="⚠  Preencha os campos com números válidos",
            fg="#FF5252"
        )

# ==============================
# JANELA PRINCIPAL
# ==============================
root = tk.Tk()
root.title("Dashboard de Investimentos")
root.geometry("1200x700")
root.configure(bg=BG)

frame_main = tk.Frame(root, bg=BG)
frame_main.pack(fill="both", expand=True)

# ==============================
# SIDEBAR (esquerda)
# ==============================
frame_sidebar = tk.Frame(frame_main, bg=CARD, width=185)
frame_sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)
frame_sidebar.pack_propagate(False)

tk.Label(frame_sidebar, text="📋  Ativos", bg=CARD, fg=ACCENT,
         font=("Arial", 11, "bold")).pack(pady=(10, 4))

# Botões Todos / Nenhum
frame_btns_sel = tk.Frame(frame_sidebar, bg=CARD)
frame_btns_sel.pack(fill="x", padx=6, pady=(0, 6))

tk.Button(frame_btns_sel, text="Todos", bg=BTN, fg=TXT,
          font=("Arial", 8), relief="flat", cursor="hand2",
          command=selecionar_todos).pack(side="left", expand=True, fill="x", padx=(0, 2))

tk.Button(frame_btns_sel, text="Nenhum", bg=BTN, fg=TXT,
          font=("Arial", 8), relief="flat", cursor="hand2",
          command=desmarcar_todos).pack(side="left", expand=True, fill="x")

# Lista de checkboxes com scroll
frame_scroll_container = tk.Frame(frame_sidebar, bg=CARD)
frame_scroll_container.pack(fill="both", expand=True, padx=4)

canvas_scroll = tk.Canvas(frame_scroll_container, bg=CARD, highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_scroll_container, orient="vertical",
                          command=canvas_scroll.yview)
canvas_scroll.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas_scroll.pack(side="left", fill="both", expand=True)

frame_lista_ativos = tk.Frame(canvas_scroll, bg=CARD)
canvas_scroll.create_window((0, 0), window=frame_lista_ativos, anchor="nw")

frame_lista_ativos.bind(
    "<Configure>",
    lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
)
canvas_scroll.bind_all(
    "<MouseWheel>",
    lambda e: canvas_scroll.yview_scroll(int(-1 * (e.delta / 120)), "units")
)

# Separador
tk.Frame(frame_sidebar, bg="#1a2a3a", height=1).pack(fill="x", padx=6, pady=6)

# Campo adicionar novo ativo
tk.Label(frame_sidebar, text="Adicionar ativo:", bg=CARD, fg="#aaaaaa",
         font=("Arial", 8)).pack(padx=6, anchor="w")

frame_add = tk.Frame(frame_sidebar, bg=CARD)
frame_add.pack(fill="x", padx=6, pady=(2, 0))

entry_novo_ativo = tk.Entry(frame_add, bg=BTN, fg="#888888", insertbackground=TXT,
                             font=("Arial", 9), width=9)
entry_novo_ativo.insert(0, "ex: EGIE3")
entry_novo_ativo.bind("<FocusIn>",  lambda e: limpar_placeholder(entry_novo_ativo, "ex: EGIE3"))
entry_novo_ativo.bind("<FocusOut>", lambda e: (
    entry_novo_ativo.insert(0, "ex: EGIE3") if entry_novo_ativo.get() == "" else None
))
entry_novo_ativo.bind("<Return>", lambda e: adicionar_ativo())
entry_novo_ativo.pack(side="left", fill="x", expand=True)

tk.Button(frame_add, text="+", bg=ACCENT, fg="#000000",
          font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
          width=2, command=adicionar_ativo).pack(side="left", padx=(4, 0))

label_status = tk.Label(frame_sidebar, text="", bg=CARD, fg="#00E676",
                         font=("Arial", 8), wraplength=160)
label_status.pack(padx=6, pady=4)

# ==============================
# CONTEÚDO DIREITO
# ==============================
frame_conteudo = tk.Frame(frame_main, bg=BG)
frame_conteudo.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# -- TOPO --
frame_topo = tk.Frame(frame_conteudo, bg=BG)
frame_topo.pack(fill="x", pady=(0, 6))

tk.Label(frame_topo, text="Data início (DDMMAAAA)", bg=BG, fg=TXT,
         font=("Arial", 9)).pack(side="left", padx=(0, 4))
entry_inicio = tk.Entry(frame_topo, width=12, bg=BTN, fg=TXT, insertbackground=TXT)
entry_inicio.pack(side="left")

tk.Label(frame_topo, text="Data fim (DDMMAAAA)", bg=BG, fg=TXT,
         font=("Arial", 9)).pack(side="left", padx=(12, 4))
entry_fim = tk.Entry(frame_topo, width=12, bg=BTN, fg=TXT, insertbackground=TXT)
entry_fim.pack(side="left")

tk.Button(frame_topo, text="  Gerar Gráfico  ", bg=ACCENT, fg="#000000",
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=gerar_grafico).pack(side="left", padx=14)

# -- GRÁFICO --
frame_grafico = tk.Frame(frame_conteudo, bg=CARD)
frame_grafico.pack(fill="both", expand=True)

# -- CARD CDB --
frame_cdb_outer = tk.Frame(frame_conteudo, bg=ACCENT)
frame_cdb_outer.pack(fill="x", pady=(10, 0))

frame_cdb = tk.Frame(frame_cdb_outer, bg=CDB_BG)
frame_cdb.pack(fill="both", expand=True, padx=2, pady=2)

cabecalho = tk.Frame(frame_cdb, bg="#0a2235")
cabecalho.pack(fill="x")
tk.Label(cabecalho, text="💵  Simulador de CDB", bg="#0a2235", fg=ACCENT,
         font=("Arial", 11, "bold"), pady=6).pack(side="left", padx=12)

linha_inputs = tk.Frame(frame_cdb, bg=CDB_BG)
linha_inputs.pack(pady=8)

def make_label(parent, text):
    tk.Label(parent, text=text, bg=CDB_BG, fg="#aaaaaa", font=("Arial", 8)).pack()

col1 = tk.Frame(linha_inputs, bg=CDB_BG); col1.pack(side="left", padx=10)
make_label(col1, "Valor (R$)")
entry_valor = tk.Entry(col1, width=13, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_valor.insert(0, "2000")
entry_valor.bind("<FocusIn>", lambda e: limpar_placeholder(entry_valor, "2000"))
entry_valor.pack()

col2 = tk.Frame(linha_inputs, bg=CDB_BG); col2.pack(side="left", padx=10)
make_label(col2, "% do CDI")
entry_cdi = tk.Entry(col2, width=13, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_cdi.insert(0, "110")
entry_cdi.bind("<FocusIn>", lambda e: limpar_placeholder(entry_cdi, "110"))
entry_cdi.pack()

col3 = tk.Frame(linha_inputs, bg=CDB_BG); col3.pack(side="left", padx=10)
make_label(col3, "Dias")
entry_dias = tk.Entry(col3, width=13, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_dias.insert(0, "365")
entry_dias.bind("<FocusIn>", lambda e: limpar_placeholder(entry_dias, "365"))
entry_dias.pack()

col4 = tk.Frame(linha_inputs, bg=CDB_BG); col4.pack(side="left", padx=12)
make_label(col4, " ")
tk.Button(col4, text="  Simular  ", bg=ACCENT, fg="#000000",
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=simular_cdb).pack()

resultado_cdb = tk.Label(frame_cdb, text="", bg=CDB_BG, fg="#00E676",
                          font=("Arial", 11, "bold"), pady=6)
resultado_cdb.pack()

# ==============================
# INICIALIZAR CHECKBOXES PADRÃO
# ==============================
for ticker in ATIVOS_PADRAO:
    var = tk.BooleanVar(value=True)
    ativos_vars[ticker] = var
    ativos_ordem.append(ticker)
    _criar_checkbox(ticker, var)

root.mainloop()