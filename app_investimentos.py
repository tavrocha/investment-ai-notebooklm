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
import matplotlib.dates as mdates
import numpy as np

# estado global do gráfico para tooltip
_estado_grafico = {
    "ax": None, "canvas": None,
    "series": {},   # ticker -> (xs_num, ys, cor)
    "modo": "preco" # "preco" ou "base100"
}

def _montar_grafico(dados, selecionados, modo):
    """Monta a figura matplotlib e retorna (fig, series_dict)."""
    fig = plt.figure(figsize=(11, 4.2))
    fig.patch.set_facecolor(BG)

    ax = fig.add_axes([0.07, 0.16, 0.68, 0.74])
    ax.set_facecolor(BG)

    ax_leg = fig.add_axes([0.77, 0.05, 0.22, 0.90])
    ax_leg.set_facecolor("#0d1a24")
    ax_leg.set_xticks([]); ax_leg.set_yticks([])
    for spine in ax_leg.spines.values():
        spine.set_edgecolor(ACCENT); spine.set_linewidth(1.2)

    linhas, nomes, series = [], [], {}

    for ativo in selecionados:
        cor = CORES_ATIVOS[ativos_ordem.index(ativo) % len(CORES_ATIVOS)]
        try:
            raw = (dados["Close"] if len(selecionados) == 1
                   else dados["Close"][ativo]).dropna()

            if modo == "base100":
                serie = (raw / raw.iloc[0]) * 100
            else:
                serie = raw

            xs_num = mdates.date2num(serie.index.to_pydatetime())
            ys     = serie.values.astype(float)

            linha, = ax.plot(serie.index, ys, linewidth=2.5,
                             color=cor, label=nome_exibicao(ativo))
            linhas.append(linha)
            nomes.append(nome_exibicao(ativo))
            series[ativo] = (xs_num, ys, cor)

            # Média móvel (se ativada)
            mm = _mm_estado.get("periodo", 0)
            if mm > 0 and len(serie) >= mm:
                mm_serie = serie.rolling(window=mm).mean().dropna()
                ax.plot(mm_serie.index, mm_serie.values,
                        linewidth=1.2, color=cor, linestyle="--", alpha=0.5)
        except Exception:
            pass

    titulo = "Desempenho Relativo (Base 100)" if modo == "base100" else "Evolução dos Ativos"
    ylabel = "Retorno (Base 100)" if modo == "base100" else "Preço (R$)"

    ax.set_title(titulo, color=TXT, fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel, color=TXT)

    if modo == "preco":
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
    else:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1f}"))
        ax.axhline(100, color="#444", linewidth=0.8, linestyle="--")

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

    return fig, ax, series


def _conectar_tooltip(fig, ax, canvas, series, modo):
    """
    Tooltip robusto — mede distância em PIXELS para cada série,
    só ativa se o cursor estiver a menos de 25px de alguma linha.
    """
    annot = ax.annotate(
        "", xy=(0, 0), xytext=(15, 15),
        xycoords="data", textcoords="offset points",
        fontsize=9, color="#000000", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.45", facecolor=ACCENT,
                  alpha=0.92, edgecolor="none"),
        zorder=10, visible=False
    )
    dot, = ax.plot([], [], "o", markersize=8, zorder=11, visible=False,
                   markeredgecolor="#000000", markeredgewidth=0.5)

    LIMIAR_PX = 25

    def on_move(event):
        if event.inaxes != ax or not series or event.xdata is None:
            annot.set_visible(False)
            dot.set_visible(False)
            canvas.draw_idle()
            return

        cx, cy = event.x, event.y

        melhor_ticker = None
        melhor_dist   = float("inf")
        melhor_xd = melhor_yd = 0.0
        melhor_cor = ACCENT

        for ticker, (xs_num, ys, cor) in series.items():
            pts_px = ax.transData.transform(np.column_stack([xs_num, ys]))
            dists  = np.sqrt((pts_px[:, 0] - cx)**2 + (pts_px[:, 1] - cy)**2)
            idx    = int(np.argmin(dists))
            d      = dists[idx]
            if d < melhor_dist:
                melhor_dist   = d
                melhor_ticker = ticker
                melhor_xd     = xs_num[idx]
                melhor_yd     = ys[idx]
                melhor_cor    = cor

        if melhor_ticker is None or melhor_dist > LIMIAR_PX:
            annot.set_visible(False)
            dot.set_visible(False)
            canvas.draw_idle()
            return

        data_str = mdates.num2date(melhor_xd).strftime("%d/%m/%Y")
        val_str  = (f"{melhor_yd:.2f}" if modo == "base100"
                    else f"R$ {melhor_yd:,.2f}")

        annot.set_text(
            f"  {nome_exibicao(melhor_ticker)}\n"
            f"  📅 {data_str}\n"
            f"  💰 {val_str}  "
        )
        annot.get_bbox_patch().set_facecolor(melhor_cor)
        annot.xy = (melhor_xd, melhor_yd)

        xlim  = ax.get_xlim()
        off_x = -120 if melhor_xd > xlim[0] + (xlim[1] - xlim[0]) * 0.72 else 15
        annot.set_position((off_x, 15))
        annot.set_visible(True)

        dot.set_data([melhor_xd], [melhor_yd])
        dot.set_color(melhor_cor)
        dot.set_visible(True)
        canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", on_move)


