# -*- coding: utf-8 -*-
"""
JICHI — Simulación interactiva del Observatorio de Seguridad Vial
Explica, paso a paso, cómo JICHI detecta, cruza datos, recomienda,
el Comité decide y se miden resultados.

Solo usa la librería estándar de Python (tkinter). No requiere instalar nada.
Ejecutar:  python jichi_simulacion.py   (o:  py jichi_simulacion.py)
"""

import tkinter as tk
import math
import time

# ───────────────────────────── Paleta (igual que la presentación) ──────────
BG      = "#08091f"   # azul noche
PANEL   = "#12152e"   # tarjeta
PANEL2  = "#171a36"   # tarjeta interna
LINE    = "#252a45"
GOLD    = "#f5a623"
GOLD3   = "#ffcc33"
GREEN   = "#00e676"
GREEN2  = "#00c853"
RED     = "#e63946"
RED2    = "#ff6b78"
BLUE    = "#5a8bff"
WHITE   = "#ffffff"
MUTED   = "#aab6c6"
MUTED2  = "#6a7a90"

FONT = "Segoe UI"

# Intervenciones que llegan al Comité.  (nombre, costo, detalle, impacto)
# impacto = (atropellamientos %, velocidad %, visibilidad %) — suman el plan completo
OPCIONES = [
    ("Arreglar las 6 luminarias apagadas", 28000, "Restaura la iluminación nocturna del tramo", (-18, 0, 60)),
    ("Repintar el paso peatonal",            6500, "Demarcación + señal vertical reflectiva",     (-8, 0, 30)),
    ("Instalar un reductor de velocidad",   12000, "Badén antes del cruce peatonal",            (-15, -33, 0)),
]

PASOS = ["Detección", "Análisis", "Recomendación", "Decisión", "Resultado", "Sostenibilidad"]


def miles(n):
    """Formatea 46500 -> '46.500' (estilo Bolivia)."""
    return f"{int(round(n)):,}".replace(",", ".")


def pct(v):
    """Formatea porcentaje con signo bonito: -41 -> '−41%', 90 -> '+90%'."""
    if v < 0:
        return f"−{abs(v)}%"
    if v > 0:
        return f"+{v}%"
    return "0%"


