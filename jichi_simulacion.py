# -*- coding: utf-8 -*-
"""
JICHI — Simulación interactiva del Observatorio de Seguridad Vial
Explica, paso a paso, cómo JICHI detecta, cruza datos, recomienda,
el Comité decide y se miden resultados.

Solo usa la librería estándar de Python (tkinter). No requiere instalar nada.
Ejecutar:  python jichi_simulacion.py
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

# Intervenciones que llegan al Comité (suman Bs 46.500)
OPCIONES = [
    ("Arreglar las 6 luminarias apagadas", 28000, "Restaura la iluminación nocturna del tramo"),
    ("Repintar el paso peatonal",            6500, "Demarcación + señal vertical reflectiva"),
    ("Instalar un reductor de velocidad",   12000, "Badén antes del cruce peatonal"),
]

PASOS = ["Detección", "Análisis", "Recomendación", "Decisión", "Resultado", "Sostenibilidad"]


def miles(n):
    """Formatea 46500 -> '46.500' (estilo Bolivia)."""
    return f"{int(round(n)):,}".replace(",", ".")


class JichiApp:
    def __init__(self, root):
        self.root = root
        root.title("JICHI — Simulación del Observatorio de Seguridad Vial")
        root.configure(bg=BG)
        root.geometry("1060x720")
        root.minsize(940, 660)

        self.current = 0
        self.token = 0                       # invalida animaciones al cambiar de paso
        self.aprobado_total = sum(c for _, c, _ in OPCIONES)
        self.opt_vars = []

        self.f_brand  = (FONT, 30, "bold")
        self.f_title  = (FONT, 21, "bold")
        self.f_h      = (FONT, 15, "bold")
        self.f_body   = (FONT, 11)
        self.f_small  = (FONT, 9)
        self.f_label  = (FONT, 9, "bold")
        self.f_num    = (FONT, 38, "bold")
        self.f_big    = (FONT, 60, "bold")
        self.f_kpi    = (FONT, 26, "bold")

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
        h.pack(fill="x", padx=26, pady=(18, 4))
        tk.Label(h, text="OBSERVATORIO DE SEGURIDAD VIAL", font=(FONT, 9, "bold"),
                 fg=GOLD, bg=BG).pack()
        tk.Label(h, text="JICHI", font=self.f_brand, fg=GOLD3, bg=BG).pack()
        tk.Label(h, text="Simulación interactiva · cómo funciona, paso a paso",
                 font=self.f_small, fg=MUTED, bg=BG).pack()

    def _build_stepper(self):
        s = tk.Frame(self.root, bg=BG)
        s.pack(fill="x", padx=26, pady=(8, 2))
        self.step_lbls = []
        for i, name in enumerate(PASOS):
            cell = tk.Frame(s, bg=BG)
            cell.pack(side="left", expand=True, fill="x")
            num = tk.Label(cell, text=str(i + 1), font=(FONT, 12, "bold"),
                           width=3, fg=MUTED2, bg=PANEL)
            num.pack(pady=(0, 4))
            txt = tk.Label(cell, text=name.upper(), font=(FONT, 8, "bold"),
                           fg=MUTED2, bg=BG)
            txt.pack()
            self.step_lbls.append((num, txt))

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
            b = tk.Button(parent, text=text, command=cmd, font=(FONT, 11, "bold"),
                          fg="#1a1000", bg=GOLD, activebackground=GOLD3,
                          activeforeground="#1a1000", relief="flat", bd=0,
                          padx=22, pady=10, cursor="hand2")
        else:
            b = tk.Button(parent, text=text, command=cmd, font=(FONT, 11, "bold"),
                          fg=WHITE, bg=PANEL, activebackground=PANEL2,
                          activeforeground=WHITE, relief="flat", bd=0,
                          padx=22, pady=10, cursor="hand2")
        return b

    # ───────────────────────────── navegación ──────────────────────────────
    def show(self, i):
        self.current = i
        self.token += 1
        for w in self.content.winfo_children():
            w.destroy()

        for k, (num, txt) in enumerate(self.step_lbls):
            if k == i:
                num.config(fg="#1a1000", bg=GOLD); txt.config(fg=WHITE)
            elif k < i:
                num.config(fg=GREEN, bg=PANEL); txt.config(fg=MUTED)
            else:
                num.config(fg=MUTED2, bg=PANEL); txt.config(fg=MUTED2)

        self.prev_btn.config(state="normal" if i > 0 else "disabled")
        last = (i == len(PASOS) - 1)
        self.next_btn.config(state="normal",
                             text="↺  Reiniciar" if last else "Siguiente  →")
        self.counter.config(text=f"Paso {i + 1} de {len(PASOS)}")

        self.steps[i]()

    def next(self):
        if self.current >= len(PASOS) - 1:
            self.show(0)
        else:
            self.show(self.current + 1)

    def prev(self):
        if self.current > 0:
            self.show(self.current - 1)

    # ───────────────────────────── helpers de UI ───────────────────────────
    def card(self, parent, accent=LINE):
        f = tk.Frame(parent, bg=PANEL, highlightbackground=accent,
                     highlightthickness=1, bd=0)
        return f

    def head(self, accent_color, label, title, intro):
        tk.Label(self.content, text=label.upper(), font=(FONT, 9, "bold"),
                 fg=accent_color, bg=BG).pack(anchor="w")
        tk.Label(self.content, text=title, font=self.f_title, fg=WHITE, bg=BG,
                 justify="left").pack(anchor="w", pady=(2, 2))
        tk.Label(self.content, text=intro, font=self.f_body, fg=MUTED, bg=BG,
                 justify="left", wraplength=980).pack(anchor="w", pady=(0, 10))

    def card_label(self, parent, text):
        tk.Label(parent, text=text.upper(), font=self.f_label, fg=MUTED2,
                 bg=PANEL).pack(anchor="w", padx=16, pady=(14, 6))

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
            txt = (prefix + (miles(v) if sep else str(int(round(v)))) + suffix)
            label.config(text=txt)
        final = prefix + (miles(target) if sep else str(int(round(target)))) + suffix
        self.animate(dur, frame, on_done=lambda: label.config(text=final))

    # ───────────────────────────── medidor (gauge) ─────────────────────────
    def gauge(self, parent, value, maxv, limit, color):
        cv = tk.Canvas(parent, width=320, height=205, bg=PANEL,
                       highlightthickness=0)
        cx, cy, r = 160, 130, 100
        bbox = (cx - r, cy - r, cx + r, cy + r)

        # arco de fondo
        cv.create_arc(*bbox, start=180, extent=-180, style="arc",
                      width=15, outline="#2a3150")

        # marca de límite (dorada)
        th = math.radians(180 - (limit / maxv) * 180)
        x1 = cx + (r + 4) * math.cos(th); y1 = cy - (r + 4) * math.sin(th)
        x2 = cx + (r - 20) * math.cos(th); y2 = cy - (r - 20) * math.sin(th)
        cv.create_line(x1, y1, x2, y2, fill=GOLD, width=3)
        lx = cx + (r + 18) * math.cos(th); ly = cy - (r + 18) * math.sin(th)
        cv.create_text(lx, ly, text=str(limit), fill=GOLD3, font=(FONT, 9, "bold"))

        def render(e):
            cv.delete("dyn")
            cur = value * e
            f = cur / maxv
            cv.create_arc(*bbox, start=180, extent=-180 * f, style="arc",
                          width=15, outline=color, tags="dyn")
            ang = math.radians(180 - f * 180)
            nx = cx + (r - 22) * math.cos(ang); ny = cy - (r - 22) * math.sin(ang)
            cv.create_line(cx, cy, nx, ny, fill=WHITE, width=4,
                           capstyle="round", tags="dyn")
            cv.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#15173a",
                           outline=WHITE, width=2, tags="dyn")
            cv.create_text(cx, cy + 38, text=str(int(round(cur))), fill=color,
                           font=self.f_num, tags="dyn")
            cv.create_text(cx, cy + 68, text="km/h", fill=MUTED,
                           font=(FONT, 9, "bold"), tags="dyn")

        render(0)
        self.animate(1.3, render)
        return cv

    # ═════════════════════════════ PASOS ═══════════════════════════════════
    def s_deteccion(self):
        self.head(RED, "Paso 1 · Detección",
                  "Los sensores detectan algo fuera de lo normal",
                  "Cuarto Anillo, entre la Av. Banzer y la Radial 17½. "
                  "Los autos circulan muy por encima del límite y, al mismo "
                  "tiempo, la Policía acumula atropellamientos en esa misma "
                  "intersección.")

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True)

        c1 = self.card(row, RED)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(c1, "Sensor de velocidad · Cuarto Anillo")
        self.gauge(c1, 78, 120, 40, RED2).pack(pady=(0, 4))
        tk.Label(c1, text="Promedio detectado · límite permitido 40 km/h (+95%)",
                 font=self.f_small, fg=MUTED, bg=PANEL).pack(pady=(0, 14))

        c2 = self.card(row, RED)
        c2.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.card_label(c2, "Registros de la Policía · 6 meses")
        n = tk.Label(c2, text="0", font=(FONT, 64, "bold"), fg=RED2, bg=PANEL)
        n.pack(pady=(18, 0))
        tk.Label(c2, text="ATROPELLAMIENTOS", font=self.f_label, fg=MUTED, bg=PANEL).pack()
        det = tk.Frame(c2, bg=PANEL); det.pack(pady=18)
        nb = tk.Label(det, text="0", font=self.f_kpi, fg=RED2, bg=PANEL); nb.grid(row=0, column=0, padx=18)
        nd = tk.Label(det, text="0", font=self.f_kpi, fg=WHITE, bg=PANEL); nd.grid(row=0, column=1, padx=18)
        tk.Label(det, text="de noche", font=self.f_small, fg=MUTED, bg=PANEL).grid(row=1, column=0)
        tk.Label(det, text="de día", font=self.f_small, fg=MUTED, bg=PANEL).grid(row=1, column=1)
        self.count(n, 23); self.count(nb, 14); self.count(nd, 9)

        al = self.card(self.content, RED); al.pack(fill="x", pady=(12, 4))
        tk.Label(al, text="⚠  ALERTA AUTOMÁTICA GENERADA POR JICHI",
                 font=self.f_h, fg=RED2, bg=PANEL).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Label(al, text="Exceso de velocidad sostenido + alta siniestralidad "
                 "nocturna en el mismo punto.", font=self.f_body, fg=MUTED,
                 bg=PANEL).pack(anchor="w", padx=16, pady=(0, 12))

    def s_analisis(self):
        self.head(BLUE, "Paso 2 · Análisis",
                  "JICHI cruza las fuentes de datos",
                  "JICHI junta lo que miden los sensores con lo que registra la "
                  "Policía y lanza la alerta. El equipo revisa los datos del "
                  "Municipio y la causa se hace evidente.")

        flow = self.card(self.content, BLUE); flow.pack(fill="x")
        self.card_label(flow, "Cruce de fuentes · tres bases de datos")
        fr = tk.Frame(flow, bg=PANEL); fr.pack(pady=(0, 14))

        def src(parent, color, name, metric):
            f = tk.Frame(parent, bg=PANEL2, highlightbackground=color,
                         highlightthickness=1)
            tk.Label(f, text=name, font=self.f_label, fg=WHITE, bg=PANEL2).pack(padx=14, pady=(10, 0))
            tk.Label(f, text=metric, font=self.f_small, fg=MUTED, bg=PANEL2).pack(padx=14, pady=(0, 10))
            return f

        left = tk.Frame(fr, bg=PANEL); left.grid(row=0, column=0, padx=8)
        src(left, BLUE, "SENSORES", "78 km/h · límite 40").pack(pady=4, fill="x")
        src(left, RED, "POLICÍA", "23 atropellos · 14 noche").pack(pady=4, fill="x")
        src(left, GOLD, "MUNICIPIO", "2/8 luminarias · sin pintura").pack(pady=4, fill="x")

        tk.Label(fr, text="➜", font=(FONT, 22, "bold"), fg=GOLD, bg=PANEL).grid(row=0, column=1, padx=6)

        hub = tk.Frame(fr, bg=PANEL2, highlightbackground=GOLD, highlightthickness=2)
        hub.grid(row=0, column=2, padx=10)
        tk.Label(hub, text="JICHI", font=(FONT, 22, "bold"), fg=GOLD3, bg=PANEL2).pack(padx=24, pady=(16, 0))
        tk.Label(hub, text="CRUZA LOS DATOS", font=(FONT, 8, "bold"), fg=GOLD, bg=PANEL2).pack(padx=24, pady=(0, 16))

        tk.Label(fr, text="➜", font=(FONT, 22, "bold"), fg=GREEN, bg=PANEL).grid(row=0, column=3, padx=6)

        out = tk.Frame(fr, bg=PANEL2, highlightbackground=GREEN, highlightthickness=1)
        out.grid(row=0, column=4, padx=8)
        tk.Label(out, text="CAUSA HALLADA", font=self.f_label, fg=GREEN, bg=PANEL2).pack(padx=14, pady=(12, 0))
        tk.Label(out, text="Tramo sin luz +\nsin paso peatonal", font=self.f_small,
                 fg=MUTED, bg=PANEL2, justify="center").pack(padx=14, pady=(2, 12))

        row = tk.Frame(self.content, bg=BG); row.pack(fill="both", expand=True, pady=(12, 0))
        cl = self.card(row, LINE); cl.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(cl, "Luminarias del tramo · 2 de 8 operativas")
        lc = tk.Canvas(cl, width=360, height=70, bg=PANEL, highlightthickness=0)
        lc.pack(pady=(0, 6))
        for i in range(8):
            x = 30 + i * 42
            on = i in (1, 5)
            col = GOLD3 if on else "#2a3150"
            if on:
                lc.create_oval(x - 16, 6, x + 16, 38, outline="", fill="#3a2e08")
            lc.create_oval(x - 11, 11, x + 11, 33, fill=col, outline="")
            lc.create_line(x, 33, x, 50, fill="#3a4566", width=2)
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
                  "Comité: marca o desmarca opciones y observa cómo cambia el "
                  "costo total en tiempo real.")

        wrap = tk.Frame(self.content, bg=BG); wrap.pack(fill="both", expand=True)

        c = self.card(wrap, GOLD); c.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.card_label(c, "Opciones de intervención (marca las que apruebas)")
        self.opt_vars = []
        total_lbl = tk.Label(c, text="", font=(FONT, 30, "bold"), fg=GOLD3, bg=PANEL)

        def recompute():
            t = sum(cost for var, (_, cost, _) in zip(self.opt_vars, OPCIONES) if var.get())
            self.aprobado_total = t
            total_lbl.config(text="Bs " + miles(t))

        for nombre, costo, detalle in OPCIONES:
            var = tk.BooleanVar(value=True)
            self.opt_vars.append(var)
            box = tk.Frame(c, bg=PANEL2); box.pack(fill="x", padx=14, pady=5)
            cb = tk.Checkbutton(box, variable=var, command=recompute,
                                bg=PANEL2, activebackground=PANEL2,
                                selectcolor=PANEL, highlightthickness=0, bd=0)
            cb.pack(side="left", padx=(8, 4))
            txt = tk.Frame(box, bg=PANEL2); txt.pack(side="left", fill="x", expand=True, pady=8)
            tk.Label(txt, text=nombre, font=(FONT, 11, "bold"), fg=WHITE,
                     bg=PANEL2, anchor="w").pack(anchor="w")
            tk.Label(txt, text=detalle, font=self.f_small, fg=MUTED, bg=PANEL2,
                     anchor="w").pack(anchor="w")
            tk.Label(box, text="Bs " + miles(costo), font=(FONT, 12, "bold"),
                     fg=GOLD3, bg=PANEL2).pack(side="right", padx=14)

        tk.Frame(c, bg=LINE, height=1).pack(fill="x", padx=14, pady=(8, 0))
        tk.Label(c, text="COSTO TOTAL DE LO SELECCIONADO", font=self.f_label,
                 fg=MUTED2, bg=PANEL).pack(pady=(12, 0))
        total_lbl.pack(pady=(2, 16))
        recompute()

        c2 = self.card(wrap, GOLD); c2.pack(side="left", fill="y", padx=(8, 0))
        self.card_label(c2, "Impacto proyectado por el modelo")
        for nombre, val in [("Atropellamientos", "−41%"), ("Velocidad", "−33%"),
                            ("Visibilidad nocturna", "+90%")]:
            f = tk.Frame(c2, bg=PANEL); f.pack(fill="x", padx=16, pady=6)
            tk.Label(f, text=nombre, font=self.f_body, fg=MUTED, bg=PANEL).pack(side="left")
            tk.Label(f, text=val, font=(FONT, 15, "bold"), fg=GREEN, bg=PANEL).pack(side="right")
        tk.Label(c2, text="Plan completo de referencia:\nBs 46.500",
                 font=self.f_small, fg=MUTED2, bg=PANEL, justify="left").pack(anchor="w", padx=16, pady=(18, 16))

    def s_decision(self):
        self.head(GREEN, "Paso 4 · Decisión",
                  "El Comité aprueba la intervención",
                  "El Comité revisa la evidencia y aprueba el plan. Se define "
                  "responsable y plazo. Pulsa APROBAR para emitir la orden de "
                  "ejecución.")

        c = self.card(self.content, GREEN); c.pack(fill="x")
        self.card_label(c, "Comité de Seguridad Vial · resolución")
        tk.Label(c, text="PRESUPUESTO APROBADO", font=self.f_label, fg=MUTED2, bg=PANEL).pack(pady=(6, 0))
        tk.Label(c, text="Bs " + miles(self.aprobado_total), font=self.f_big,
                 fg=GREEN, bg=PANEL).pack()

        info = tk.Frame(c, bg=PANEL); info.pack(pady=10)
        for k, v in [("RESPONSABLE", "Municipio"), ("PLAZO", "30 días"),
                     ("SEGUIMIENTO", "JICHI")]:
            cell = tk.Frame(info, bg=PANEL); cell.pack(side="left", padx=26)
            tk.Label(cell, text=k, font=self.f_label, fg=MUTED2, bg=PANEL).pack()
            tk.Label(cell, text=v, font=self.f_h, fg=WHITE, bg=PANEL).pack()

        estado = tk.Label(c, text="", font=(FONT, 16, "bold"), fg=GREEN, bg=PANEL)
        estado.pack(pady=(4, 4))

        self.next_btn.config(state="disabled")

        def aprobar():
            estado.config(text="✓  APROBADO — ORDEN DE EJECUCIÓN EMITIDA")
            ap_btn.config(state="disabled", text="APROBADO", bg=PANEL2, fg=GREEN)
            self.next_btn.config(state="normal")

        ap_btn = tk.Button(c, text="✔  APROBAR INTERVENCIÓN", command=aprobar,
                           font=(FONT, 12, "bold"), fg="#04130b", bg=GREEN,
                           activebackground=GREEN2, relief="flat", bd=0,
                           padx=26, pady=12, cursor="hand2")
        ap_btn.pack(pady=(4, 18))

    def s_resultado(self):
        self.head(GREEN, "Paso 5 · Resultado",
                  "Cuatro meses después, JICHI mide",
                  "No es un reporte: es una decisión ejecutada y con resultados "
                  "medibles en la misma intersección.")

        hero = self.card(self.content, GREEN); hero.pack(fill="x")
        tk.Label(hero, text="CUATRO MESES DESPUÉS DE LA INTERVENCIÓN",
                 font=self.f_label, fg=GREEN2, bg=PANEL).pack(pady=(14, 0))
        big = tk.Label(hero, text="−0%", font=(FONT, 70, "bold"), fg=GREEN, bg=PANEL)
        big.pack()
        tk.Label(hero, text="menos atropellamientos en el corredor",
                 font=self.f_h, fg=WHITE, bg=PANEL).pack(pady=(0, 16))
        self.count(big, 41, dur=1.3, prefix="−", suffix="%")

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
                     anchor="w").grid(row=r, column=0, sticky="w", pady=6)
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
        puntos = [
            ("✓", "Los acuerdos se firman antes de arrancar."),
            ("✓", "Plataforma de código abierto y servidores en Bolivia."),
            ("✓", "La ciudad se queda con todo al terminar."),
            ("✓", "Ordenanza municipal en gestión para darle continuidad."),
        ]
        for ic, txt in puntos:
            f = tk.Frame(c, bg=PANEL); f.pack(fill="x", padx=18, pady=6)
            tk.Label(f, text=ic, font=(FONT, 13, "bold"), fg=GREEN, bg=PANEL).pack(side="left", padx=(0, 10))
            tk.Label(f, text=txt, font=self.f_body, fg=WHITE, bg=PANEL).pack(side="left")

        box = tk.Frame(c, bg=PANEL2); box.pack(fill="x", padx=18, pady=(16, 18))
        tk.Label(box, text="COSTO DE OPERACIÓN ANUAL", font=self.f_label,
                 fg=MUTED2, bg=PANEL2).pack(pady=(14, 0))
        amt = tk.Label(box, text="Bs 0", font=(FONT, 40, "bold"), fg=GOLD3, bg=PANEL2)
        amt.pack()
        tk.Label(box, text="Una fracción mínima del presupuesto municipal",
                 font=self.f_small, fg=MUTED, bg=PANEL2).pack(pady=(0, 14))
        self.count(amt, 1080000, dur=1.4, prefix="Bs ", sep=True)


if __name__ == "__main__":
    root = tk.Tk()
    JichiApp(root)
    root.mainloop()