def _montar_tabela(dados, selecionados, frame_pai):
    """Cria tabela de análise dentro de frame_pai — usa grid no frame mestre."""
    for w in frame_pai.winfo_children(): w.destroy()

    colunas  = ["Ativo", "Início", "Fim", "Retorno %", "Volatil. %", "Risco", "Máximo", "Mínimo"]
    larguras = [80, 85, 85, 85, 85, 70, 85, 85]

    # Frame mestre com grid
    tbl = tk.Frame(frame_pai, bg="#0d1a24")
    tbl.pack(fill="x", padx=8)

    # Cabeçalho
    for c, (col, w) in enumerate(zip(colunas, larguras)):
        tk.Label(tbl, text=col, bg="#0d1a24", fg=ACCENT,
                 font=("Arial", 8, "bold"), width=w//8,
                 anchor="center").grid(row=0, column=c, padx=1, pady=3, sticky="ew")

    # Separador
    sep = tk.Frame(tbl, bg="#1a2a3a", height=1)
    sep.grid(row=1, column=0, columnspan=len(colunas), sticky="ew", pady=0)

    # Linhas de dados
    for idx_a, ativo in enumerate(selecionados):
        try:
            serie = (dados["Close"] if len(selecionados) == 1
                     else dados["Close"][ativo]).dropna()

            inicio    = float(serie.iloc[0])
            fim       = float(serie.iloc[-1])
            retorno   = ((fim - inicio) / inicio) * 100
            vol       = serie.pct_change().std() * 100
            maximo    = float(serie.max())
            minimo    = float(serie.min())
            cor_ativo = CORES_ATIVOS[ativos_ordem.index(ativo) % len(CORES_ATIVOS)]
            cor_ret   = "#00E676" if retorno >= 0 else "#FF5252"
            row_bg    = "#0a0a0f" if idx_a % 2 == 0 else "#0f0f18"

            risco_txt, cor_risco = _classificar_risco(vol)
            valores = [
                (nome_exibicao(ativo), cor_ativo),
                (f"R$ {inicio:.2f}",   "#cccccc"),
                (f"R$ {fim:.2f}",      "#cccccc"),
                (f"{retorno:+.2f}%",   cor_ret),
                (f"{vol:.2f}%",        "#cccccc"),
                (risco_txt,            cor_risco),
                (f"R$ {maximo:.2f}",   "#cccccc"),
                (f"R$ {minimo:.2f}",   "#cccccc"),
            ]
            r = idx_a + 2   # +2 por causa do header e separador
            for c, (val, fg) in enumerate(valores):
                tk.Label(tbl, text=val, bg=row_bg, fg=fg,
                         font=("Arial", 8), width=larguras[c]//8,
                         anchor="center").grid(row=r, column=c, padx=1, pady=2, sticky="ew")
        except Exception:
            pass


# Estado da média móvel
_mm_estado = {"periodo": 0}   # 0 = desligada

def _toggle_mm(periodo):
    """Liga/desliga média móvel e re-renderiza."""
    if _mm_estado["periodo"] == periodo:
        _mm_estado["periodo"] = 0
    else:
        _mm_estado["periodo"] = periodo
    _atualizar_btn_mm()
    if _cache["dados"] is not None:
        _renderizar(_estado_grafico["modo"])

def _atualizar_btn_mm():
    p = _mm_estado["periodo"]
    btn_mm20.config(bg=ACCENT if p == 20 else BTN,
                    fg="#000000" if p == 20 else TXT)
    btn_mm50.config(bg=ACCENT if p == 50 else BTN,
                    fg="#000000" if p == 50 else TXT)

