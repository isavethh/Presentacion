# -*- coding: utf-8 -*-
"""
JICHI — Simulación interactiva del Observatorio de Seguridad Vial
Explica, paso a paso, cómo JICHI detecta, cruza datos, recomienda,
el Comité decide y se miden resultados.

El contenido ESCALA con el tamaño de la ventana (incluida pantalla completa):
fuentes, medidores y diagramas crecen de forma proporcional.

Solo usa la librería estándar de Python (tkinter). No requiere instalar nada.
Ejecutar:  python jichi_simulacion.py   (o:  py jichi_simulacion.py)
"""

import tkinter as tk
import math
import time

# ───────────────────────────── Paleta (igual que la presentación) ──────────
BG      = "#08091f"
PANEL   = "#12152e"
PANEL2  = "#171a36"
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

# Tamaños base de referencia (a escala 1.0)
BASE_W = 1040.0
BASE_H = 500.0

# Intervenciones. (nombre, costo, detalle, impacto=(atropellos%, velocidad%, visibilidad%))
OPCIONES = [
    ("Arreglar las 6 luminarias apagadas", 28000, "Restaura la iluminación nocturna del tramo", (-18, 0, 60)),
    ("Repintar el paso peatonal",            6500, "Demarcación + señal vertical reflectiva",     (-8, 0, 30)),
    ("Instalar un reductor de velocidad",   12000, "Badén antes del cruce peatonal",            (-15, -33, 0)),
]

PASOS = ["Detección", "Análisis", "Recomendación", "Decisión", "Resultado", "Sostenibilidad"]


def miles(n):
    return f"{int(round(n)):,}".replace(",", ".")


