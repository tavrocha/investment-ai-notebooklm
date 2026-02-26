# ==============================
# Dashboard de Investimentos v3
# Verificação de ativo + máscara de data
# Vinícius Tavares Rocha
# ==============================

import tkinter as tk
from tkinter import ttk
import yfinance as yf
from datetime import datetime
import threading
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

ATIVOS_PADRAO = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA",
    "BBAS3.SA", "WEGE3.SA", "SUZB3.SA", "CPFE3.SA",
    "TAEE11.SA", "PRIO3.SA", "MGLU3.SA",
]

# ==============================
# ESTADO
# ==============================
ativos_vars  = {}
ativos_ordem = []

# ==============================
# MÁSCARA DE DATA — lógica corrigida
# ==============================
class MascaraData:
    """
    Aplica máscara DD/MM/AAAA num Entry do tkinter.
    Funciona extraindo só os dígitos digitados, limitando a 8,
    e remontando a string com as barras nas posições certas.
    Usa um flag para evitar recursão ao setar o valor.
    """
    def __init__(self, entry):
        self.entry    = entry
        self._editing = False
        self.entry.bind("<KeyRelease>", self._aplicar)
        self.entry.bind("<BackSpace>",  self._aplicar)

    def _aplicar(self, event=None):
        if self._editing:
            return
        self._editing = True

        # 1. Pega o conteúdo atual e extrai só dígitos
        texto = self.entry.get()
        digitos = "".join(ch for ch in texto if ch.isdigit())

        # 2. Limita a 8 dígitos
        digitos = digitos[:8]

        # 3. Remonta com barras: DD/MM/AAAA
        resultado = ""
        for i, ch in enumerate(digitos):
            if i == 2 or i == 4:
                resultado += "/"
            resultado += ch

        # 4. Substitui o conteúdo do entry
        self.entry.delete(0, tk.END)
        self.entry.insert(0, resultado)
        self.entry.icursor(tk.END)

        self._editing = False

    def get_data_yf(self):
        """Retorna a data no formato YYYY-MM-DD para o yfinance, ou None se inválida."""
        digitos = "".join(ch for ch in self.entry.get() if ch.isdigit())
        if len(digitos) != 8:
            return None
        try:
            data = datetime.strptime(digitos, "%d%m%Y")
            if data > datetime.now():
                return None
            return data.strftime("%Y-%m-%d")
        except ValueError:
            return None


# ==============================
# HELPERS
# ==============================
def nome_exibicao(ticker):
    return ticker.replace(".SA", "").upper()

