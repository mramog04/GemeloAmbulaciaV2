import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import AppState, FaseSimulacion
from Model.Visualizacion.route_utils import calcular_5_rutas


class VentanaConductor:
    """Ventana de control del conductor de la ambulancia."""

    def __init__(self, root: tk.Tk, state: AppState, tick_callback):
        self.state = state
        self.root = root
        self.tick_callback = tick_callback
        self._rutas = []
        self._rutas_hospital = []
        self._ruta_var = tk.IntVar(value=0)
        self._hosp_var = tk.IntVar(value=0)

        self.win = tk.Toplevel(root)
        self.win.title("🚑 Vista Conductor")
        self.win.geometry("500x600")
        self.win.protocol("WM_DELETE_WINDOW", root.quit)
        self.win.resizable(False, False)

        self._frame_main = tk.Frame(self.win, bg='#f0f0f0')
        self._frame_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._construir_footer()
        self._refrescar()

        state.registrar_listener(self._refrescar)

    # ------------------------------------------------------------------ #
    # Footer siempre visible                                               #
    # ------------------------------------------------------------------ #

    def _construir_footer(self):
        foot = tk.Frame(self.win, bg='#dde', relief=tk.GROOVE, bd=1)
        foot.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 6))

        self._lbl_motor = tk.Label(foot, text="Estado motor: —",
                                   bg='#dde', font=('Arial', 9))
        self._lbl_motor.pack(side=tk.LEFT, padx=8, pady=4)

        self._btn_auto = tk.Button(foot, text="🔄 Automático",
                                   command=self._toggle_modo, font=('Arial', 9))
        self._btn_auto.pack(side=tk.RIGHT, padx=4, pady=4)

        self._btn_tick = tk.Button(foot, text="▶ Tick",
                                   command=self._manual_tick, font=('Arial', 9))
        self._btn_tick.pack(side=tk.RIGHT, padx=4, pady=4)

    def _toggle_modo(self):
        self.state.modo_automatico = not self.state.modo_automatico
        self._actualizar_footer()

    def _manual_tick(self):
        if not self.state.modo_automatico:
            self.tick_callback()

    def _actualizar_footer(self):
        model = self.state.model
        snap = model.snapshot()
        eng = snap.get('ambulancia_fisica', {}).get('engine', {})
        temp = eng.get('temperature', '—')
        rpm = eng.get('rpm', '—')
        self._lbl_motor.config(text=f"Estado motor: Temp {temp}°C | RPM {rpm}")
        modo = "🔄 Automático" if self.state.modo_automatico else "⏩ Manual"
        self._btn_auto.config(text=modo)
        vis = tk.NORMAL if not self.state.modo_automatico else tk.DISABLED
        self._btn_tick.config(state=vis)

    # ------------------------------------------------------------------ #
    # Refresco principal                                                   #
    # ------------------------------------------------------------------ #

    def _refrescar(self):
        self._actualizar_footer()
        for w in self._frame_main.winfo_children():
            w.destroy()

        fase = self.state.fase
        if fase in (FaseSimulacion.YENDO_A_PACIENTE, FaseSimulacion.YENDO_A_HOSPITAL):
            self._panel_rutas()
        elif fase == FaseSimulacion.EN_PACIENTE:
            self._panel_hospital()
        elif fase == FaseSimulacion.FIN:
            self._panel_fin()
        else:
            tk.Label(self._frame_main, text="Configurando simulación…",
                     bg='#f0f0f0', font=('Arial', 12)).pack(pady=30)

    # ------------------------------------------------------------------ #
    # Panel: selección de ruta                                             #
    # ------------------------------------------------------------------ #

    def _panel_rutas(self):
        state = self.state
        fm = self._frame_main
        fm.config(bg='#f0f0f0')

        if state.fase == FaseSimulacion.YENDO_A_PACIENTE:
            destino_txt = f"Paciente: {state.nombre_paciente}"
            dest_id = state.nodo_paciente
        else:
            dest_id = state.hospital_destino_node_id
            hosp_node = state.model.road.get_node(dest_id) if dest_id else None
            nombre_h = "Hospital"
            if hosp_node and hosp_node.is_hospital():
                nombre_h = hosp_node.hospital.name
            destino_txt = f"Hospital: {nombre_h}"

        tk.Label(fm, text="🚑 VISTA CONDUCTOR", font=('Arial', 14, 'bold'),
                 bg='#f0f0f0').pack(pady=(8, 2))
        tk.Label(fm, text=f"Destino: {destino_txt}", font=('Arial', 10),
                 bg='#f0f0f0').pack()
        ttk.Separator(fm, orient='horizontal').pack(fill=tk.X, pady=6)

        origin_id = state.model.posicion.nodo_actual
        if dest_id is None:
            tk.Label(fm, text="Sin destino configurado.", bg='#f0f0f0').pack()
            return

        # Calcular rutas si no las tenemos aún o cambiaron
        rutas = calcular_5_rutas(state.model.analisis, origin_id, dest_id)
        self._rutas = rutas

        if not rutas:
            tk.Label(fm, text="No se pudo calcular ninguna ruta.",
                     bg='#f0f0f0', fg='red').pack(pady=10)
            return

        tk.Label(fm, text="Selecciona una ruta:", font=('Arial', 10, 'bold'),
                 bg='#f0f0f0').pack(anchor='w', padx=10)

        self._ruta_var.set(0)
        for i, sr in enumerate(rutas):
            km = sr.route.total_distance_m / 1000
            mins = sr.breakdown.get('tiempo', sr.route.total_time_min)
            texto = f"Ruta {i+1} — {sr.label}   |  {km:.1f} km  |  {mins:.1f} min"
            rb = tk.Radiobutton(fm, text=texto, variable=self._ruta_var, value=i,
                                bg='#f0f0f0', font=('Arial', 10), anchor='w')
            rb.pack(fill=tk.X, padx=20, pady=2)

        tk.Button(fm, text="✅ CONFIRMAR RUTA", font=('Arial', 11, 'bold'),
                  bg='#27ae60', fg='white',
                  command=self._confirmar_ruta).pack(pady=14)

    def _confirmar_ruta(self):
        idx = self._ruta_var.get()
        if idx < len(self._rutas):
            sr = self._rutas[idx]
            # Saltar el nodo origen (ya estamos ahí)
            self.state.ruta_activa = sr.route.nodes[1:]
            self.state.ruta_idx = 0
            self.state.notificar()

    # ------------------------------------------------------------------ #
    # Panel: selección de hospital                                         #
    # ------------------------------------------------------------------ #

    def _panel_hospital(self):
        state = self.state
        fm = self._frame_main
        fm.config(bg='#f0f0f0')

        tk.Label(fm, text="🚑 LLEGASTE AL PACIENTE", font=('Arial', 13, 'bold'),
                 bg='#f0f0f0').pack(pady=(8, 2))
        tk.Label(fm, text=f"Paciente: {state.nombre_paciente}  |  Afección: {state.afeccion_paciente}",
                 font=('Arial', 9), bg='#f0f0f0').pack()
        ttk.Separator(fm, orient='horizontal').pack(fill=tk.X, pady=6)

        tk.Label(fm, text="Elige hospital destino:", font=('Arial', 10, 'bold'),
                 bg='#f0f0f0').pack(anchor='w', padx=10)

        origin_id = state.model.posicion.nodo_actual
        rutas_hosp = state.model.analisis.recomendar_hospital(origin_id)
        self._rutas_hospital = rutas_hosp

        if not rutas_hosp:
            tk.Label(fm, text="No hay hospitales alcanzables.", bg='#f0f0f0', fg='red').pack()
            return

        self._hosp_var.set(0)
        for i, sr in enumerate(rutas_hosp):
            dest_node_id = sr.route.nodes[-1]
            hosp_node = state.model.road.get_node(dest_node_id)
            if hosp_node is None or not hosp_node.is_hospital():
                continue
            hosp = hosp_node.hospital
            specs = ', '.join(hosp.specialties) if hosp.specialties else '—'
            camas = hosp.get_available_beds()
            cap = hosp.capacity
            urg = "Sí" if hosp.has_emergency else "No"
            mins = sr.breakdown.get('tiempo', sr.route.total_time_min)
            recom = "  ★ RECOMENDADO" if i == 0 else ""

            frm = tk.Frame(fm, bg='#f0f0f0')
            frm.pack(fill=tk.X, padx=10, pady=3)
            rb = tk.Radiobutton(frm, text=f"{hosp.name}{recom}",
                                variable=self._hosp_var, value=i,
                                bg='#f0f0f0', font=('Arial', 10, 'bold'), anchor='w')
            rb.pack(anchor='w')
            tk.Label(frm, text=f"   Especialidades: {specs}", bg='#f0f0f0',
                     font=('Arial', 9)).pack(anchor='w')
            tk.Label(frm, text=f"   Camas libres: {camas}/{cap}  |  Urgencias: {urg}",
                     bg='#f0f0f0', font=('Arial', 9)).pack(anchor='w')
            tk.Label(frm, text=f"   Tiempo estimado: {mins:.1f} min",
                     bg='#f0f0f0', font=('Arial', 9)).pack(anchor='w')

        tk.Button(fm, text="🏥 IR AL HOSPITAL", font=('Arial', 11, 'bold'),
                  bg='#2980b9', fg='white',
                  command=self._ir_hospital).pack(pady=14)

    def _ir_hospital(self):
        idx = self._hosp_var.get()
        if idx < len(self._rutas_hospital):
            sr = self._rutas_hospital[idx]
            dest_node_id = sr.route.nodes[-1]
            self.state.hospital_destino_node_id = dest_node_id
            self.state.ruta_activa = sr.route.nodes[1:]
            self.state.ruta_idx = 0
            self.state.cambiar_fase(FaseSimulacion.YENDO_A_HOSPITAL)

    # ------------------------------------------------------------------ #
    # Panel: misión completada                                             #
    # ------------------------------------------------------------------ #

    def _panel_fin(self):
        state = self.state
        fm = self._frame_main
        fm.config(bg='#f0f0f0')

        tk.Label(fm, text="✅ MISIÓN COMPLETADA", font=('Arial', 14, 'bold'),
                 fg='#27ae60', bg='#f0f0f0').pack(pady=(30, 10))

        hosp_nombre = "Hospital"
        if state.hospital_destino_node_id is not None:
            hn = state.model.road.get_node(state.hospital_destino_node_id)
            if hn and hn.is_hospital():
                hosp_nombre = hn.hospital.name
        tk.Label(fm, text=f"Llegaste a: {hosp_nombre}", font=('Arial', 11),
                 bg='#f0f0f0').pack()
        tk.Label(fm, text="Paciente entregado correctamente.", font=('Arial', 10),
                 bg='#f0f0f0').pack(pady=6)

        tk.Button(fm, text="🔄 Nueva Misión", font=('Arial', 11, 'bold'),
                  bg='#8e44ad', fg='white',
                  command=self._nueva_mision).pack(pady=20)

    def _nueva_mision(self):
        self.win.destroy()
        self.root.quit()