def pct(v):
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
        w, h = 1100, 740
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//4)}")
        root.minsize(900, 600)

        self.current = 0
        self.token = 0
        self.scale = 1.0
        self._resize_job = None
        self.aprobado_total = sum(c for _, c, _, _ in OPCIONES)
        self.opt_vars = []
        self._connectors = []
        self._flow_cv = None

        self._build_header()
        self._build_stepper()
        self._build_nav()
        self.area = tk.Frame(root, bg=BG)
        self.area.pack(fill="both", expand=True)
        self.content = tk.Frame(self.area, bg=BG)
        self.content.place(relx=0.5, rely=0.5, anchor="center", width=int(BASE_W))
        self.area.bind("<Configure>", self._on_area_resize)

        self.steps = [self.s_deteccion, self.s_analisis, self.s_recomendacion,
                      self.s_decision, self.s_resultado, self.s_sostenibilidad]

        root.bind("<Right>", lambda e: self.next())
        root.bind("<Left>", lambda e: self.prev())
        root.bind("<F11>", lambda e: self._toggle_fs())
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
        self.show(0)

    # ───────────────────────────── escala ──────────────────────────────────
    def F(self, size, bold=True):
        return (FONT, max(7, int(round(size * self.scale))), "bold" if bold else "normal")

    def S(self, v):
        return int(round(v * self.scale))

    def _toggle_fs(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def _on_area_resize(self, e):
        s = min(e.width / BASE_W, e.height / BASE_H)
        s = max(0.8, min(2.4, s))
        self.content.place_configure(width=int(BASE_W * s))
        if abs(s - self.scale) >= 0.015:
            self.scale = s
            if self._resize_job:
                self.root.after_cancel(self._resize_job)
            self._resize_job = self.root.after(70, lambda: self.show(self.current))

    # ───────────────────────────── estructura fija ─────────────────────────
    def _build_header(self):
        h = tk.Frame(self.root, bg=BG)
        h.pack(fill="x", padx=26, pady=(10, 0))
        tk.Label(h, text="OBSERVATORIO DE SEGURIDAD VIAL", font=(FONT, 8, "bold"),
                 fg=GOLD, bg=BG).pack()
        tk.Label(h, text="JICHI", font=(FONT, 25, "bold"), fg=GOLD3, bg=BG).pack()

    def _build_stepper(self):
        self.step_cv = tk.Canvas(self.root, height=68, bg=BG, highlightthickness=0, cursor="hand2")
        self.step_cv.pack(fill="x", padx=20, pady=(6, 0))
        self.step_cv.bind("<Configure>", lambda e: self._draw_stepper())
        self.step_cv.bind("<Button-1>", self._stepper_click)
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
        ys = 23
        xs = [margin + i * gap for i in range(n)]
        self._node_x = xs
        cv.create_line(xs[0], ys, xs[-1], ys, fill=LINE, width=2)
        if self.current > 0:
            cv.create_line(xs[0], ys, xs[self.current], ys, fill=GOLD, width=3)
        for i, x in enumerate(xs):
            if i == self.current:
                cv.create_oval(x - 19, ys - 19, x + 19, ys + 19, fill="#2a2208", outline=GOLD, width=2)
                cv.create_text(x, ys, text=str(i + 1), fill=GOLD3, font=(FONT, 12, "bold"))
                tcol = WHITE
            elif i < self.current:
                cv.create_oval(x - 16, ys - 16, x + 16, ys + 16, fill=PANEL, outline=GREEN, width=2)
                cv.create_text(x, ys, text="✓", fill=GREEN, font=(FONT, 12, "bold"))
                tcol = MUTED
            else:
                cv.create_oval(x - 16, ys - 16, x + 16, ys + 16, fill=PANEL, outline=LINE, width=2)
                cv.create_text(x, ys, text=str(i + 1), fill=MUTED2, font=(FONT, 12, "bold"))
                tcol = MUTED2
            cv.create_text(x, ys + 34, text=PASOS[i].upper(), fill=tcol, font=(FONT, 8, "bold"))

    def _stepper_click(self, e):
        for i, x in enumerate(self._node_x):
            if abs(e.x - x) <= 26:
                self.show(i)
                return

    def _build_nav(self):
        n = tk.Frame(self.root, bg=BG)
        n.pack(side="bottom", fill="x", padx=26, pady=12)
        self.prev_btn = self._btn(n, "←  Anterior", self.prev, primary=False)
        self.prev_btn.pack(side="left")
        self.counter = tk.Label(n, text="", font=(FONT, 9), fg=MUTED2, bg=BG)
        self.counter.pack(side="left", expand=True)
        self.next_btn = self._btn(n, "Siguiente  →", self.next, primary=True)
        self.next_btn.pack(side="right")

    def _btn(self, parent, text, cmd, primary=True):
        base, hov, fg = (GOLD, GOLD3, "#1a1000") if primary else (PANEL, PANEL2, WHITE)
        b = tk.Button(parent, text=text, command=cmd, font=(FONT, 11, "bold"),
                      fg=fg, bg=base, activebackground=hov, activeforeground=fg,
                      relief="flat", bd=0, padx=22, pady=10, cursor="hand2")
        self._hover(b, base, hov)
        return b

    def _hover(self, widget, base, hov):
        widget.bind("<Enter>", lambda e: widget.config(bg=hov) if str(widget["state"]) != "disabled" else None)
        widget.bind("<Leave>", lambda e: widget.config(bg=base) if str(widget["state"]) != "disabled" else None)

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
        self.counter.config(text=f"Paso {i + 1} de {len(PASOS)}   ·   ←  →   ·   F11 pantalla completa")
        self.steps[i]()

    def next(self):
        self.show(0 if self.current >= len(PASOS) - 1 else self.current + 1)

    def prev(self):
        if self.current > 0:
            self.show(self.current - 1)

    # ───────────────────────────── helpers de UI ───────────────────────────
    def card(self, parent, accent=LINE):
        return tk.Frame(parent, bg=PANEL, highlightbackground=accent, highlightthickness=1, bd=0)

    def head(self, accent, label, title, intro):
        tk.Label(self.content, text=label.upper(), font=self.F(9), fg=accent, bg=BG).pack(anchor="w")
        tk.Label(self.content, text=title, font=self.F(21), fg=WHITE, bg=BG,
                 justify="left").pack(anchor="w", pady=(self.S(2), self.S(2)))
        tk.Label(self.content, text=intro, font=self.F(11, False), fg=MUTED, bg=BG,
                 justify="left", wraplength=int(BASE_W * self.scale) - 40).pack(anchor="w", pady=(0, self.S(10)))

    def card_label(self, parent, text):
        tk.Label(parent, text=text.upper(), font=self.F(9), fg=MUTED2,
                 bg=PANEL).pack(anchor="w", padx=self.S(16), pady=(self.S(14), self.S(6)))

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

    # ───────────────────────────── medidor ─────────────────────────────────
    def gauge(self, parent, value, maxv, limit, color):
        S = self.S
        cv = tk.Canvas(parent, width=S(300), height=S(184), bg=PANEL, highlightthickness=0)
        cx, cy, r = S(150), S(120), S(88)
        aw = max(8, S(15))
        bbox = (cx - r, cy - r, cx + r, cy + r)
        cv.create_arc(*bbox, start=180, extent=-180, style="arc", width=aw, outline="#2a3150")
        for i in range(7):
            f = i / 6
            th = math.radians(180 - f * 180)
            cv.create_line(cx + (r + S(2)) * math.cos(th), cy - (r + S(2)) * math.sin(th),
                           cx + (r - S(14)) * math.cos(th), cy - (r - S(14)) * math.sin(th),
                           fill="#3a4566", width=2)
        th = math.radians(180 - (limit / maxv) * 180)
        cv.create_line(cx + (r + S(6)) * math.cos(th), cy - (r + S(6)) * math.sin(th),
                       cx + (r - S(20)) * math.cos(th), cy - (r - S(20)) * math.sin(th),
                       fill=GOLD, width=3)
        cv.create_text(cx + (r + S(20)) * math.cos(th), cy - (r + S(20)) * math.sin(th),
                       text=str(limit), fill=GOLD3, font=self.F(9))

        def render(e):
            cv.delete("dyn")
            cur = value * e
            f = cur / maxv
            cv.create_arc(*bbox, start=180, extent=-180 * f, style="arc", width=aw, outline=color, tags="dyn")
            ang = math.radians(180 - f * 180)
            cv.create_line(cx, cy, cx + (r - S(22)) * math.cos(ang), cy - (r - S(22)) * math.sin(ang),
                           fill=WHITE, width=max(3, S(4)), capstyle="round", tags="dyn")
            cv.create_oval(cx - S(8), cy - S(8), cx + S(8), cy + S(8), fill="#15173a", outline=WHITE, width=2, tags="dyn")
            cv.create_text(cx, cy + S(28), text=str(int(round(cur))), fill=color, font=self.F(33), tags="dyn")
            cv.create_text(cx, cy + S(52), text="km/h", fill=MUTED, font=self.F(9), tags="dyn")

        render(0)
        self.animate(1.3, render)
        return cv

    # ───────────────────────────── dona ────────────────────────────────────
    def donut(self, parent, parte, total, color, centro_txt):
        S = self.S
        D = S(128)
        cv = tk.Canvas(parent, width=D, height=D, bg=PANEL, highlightthickness=0)
        cx, cy, r = S(64), S(64), S(48)
        wdt = max(7, S(13))
        bb = (cx - r, cy - r, cx + r, cy + r)
        cv.create_oval(*bb, outline="#2a3150", width=wdt)
        full = parte / total * 360

        def render(e):
            cv.delete("dyn")
            cv.create_arc(*bb, start=90, extent=-full * e, style="arc", width=wdt, outline=color, tags="dyn")
        render(0)
        self.animate(1.2, render)
        cv.create_text(cx, cy - S(5), text=centro_txt, fill=WHITE, font=self.F(22))
        cv.create_text(cx, cy + S(16), text="ATROPELLOS", fill=MUTED2, font=self.F(7))
        return cv

    # ───────────────────────────── cruce de fuentes ────────────────────────
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
        S = self.S
        hubx, huby, r = 440, 100, 44
        hl, hr = hubx - r, hubx + r
        sources = [("SENSORES", "78 km/h · límite 40", BLUE, 32),
                   ("POLICÍA", "23 atropellos · 14 noche", RED2, 100),
                   ("MUNICIPIO", "2/8 luminarias · sin pintura", GOLD3, 168)]
        conns = []
        for name, metric, col, cy in sources:
            self.round_rect(cv, S(6), S(cy - 24), S(176), S(cy + 24), S(11), PANEL2, col, 1)
            cv.create_text(S(91), S(cy - 7), text=name, fill=WHITE, font=self.F(10))
            cv.create_text(S(91), S(cy + 11), text=metric, fill=MUTED, font=self.F(8, False))
            pts = self.quad_points((S(176), S(cy)), (S((176 + hl) / 2), S(cy)), (S(hl), S(huby)))
            cv.create_line(*[c for p in pts for c in p], smooth=True, fill=col, width=1, dash=(5, 4))
            cv.create_oval(S(172), S(cy - 4), S(180), S(cy + 4), fill=col, outline="")
            dots = [cv.create_oval(0, 0, 0, 0, fill=col, outline="") for _ in range(2)]
            conns.append({"pts": pts, "dots": dots, "offs": [0, 22]})

        cv.create_oval(S(hubx - 60), S(huby - 60), S(hubx + 60), S(huby + 60), outline="#4a3a10", width=1)
        cv.create_oval(S(hl), S(huby - r), S(hr), S(huby + r), fill="#1a1604", outline=GOLD, width=2)
        cv.create_text(S(hubx), S(huby - 7), text="JICHI", fill=GOLD3, font=self.F(15))
        cv.create_text(S(hubx), S(huby + 12), text="CRUZA LOS DATOS", fill=GOLD, font=self.F(6))

        self.round_rect(cv, S(700), S(74), S(874), S(126), S(11), PANEL2, GREEN, 1)
        cv.create_text(S(787), S(92), text="CAUSA HALLADA", fill=GREEN, font=self.F(10))
        cv.create_text(S(787), S(112), text="Tramo sin luz + sin paso", fill=MUTED, font=self.F(8, False))
        pts = self.quad_points((S(hr), S(huby)), (S((hr + 700) / 2), S(huby)), (S(700), S(huby)))
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
        rr = max(2, self.S(3))
        try:
            for c in self._connectors:
                L = len(c["pts"])
                for it, off in zip(c["dots"], c["offs"]):
                    x, y = c["pts"][(self._flow_t + off) % L]
                    self._flow_cv.coords(it, x - rr, y - rr, x + rr, y + rr)
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
        self.gauge(c1, 78, 120, 40, RED2).pack(pady=(0, self.S(2)))
        tk.Label(c1, text="Promedio detectado · límite 40 km/h  (+95%)",
                 font=self.F(9, False), fg=MUTED, bg=PANEL).pack(pady=(0, self.S(14)))

        c2 = self.card(row, RED); c2.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(c2, "Registros de la Policía · 6 meses")
        box = tk.Frame(c2, bg=PANEL); box.pack(expand=True)
        self.donut(box, 14, 23, RED2, "23").grid(row=0, column=0, padx=(self.S(10), self.S(18)), pady=self.S(10))
        leg = tk.Frame(box, bg=PANEL); leg.grid(row=0, column=1)
        for sw, val, txt in [(RED2, "14", "de noche"), ("#2a3150", "9", "de día")]:
            r = tk.Frame(leg, bg=PANEL); r.pack(anchor="w", pady=self.S(6))
            tk.Canvas(r, width=self.S(12), height=self.S(12), bg=sw, highlightthickness=0).pack(side="left", padx=(0, 8))
            tk.Label(r, text=val, font=self.F(17), fg=WHITE, bg=PANEL).pack(side="left")
            tk.Label(r, text=" " + txt, font=self.F(11, False), fg=MUTED, bg=PANEL).pack(side="left")
        tk.Label(leg, text="61% ocurre en horario nocturno", font=self.F(9, False),
                 fg=MUTED2, bg=PANEL).pack(anchor="w", pady=(self.S(4), 0))

        al = self.card(self.content, RED); al.pack(fill="x", pady=(self.S(12), self.S(4)))
        tk.Label(al, text="⚠  ALERTA AUTOMÁTICA GENERADA POR JICHI", font=self.F(15),
                 fg=RED2, bg=PANEL).pack(anchor="w", padx=self.S(16), pady=(self.S(12), self.S(2)))
        tk.Label(al, text="Exceso de velocidad sostenido + alta siniestralidad nocturna en el mismo punto.",
                 font=self.F(11, False), fg=MUTED, bg=PANEL).pack(anchor="w", padx=self.S(16), pady=(0, self.S(12)))

    def s_analisis(self):
        self.head(BLUE, "Paso 2 · Análisis",
                  "JICHI cruza las fuentes de datos",
                  "JICHI junta lo que miden los sensores con lo que registra la "
                  "Policía y lanza la alerta. El equipo revisa los datos del "
                  "Municipio y la causa se hace evidente.")

        flow = self.card(self.content, BLUE); flow.pack(fill="x")
        self.card_label(flow, "Cruce de fuentes · tres bases de datos conectadas")
        fcv = tk.Canvas(flow, width=self.S(880), height=self.S(200), bg=PANEL, highlightthickness=0)
        fcv.pack(pady=(0, self.S(10)))
        self.build_flow(fcv)

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True, pady=(self.S(10), 0))
        cl = self.card(row, LINE); cl.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(cl, "Luminarias del tramo · 2 de 8 operativas")
        S = self.S
        lc = tk.Canvas(cl, width=S(360), height=S(54), bg=PANEL, highlightthickness=0)
        lc.pack()
        for i in range(8):
            x = S(30 + i * 42)
            on = i in (1, 5)
            if on:
                lc.create_oval(x - S(15), S(2), x + S(15), S(28), outline="", fill="#3a2e08")
            lc.create_oval(x - S(10), S(5), x + S(10), S(25), fill=GOLD3 if on else "#2a3150", outline="")
            lc.create_line(x, S(25), x, S(38), fill="#3a4566", width=2)
            lc.create_text(x, S(47), text="ON" if on else "off", fill=GOLD3 if on else MUTED2, font=self.F(7))
        tk.Label(cl, text="75% del corredor sin iluminación de noche",
                 font=self.F(9, False), fg=MUTED, bg=PANEL).pack(pady=(self.S(2), self.S(12)))

        cr = self.card(row, LINE); cr.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(cr, "Paso peatonal · sin pintura")
        cc = tk.Canvas(cr, width=S(300), height=S(54), bg=PANEL, highlightthickness=0)
        cc.pack()
        for i in range(6):
            x = S(70 + i * 30)
            cc.create_rectangle(x, S(6), x + S(17), S(48), fill="#1c2138", outline="")
        tk.Label(cr, text="Demarcación borrada · sin visibilidad nocturna",
                 font=self.F(9, False), fg=MUTED, bg=PANEL).pack(pady=(self.S(2), self.S(12)))

    def s_recomendacion(self):
        self.head(GOLD, "Paso 3 · Recomendación",
                  "El informe llega al Comité con opciones y costos",
                  "JICHI propone intervenciones priorizadas. Actúa como el "
                  "Comité: marca o desmarca opciones y observa cómo cambian el "
                  "costo total y el impacto proyectado en tiempo real.")

        wrap = tk.Frame(self.content, bg=BG); wrap.pack(fill="both", expand=True)
        c = self.card(wrap, GOLD); c.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(c, "Opciones de intervención (haz clic para aprobar/quitar)")
        self.opt_vars = [tk.BooleanVar(value=True) for _ in OPCIONES]
        total_lbl = tk.Label(c, text="", font=self.F(30), fg=GOLD3, bg=PANEL)
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

        S = self.S

        def draw_check(canvas, var):
            canvas.delete("all")
            if var.get():
                self.round_rect(canvas, S(3), S(3), S(25), S(25), S(7), GREEN, GREEN, 1)
                canvas.create_line(S(8), S(14), S(12), S(19), fill="#04130b", width=max(2, S(3)), capstyle="round")
                canvas.create_line(S(12), S(19), S(20), S(8), fill="#04130b", width=max(2, S(3)), capstyle="round")
            else:
                self.round_rect(canvas, S(3), S(3), S(25), S(25), S(7), PANEL, "#46506e", 2)

        for idx, (nombre, costo, detalle, _) in enumerate(OPCIONES):
            var = self.opt_vars[idx]
            b = tk.Frame(c, bg=PANEL2, cursor="hand2"); b.pack(fill="x", padx=S(14), pady=S(5))
            chk = tk.Canvas(b, width=S(28), height=S(28), bg=PANEL2, highlightthickness=0)
            chk.pack(side="left", padx=(S(12), S(10)))
            draw_check(chk, var)
            cost_lbl = tk.Label(b, text="Bs " + miles(costo), font=self.F(12), fg=GOLD3, bg=PANEL2)
            cost_lbl.pack(side="right", padx=S(14))
            txt = tk.Frame(b, bg=PANEL2); txt.pack(side="left", fill="x", expand=True, pady=S(9))
            name_lbl = tk.Label(txt, text=nombre, font=self.F(11), fg=WHITE, bg=PANEL2, anchor="w")
            name_lbl.pack(anchor="w")
            det_lbl = tk.Label(txt, text=detalle, font=self.F(9, False), fg=MUTED, bg=PANEL2, anchor="w")
            det_lbl.pack(anchor="w")

            def toggle(_e, v=var, ca=chk):
                v.set(not v.get())
                draw_check(ca, v)
                recompute()
            for wdg in (b, chk, txt, name_lbl, det_lbl, cost_lbl):
                wdg.bind("<Button-1>", toggle)

        tk.Frame(c, bg=LINE, height=1).pack(fill="x", padx=S(14), pady=(S(8), 0))
        tk.Label(c, text="COSTO TOTAL DE LO SELECCIONADO", font=self.F(9), fg=MUTED2, bg=PANEL).pack(pady=(S(12), 0))
        total_lbl.pack(pady=(S(2), S(16)))

        c2 = self.card(wrap, GOLD); c2.pack(side="left", fill="both", padx=(8, 0))
        self.card_label(c2, "Impacto proyectado (en vivo)")
        for key, nombre in [("acc", "Atropellamientos"), ("spd", "Velocidad"), ("vis", "Visibilidad nocturna")]:
            f = tk.Frame(c2, bg=PANEL); f.pack(fill="x", padx=S(16), pady=S(8))
            tk.Label(f, text=nombre, font=self.F(11, False), fg=MUTED, bg=PANEL).pack(side="left")
            lbl = tk.Label(f, text="0%", font=self.F(16), fg=GREEN, bg=PANEL); lbl.pack(side="right")
            impact_lbls[key] = lbl
        tk.Label(c2, text="Plan completo de referencia:\nBs 46.500  ·  −41% atropellos",
                 font=self.F(9, False), fg=MUTED2, bg=PANEL, justify="left").pack(anchor="w", padx=S(16), pady=(S(20), S(16)))

        recompute()

    def s_decision(self):
        self.head(GREEN, "Paso 4 · Decisión",
                  "El Comité aprueba la intervención",
                  "El Comité revisa la evidencia y aprueba el plan. Se define "
                  "responsable y plazo. Pulsa APROBAR para emitir la orden de ejecución.")

        S = self.S
        c = self.card(self.content, GREEN); c.pack(fill="x")
        self.card_label(c, "Comité de Seguridad Vial · resolución")
        tk.Label(c, text="PRESUPUESTO APROBADO", font=self.F(9), fg=MUTED2, bg=PANEL).pack(pady=(S(6), 0))
        tk.Label(c, text="Bs " + miles(self.aprobado_total), font=self.F(54), fg=GREEN, bg=PANEL).pack()

        info = tk.Frame(c, bg=PANEL); info.pack(pady=S(10))
        for k, v in [("RESPONSABLE", "Municipio"), ("PLAZO", "30 días"), ("SEGUIMIENTO", "JICHI")]:
            cell = tk.Frame(info, bg=PANEL); cell.pack(side="left", padx=S(26))
            tk.Label(cell, text=k, font=self.F(9), fg=MUTED2, bg=PANEL).pack()
            tk.Label(cell, text=v, font=self.F(15), fg=WHITE, bg=PANEL).pack()

        estado = tk.Label(c, text="", font=self.F(16), fg=GREEN, bg=PANEL)
        estado.pack(pady=(S(2), S(2)))
        self.next_btn.config(state="disabled")

        def aprobar():
            estado.config(text="✓  APROBADO — ORDEN DE EJECUCIÓN EMITIDA")
            ap.config(state="disabled", text="APROBADO", bg=PANEL2, fg=GREEN)
            self.next_btn.config(state="normal")

        ap = tk.Button(c, text="✔  APROBAR INTERVENCIÓN", command=aprobar, font=self.F(12),
                       fg="#04130b", bg=GREEN, activebackground=GREEN2, relief="flat",
                       bd=0, padx=S(26), pady=S(12), cursor="hand2")
        self._hover(ap, GREEN, GREEN2)
        ap.pack(pady=(S(6), S(18)))

    def s_resultado(self):
        self.head(GREEN, "Paso 5 · Resultado",
                  "Cuatro meses después, JICHI mide",
                  "No es un reporte: es una decisión ejecutada y con resultados "
                  "medibles en la misma intersección.")

        S = self.S
        hero = self.card(self.content, GREEN); hero.pack(fill="x")
        tk.Label(hero, text="CUATRO MESES DESPUÉS DE LA INTERVENCIÓN", font=self.F(9),
                 fg=GREEN2, bg=PANEL).pack(pady=(S(14), 0))
        big = tk.Label(hero, text="−0%", font=self.F(62), fg=GREEN, bg=PANEL); big.pack()
        tk.Label(hero, text="menos atropellamientos en el corredor", font=self.F(15),
                 fg=WHITE, bg=PANEL).pack(pady=(0, S(16)))
        self.count(big, 41, dur=1.4, prefix="−", suffix="%")

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True, pady=(S(12), 0))
        g = self.card(row, GREEN); g.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(g, "Velocidad promedio · 78 → 52 km/h")
        self.gauge(g, 52, 120, 40, GREEN).pack(pady=(0, S(14)))

        comp = self.card(row, GREEN); comp.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(comp, "Antes  →  después")
        grid = tk.Frame(comp, bg=PANEL); grid.pack(padx=S(16), pady=(0, S(14)), fill="x")
        datos = [("Velocidad promedio", "78 km/h", "52 km/h"), ("Atropellamientos", "23", "14"),
                 ("Luminarias activas", "2/8", "8/8"), ("Paso peatonal", "sin pintura", "demarcado")]
        for r, (etq, antes, desp) in enumerate(datos):
            tk.Label(grid, text=etq, font=self.F(9, False), fg=MUTED, bg=PANEL, anchor="w").grid(row=r, column=0, sticky="w", pady=S(7))
            tk.Label(grid, text=antes, font=self.F(12), fg=RED2, bg=PANEL).grid(row=r, column=1, padx=S(14))
            tk.Label(grid, text="→", font=self.F(11, False), fg=MUTED2, bg=PANEL).grid(row=r, column=2)
            tk.Label(grid, text=desp, font=self.F(12), fg=GREEN, bg=PANEL).grid(row=r, column=3, padx=S(14))
        grid.columnconfigure(0, weight=1)

    def s_sostenibilidad(self):
        self.head(GOLD, "Paso 6 · Por qué funciona aquí",
                  "Una decisión ejecutada, no un reporte",
                  "JICHI está diseñado para seguir funcionando sin importar qué "
                  "gobierno esté en turno.")

        S = self.S
        c = self.card(self.content, GOLD); c.pack(fill="both", expand=True)
        self.card_label(c, "Garantías del modelo")
        for txt in ["Los acuerdos se firman antes de arrancar.",
                    "Plataforma de código abierto y servidores en Bolivia.",
                    "La ciudad se queda con todo al terminar.",
                    "Ordenanza municipal en gestión para darle continuidad."]:
            f = tk.Frame(c, bg=PANEL); f.pack(fill="x", padx=S(18), pady=S(6))
            tk.Label(f, text="✓", font=self.F(13), fg=GREEN, bg=PANEL).pack(side="left", padx=(0, S(10)))
            tk.Label(f, text=txt, font=self.F(11, False), fg=WHITE, bg=PANEL).pack(side="left")

        box = tk.Frame(c, bg=PANEL2); box.pack(fill="x", padx=S(18), pady=(S(16), S(18)))
        tk.Label(box, text="COSTO DE OPERACIÓN ANUAL", font=self.F(9), fg=MUTED2, bg=PANEL2).pack(pady=(S(14), 0))
        amt = tk.Label(box, text="Bs 0", font=self.F(40), fg=GOLD3, bg=PANEL2); amt.pack()
        tk.Label(box, text="Una fracción mínima del presupuesto municipal",
                 font=self.F(9, False), fg=MUTED, bg=PANEL2).pack(pady=(0, S(14)))
        self.count(amt, 1080000, dur=1.5, prefix="Bs ", sep=True)


if __name__ == "__main__":
    root = tk.Tk()
    JichiApp(root)
    root.mainloop()