def limpar_entry_placeholder(entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(fg=TXT)

def restaurar_placeholder(entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg="#888888")

# ==============================
# VERIFICAÇÃO + ADIÇÃO DE ATIVO
# ==============================
def adicionar_ativo():
    raw = entry_novo_ativo.get().strip().upper()
    if not raw or raw == "EX: EGIE3":
        return

    ticker = raw if raw.endswith(".SA") else raw + ".SA"

    if ticker in ativos_vars:
        label_status.config(text=f"{nome_exibicao(ticker)} já está na lista.", fg="#FFD600")
        return

    btn_add.config(state="disabled", text="...")
    label_status.config(text=f"Verificando {nome_exibicao(ticker)}...", fg="#aaaaaa")

    def verificar():
        valido = False
        try:
            hist = yf.download(ticker, period="5d", auto_adjust=True, progress=False)
            valido = not hist.empty
        except Exception:
            valido = False
        root.after(0, lambda: _pos_verificacao(ticker, valido))

    threading.Thread(target=verificar, daemon=True).start()

def _pos_verificacao(ticker, valido):
    btn_add.config(state="normal", text="+")
    if not valido:
        label_status.config(text=f"❌ {nome_exibicao(ticker)} não encontrado.", fg="#FF5252")
        return
    var = tk.BooleanVar(value=True)
    ativos_vars[ticker] = var
    ativos_ordem.append(ticker)
    _criar_checkbox(ticker, var)
    entry_novo_ativo.delete(0, tk.END)
    entry_novo_ativo.insert(0, "ex: EGIE3")
    entry_novo_ativo.config(fg="#888888")
    label_status.config(text=f"✔ {nome_exibicao(ticker)} adicionado!", fg="#00E676")

def _criar_checkbox(ticker, var):
    idx = ativos_ordem.index(ticker)
    cor = CORES_ATIVOS[idx % len(CORES_ATIVOS)]

    row_frame = tk.Frame(frame_lista_ativos, bg=CARD)
    row_frame.pack(anchor="w", padx=6, pady=1)

    c = tk.Canvas(row_frame, width=12, height=12, bg=CARD, highlightthickness=0)
    c.create_rectangle(0, 0, 12, 12, fill=cor, outline="")
    c.pack(side="left", padx=(0, 4))

    tk.Checkbutton(
        row_frame, text=nome_exibicao(ticker), variable=var,
        bg=CARD, fg=TXT, selectcolor="#1a2a3a",
        activebackground=CARD, activeforeground=TXT,
        font=("Arial", 9), cursor="hand2"
    ).pack(side="left")

def selecionar_todos():
    for v in ativos_vars.values(): v.set(True)

def desmarcar_todos():
    for v in ativos_vars.values(): v.set(False)

# ==============================
# GERAR GRÁFICO
# ==============================
def gerar_grafico():
    for widget in frame_grafico.winfo_children():
        widget.destroy()

    start = mascara_inicio.get_data_yf()
    end   = mascara_fim.get_data_yf()

    if not start or not end:
        tk.Label(frame_grafico, text="Data inválida. Use DD/MM/AAAA.",
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
    ax_leg.set_xticks([]); ax_leg.set_yticks([])
    for spine in ax_leg.spines.values():
        spine.set_edgecolor(ACCENT); spine.set_linewidth(1.2)

    linhas, nomes = [], []

    for ativo in selecionados:
        cor = CORES_ATIVOS[ativos_ordem.index(ativo) % len(CORES_ATIVOS)]
        try:
            serie = (dados["Close"] if len(selecionados) == 1
                     else dados["Close"][ativo]).dropna()
            linha, = ax.plot(serie.index, serie.values,
                             linewidth=2.5, color=cor, label=nome_exibicao(ativo))
            linhas.append(linha)
            nomes.append(nome_exibicao(ativo))
        except Exception:
            pass

    ax.set_title("Evolução dos Ativos", color=TXT, fontsize=13, fontweight="bold")
    ax.set_ylabel("Preço (R$)", color=TXT)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))

    # Datas no eixo X: espaçadas e rotacionadas
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%Y"))
    ax.tick_params(axis="x", colors="#FFF", rotation=35, labelsize=8)
    ax.tick_params(axis="y", colors="#FFF")
    for spine in ax.spines.values(): spine.set_color("#444")

    ax_leg.text(0.5, 0.97, "Ativos", transform=ax_leg.transAxes,
                color=ACCENT, fontsize=10, fontweight="bold", ha="center", va="top")
    leg = ax_leg.legend(handles=linhas, labels=nomes, loc="upper center",
                        bbox_to_anchor=(0.5, 0.90), frameon=False, ncol=1,
                        fontsize=9, handlelength=1.5, labelspacing=0.5)
    for t in leg.get_texts(): t.set_color("#FFF")

    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

# ==============================
# COTAÇÕES — MOEDAS + BITCOIN
# ==============================
MOEDAS = [
    ("BTC",  "BTC-USD",  "₿",  "#F7931A"),
    ("USD",  "USDBRL=X", "$",  "#00E676"),
    ("EUR",  "EURBRL=X", "€",  "#448AFF"),
    ("GBP",  "GBPBRL=X", "£",  "#E040FB"),
    ("JPY",  "JPYBRL=X", "¥",  "#FF4081"),
    ("CHF",  "CHFBRL=X", "₣",  "#FFFFFF"),
    ("CNY",  "CNYBRL=X", "¥",  "#FF1744"),
    ("AUD",  "AUDBRL=X", "A$", "#FFD600"),
    ("CAD",  "CADBRL=X", "C$", "#FF9100"),
    ("BRL",  None,        "R$", "#00E5FF"),  # referência fixa
]

