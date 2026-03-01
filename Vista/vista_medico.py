import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import FaseSimulacion
from Model.Visualizacion.afecciones_db import AFECCIONES_DB
from Model.Visualizacion.route_utils import calcular_rutas_por_algoritmo

BG = '#1a1a2e'
FG = '#e0e0e0'
ACCENT = '#4a9eff'


def _semaforo_fc(fc):
    if 60 <= fc <= 100:
        return '✅ OK', 'green'
    if (40 <= fc < 60) or (100 < fc <= 130):
        return '⚠️ ELEVADO' if fc > 100 else '⚠️ BAJO', 'orange'
    return '🔴 CRÍTICO', 'red'


def _semaforo_spo2(spo2):
    if spo2 > 95:
        return '✅ OK', 'green'
    if 90 <= spo2 <= 95:
        return '⚠️ BAJO', 'orange'
    return '🔴 CRÍTICO', 'red'


def _semaforo_fr(fr):
    if 12 <= fr <= 20:
        return '✅ OK', 'green'
    if (8 <= fr < 12) or (20 < fr <= 30):
        return '⚠️ ELEVADO' if fr > 20 else '⚠️ BAJO', 'orange'
    return '🔴 CRÍTICO', 'red'


def _semaforo_pa(pa_sis):
    if 90 <= pa_sis <= 140:
        return '✅ OK', 'green'
    if (70 <= pa_sis < 90) or (140 < pa_sis <= 160):
        return '⚠️ ATENCIÓN', 'orange'
    return '🔴 CRÍTICO', 'red'