# ── Análise inteligente ──
def _calcular_analise(dados, selecionados):
    """Calcula métricas de todos os ativos e retorna lista de dicts."""
    analises = []
    for ativo in selecionados:
        try:
            serie = (dados["Close"] if len(selecionados) == 1
                     else dados["Close"][ativo]).dropna()
            inicio  = float(serie.iloc[0])
            fim     = float(serie.iloc[-1])
            retorno = ((fim - inicio) / inicio) * 100
            vol     = serie.pct_change().std() * 100
            analises.append({
                "ticker":  ativo,
                "nome":    nome_exibicao(ativo),
                "retorno": retorno,
                "vol":     vol,
                "cor":     CORES_ATIVOS[ativos_ordem.index(ativo) % len(CORES_ATIVOS)]
            })
        except Exception:
            pass
    return analises

def _classificar_risco(vol):
    if vol < 1.5:
        return ("Baixo",  "#00E676")
    elif vol < 2.5:
        return ("Médio",  "#FFD600")
    else:
        return ("Alto",   "#FF5252")

def _gerar_insights(analises):
    """Gera frases automáticas baseadas nas métricas."""
    if not analises: return []

    por_retorno = sorted(analises, key=lambda x: x["retorno"], reverse=True)
    por_vol     = sorted(analises, key=lambda x: x["vol"],     reverse=True)
    por_estab   = sorted(analises, key=lambda x: x["vol"])

    melhor   = por_retorno[0]
    pior     = por_retorno[-1]
    mais_vol = por_vol[0]
    mais_est = por_estab[0]

    frases = []

    # 🏆 Top performer
    sinal = "+" if melhor["retorno"] >= 0 else ""
    frases.append({
        "icone": "🏆",
        "titulo": "Top performer",
        "texto": f"{melhor['nome']} apresentou o maior retorno no período ({sinal}{melhor['retorno']:.2f}%).",
        "cor": "#00E676"
    })

    # 📉 Pior desempenho
    sinal2 = "+" if pior["retorno"] >= 0 else ""
    frases.append({
        "icone": "📉",
        "titulo": "Menor retorno",
        "texto": f"{pior['nome']} teve o menor desempenho ({sinal2}{pior['retorno']:.2f}%).",
        "cor": "#FF5252"
    })

    # ⚠ Mais arriscado
    risco_txt, _ = _classificar_risco(mais_vol["vol"])
    frases.append({
        "icone": "⚠",
        "titulo": "Maior risco",
        "texto": f"{mais_vol['nome']} possui alta volatilidade ({mais_vol['vol']:.2f}%) — risco {risco_txt}.",
        "cor": "#FFD600"
    })

    # 🛡 Mais estável
    frases.append({
        "icone": "🛡",
        "titulo": "Mais estável",
        "texto": f"{mais_est['nome']} foi o ativo mais estável (vol. {mais_est['vol']:.2f}%).",
        "cor": "#00E5FF"
    })

    # 📊 Concentração de retornos positivos
    positivos = sum(1 for a in analises if a["retorno"] > 0)
    total     = len(analises)
    pct       = positivos / total * 100
    frases.append({
        "icone": "📊",
        "titulo": "Visão geral",
        "texto": f"{positivos} de {total} ativos ({pct:.0f}%) tiveram retorno positivo no período.",
        "cor": "#aaaaaa"
    })

    return frases