# Guarda os Labels para atualizar
_labels_cotacao = {}   # sigla -> (label_valor, label_var)

def _buscar_cotacoes():
    """Roda em thread — busca preços via history() e atualiza labels."""
    for sigla, ticker_yf, simbolo, cor in MOEDAS:
        if ticker_yf is None:
            root.after(0, lambda s=sigla, sm=simbolo, c=cor:
                       _atualizar_label_moeda(s, 1.0, sm, c, 0.0))
            continue
        try:
            hist = yf.Ticker(ticker_yf).history(period="2d")
            if hist.empty or len(hist) < 1:
                continue

            preco = float(hist["Close"].iloc[-1])
            prev  = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else preco
            var   = ((preco - prev) / prev * 100) if prev else 0.0

            root.after(0, lambda s=sigla, p=preco, sm=simbolo, c=cor, v=var:
                       _atualizar_label_moeda(s, p, sm, c, v))
        except Exception:
            pass

def _atualizar_label_moeda(sigla, preco, simbolo, cor, variacao):
    if sigla not in _labels_cotacao:
        return
    lbl_val, lbl_var = _labels_cotacao[sigla]

    if sigla == "BTC":
        texto = f"R$ {preco:,.0f}"
    elif sigla in ("JPY", "CNY"):
        texto = f"R$ {preco:.4f}"
    elif sigla == "BRL":
        texto = "R$ 1,00"
    else:
        texto = f"R$ {preco:.4f}"

    lbl_val.config(text=texto, fg=cor)

    sinal = "▲" if variacao >= 0 else "▼"
    cor_var = "#00E676" if variacao >= 0 else "#FF5252"
    lbl_var.config(text=f"{sinal} {abs(variacao):.2f}%", fg=cor_var)

def atualizar_cotacoes():
    """Dispara busca em background e agenda próxima atualização em 60s."""
    for _, lbl_val, lbl_var in [(k, v[0], v[1]) for k, v in _labels_cotacao.items()]:
        lbl_val.config(text="...")
    threading.Thread(target=_buscar_cotacoes, daemon=True).start()
    root.after(60_000, atualizar_cotacoes)

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
        taxa  = 0.105 * (percentual / 100)
        final = valor * (1 + taxa) ** (dias / 365)
        lucro = final - valor
        resultado_cdb.config(
            text=f"💰  Valor final: R$ {final:,.2f}   |   Lucro: R$ {lucro:,.2f}",
            fg="#00E676")
    except Exception:
        resultado_cdb.config(text="⚠  Preencha os campos com números válidos", fg="#FF5252")