class VentanaMedico(tk.Toplevel):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state
        self.title("🏥 Vista Médico")
        self.geometry("500x650")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient='vertical', command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._frame = tk.Frame(self._canvas, bg=BG)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._frame, anchor='nw')
        self._frame.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._canvas_window, width=e.width))

        state.registrar_listener(self.actualizar)
        self.actualizar()

    # ------------------------------------------------------------------
    def _clear(self):
        for widget in self._frame.winfo_children():
            widget.destroy()

    def _lbl(self, parent, text, font=("Arial", 10), fg=FG, bg=BG, **kw):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

    def _sep(self, parent):
        frm = tk.Frame(parent, bg='#333366', height=1)
        frm.pack(fill='x', padx=10, pady=6)

    # ------------------------------------------------------------------
    def actualizar(self):
        self._clear()
        fase = self.state.fase

        self._lbl(self._frame, "🏥 VISTA MÉDICO",
                  font=("Arial", 13, "bold"), fg=ACCENT).pack(pady=(14, 2))

        if fase == FaseSimulacion.YENDO_A_PACIENTE:
            self._build_espera()
        elif fase in (FaseSimulacion.EN_PACIENTE, FaseSimulacion.YENDO_A_HOSPITAL):
            self._build_panel_completo()
        elif fase == FaseSimulacion.FIN:
            self._build_fin()
        else:
            self._lbl(self._frame, "Iniciando...").pack(pady=40)

    # ------------------------------------------------------------------
    def _build_espera(self):
        state = self.state
        f = self._frame

        self._lbl(f, "🚨 En camino al paciente",
                  font=("Arial", 12, "bold"), fg='#ff6600').pack(pady=(10, 4))
        self._lbl(f, f"Paciente: {state.nombre_paciente}",
                  font=("Arial", 11)).pack()
        self._lbl(f, f"Afección registrada: {state.afeccion_paciente}",
                  font=("Arial", 10), fg='#aaa').pack(pady=2)

        self._sep(f)

        afeccion_data = AFECCIONES_DB.get(state.afeccion_paciente, {})
        desc = afeccion_data.get('descripcion', '')
        if desc:
            self._lbl(f, "Descripción:", font=("Arial", 10, "bold")).pack(anchor='w', padx=16)
            self._lbl(f, desc, font=("Arial", 9), wraplength=440,
                      justify='left').pack(anchor='w', padx=16, pady=2)

        specs = afeccion_data.get('specialties_required', [])
        if specs:
            self._sep(f)
            self._lbl(f, "Especialidades requeridas:",
                      font=("Arial", 10, "bold")).pack(anchor='w', padx=16)
            spec_frame = tk.Frame(f, bg=BG)
            spec_frame.pack(anchor='w', padx=16, pady=4)
            for sp in specs:
                tk.Label(spec_frame, text=f"[{sp}]", font=("Arial", 10, "bold"),
                         fg=ACCENT, bg=BG).pack(side='left', padx=4)

        self._sep(f)
        self._lbl(f, "⏳ Esperando llegada...",
                  font=("Arial", 11), fg='#aaaaff').pack(pady=10)

    # ------------------------------------------------------------------
    def _build_panel_completo(self):
        state = self.state
        f = self._frame

        paciente = state.model.paciente
        gravedad = paciente.gravedad
        grav_color = {'leve': 'lightgreen', 'media': 'orange', 'grave': 'red'}.get(gravedad, FG)
        grav_icon = {'leve': '✅ LEVE', 'media': '⚠️ MEDIA', 'grave': '🔴 GRAVE'}.get(gravedad, gravedad.upper())

        self._lbl(f, f"Paciente: {state.nombre_paciente}",
                  font=("Arial", 11, "bold")).pack(anchor='w', padx=16, pady=2)
        self._lbl(f, f"Gravedad: {grav_icon}   │   Afección: {state.afeccion_paciente}",
                  font=("Arial", 10), fg=grav_color).pack(anchor='w', padx=16)

        self._sep(f)

        # Vitals
        self._lbl(f, "CONSTANTES VITALES",
                  font=("Arial", 11, "bold")).pack(anchor='w', padx=16)

        vitals_frame = tk.Frame(f, bg=BG)
        vitals_frame.pack(fill='x', padx=16, pady=4)

        fc_txt, fc_col = _semaforo_fc(paciente.fc)
        spo2_txt, spo2_col = _semaforo_spo2(paciente.spo2)
        fr_txt, fr_col = _semaforo_fr(paciente.fr)
        pa_txt, pa_col = _semaforo_pa(paciente.pa_sis)

        vitals = [
            (f"❤️  FC:", f"{paciente.fc} BPM", fc_txt, fc_col),
            (f"🫁  SpO2:", f"{paciente.spo2:.1f} %", spo2_txt, spo2_col),
            (f"💨  FR:", f"{paciente.fr} r/min", fr_txt, fr_col),
            (f"🩸  PA:", f"{paciente.pa_sis} / {paciente.pa_dia} mmHg", pa_txt, pa_col),
        ]
        for label, val, status, color in vitals:
            row = tk.Frame(vitals_frame, bg=BG)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=label, font=("Arial", 10), fg=FG, bg=BG, width=10,
                     anchor='w').pack(side='left')
            tk.Label(row, text=val, font=("Arial", 10, "bold"), fg=FG, bg=BG,
                     width=18, anchor='w').pack(side='left')
            tk.Label(row, text=f"[{status}]", font=("Arial", 9),
                     fg=color, bg=BG).pack(side='left')

        self._sep(f)

        if state.fase == FaseSimulacion.EN_PACIENTE:
            self._build_selector_hospital(f)
        elif state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
            self._build_info_hospital(f)

    # ------------------------------------------------------------------
    def _build_selector_hospital(self, f):
        state = self.state
        road = state.model.road

        self._lbl(f, "ELIGE HOSPITAL DESTINO",
                  font=("Arial", 11, "bold")).pack(anchor='w', padx=16)

        # Get scored hospitals
        nodo_actual = state.model.posicion.nodo_actual
        scored_hospitals = state.model.analisis.recomendar_hospital(
            nodo_actual,
            afeccion=state.afeccion_paciente,
            afecciones_db=AFECCIONES_DB
        )

        afeccion_data = AFECCIONES_DB.get(state.afeccion_paciente, {})
        required_specs = afeccion_data.get('specialties_required', [])

        self._hosp_var = tk.StringVar(value="")
        if scored_hospitals:
            self._hosp_var.set(str(scored_hospitals[0].route.nodes[-1]))

        for i, scored in enumerate(scored_hospitals):
            dest_node_id = scored.route.nodes[-1]
            dest_node = road.get_node(dest_node_id)
            if not dest_node or not dest_node.hospital:
                continue
            hospital = dest_node.hospital

            label_prefix = "★ RECOMENDADO  " if i == 0 else "   "
            tiempo = scored.route.total_time_min

            has_spec = any(hospital.has_specialty(sp) for sp in required_specs)
            spec_warning = "" if has_spec else "⚠️ No tiene especialidad requerida"

            row_frame = tk.Frame(f, bg='#2a2a4e', relief='groove', bd=1)
            row_frame.pack(fill='x', padx=16, pady=4)

            rb_frame = tk.Frame(row_frame, bg='#2a2a4e')
            rb_frame.pack(anchor='w', fill='x', padx=4, pady=4)

            tk.Radiobutton(
                rb_frame,
                text=f"{label_prefix}{hospital.name}",
                variable=self._hosp_var,
                value=str(dest_node_id),
                font=("Arial", 10, "bold"),
                fg=FG if i > 0 else '#ffd700',
                bg='#2a2a4e',
                selectcolor='#2a2a4e',
                activebackground='#2a2a4e',
                activeforeground=FG,
            ).pack(anchor='w')

            specs_str = ", ".join(hospital.specialties) if hospital.specialties else "—"
            tk.Label(rb_frame, text=f"Especialidades: {specs_str}",
                     font=("Arial", 9), fg='#aaa', bg='#2a2a4e').pack(anchor='w', padx=20)

            if spec_warning:
                tk.Label(rb_frame, text=spec_warning,
                         font=("Arial", 9), fg='orange', bg='#2a2a4e').pack(anchor='w', padx=20)

            beds = hospital.get_available_beds()
            urg = "Sí" if hospital.has_emergency else "No"
            tk.Label(rb_frame,
                     text=f"Camas libres: {beds}  │  Urgencias: {urg}  │  Tiempo: {tiempo:.1f} min",
                     font=("Arial", 9), fg='#aaa', bg='#2a2a4e').pack(anchor='w', padx=20)

        self._sep(f)

        def confirmar_hospital():
            val = self._hosp_var.get()
            if not val:
                return
            hospital_node_id = int(val)
            state.hospital_destino_node_id = hospital_node_id
            nodo_actual = state.model.posicion.nodo_actual
            state.rutas_disponibles = calcular_rutas_por_algoritmo(
                road, nodo_actual, hospital_node_id)
            state.ruta_activa_nodes = []
            state.ruta_activa_label = ""
            state.cambiar_fase(FaseSimulacion.YENDO_A_HOSPITAL)

        tk.Button(f, text="🏥 CONFIRMAR HOSPITAL", command=confirmar_hospital,
                  font=("Arial", 11, "bold"), bg='#00aa44', fg='white',
                  padx=12, pady=6).pack(pady=10)

    # ------------------------------------------------------------------
    def _build_info_hospital(self, f):
        state = self.state
        road = state.model.road

        h_node = road.get_node(state.hospital_destino_node_id)
        if not h_node or not h_node.hospital:
            self._lbl(f, "Hospital destino no encontrado.", fg='red').pack(pady=10)
            return

        hospital = h_node.hospital
        self._lbl(f, "HOSPITAL DESTINO", font=("Arial", 11, "bold")).pack(anchor='w', padx=16)

        info_frame = tk.Frame(f, bg='#2a2a4e', relief='groove', bd=1)
        info_frame.pack(fill='x', padx=16, pady=6)

        self._lbl(info_frame, f"  {hospital.name}",
                  font=("Arial", 11, "bold"), fg='#ffd700',
                  bg='#2a2a4e').pack(anchor='w', pady=4)
        specs_str = ", ".join(hospital.specialties) if hospital.specialties else "—"
        self._lbl(info_frame, f"  Especialidades: {specs_str}",
                  font=("Arial", 9), fg='#aaa', bg='#2a2a4e').pack(anchor='w')
        beds = hospital.get_available_beds()
        urg = "Sí" if hospital.has_emergency else "No"
        self._lbl(info_frame, f"  Camas libres: {beds}  │  Urgencias: {urg}",
                  font=("Arial", 9), fg='#aaa', bg='#2a2a4e').pack(anchor='w', pady=4)

    # ------------------------------------------------------------------
    def _build_fin(self):
        f = self._frame
        self._lbl(f, "✅ MISIÓN COMPLETADA",
                  font=("Arial", 14, "bold"), fg='lightgreen').pack(pady=(40, 10))
        self._lbl(f, "El paciente fue entregado correctamente.",
                  font=("Arial", 11)).pack()
