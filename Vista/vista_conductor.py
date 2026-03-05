import math
import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import FaseSimulacion
from Vista import theme


def _edge_name(edge, idx):
    """Devuelve el nombre de una arista o un tramo genérico."""
    name = getattr(edge, 'name', None) or getattr(edge, 'street_name', None)
    if name and str(name).strip() and str(name).lower() not in ('nan', 'none'):
        return str(name).strip()
    return f"Tramo {idx + 1}"


def _format_dist(m):
    if m < 1000:
        return f"{m:.0f} m"
    return f"{m / 1000:.2f} km"


def _bearing_arrow(node_a, node_b):
    """Calcula el ángulo entre dos nodos y devuelve una flecha direccional.

    Nota: usa coordenadas cartesianas simples (lon/lat) para estimar la
    dirección. Suficiente para indicación visual aproximada en distancias
    cortas entre nodos consecutivos de la ruta.
    """
    if node_a is None or node_b is None:
        return "↑"
    dlat = node_b.lat - node_a.lat
    dlon = node_b.lon - node_a.lon
    angle = math.degrees(math.atan2(dlon, dlat)) % 360
    arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
    idx = int((angle + 22.5) / 45) % 8
    return arrows[idx]


class VentanaConductor(tk.Toplevel):
    def __init__(self, master, state, tick_callback):
        super().__init__(master)
        self.state = state
        self.tick_callback = tick_callback
        self.title("🚑 Vista Conductor")
        self.geometry("820x480")
        self.resizable(False, False)
        self.configure(bg=theme.BG)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        self._blink_on = True
        self._blink_job = None

        self._frame = tk.Frame(self, bg=theme.BG)
        self._frame.pack(fill=tk.BOTH, expand=True)

        state.registrar_listener(self.actualizar)
        self.actualizar()

    # ------------------------------------------------------------------
    def _clear(self):
        for widget in self._frame.winfo_children():
            widget.destroy()
        if self._blink_job is not None:
            self.after_cancel(self._blink_job)
            self._blink_job = None

    # ------------------------------------------------------------------
    def actualizar(self):
        self._clear()
        fase = self.state.fase

        if fase in (FaseSimulacion.YENDO_A_PACIENTE, FaseSimulacion.YENDO_A_HOSPITAL):
            if not self.state.ruta_activa_nodes:
                self._build_selector_ruta()
            else:
                self._build_en_trayecto()
        elif fase == FaseSimulacion.EN_PACIENTE:
            self._build_en_paciente()
        elif fase == FaseSimulacion.FIN:
            self._build_fin()
        else:
            tk.Label(self._frame, text="Iniciando...", font=(theme.FONT, 14),
                     fg=theme.FG, bg=theme.BG).pack(pady=40)

    # ------------------------------------------------------------------
    def _lbl(self, parent, text, font=None, fg=None, bg=None, **kw):
        if font is None:
            font = (theme.FONT, 10)
        if fg is None:
            fg = theme.FG
        if bg is None:
            bg = theme.BG
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

    # ------------------------------------------------------------------
    def _build_selector_ruta(self):
        state = self.state
        f = self._frame

        if state.fase == FaseSimulacion.YENDO_A_PACIENTE:
            destino_label = f"Paciente: {state.nombre_paciente}"
        else:
            road = state.model.road
            h_node = road.get_node(state.hospital_destino_node_id)
            h_name = h_node.hospital.name if h_node and h_node.hospital else "Hospital"
            destino_label = f"Hospital: {h_name}"

        self._lbl(f, "🚑 CONDUCTOR — Elige ruta",
                  font=(theme.FONT, 14, "bold"), fg=theme.ACCENT).pack(pady=(20, 4))
        self._lbl(f, f"Destino: {destino_label}",
                  font=(theme.FONT, 11), fg=theme.FG_DIM).pack()
        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=16, pady=10)

        self._ruta_var = tk.StringVar(value="")
        rutas = state.rutas_disponibles
        if not rutas:
            self._lbl(f, "No hay rutas disponibles.", fg=theme.DANGER).pack(pady=20)
            return

        first_key = next(iter(rutas))
        self._ruta_var.set(first_key)

        for nombre, scored in rutas.items():
            km = scored.route.total_distance_m / 1000
            mins = scored.route.total_time_min
            stars = round(scored.score * 5, 1)
            text = f"{nombre}   │  {km:.1f} km  │  {mins:.1f} min  │  ★{stars}"
            tk.Radiobutton(f, text=text, variable=self._ruta_var,
                           value=nombre, font=(theme.FONT, 10),
                           fg=theme.FG, bg=theme.BG,
                           selectcolor=theme.BG_CARD,
                           activebackground=theme.BG,
                           activeforeground=theme.ACCENT).pack(anchor='w', padx=36, pady=4)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=16, pady=10)

        def confirmar():
            elegida = self._ruta_var.get()
            if elegida and elegida in state.rutas_disponibles:
                scored = state.rutas_disponibles[elegida]
                state.ruta_activa_nodes = list(scored.route.nodes[1:])
                state.ruta_activa_edges = list(scored.route.edges)
                state.ruta_activa_label = elegida
                state.ruta_idx = 0
                state.notificar()

        tk.Button(f, text="✅ CONFIRMAR RUTA", font=(theme.FONT, 12, "bold"),
                  bg=theme.ACCENT, fg="white",
                  activebackground="#3a8eef", activeforeground="white",
                  relief='flat', command=confirmar,
                  padx=12, pady=6).pack(pady=18)

    # ------------------------------------------------------------------
    def _build_en_trayecto(self):
        state = self.state
        f = self._frame

        if state.fase == FaseSimulacion.YENDO_A_PACIENTE:
            destino_label = f"Paciente: {state.nombre_paciente}"
        else:
            road = state.model.road
            h_node = road.get_node(state.hospital_destino_node_id)
            h_name = h_node.hospital.name if h_node and h_node.hospital else "Hospital"
            destino_label = f"Hospital: {h_name}"

        alg_label = state.ruta_activa_label

        # ── Header ────────────────────────────────────────────────
        header = tk.Frame(f, bg=theme.BG_CARD)
        header.pack(fill='x', padx=0, pady=0)
        self._lbl(header, f"🚑  {alg_label}  │  {destino_label}",
                  font=(theme.FONT, 11, "bold"), fg=theme.ACCENT,
                  bg=theme.BG_CARD).pack(side='left', padx=14, pady=8)
        fase_txt = "Yendo al paciente" if state.fase == FaseSimulacion.YENDO_A_PACIENTE else "Yendo al hospital"
        self._lbl(header, fase_txt, font=(theme.FONT, 10),
                  fg=theme.FG_DIM, bg=theme.BG_CARD).pack(side='right', padx=14, pady=8)

        # ── Body: two columns ─────────────────────────────────────
        body = tk.Frame(f, bg=theme.BG)
        body.pack(fill='both', expand=True, padx=8, pady=4)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Left column (~2/3)
        left = tk.Frame(body, bg=theme.BG)
        left.grid(row=0, column=0, sticky='nsew', padx=(4, 4), pady=4)

        road = state.model.road
        edges = state.ruta_activa_edges
        nodes = state.ruta_activa_nodes
        idx = state.ruta_idx

        # Current street name
        if edges and idx < len(edges):
            current_edge = edges[idx]
            current_street = _edge_name(current_edge, idx)
        else:
            current_street = "—"

        self._lbl(left, "CALLE ACTUAL", font=(theme.FONT, 9),
                  fg=theme.FG_DIM).pack(anchor='w', padx=4)
        self._lbl(left, current_street,
                  font=(theme.FONT, 13, "bold"), fg=theme.FG).pack(anchor='w', padx=4)

        # Direction arrow
        arrow_char = "↑"
        if idx < len(nodes):
            nodo_actual = state.model.posicion.nodo_actual
            next_nid = nodes[idx]
            node_a = road.get_node(nodo_actual)
            node_b = road.get_node(next_nid)
            arrow_char = _bearing_arrow(node_a, node_b)

        arrow_canvas = tk.Canvas(left, width=180, height=160,
                                 bg=theme.BG_CARD, highlightthickness=0)
        arrow_canvas.pack(pady=8)
        arrow_canvas.create_text(90, 80, text=arrow_char,
                                 font=(theme.FONT, 72), fill=theme.ACCENT)

        # Next street and distance
        next_street = "—"
        next_dist = ""
        if edges and idx + 1 < len(edges):
            next_edge = edges[idx + 1]
            next_street = _edge_name(next_edge, idx + 1)
            next_dist = _format_dist(getattr(next_edge, 'length_m', 0))
        elif edges and idx < len(edges):
            next_dist = _format_dist(getattr(edges[idx], 'length_m', 0))

        self._lbl(left, f"Próxima: {next_street}  {next_dist}",
                  font=(theme.FONT, 9), fg=theme.FG_DIM).pack(anchor='w', padx=4)

        # Right column (~1/3)
        right = tk.Frame(body, bg=theme.BG)
        right.grid(row=0, column=1, sticky='nsew', padx=(4, 4), pady=4)

        # Card: Info Motor
        motor_card = tk.Frame(right, bg=theme.BG_CARD, relief='flat', bd=0)
        motor_card.pack(fill='x', padx=0, pady=(0, 6))

        self._lbl(motor_card, "⚙  INFO MOTOR",
                  font=(theme.FONT, 9, "bold"), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(anchor='w', padx=8, pady=(6, 2))

        telem = state.model.engine.get_telemetry()
        score = telem.get('health_score', 100)
        severity = telem.get('severity', 'OK')
        sev_color = {
            'OK': theme.SUCCESS,
            'WARNING': theme.WARNING,
            'CRITICAL': theme.DANGER
        }.get(severity, theme.FG)

        self._lbl(motor_card,
                  f"🌡  {telem.get('temperature', 0):.1f}°C   "
                  f"⚡ {telem.get('rpm', 0):.0f} RPM",
                  font=(theme.FONT, 9), bg=theme.BG_CARD).pack(anchor='w', padx=8)
        self._lbl(motor_card, f"Estado: {severity}",
                  font=(theme.FONT, 9, "bold"), fg=sev_color,
                  bg=theme.BG_CARD).pack(anchor='w', padx=8, pady=(2, 4))

        health_bar = ttk.Progressbar(motor_card, maximum=100, value=score, length=200)
        health_bar.pack(padx=8, pady=(0, 2))
        self._lbl(motor_card, f"Salud motor: {score:.0f}/100",
                  font=(theme.FONT, 8), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(anchor='w', padx=8, pady=(0, 6))

        # Card: Aviso Paciente Crítico
        if state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
            paciente = state.model.paciente
            if paciente.gravedad == "grave":
                self._alert_label = tk.Label(right,
                                             text="🚨 PACIENTE CRÍTICO",
                                             font=(theme.FONT, 11, "bold"),
                                             fg="white", bg=theme.DANGER,
                                             relief='flat', padx=8, pady=8)
                self._alert_label.pack(fill='x', pady=(2, 0))
                self._blink()

        # ── Footer ────────────────────────────────────────────────
        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=0, pady=0)
        footer = tk.Frame(f, bg=theme.BG_CARD)
        footer.pack(fill='x', pady=0)

        total = len(nodes)
        self._lbl(footer, f"Progreso: {idx}/{total} nodos",
                  font=(theme.FONT, 9), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(side='left', padx=10, pady=6)

        progress_bar = ttk.Progressbar(footer, maximum=max(total, 1),
                                       value=idx, length=300)
        progress_bar.pack(side='left', padx=6, pady=6)

        mode_lbl = "🔄 Auto" if state.modo_automatico else "🖱️ Manual"

        def toggle_mode():
            state.modo_automatico = not state.modo_automatico
            state.notificar()

        tk.Button(footer, text=mode_lbl, command=toggle_mode,
                  font=(theme.FONT, 9), bg=theme.BG_CARD, fg=theme.FG,
                  activebackground=theme.BG, activeforeground=theme.ACCENT,
                  relief='flat', width=10).pack(side='left', padx=6, pady=6)

        tick_state = tk.NORMAL if not state.modo_automatico else tk.DISABLED
        tk.Button(footer, text="▶ Tick", state=tick_state,
                  command=self.tick_callback,
                  font=(theme.FONT, 9), bg=theme.ACCENT, fg="white",
                  activebackground="#3a8eef", activeforeground="white",
                  relief='flat', width=8).pack(side='left', padx=4, pady=6)

    # ------------------------------------------------------------------
    def _blink(self):
        if not hasattr(self, '_alert_label') or not self._alert_label.winfo_exists():
            return
        self._blink_on = not self._blink_on
        bg = theme.DANGER if self._blink_on else "#aa1111"
        self._alert_label.config(bg=bg)
        self._blink_job = self.after(800, self._blink)

    # ------------------------------------------------------------------
    def _build_en_paciente(self):
        state = self.state
        f = self._frame

        self._lbl(f, "🚑 LLEGASTE AL PACIENTE",
                  font=(theme.FONT, 14, "bold"), fg=theme.SUCCESS).pack(pady=(28, 8))
        self._lbl(f, f"Paciente: {state.nombre_paciente}",
                  font=(theme.FONT, 12)).pack()
        self._lbl(f, f"Afección: {state.afeccion_paciente}",
                  font=(theme.FONT, 11), fg=theme.FG_DIM).pack(pady=4)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=16, pady=14)

        self._lbl(f, "⏳ Esperando decisión del médico...",
                  font=(theme.FONT, 11), fg=theme.ACCENT).pack()

    # ------------------------------------------------------------------
    def _build_fin(self):
        f = self._frame
        self._lbl(f, "✅ MISIÓN COMPLETADA",
                  font=(theme.FONT, 15, "bold"), fg=theme.SUCCESS).pack(pady=(50, 10))
        self._lbl(f, "Paciente entregado en el hospital.",
                  font=(theme.FONT, 11), fg=theme.FG_DIM).pack()