# ==============================
# CALCULADORA REVERSA CDB
# Dado: meta, % CDI e aporte mensal → tempo necessário
# Dado: meta, % CDI e prazo → aporte mensal necessário
# ==============================
def calcular_meta():
    try:
        meta       = float(entry_meta.get())
        percentual = float(entry_meta_cdi.get())
        if meta <= 0 or percentual <= 0:
            raise ValueError

        taxa_anual  = 0.105 * (percentual / 100)
        taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

        modo = modo_var.get()  # "aporte" ou "prazo"

        if modo == "aporte":
            # Usuário informou o aporte mensal → calcula quantos meses
            aporte = float(entry_aporte_ou_prazo.get())
            if aporte <= 0:
                raise ValueError

            # Fórmula: n = log(1 + meta*r/PMT) / log(1+r)
            import math
            if taxa_mensal == 0:
                meses = meta / aporte
            else:
                meses = math.log(1 + (meta * taxa_mensal) / aporte) / math.log(1 + taxa_mensal)

            meses = int(math.ceil(meses))
            anos  = meses // 12
            resto = meses % 12

            if anos > 0 and resto > 0:
                tempo_str = f"{anos} ano(s) e {resto} mês(es)  ({meses} meses)"
            elif anos > 0:
                tempo_str = f"{anos} ano(s)  ({meses} meses)"
            else:
                tempo_str = f"{meses} mês(es)"

            resultado_meta.config(
                text=f"⏱  Tempo necessário: {tempo_str}",
                fg="#00E676")

        else:
            # Usuário informou o prazo em meses → calcula aporte mensal
            import math
            meses = int(entry_aporte_ou_prazo.get())
            if meses <= 0:
                raise ValueError

            # Fórmula PMT: aporte = meta * r / ((1+r)^n - 1)
            if taxa_mensal == 0:
                aporte = meta / meses
            else:
                aporte = meta * taxa_mensal / ((1 + taxa_mensal) ** meses - 1)

            resultado_meta.config(
                text=f"💸  Aporte mensal necessário: R$ {aporte:,.2f}",
                fg="#00E676")

    except Exception:
        resultado_meta.config(text="⚠  Preencha os campos corretamente", fg="#FF5252")

def _atualizar_label_modo(*args):
    if modo_var.get() == "aporte":
        label_aporte_ou_prazo.config(text="Aporte mensal (R$)")
        entry_aporte_ou_prazo.delete(0, tk.END)
        entry_aporte_ou_prazo.insert(0, "500")
    else:
        label_aporte_ou_prazo.config(text="Prazo (meses)")
        entry_aporte_ou_prazo.delete(0, tk.END)
        entry_aporte_ou_prazo.insert(0, "24")

# ==============================
# JANELA PRINCIPAL
# ==============================
root = tk.Tk()
root.title("Dashboard de Investimentos")
root.geometry("1200x700")
root.configure(bg=BG)

frame_main = tk.Frame(root, bg=BG)
frame_main.pack(fill="both", expand=True)

# ── SIDEBAR ──
frame_sidebar = tk.Frame(frame_main, bg=CARD, width=210)
frame_sidebar.pack(side="left", fill="y", padx=(10, 0), pady=10)
frame_sidebar.pack_propagate(False)

tk.Label(frame_sidebar, text="📋  Ativos", bg=CARD, fg=ACCENT,
         font=("Arial", 11, "bold")).pack(pady=(10, 4))

frame_btns_sel = tk.Frame(frame_sidebar, bg=CARD)
frame_btns_sel.pack(fill="x", padx=6, pady=(0, 6))
tk.Button(frame_btns_sel, text="Todos", bg=BTN, fg=TXT, font=("Arial", 8),
          relief="flat", cursor="hand2", command=selecionar_todos
          ).pack(side="left", expand=True, fill="x", padx=(0, 2))
