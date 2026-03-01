import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import FaseSimulacion


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


class VentanaConductor(tk.Toplevel):
    def __init__(self, master, state, tick_callback):
        super().__init__(master)
        self.state = state
        self.tick_callback = tick_callback
        self.title("🚑 Vista Conductor")
        self.geometry("520x680")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        self._blink_on = True
        self._blink_job = None

        self._frame = tk.Frame(self)
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
            tk.Label(self._frame, text="Iniciando...", font=("Arial", 14)).pack(pady=40)

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

        tk.Label(f, text="🚑 CONDUCTOR — Elige ruta", font=("Arial", 14, "bold")).pack(pady=(16, 4))
        tk.Label(f, text=f"Destino: {destino_label}", font=("Arial", 11)).pack()
        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=8)

        self._ruta_var = tk.StringVar(value="")
        rutas = state.rutas_disponibles
        if not rutas:
            tk.Label(f, text="No hay rutas disponibles.", fg="red").pack(pady=20)
            return

        # Set default selection
        first_key = next(iter(rutas))
        self._ruta_var.set(first_key)

        for nombre, scored in rutas.items():
            km = scored.route.total_distance_m / 1000
            mins = scored.route.total_time_min
            stars = round(scored.score * 5, 1)
            text = f"{nombre}   │  {km:.1f} km  │  {mins:.1f} min  │  ★{stars}"
            tk.Radiobutton(f, text=text, variable=self._ruta_var,
                           value=nombre, font=("Arial", 10)).pack(anchor='w', padx=30, pady=4)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=8)

        def confirmar():
            elegida = self._ruta_var.get()
            if elegida and elegida in state.rutas_disponibles:
                scored = state.rutas_disponibles[elegida]
                state.ruta_activa_nodes = list(scored.route.nodes[1:])
                state.ruta_activa_edges = list(scored.route.edges)
                state.ruta_activa_label = elegida
                state.ruta_idx = 0
                state.notificar()

        tk.Button(f, text="✅ CONFIRMAR RUTA", font=("Arial", 12, "bold"),
                  bg="#0055ff", fg="white", command=confirmar,
                  padx=12, pady=6).pack(pady=16)

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

        tk.Label(f, text="🚑 CONDUCTOR — En ruta", font=("Arial", 13, "bold")).pack(pady=(14, 2))
        tk.Label(f, text=f"Ruta: {alg_label}  │  {destino_label}",
                 font=("Arial", 10)).pack()
        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=8)

        # Route progress
        nodes = state.ruta_activa_nodes
        idx = state.ruta_idx
        total = len(nodes)
        tk.Label(f, text=f"Progreso: {idx}/{total} nodos",
                 font=("Arial", 10)).pack(anchor='w', padx=16)
        progress_bar = ttk.Progressbar(f, maximum=max(total, 1), value=idx, length=460)
        progress_bar.pack(padx=16, pady=4)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=6)

        # Next steps
        tk.Label(f, text="Próximos tramos:", font=("Arial", 10, "bold")).pack(anchor='w', padx=16)
        edges = state.ruta_activa_edges
        shown = 0
        for i in range(idx, min(idx + 4, len(edges))):
            edge = edges[i]
            name = _edge_name(edge, i)
            dist = _format_dist(getattr(edge, 'length_m', 0))
            tk.Label(f, text=f"  → {name}  ({dist})",
                     font=("Arial", 9), fg='#444').pack(anchor='w', padx=24)
            shown += 1
        if shown == 0:
            tk.Label(f, text="  (llegando al destino)", font=("Arial", 9),
                     fg='#888').pack(anchor='w', padx=24)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=6)

        # Engine telemetry
        telem = state.model.engine.get_telemetry()
        score = telem.get('health_score', 100)
        severity = telem.get('severity', 'OK')
        sev_color = {'OK': 'green', 'WARNING': 'orange', 'CRITICAL': 'red'}.get(severity, 'black')

        tk.Label(f, text="Motor:", font=("Arial", 10, "bold")).pack(anchor='w', padx=16)
        tk.Label(f,
                 text=f"Temp: {telem.get('temperature', 0):.1f}°C  │  "
                      f"RPM: {telem.get('rpm', 0):.0f}  │  "
                      f"[{severity}]",
                 font=("Arial", 10), fg=sev_color).pack(anchor='w', padx=16)

        health_bar = ttk.Progressbar(f, maximum=100, value=score, length=440)
        health_bar.pack(padx=16, pady=2)
        bar_style = 'green' if score > 70 else ('orange' if score >= 40 else 'red')
        tk.Label(f, text=f"Salud: {score:.0f}/100", font=("Arial", 9),
                 fg=bar_style).pack(anchor='w', padx=16)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=6)

        # ----------------------------------------------------------------
        if state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
            paciente = state.model.paciente
            if paciente.gravedad == "grave":
                self._alert_label = tk.Label(f, text="🚨 ALERTA PACIENTE CRÍTICO",
                                             font=("Arial", 12, "bold"), fg="white", bg="red",
                                             relief='raised', padx=10, pady=6)
                self._alert_label.pack(fill='x', padx=16, pady=4)
                self._blink()

        # Footer controls
        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=4)
        footer = tk.Frame(f)
        footer.pack(pady=8)

        mode_lbl = "🔄 Auto" if state.modo_automatico else "🖱️ Manual"

        def toggle_mode():
            state.modo_automatico = not state.modo_automatico
            state.notificar()

        tk.Button(footer, text=mode_lbl, command=toggle_mode,
                  font=("Arial", 10), width=10).pack(side='left', padx=4)

        tick_state = tk.NORMAL if not state.modo_automatico else tk.DISABLED
        tk.Button(footer, text="▶ Tick", state=tick_state,
                  command=self.tick_callback, font=("Arial", 10), width=8).pack(side='left', padx=4)

    # ------------------------------------------------------------------
    def _blink(self):
        if not hasattr(self, '_alert_label') or not self._alert_label.winfo_exists():
            return
        self._blink_on = not self._blink_on
        bg = "red" if self._blink_on else "#ff9999"
        self._alert_label.config(bg=bg)
        self._blink_job = self.after(800, self._blink)

    # ------------------------------------------------------------------
    def _build_en_paciente(self):
        state = self.state
        f = self._frame

        tk.Label(f, text="🚑 LLEGASTE AL PACIENTE", font=("Arial", 14, "bold")).pack(pady=(24, 8))
        tk.Label(f, text=f"Paciente: {state.nombre_paciente}", font=("Arial", 12)).pack()
        tk.Label(f, text=f"Afección: {state.afeccion_paciente}", font=("Arial", 11),
                 fg='#555').pack(pady=4)

        ttk.Separator(f, orient='horizontal').pack(fill='x', padx=10, pady=12)

        tk.Label(f, text="⏳ Esperando decisión del médico...",
                 font=("Arial", 11), fg='#0055aa').pack()

    # ------------------------------------------------------------------
    def _build_fin(self):
        f = self._frame
        tk.Label(f, text="✅ MISIÓN COMPLETADA", font=("Arial", 15, "bold"),
                 fg='green').pack(pady=(40, 10))
        tk.Label(f, text="Paciente entregado en el hospital.",
                 font=("Arial", 11)).pack()