def _montar_insights(analises, frame_pai):
    """Renderiza o card de insights."""
    for w in frame_pai.winfo_children(): w.destroy()
    frases = _gerar_insights(analises)

    for f in frases:
        row = tk.Frame(frame_pai, bg="#0d1a24")
        row.pack(fill="x", padx=8, pady=3)

        tk.Label(row, text=f["icone"], bg="#0d1a24", fg=f["cor"],
                 font=("Arial", 11), width=2).pack(side="left", padx=(0, 6))

        col = tk.Frame(row, bg="#0d1a24")
        col.pack(side="left", fill="x", expand=True)

        tk.Label(col, text=f["titulo"], bg="#0d1a24", fg=f["cor"],
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x")
        tk.Label(col, text=f["texto"], bg="#0d1a24", fg="#cccccc",
                 font=("Arial", 8), anchor="w", wraplength=700).pack(fill="x")

# Cache dos dados para alternar entre modos sem rebaixar
_cache = {"dados": None, "selecionados": None}

def _renderizar(modo):
    """Renderiza gráfico + tabela no modo especificado."""
    dados       = _cache["dados"]
    selecionados= _cache["selecionados"]
    if dados is None: return

    _estado_grafico["modo"] = modo

    # Limpa área do gráfico
    for w in frame_grafico.winfo_children(): w.destroy()

    fig, ax, series = _montar_grafico(dados, selecionados, modo)
    _fig_atual["fig"] = fig   # guarda para exportar
    canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    _conectar_tooltip(fig, ax, canvas, series, modo)

    # Atualiza botões de modo
    if modo == "preco":
        btn_preco.config(bg=ACCENT, fg="#000000")
        btn_base100.config(bg=BTN, fg=TXT)
    else:
        btn_base100.config(bg=ACCENT, fg="#000000")
        btn_preco.config(bg=BTN, fg=TXT)

    # Tabela
    _montar_tabela(dados, selecionados, frame_tabela)

    # Insights
    analises = _calcular_analise(dados, selecionados)
    _montar_insights(analises, frame_insights)


# figura atual (para exportar PNG)
_fig_atual = {"fig": None}

def exportar_png():
    """Salva o gráfico atual como PNG via diálogo de arquivo."""
    fig = _fig_atual.get("fig")
    if fig is None:
        return
    from tkinter import filedialog
    caminho = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("Imagem PNG", "*.png"), ("Todos os arquivos", "*.*")],
        initialfile="grafico_investimentos.png",
        title="Salvar gráfico como..."
    )
    if caminho:
        fig.savefig(caminho, dpi=150, bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        btn_exportar.config(text="✔ Salvo!", fg="#00E676")
        root.after(2500, lambda: btn_exportar.config(text="📥 Exportar PNG", fg=TXT))


def _mostrar_loading():
    """Exibe spinner animado no frame_grafico enquanto baixa os dados."""
    for w in frame_grafico.winfo_children(): w.destroy()
    for w in frame_tabela.winfo_children(): w.destroy()

    frame_load = tk.Frame(frame_grafico, bg=CARD)
    frame_load.pack(expand=True)

    lbl = tk.Label(frame_load, text="⏳  Baixando dados...", bg=CARD, fg=ACCENT,
                   font=("Arial", 13, "bold"))
    lbl.pack(pady=30)

    dots = ["", ".", "..", "..."]
    estado = {"i": 0, "ativo": True}

    def animar():
        if not estado["ativo"]: return
        lbl.config(text=f"⏳  Baixando dados{dots[estado['i'] % 4]}")
        estado["i"] += 1
        root.after(400, animar)

    animar()
    return estado   # retorna para poder parar a animação


def gerar_grafico():
    start = mascara_inicio.get_data_yf()
    end   = mascara_fim.get_data_yf()

    if not start or not end:
        for w in frame_grafico.winfo_children(): w.destroy()
        tk.Label(frame_grafico, text="Data inválida. Use DD/MM/AAAA.",
                 fg="#FF5252", bg=CARD).pack(pady=20); return
    if start >= end:
        for w in frame_grafico.winfo_children(): w.destroy()
        tk.Label(frame_grafico, text="Data final deve ser maior que a inicial.",
                 fg="#FF5252", bg=CARD).pack(pady=20); return

    selecionados = [t for t in ativos_ordem if ativos_vars[t].get()]
    if not selecionados:
        for w in frame_grafico.winfo_children(): w.destroy()
        tk.Label(frame_grafico, text="Selecione ao menos um ativo.",
                 fg="#FFD600", bg=CARD).pack(pady=20); return

    # Mostra loading e desabilita botão
    estado_load = _mostrar_loading()
    btn_gerar.config(state="disabled", text="Carregando...")

    def _baixar():
        try:
            dados = yf.download(selecionados, start=start, end=end, auto_adjust=True)
        except Exception:
            dados = None
        root.after(0, lambda: _pos_download(dados, selecionados, estado_load))

    threading.Thread(target=_baixar, daemon=True).start()


def _pos_download(dados, selecionados, estado_load):
    """Chamado na thread principal após o download terminar."""
    estado_load["ativo"] = False   # para animação
    btn_gerar.config(state="normal", text="  Gerar Gráfico  ")

    for w in frame_grafico.winfo_children(): w.destroy()

    if dados is None or dados.empty:
        tk.Label(frame_grafico, text="Nenhum dado retornado.",
                 fg="#FF5252", bg=CARD).pack(pady=20); return

    _cache["dados"]        = dados
    _cache["selecionados"] = selecionados
    _renderizar("preco")

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
root.geometry("1280x800")
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

# ── CONTEÚDO DIREITO com scroll vertical ──
frame_direito = tk.Frame(frame_main, bg=BG)
frame_direito.pack(side="left", fill="both", expand=True)

# Topo fixo (datas + botões) — FORA do scroll
frame_topo = tk.Frame(frame_direito, bg=BG)
frame_topo.pack(fill="x", padx=10, pady=(10, 6))

# Canvas de scroll para o resto
_scroll_canvas = tk.Canvas(frame_direito, bg=BG, highlightthickness=0)
_scroll_vbar   = ttk.Scrollbar(frame_direito, orient="vertical", command=_scroll_canvas.yview)
_scroll_canvas.configure(yscrollcommand=_scroll_vbar.set)
_scroll_vbar.pack(side="right", fill="y")
_scroll_canvas.pack(side="left", fill="both", expand=True)

frame_conteudo = tk.Frame(_scroll_canvas, bg=BG)
_scroll_window = _scroll_canvas.create_window((0, 0), window=frame_conteudo, anchor="nw")

def _on_conteudo_configure(e):
    _scroll_canvas.configure(scrollregion=_scroll_canvas.bbox("all"))
def _on_canvas_configure(e):
    _scroll_canvas.itemconfig(_scroll_window, width=e.width)
frame_conteudo.bind("<Configure>", _on_conteudo_configure)
_scroll_canvas.bind("<Configure>", _on_canvas_configure)
_scroll_canvas.bind_all("<MouseWheel>",
    lambda e: _scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

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

btn_gerar = tk.Button(frame_topo, text="  Gerar Gráfico  ", bg=ACCENT, fg="#000000",
                      font=("Arial", 9, "bold"), relief="flat", cursor="hand2",
                      command=gerar_grafico)
btn_gerar.pack(side="left", padx=(0, 6))

btn_exportar = tk.Button(frame_topo, text="📥 Exportar PNG", bg=BTN, fg=TXT,
                         font=("Arial", 8, "bold"), relief="flat", cursor="hand2",
                         command=exportar_png)
btn_exportar.pack(side="left", padx=(0, 14))

# Botões de alternância de modo
btn_preco = tk.Button(frame_topo, text="Preço (R$)", bg=ACCENT, fg="#000000",
                      font=("Arial", 8, "bold"), relief="flat", cursor="hand2",
                      command=lambda: _renderizar("preco"))
btn_preco.pack(side="left", padx=(0, 3))

btn_base100 = tk.Button(frame_topo, text="Base 100 (%)", bg=BTN, fg=TXT,
                        font=("Arial", 8, "bold"), relief="flat", cursor="hand2",
                        command=lambda: _renderizar("base100"))
btn_base100.pack(side="left")

# Botões média móvel
tk.Label(frame_topo, text="|", bg=BG, fg="#444").pack(side="left", padx=6)
tk.Label(frame_topo, text="MM:", bg=BG, fg="#aaaaaa",
         font=("Arial", 8)).pack(side="left", padx=(0, 3))

btn_mm20 = tk.Button(frame_topo, text="20", bg=BTN, fg=TXT,
                     font=("Arial", 8, "bold"), relief="flat", cursor="hand2",
                     command=lambda: _toggle_mm(20))
btn_mm20.pack(side="left", padx=(0, 2))

btn_mm50 = tk.Button(frame_topo, text="50", bg=BTN, fg=TXT,
                     font=("Arial", 8, "bold"), relief="flat", cursor="hand2",
                     command=lambda: _toggle_mm(50))
btn_mm50.pack(side="left")

# -- GRÁFICO --
frame_grafico = tk.Frame(frame_conteudo, bg=CARD)
frame_grafico.pack(fill="both", expand=True)

# -- TABELA DE ANÁLISE --
frame_tabela_outer = tk.Frame(frame_conteudo, bg="#0d1a24")
frame_tabela_outer.pack(fill="x", pady=(4, 0))

tk.Label(frame_tabela_outer, text="📊  Análise do Período",
         bg="#0d1a24", fg=ACCENT, font=("Arial", 9, "bold"),
         pady=4).pack(anchor="w", padx=8)

frame_tabela = tk.Frame(frame_tabela_outer, bg="#0d1a24")
frame_tabela.pack(fill="x", padx=4, pady=(0, 4))

# -- CARD DE INSIGHTS --
frame_insights_outer = tk.Frame(frame_conteudo, bg="#D500F9")
frame_insights_outer.pack(fill="x", pady=(6, 0))

frame_insights_inner = tk.Frame(frame_insights_outer, bg="#0d0d1a")
frame_insights_inner.pack(fill="both", expand=True, padx=2, pady=2)

cab_ins = tk.Frame(frame_insights_inner, bg="#150015")
cab_ins.pack(fill="x")
tk.Label(cab_ins, text="🧠  Inteligência do Período", bg="#150015", fg="#D500F9",
         font=("Arial", 10, "bold"), pady=6).pack(side="left", padx=12)

frame_insights = tk.Frame(frame_insights_inner, bg="#0d0d1a")
frame_insights.pack(fill="x", pady=(4, 8))

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