tk.Button(frame_btns_sel, text="Nenhum", bg=BTN, fg=TXT, font=("Arial", 8),
          relief="flat", cursor="hand2", command=desmarcar_todos
          ).pack(side="left", expand=True, fill="x")

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
frame_lista_ativos.bind("<Configure>",
    lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
canvas_scroll.bind_all("<MouseWheel>",
    lambda e: canvas_scroll.yview_scroll(int(-1*(e.delta/120)), "units"))

tk.Frame(frame_sidebar, bg="#1a2a3a", height=1).pack(fill="x", padx=6, pady=6)
tk.Label(frame_sidebar, text="Adicionar ativo:", bg=CARD, fg="#aaaaaa",
         font=("Arial", 8)).pack(padx=6, anchor="w")

frame_add = tk.Frame(frame_sidebar, bg=CARD)
frame_add.pack(fill="x", padx=6, pady=(2, 0))

entry_novo_ativo = tk.Entry(frame_add, bg=BTN, fg="#888888",
                             insertbackground=TXT, font=("Arial", 9), width=9)
entry_novo_ativo.insert(0, "ex: EGIE3")
entry_novo_ativo.bind("<FocusIn>",  lambda e: limpar_entry_placeholder(entry_novo_ativo, "ex: EGIE3"))
entry_novo_ativo.bind("<FocusOut>", lambda e: restaurar_placeholder(entry_novo_ativo, "ex: EGIE3"))
entry_novo_ativo.bind("<Return>", lambda e: adicionar_ativo())
entry_novo_ativo.pack(side="left", fill="x", expand=True)

btn_add = tk.Button(frame_add, text="+", bg=ACCENT, fg="#000000",
                    font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                    width=2, command=adicionar_ativo)
btn_add.pack(side="left", padx=(4, 0))

label_status = tk.Label(frame_sidebar, text="", bg=CARD, fg="#00E676",
                         font=("Arial", 8), wraplength=160)
label_status.pack(padx=6, pady=4)

# ── PAINEL DE COTAÇÕES ──
tk.Frame(frame_sidebar, bg="#1a2a3a", height=1).pack(fill="x", padx=6, pady=(4, 0))

frame_cab_cotacao = tk.Frame(frame_sidebar, bg=CARD)
frame_cab_cotacao.pack(fill="x", padx=6, pady=(4, 2))

tk.Label(frame_cab_cotacao, text="💱  Cotações vs BRL", bg=CARD, fg=ACCENT,
         font=("Arial", 9, "bold")).pack(side="left")

tk.Button(frame_cab_cotacao, text="↻", bg=BTN, fg=ACCENT,
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=atualizar_cotacoes).pack(side="right")

frame_cotacoes = tk.Frame(frame_sidebar, bg=CARD)
frame_cotacoes.pack(fill="x", padx=6, pady=(0, 6))

for sigla, ticker_yf, simbolo, cor in MOEDAS:
    row = tk.Frame(frame_cotacoes, bg=CARD)
    row.pack(fill="x", pady=1)

    # Ícone colorido + sigla
    tk.Label(row, text=f"{simbolo} {sigla}", bg=CARD, fg=cor,
             font=("Arial", 8, "bold"), width=7, anchor="w").pack(side="left")

    # Valor
    lbl_val = tk.Label(row, text="...", bg=CARD, fg=cor,
                       font=("Arial", 8), width=10, anchor="e")
    lbl_val.pack(side="left")

    # Variação %
    lbl_var = tk.Label(row, text="", bg=CARD, fg="#aaaaaa",
                       font=("Arial", 7), width=8, anchor="e")
    lbl_var.pack(side="left")

    _labels_cotacao[sigla] = (lbl_val, lbl_var)

# Inicia cotações ao abrir
root.after(500, atualizar_cotacoes)

# ── CONTEÚDO DIREITO ──
frame_conteudo = tk.Frame(frame_main, bg=BG)
frame_conteudo.pack(side="left", fill="both", expand=True, padx=10, pady=10)

frame_topo = tk.Frame(frame_conteudo, bg=BG)
frame_topo.pack(fill="x", pady=(0, 6))

# Data início
tk.Label(frame_topo, text="Data início", bg=BG, fg=TXT,
         font=("Arial", 9)).pack(side="left", padx=(0, 4))
entry_inicio = tk.Entry(frame_topo, width=12, bg=BTN, fg="#888888",
                        insertbackground=TXT, font=("Arial", 9))
entry_inicio.insert(0, "DD/MM/AAAA")
entry_inicio.bind("<FocusIn>",  lambda e: limpar_entry_placeholder(entry_inicio, "DD/MM/AAAA"))
entry_inicio.bind("<FocusOut>", lambda e: restaurar_placeholder(entry_inicio, "DD/MM/AAAA"))
entry_inicio.pack(side="left")
mascara_inicio = MascaraData(entry_inicio)

# Data fim
tk.Label(frame_topo, text="Data fim", bg=BG, fg=TXT,
         font=("Arial", 9)).pack(side="left", padx=(12, 4))
entry_fim = tk.Entry(frame_topo, width=12, bg=BTN, fg="#888888",
                     insertbackground=TXT, font=("Arial", 9))
entry_fim.insert(0, "DD/MM/AAAA")
entry_fim.bind("<FocusIn>",  lambda e: limpar_entry_placeholder(entry_fim, "DD/MM/AAAA"))
entry_fim.bind("<FocusOut>", lambda e: restaurar_placeholder(entry_fim, "DD/MM/AAAA"))
entry_fim.pack(side="left")
mascara_fim = MascaraData(entry_fim)

tk.Button(frame_topo, text="  Gerar Gráfico  ", bg=ACCENT, fg="#000000",
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=gerar_grafico).pack(side="left", padx=14)

# -- GRÁFICO --
frame_grafico = tk.Frame(frame_conteudo, bg=CARD)
frame_grafico.pack(fill="both", expand=True)

# -- ÁREA DOS DOIS CARDS (CDB + META) --
frame_cards = tk.Frame(frame_conteudo, bg=BG)
frame_cards.pack(fill="x", pady=(10, 0))

# ── CARD ESQUERDO: Simulador CDB ──
frame_cdb_outer = tk.Frame(frame_cards, bg=ACCENT)
frame_cdb_outer.pack(side="left", fill="both", expand=True, padx=(0, 5))

frame_cdb = tk.Frame(frame_cdb_outer, bg=CDB_BG)
frame_cdb.pack(fill="both", expand=True, padx=2, pady=2)

cab_cdb = tk.Frame(frame_cdb, bg="#0a2235")
cab_cdb.pack(fill="x")
tk.Label(cab_cdb, text="💵  Simulador de CDB", bg="#0a2235", fg=ACCENT,
         font=("Arial", 10, "bold"), pady=6).pack(side="left", padx=10)

linha_inputs = tk.Frame(frame_cdb, bg=CDB_BG)
linha_inputs.pack(pady=6)

def make_label(parent, text):
    tk.Label(parent, text=text, bg=CDB_BG, fg="#aaaaaa", font=("Arial", 8)).pack()

def limpar_cdb(entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(fg=TXT)

col1 = tk.Frame(linha_inputs, bg=CDB_BG); col1.pack(side="left", padx=8)
make_label(col1, "Valor (R$)")
entry_valor = tk.Entry(col1, width=11, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_valor.insert(0, "2000")
entry_valor.bind("<FocusIn>", lambda e: limpar_cdb(entry_valor, "2000"))
entry_valor.pack()

col2 = tk.Frame(linha_inputs, bg=CDB_BG); col2.pack(side="left", padx=8)
make_label(col2, "% do CDI")
entry_cdi = tk.Entry(col2, width=11, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_cdi.insert(0, "110")
entry_cdi.bind("<FocusIn>", lambda e: limpar_cdb(entry_cdi, "110"))
entry_cdi.pack()

col3 = tk.Frame(linha_inputs, bg=CDB_BG); col3.pack(side="left", padx=8)
make_label(col3, "Dias")
entry_dias = tk.Entry(col3, width=11, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_dias.insert(0, "365")
entry_dias.bind("<FocusIn>", lambda e: limpar_cdb(entry_dias, "365"))
entry_dias.pack()

col4 = tk.Frame(linha_inputs, bg=CDB_BG); col4.pack(side="left", padx=8)
make_label(col4, " ")
tk.Button(col4, text=" Simular ", bg=ACCENT, fg="#000000",
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=simular_cdb).pack()

resultado_cdb = tk.Label(frame_cdb, text="", bg=CDB_BG, fg="#00E676",
                          font=("Arial", 10, "bold"), pady=5)
resultado_cdb.pack()

# ── CARD DIREITO: Calculadora de Meta ──
frame_meta_outer = tk.Frame(frame_cards, bg="#FFD600")
frame_meta_outer.pack(side="left", fill="both", expand=True, padx=(5, 0))

META_BG = "#1a1a0a"
frame_meta = tk.Frame(frame_meta_outer, bg=META_BG)
frame_meta.pack(fill="both", expand=True, padx=2, pady=2)

cab_meta = tk.Frame(frame_meta, bg="#2a2a00")
cab_meta.pack(fill="x")
tk.Label(cab_meta, text="🎯  Calculadora de Meta", bg="#2a2a00", fg="#FFD600",
         font=("Arial", 10, "bold"), pady=6).pack(side="left", padx=10)

# Modo: calcular prazo OU calcular aporte
modo_var = tk.StringVar(value="aporte")
modo_var.trace_add("write", _atualizar_label_modo)

frame_modo = tk.Frame(frame_meta, bg=META_BG)
frame_modo.pack(pady=(5, 2))

tk.Label(frame_modo, text="Quero calcular:", bg=META_BG, fg="#aaaaaa",
         font=("Arial", 8)).pack(side="left", padx=(8, 6))

tk.Radiobutton(frame_modo, text="Tempo necessário", variable=modo_var, value="aporte",
               bg=META_BG, fg=TXT, selectcolor="#2a2a10", activebackground=META_BG,
               font=("Arial", 8), cursor="hand2").pack(side="left", padx=4)

tk.Radiobutton(frame_modo, text="Aporte mensal", variable=modo_var, value="prazo",
               bg=META_BG, fg=TXT, selectcolor="#2a2a10", activebackground=META_BG,
               font=("Arial", 8), cursor="hand2").pack(side="left", padx=4)

linha_meta = tk.Frame(frame_meta, bg=META_BG)
linha_meta.pack(pady=6)

def make_label_meta(parent, text):
    tk.Label(parent, text=text, bg=META_BG, fg="#aaaaaa", font=("Arial", 8)).pack()

# Meta (R$)
m1 = tk.Frame(linha_meta, bg=META_BG); m1.pack(side="left", padx=8)
make_label_meta(m1, "Meta (R$)")
entry_meta = tk.Entry(m1, width=11, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_meta.insert(0, "30000")
entry_meta.pack()

# % CDI
m2 = tk.Frame(linha_meta, bg=META_BG); m2.pack(side="left", padx=8)
make_label_meta(m2, "% do CDI")
entry_meta_cdi = tk.Entry(m2, width=11, bg=BTN, fg=TXT, insertbackground=TXT, justify="center")
entry_meta_cdi.insert(0, "110")
entry_meta_cdi.pack()

# Aporte ou Prazo (dinâmico)
m3 = tk.Frame(linha_meta, bg=META_BG); m3.pack(side="left", padx=8)
label_aporte_ou_prazo = tk.Label(m3, text="Aporte mensal (R$)", bg=META_BG,
                                  fg="#aaaaaa", font=("Arial", 8))
label_aporte_ou_prazo.pack()
entry_aporte_ou_prazo = tk.Entry(m3, width=11, bg=BTN, fg=TXT,
                                  insertbackground=TXT, justify="center")
entry_aporte_ou_prazo.insert(0, "500")
entry_aporte_ou_prazo.pack()

# Botão
m4 = tk.Frame(linha_meta, bg=META_BG); m4.pack(side="left", padx=8)
make_label_meta(m4, " ")
tk.Button(m4, text=" Calcular ", bg="#FFD600", fg="#000000",
          font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
          command=calcular_meta).pack()

resultado_meta = tk.Label(frame_meta, text="", bg=META_BG, fg="#00E676",
                           font=("Arial", 10, "bold"), pady=5)
resultado_meta.pack()

# ==============================
# INICIALIZAR CHECKBOXES PADRÃO
# ==============================
for ticker in ATIVOS_PADRAO:
    var = tk.BooleanVar(value=True)
    ativos_vars[ticker] = var
    ativos_ordem.append(ticker)
    _criar_checkbox(ticker, var)

root.mainloop()