class JichiApp:
    def __init__(self, root):
        self.root = root
        root.title("JICHI — Simulación del Observatorio de Seguridad Vial")
        root.configure(bg=BG)
        w, h = 1080, 740
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//3)}")
        root.minsize(1000, 680)

        self.current = 0
        self.token = 0                       # invalida animaciones al cambiar de paso
        self.aprobado_total = sum(c for _, c, _, _ in OPCIONES)
        self.opt_vars = []
        self._connectors = []
        self._flow_cv = None

        self.f_brand = (FONT, 30, "bold")
        self.f_title = (FONT, 21, "bold")
        self.f_h     = (FONT, 15, "bold")
        self.f_body  = (FONT, 11)
        self.f_small = (FONT, 9)
        self.f_label = (FONT, 9, "bold")
        self.f_num   = (FONT, 38, "bold")

        self._build_header()
        self._build_stepper()
        self.content = tk.Frame(root, bg=BG)
        self.content.pack(fill="both", expand=True, padx=26, pady=(6, 0))
        self._build_nav()

        self.steps = [self.s_deteccion, self.s_analisis, self.s_recomendacion,
                      self.s_decision, self.s_resultado, self.s_sostenibilidad]

        root.bind("<Right>", lambda e: self.next())
        root.bind("<Left>", lambda e: self.prev())
        self.show(0)

    # ───────────────────────────── estructura fija ─────────────────────────
    def _build_header(self):
        h = tk.Frame(self.root, bg=BG)
        h.pack(fill="x", padx=26, pady=(16, 2))
        tk.Label(h, text="OBSERVATORIO DE SEGURIDAD VIAL", font=(FONT, 9, "bold"),
                 fg=GOLD, bg=BG).pack()
        tk.Label(h, text="JICHI", font=self.f_brand, fg=GOLD3, bg=BG).pack()
        tk.Label(h, text="Simulación interactiva · cómo funciona, paso a paso",
                 font=self.f_small, fg=MUTED, bg=BG).pack()

    def _build_stepper(self):
        self.step_cv = tk.Canvas(self.root, height=80, bg=BG, highlightthickness=0)
        self.step_cv.pack(fill="x", padx=20, pady=(10, 2))
        self.step_cv.bind("<Configure>", lambda e: self._draw_stepper())
        self.step_cv.bind("<Button-1>", self._stepper_click)
        self.step_cv.configure(cursor="hand2")
        self._node_x = []

    def _draw_stepper(self):
        cv = self.step_cv
        cv.delete("all")
        w = cv.winfo_width()
        if w <= 1:
            w = 1040
        n = len(PASOS)
        margin = 70
        gap = (w - 2 * margin) / (n - 1) if n > 1 else 0
        ys = 28
        xs = [margin + i * gap for i in range(n)]
        self._node_x = xs
        cv.create_line(xs[0], ys, xs[-1], ys, fill=LINE, width=2)
        if self.current > 0:
            cv.create_line(xs[0], ys, xs[self.current], ys, fill=GOLD, width=3)
        for i, x in enumerate(xs):
            if i == self.current:
                cv.create_oval(x - 19, ys - 19, x + 19, ys + 19, fill="#2a2208",
                               outline=GOLD, width=2)
                cv.create_text(x, ys, text=str(i + 1), fill=GOLD3, font=(FONT, 12, "bold"))
                tcol = WHITE
            elif i < self.current:
                cv.create_oval(x - 16, ys - 16, x + 16, ys + 16, fill=PANEL,
                               outline=GREEN, width=2)
                cv.create_text(x, ys, text="✓", fill=GREEN, font=(FONT, 12, "bold"))
                tcol = MUTED
            else:
                cv.create_oval(x - 16, ys - 16, x + 16, ys + 16, fill=PANEL,
                               outline=LINE, width=2)
                cv.create_text(x, ys, text=str(i + 1), fill=MUTED2, font=(FONT, 12, "bold"))
                tcol = MUTED2
            cv.create_text(x, ys + 36, text=PASOS[i].upper(), fill=tcol, font=(FONT, 8, "bold"))

    def _stepper_click(self, e):
        for i, x in enumerate(self._node_x):
            if abs(e.x - x) <= 26:
                self.show(i)
                return

    def _build_nav(self):
        n = tk.Frame(self.root, bg=BG)
        n.pack(fill="x", padx=26, pady=14)
        self.prev_btn = self._btn(n, "←  Anterior", self.prev, primary=False)
        self.prev_btn.pack(side="left")
        self.counter = tk.Label(n, text="", font=self.f_small, fg=MUTED2, bg=BG)
        self.counter.pack(side="left", expand=True)
        self.next_btn = self._btn(n, "Siguiente  →", self.next, primary=True)
        self.next_btn.pack(side="right")

    def _btn(self, parent, text, cmd, primary=True):
        if primary:
            base, hov, fg = GOLD, GOLD3, "#1a1000"
        else:
            base, hov, fg = PANEL, PANEL2, WHITE
        b = tk.Button(parent, text=text, command=cmd, font=(FONT, 11, "bold"),
                      fg=fg, bg=base, activebackground=hov, activeforeground=fg,
                      relief="flat", bd=0, padx=22, pady=10, cursor="hand2")
        self._hover(b, base, hov)
        return b

    def _hover(self, widget, base, hov):
        widget.bind("<Enter>", lambda e: widget.config(bg=hov) if widget["state"] != "disabled" else None)
        widget.bind("<Leave>", lambda e: widget.config(bg=base) if widget["state"] != "disabled" else None)

    # ───────────────────────────── navegación ──────────────────────────────
    def show(self, i):
        self.current = i
        self.token += 1
        self._connectors = []
        for w in self.content.winfo_children():
            w.destroy()
        self._draw_stepper()
        self.prev_btn.config(state="normal" if i > 0 else "disabled")
        last = (i == len(PASOS) - 1)
        self.next_btn.config(state="normal", text="↺  Reiniciar" if last else "Siguiente  →")
        self.counter.config(text=f"Paso {i + 1} de {len(PASOS)}   ·   usa  ←  →")
        self.steps[i]()

    def next(self):
        self.show(0 if self.current >= len(PASOS) - 1 else self.current + 1)

    def prev(self):
        if self.current > 0:
            self.show(self.current - 1)

    # ───────────────────────────── helpers de UI ───────────────────────────
    def card(self, parent, accent=LINE):
        return tk.Frame(parent, bg=PANEL, highlightbackground=accent,
                        highlightthickness=1, bd=0)

    def head(self, accent, label, title, intro):
        tk.Label(self.content, text=label.upper(), font=(FONT, 9, "bold"),
                 fg=accent, bg=BG).pack(anchor="w")
        tk.Label(self.content, text=title, font=self.f_title, fg=WHITE, bg=BG,
                 justify="left").pack(anchor="w", pady=(2, 2))
        tk.Label(self.content, text=intro, font=self.f_body, fg=MUTED, bg=BG,
                 justify="left", wraplength=1000).pack(anchor="w", pady=(0, 10))

    def card_label(self, parent, text):
        tk.Label(parent, text=text.upper(), font=self.f_label, fg=MUTED2,
                 bg=PANEL).pack(anchor="w", padx=16, pady=(14, 6))

    def round_rect(self, cv, x1, y1, x2, y2, r, fill, outline, width=1):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return cv.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=width)

    # ───────────────────────────── animaciones ─────────────────────────────
    def animate(self, dur, on_frame, on_done=None):
        token = self.token
        start = time.time()

        def tick():
            if token != self.token:
                return
            t = min(1.0, (time.time() - start) / dur)
            e = 1 - (1 - t) ** 3
            try:
                on_frame(e)
            except tk.TclError:
                return
            if t < 1:
                self.root.after(16, tick)
            elif on_done:
                try:
                    on_done()
                except tk.TclError:
                    pass
        tick()

    def count(self, label, target, dur=1.1, prefix="", suffix="", sep=False):
        def frame(e):
            v = target * e
            label.config(text=prefix + (miles(v) if sep else str(int(round(v)))) + suffix)
        final = prefix + (miles(target) if sep else str(int(round(target)))) + suffix
        self.animate(dur, frame, on_done=lambda: label.config(text=final))

    # ───────────────────────────── medidor (gauge) ─────────────────────────
    def gauge(self, parent, value, maxv, limit, color):
        cv = tk.Canvas(parent, width=320, height=205, bg=PANEL, highlightthickness=0)
        cx, cy, r = 160, 132, 100
        bbox = (cx - r, cy - r, cx + r, cy + r)
        cv.create_arc(*bbox, start=180, extent=-180, style="arc", width=15, outline="#2a3150")

        # marcas menores
        for i in range(7):
            f = i / 6
            th = math.radians(180 - f * 180)
            x1 = cx + (r + 2) * math.cos(th); y1 = cy - (r + 2) * math.sin(th)
            x2 = cx + (r - 14) * math.cos(th); y2 = cy - (r - 14) * math.sin(th)
            cv.create_line(x1, y1, x2, y2, fill="#3a4566", width=2)
        # marca de límite (dorada)
        th = math.radians(180 - (limit / maxv) * 180)
        x1 = cx + (r + 6) * math.cos(th); y1 = cy - (r + 6) * math.sin(th)
        x2 = cx + (r - 20) * math.cos(th); y2 = cy - (r - 20) * math.sin(th)
        cv.create_line(x1, y1, x2, y2, fill=GOLD, width=3)
        lx = cx + (r + 20) * math.cos(th); ly = cy - (r + 20) * math.sin(th)
        cv.create_text(lx, ly, text=str(limit), fill=GOLD3, font=(FONT, 9, "bold"))

        def render(e):
            cv.delete("dyn")
            cur = value * e
            f = cur / maxv
            cv.create_arc(*bbox, start=180, extent=-180 * f, style="arc",
                          width=15, outline=color, tags="dyn")
            ang = math.radians(180 - f * 180)
            nx = cx + (r - 22) * math.cos(ang); ny = cy - (r - 22) * math.sin(ang)
            cv.create_line(cx, cy, nx, ny, fill=WHITE, width=4, capstyle="round", tags="dyn")
            cv.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#15173a", outline=WHITE, width=2, tags="dyn")
            cv.create_text(cx, cy + 36, text=str(int(round(cur))), fill=color, font=self.f_num, tags="dyn")
            cv.create_text(cx, cy + 66, text="km/h", fill=MUTED, font=(FONT, 9, "bold"), tags="dyn")

        render(0)
        self.animate(1.3, render)
        return cv

    # ───────────────────────────── dona (donut) ────────────────────────────
    def donut(self, parent, parte, total, color, centro_txt):
        cv = tk.Canvas(parent, width=150, height=150, bg=PANEL, highlightthickness=0)
        cx, cy, r = 75, 75, 56
        bb = (cx - r, cy - r, cx + r, cy + r)
        cv.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#2a3150", width=15)
        full = parte / total * 360

        def render(e):
            cv.delete("dyn")
            cv.create_arc(*bb, start=90, extent=-full * e, style="arc",
                          width=15, outline=color, tags="dyn")
        render(0)
        self.animate(1.2, render)
        cv.create_text(cx, cy - 6, text=centro_txt, fill=WHITE, font=(FONT, 26, "bold"))
        cv.create_text(cx, cy + 18, text="ATROPELLOS", fill=MUTED2, font=(FONT, 7, "bold"))
        return cv

    # ───────────────────────────── flujo / cruce de fuentes ────────────────
    def quad_points(self, p0, p1, p2, n=44):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((x, y))
        return pts

    def build_flow(self, cv):
        cv.delete("all")
        self._flow_cv = cv
        hubx, huby = 450, 140
        sources = [("SENSORES", "78 km/h · límite 40", BLUE, 46),
                   ("POLICÍA", "23 atropellos · 14 noche", RED2, 140),
                   ("MUNICIPIO", "2/8 luminarias · sin pintura", GOLD3, 234)]
        conns = []
        for name, metric, col, cy in sources:
            self.round_rect(cv, 10, cy - 30, 190, cy + 30, 12, PANEL2, col, 1)
            cv.create_text(100, cy - 8, text=name, fill=WHITE, font=(FONT, 10, "bold"))
            cv.create_text(100, cy + 12, text=metric, fill=MUTED, font=(FONT, 8))
            pts = self.quad_points((190, cy), ((190 + 392) / 2, cy), (392, huby))
            cv.create_line(*[c for p in pts for c in p], smooth=True, fill=col, width=1, dash=(5, 4))
            cv.create_oval(186, cy - 4, 194, cy + 4, fill=col, outline="")
            dots = [cv.create_oval(0, 0, 0, 0, fill=col, outline="") for _ in range(2)]
            conns.append({"pts": pts, "dots": dots, "offs": [0, 22]})

        # hub
        cv.create_oval(hubx - 76, huby - 76, hubx + 76, huby + 76, outline="#4a3a10", width=1)
        cv.create_oval(hubx - 58, huby - 58, hubx + 58, huby + 58, fill="#1a1604", outline=GOLD, width=2)
        cv.create_text(hubx, huby - 8, text="JICHI", fill=GOLD3, font=(FONT, 18, "bold"))
        cv.create_text(hubx, huby + 14, text="CRUZA LOS DATOS", fill=GOLD, font=(FONT, 7, "bold"))

        # salida
        self.round_rect(cv, 700, 108, 890, 172, 12, PANEL2, GREEN, 1)
        cv.create_text(795, 128, text="CAUSA HALLADA", fill=GREEN, font=(FONT, 10, "bold"))
        cv.create_text(795, 150, text="Tramo sin luz + sin paso peatonal", fill=MUTED, font=(FONT, 8))
        pts = self.quad_points((508, huby), (604, huby), (700, huby))
        cv.create_line(*[c for p in pts for c in p], smooth=True, fill=GREEN, width=1, dash=(5, 4))
        dots = [cv.create_oval(0, 0, 0, 0, fill=GREEN, outline="") for _ in range(2)]
        conns.append({"pts": pts, "dots": dots, "offs": [0, 20]})

        self._connectors = conns
        self._flow_t = 0
        self._animate_flow(self.token)

    def _animate_flow(self, token):
        if token != self.token or self._flow_cv is None:
            return
        self._flow_t += 1
        try:
            for c in self._connectors:
                L = len(c["pts"])
                for it, off in zip(c["dots"], c["offs"]):
                    x, y = c["pts"][(self._flow_t + off) % L]
                    self._flow_cv.coords(it, x - 3, y - 3, x + 3, y + 3)
        except tk.TclError:
            return
        self.root.after(45, lambda: self._animate_flow(token))

    # ═════════════════════════════ PASOS ═══════════════════════════════════
    def s_deteccion(self):
        self.head(RED, "Paso 1 · Detección",
                  "Los sensores detectan algo fuera de lo normal",
                  "Cuarto Anillo, entre la Av. Banzer y la Radial 17½. Los autos "
                  "circulan muy por encima del límite y, al mismo tiempo, la "
                  "Policía acumula atropellamientos en esa misma intersección.")

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True)

        c1 = self.card(row, RED); c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(c1, "Sensor de velocidad · Cuarto Anillo")
        self.gauge(c1, 78, 120, 40, RED2).pack(pady=(0, 2))
        tk.Label(c1, text="Promedio detectado · límite 40 km/h  (+95%)",
                 font=self.f_small, fg=MUTED, bg=PANEL).pack(pady=(0, 14))

        c2 = self.card(row, RED); c2.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(c2, "Registros de la Policía · 6 meses")
        box = tk.Frame(c2, bg=PANEL); box.pack(expand=True)
        self.donut(box, 14, 23, RED2, "23").grid(row=0, column=0, padx=(10, 18), pady=10)
        leg = tk.Frame(box, bg=PANEL); leg.grid(row=0, column=1)
        for sw, val, txt in [(RED2, "14", "de noche"), ("#2a3150", "9", "de día")]:
            r = tk.Frame(leg, bg=PANEL); r.pack(anchor="w", pady=6)
            tk.Canvas(r, width=12, height=12, bg=sw, highlightthickness=0).pack(side="left", padx=(0, 8))
            tk.Label(r, text=val, font=(FONT, 17, "bold"), fg=WHITE, bg=PANEL).pack(side="left")
            tk.Label(r, text=" " + txt, font=self.f_body, fg=MUTED, bg=PANEL).pack(side="left")
        tk.Label(leg, text="61% ocurre en horario nocturno", font=self.f_small,
                 fg=MUTED2, bg=PANEL).pack(anchor="w", pady=(4, 0))

        al = self.card(self.content, RED); al.pack(fill="x", pady=(12, 4))
        tk.Label(al, text="⚠  ALERTA AUTOMÁTICA GENERADA POR JICHI", font=self.f_h,
                 fg=RED2, bg=PANEL).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(al, text="Exceso de velocidad sostenido + alta siniestralidad nocturna en el mismo punto.",
                 font=self.f_body, fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(0, 12))

    def s_analisis(self):
        self.head(BLUE, "Paso 2 · Análisis",
                  "JICHI cruza las fuentes de datos",
                  "JICHI junta lo que miden los sensores con lo que registra la "
                  "Policía y lanza la alerta. El equipo revisa los datos del "
                  "Municipio y la causa se hace evidente.")

        flow = self.card(self.content, BLUE); flow.pack(fill="x")
        self.card_label(flow, "Cruce de fuentes · tres bases de datos conectadas")
        fcv = tk.Canvas(flow, width=900, height=280, bg=PANEL, highlightthickness=0)
        fcv.pack(pady=(0, 12))
        self.build_flow(fcv)

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True, pady=(12, 0))
        cl = self.card(row, LINE); cl.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(cl, "Luminarias del tramo · 2 de 8 operativas")
        lc = tk.Canvas(cl, width=360, height=70, bg=PANEL, highlightthickness=0)
        lc.pack(pady=(0, 6))
        for i in range(8):
            x = 30 + i * 42
            on = i in (1, 5)
            if on:
                lc.create_oval(x - 16, 4, x + 16, 38, outline="", fill="#3a2e08")
            lc.create_oval(x - 11, 9, x + 11, 31, fill=GOLD3 if on else "#2a3150", outline="")
            lc.create_line(x, 31, x, 48, fill="#3a4566", width=2)
            lc.create_text(x, 60, text="ON" if on else "off",
                           fill=GOLD3 if on else MUTED2, font=(FONT, 7, "bold"))
        tk.Label(cl, text="75% del corredor sin iluminación de noche",
                 font=self.f_small, fg=MUTED, bg=PANEL).pack(pady=(0, 12))

        cr = self.card(row, LINE); cr.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(cr, "Paso peatonal · sin pintura")
        cc = tk.Canvas(cr, width=300, height=70, bg=PANEL, highlightthickness=0)
        cc.pack(pady=(0, 6))
        for i in range(6):
            x = 60 + i * 32
            cc.create_rectangle(x, 12, x + 18, 58, fill="#1c2138", outline="")
        tk.Label(cr, text="Demarcación borrada · sin visibilidad nocturna",
                 font=self.f_small, fg=MUTED, bg=PANEL).pack(pady=(0, 12))

    def s_recomendacion(self):
        self.head(GOLD, "Paso 3 · Recomendación",
                  "El informe llega al Comité con opciones y costos",
                  "JICHI propone intervenciones priorizadas. Actúa como el "
                  "Comité: marca o desmarca opciones y observa cómo cambian el "
                  "costo total y el impacto proyectado en tiempo real.")

        wrap = tk.Frame(self.content, bg=BG); wrap.pack(fill="both", expand=True)

        c = self.card(wrap, GOLD); c.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(c, "Opciones de intervención (marca las que apruebas)")
        self.opt_vars = []
        total_lbl = tk.Label(c, text="", font=(FONT, 30, "bold"), fg=GOLD3, bg=PANEL)
        impact_lbls = {}

        def recompute():
            t = acc = spd = vis = 0
            for var, (_, cost, _, (a, s, v)) in zip(self.opt_vars, OPCIONES):
                if var.get():
                    t += cost; acc += a; spd += s; vis += v
            self.aprobado_total = t
            total_lbl.config(text="Bs " + miles(t))
            impact_lbls["acc"].config(text=pct(acc))
            impact_lbls["spd"].config(text=pct(spd))
            impact_lbls["vis"].config(text=pct(vis))

        for nombre, costo, detalle, _ in OPCIONES:
            var = tk.BooleanVar(value=True)
            self.opt_vars.append(var)
            b = tk.Frame(c, bg=PANEL2); b.pack(fill="x", padx=14, pady=5)
            cb = tk.Checkbutton(b, variable=var, command=recompute, bg=PANEL2,
                                activebackground=PANEL2, selectcolor=PANEL,
                                highlightthickness=0, bd=0, cursor="hand2")
            cb.pack(side="left", padx=(8, 4))
            txt = tk.Frame(b, bg=PANEL2); txt.pack(side="left", fill="x", expand=True, pady=8)
            tk.Label(txt, text=nombre, font=(FONT, 11, "bold"), fg=WHITE, bg=PANEL2,
                     anchor="w").pack(anchor="w")
            tk.Label(txt, text=detalle, font=self.f_small, fg=MUTED, bg=PANEL2,
                     anchor="w").pack(anchor="w")
            tk.Label(b, text="Bs " + miles(costo), font=(FONT, 12, "bold"),
                     fg=GOLD3, bg=PANEL2).pack(side="right", padx=14)

        tk.Frame(c, bg=LINE, height=1).pack(fill="x", padx=14, pady=(8, 0))
        tk.Label(c, text="COSTO TOTAL DE LO SELECCIONADO", font=self.f_label,
                 fg=MUTED2, bg=PANEL).pack(pady=(12, 0))
        total_lbl.pack(pady=(2, 16))

        c2 = self.card(wrap, GOLD); c2.pack(side="left", fill="y", padx=(8, 0))
        self.card_label(c2, "Impacto proyectado (en vivo)")
        for key, nombre in [("acc", "Atropellamientos"), ("spd", "Velocidad"),
                            ("vis", "Visibilidad nocturna")]:
            f = tk.Frame(c2, bg=PANEL); f.pack(fill="x", padx=16, pady=8)
            tk.Label(f, text=nombre, font=self.f_body, fg=MUTED, bg=PANEL).pack(side="left")
            lbl = tk.Label(f, text="0%", font=(FONT, 16, "bold"), fg=GREEN, bg=PANEL)
            lbl.pack(side="right")
            impact_lbls[key] = lbl
        tk.Label(c2, text="Plan completo de referencia:\nBs 46.500  ·  −41% atropellos",
                 font=self.f_small, fg=MUTED2, bg=PANEL, justify="left").pack(anchor="w", padx=16, pady=(20, 16))

        recompute()

    def s_decision(self):
        self.head(GREEN, "Paso 4 · Decisión",
                  "El Comité aprueba la intervención",
                  "El Comité revisa la evidencia y aprueba el plan. Se define "
                  "responsable y plazo. Pulsa APROBAR para emitir la orden de ejecución.")

        c = self.card(self.content, GREEN); c.pack(fill="x")
        self.card_label(c, "Comité de Seguridad Vial · resolución")
        tk.Label(c, text="PRESUPUESTO APROBADO", font=self.f_label, fg=MUTED2, bg=PANEL).pack(pady=(6, 0))
        tk.Label(c, text="Bs " + miles(self.aprobado_total), font=(FONT, 56, "bold"),
                 fg=GREEN, bg=PANEL).pack()

        info = tk.Frame(c, bg=PANEL); info.pack(pady=10)
        for k, v in [("RESPONSABLE", "Municipio"), ("PLAZO", "30 días"), ("SEGUIMIENTO", "JICHI")]:
            cell = tk.Frame(info, bg=PANEL); cell.pack(side="left", padx=26)
            tk.Label(cell, text=k, font=self.f_label, fg=MUTED2, bg=PANEL).pack()
            tk.Label(cell, text=v, font=self.f_h, fg=WHITE, bg=PANEL).pack()

        estado = tk.Label(c, text="", font=(FONT, 16, "bold"), fg=GREEN, bg=PANEL)
        estado.pack(pady=(2, 2))
        self.next_btn.config(state="disabled")

        def aprobar():
            estado.config(text="✓  APROBADO — ORDEN DE EJECUCIÓN EMITIDA")
            ap.config(state="disabled", text="APROBADO", bg=PANEL2, fg=GREEN)
            self.next_btn.config(state="normal")

        ap = tk.Button(c, text="✔  APROBAR INTERVENCIÓN", command=aprobar,
                       font=(FONT, 12, "bold"), fg="#04130b", bg=GREEN,
                       activebackground=GREEN2, relief="flat", bd=0, padx=26,
                       pady=12, cursor="hand2")
        self._hover(ap, GREEN, GREEN2)
        ap.pack(pady=(6, 18))

    def s_resultado(self):
        self.head(GREEN, "Paso 5 · Resultado",
                  "Cuatro meses después, JICHI mide",
                  "No es un reporte: es una decisión ejecutada y con resultados "
                  "medibles en la misma intersección.")

        hero = self.card(self.content, GREEN); hero.pack(fill="x")
        tk.Label(hero, text="CUATRO MESES DESPUÉS DE LA INTERVENCIÓN", font=self.f_label,
                 fg=GREEN2, bg=PANEL).pack(pady=(14, 0))
        big = tk.Label(hero, text="−0%", font=(FONT, 68, "bold"), fg=GREEN, bg=PANEL)
        big.pack()
        tk.Label(hero, text="menos atropellamientos en el corredor", font=self.f_h,
                 fg=WHITE, bg=PANEL).pack(pady=(0, 16))
        self.count(big, 41, dur=1.4, prefix="−", suffix="%")

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True, pady=(12, 0))
        g = self.card(row, GREEN); g.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(g, "Velocidad promedio · 78 → 52 km/h")
        self.gauge(g, 52, 120, 40, GREEN).pack(pady=(0, 14))

        comp = self.card(row, GREEN); comp.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(comp, "Antes  →  después")
        grid = tk.Frame(comp, bg=PANEL); grid.pack(padx=16, pady=(0, 14), fill="x")
        datos = [("Velocidad promedio", "78 km/h", "52 km/h"),
                 ("Atropellamientos", "23", "14"),
                 ("Luminarias activas", "2/8", "8/8"),
                 ("Paso peatonal", "sin pintura", "demarcado")]
        for r, (etq, antes, desp) in enumerate(datos):
            tk.Label(grid, text=etq, font=self.f_small, fg=MUTED, bg=PANEL,
                     anchor="w").grid(row=r, column=0, sticky="w", pady=7)
            tk.Label(grid, text=antes, font=(FONT, 12, "bold"), fg=RED2,
                     bg=PANEL).grid(row=r, column=1, padx=14)
            tk.Label(grid, text="→", font=self.f_body, fg=MUTED2, bg=PANEL).grid(row=r, column=2)
            tk.Label(grid, text=desp, font=(FONT, 12, "bold"), fg=GREEN,
                     bg=PANEL).grid(row=r, column=3, padx=14)
        grid.columnconfigure(0, weight=1)

    def s_sostenibilidad(self):
        self.head(GOLD, "Paso 6 · Por qué funciona aquí",
                  "Una decisión ejecutada, no un reporte",
                  "JICHI está diseñado para seguir funcionando sin importar qué "
                  "gobierno esté en turno.")

        c = self.card(self.content, GOLD); c.pack(fill="both", expand=True)
        self.card_label(c, "Garantías del modelo")
        for txt in ["Los acuerdos se firman antes de arrancar.",
                    "Plataforma de código abierto y servidores en Bolivia.",
                    "La ciudad se queda con todo al terminar.",
                    "Ordenanza municipal en gestión para darle continuidad."]:
            f = tk.Frame(c, bg=PANEL); f.pack(fill="x", padx=18, pady=6)
            tk.Label(f, text="✓", font=(FONT, 13, "bold"), fg=GREEN, bg=PANEL).pack(side="left", padx=(0, 10))
            tk.Label(f, text=txt, font=self.f_body, fg=WHITE, bg=PANEL).pack(side="left")

        box = tk.Frame(c, bg=PANEL2); box.pack(fill="x", padx=18, pady=(16, 18))
        tk.Label(box, text="COSTO DE OPERACIÓN ANUAL", font=self.f_label, fg=MUTED2, bg=PANEL2).pack(pady=(14, 0))
        amt = tk.Label(box, text="Bs 0", font=(FONT, 40, "bold"), fg=GOLD3, bg=PANEL2)
        amt.pack()
        tk.Label(box, text="Una fracción mínima del presupuesto municipal",
                 font=self.f_small, fg=MUTED, bg=PANEL2).pack(pady=(0, 14))
        self.count(amt, 1080000, dur=1.5, prefix="Bs ", sep=True)


if __name__ == "__main__":
    root = tk.Tk()
    JichiApp(root)
    root.mainloop()
