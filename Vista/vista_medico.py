import os
import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import FaseSimulacion
from Model.Visualizacion.afecciones_db import AFECCIONES_DB
from Model.Visualizacion.route_utils import calcular_rutas_por_algoritmo
from Vista import theme

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def _semaforo_fc(fc):
    if 60 <= fc <= 100:
        return '✅ OK', theme.SUCCESS
    if (40 <= fc < 60) or (100 < fc <= 130):
        return '⚠️ ELEVADO' if fc > 100 else '⚠️ BAJO', theme.WARNING
    return '🔴 CRÍTICO', theme.DANGER


def _semaforo_spo2(spo2):
    if spo2 > 95:
        return '✅ OK', theme.SUCCESS
    if 90 <= spo2 <= 95:
        return '⚠️ BAJO', theme.WARNING
    return '🔴 CRÍTICO', theme.DANGER


def _semaforo_fr(fr):
    if 12 <= fr <= 20:
        return '✅ OK', theme.SUCCESS
    if (8 <= fr < 12) or (20 < fr <= 30):
        return '⚠️ ELEVADO' if fr > 20 else '⚠️ BAJO', theme.WARNING
    return '🔴 CRÍTICO', theme.DANGER


def _semaforo_pa(pa_sis):
    if 90 <= pa_sis <= 140:
        return '✅ OK', theme.SUCCESS
    if (70 <= pa_sis < 90) or (140 < pa_sis <= 160):
        return '⚠️ ATENCIÓN', theme.WARNING
    return '🔴 CRÍTICO', theme.DANGER


class VentanaMedico(tk.Toplevel):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state
        self.title("🏥 Vista Médico")
        self.geometry("900x500")
        self.resizable(False, False)
        self.configure(bg=theme.BG)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        self._blink_on = True
        self._blink_job = None

        # Try to load patient image
        self._img_paciente = None
        try:
            from PIL import Image, ImageTk
            img_path = os.path.join(_ASSETS_DIR, "paciente.png")
            if os.path.exists(img_path):
                pil_img = Image.open(img_path).resize((64, 64))
                self._img_paciente = ImageTk.PhotoImage(pil_img)
        except Exception:
            pass

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

    def _lbl(self, parent, text, font=None, fg=None, bg=None, **kw):
        if font is None:
            font = (theme.FONT, 10)
        if fg is None:
            fg = theme.FG
        if bg is None:
            bg = theme.BG
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

    def _sep(self, parent):
        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=6)

    # ------------------------------------------------------------------
    def actualizar(self):
        self._clear()
        fase = self.state.fase

        # Top header bar
        header = tk.Frame(self._frame, bg=theme.BG_CARD)
        header.pack(fill='x')
        self._lbl(header, "🏥 VISTA MÉDICO",
                  font=(theme.FONT, 12, "bold"), fg=theme.ACCENT,
                  bg=theme.BG_CARD).pack(side='left', padx=14, pady=8)
        fase_names = {
            FaseSimulacion.YENDO_A_PACIENTE: "Yendo al paciente",
            FaseSimulacion.EN_PACIENTE: "En paciente",
            FaseSimulacion.YENDO_A_HOSPITAL: "Yendo al hospital",
            FaseSimulacion.FIN: "Fin",
        }
        self._lbl(header, fase_names.get(fase, ""),
                  font=(theme.FONT, 10), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(side='right', padx=14, pady=8)

        content = tk.Frame(self._frame, bg=theme.BG)
        content.pack(fill='both', expand=True)

        if fase == FaseSimulacion.YENDO_A_PACIENTE:
            self._build_espera(content)
        elif fase in (FaseSimulacion.EN_PACIENTE, FaseSimulacion.YENDO_A_HOSPITAL):
            self._build_panel_completo(content)
        elif fase == FaseSimulacion.FIN:
            self._build_fin(content)
        else:
            self._lbl(content, "Iniciando...").pack(pady=40)

    # ------------------------------------------------------------------
    def _build_espera(self, parent):
        state = self.state

        card = tk.Frame(parent, bg=theme.BG_CARD, relief='flat', bd=0)
        card.place(relx=0.5, rely=0.5, anchor='center', width=560, height=360)

        self._lbl(card, "📞 AVISO 112",
                  font=(theme.FONT, 18, "bold"), fg=theme.DANGER,
                  bg=theme.BG_CARD).pack(pady=(20, 6))

        self._lbl(card, f"Paciente: {state.nombre_paciente}   │   Afección: {state.afeccion_paciente}",
                  font=(theme.FONT, 11, "bold"), bg=theme.BG_CARD).pack(pady=2)

        ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20, pady=8)

        afeccion_data = AFECCIONES_DB.get(state.afeccion_paciente, {})
        desc = afeccion_data.get('descripcion', '')
        if desc:
            self._lbl(card, desc, font=(theme.FONT, 9), fg=theme.FG_DIM,
                      bg=theme.BG_CARD, wraplength=500,
                      justify='left').pack(anchor='w', padx=20, pady=2)

        specs = afeccion_data.get('specialties_required', [])
        if specs:
            spec_frame = tk.Frame(card, bg=theme.BG_CARD)
            spec_frame.pack(anchor='w', padx=20, pady=6)
            self._lbl(spec_frame, "Especialidades: ",
                      font=(theme.FONT, 9, "bold"),
                      bg=theme.BG_CARD).pack(side='left')
            for sp in specs:
                tk.Label(spec_frame, text=f" {sp} ",
                         font=(theme.FONT, 9, "bold"),
                         fg="white", bg=theme.ACCENT,
                         padx=4, pady=2).pack(side='left', padx=3)

        ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20, pady=8)

        # ETA
        eta = "Calculando..."
        if state.rutas_disponibles:
            try:
                first = next(iter(state.rutas_disponibles.values()))
                eta = f"{first.route.total_time_min:.1f} min"
            except Exception:
                pass
        self._lbl(card, f"⏱  ETA: {eta}",
                  font=(theme.FONT, 10), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(pady=2)

        self._wait_label = self._lbl(card, "⏳ En camino...",
                                     font=(theme.FONT, 11, "bold"), fg=theme.ACCENT,
                                     bg=theme.BG_CARD)
        self._wait_label.pack(pady=(8, 16))

    # ------------------------------------------------------------------
    def _build_panel_completo(self, parent):
        state = self.state
        paciente = state.model.paciente
        gravedad = paciente.gravedad
        grav_color = {'leve': theme.SUCCESS, 'media': theme.WARNING,
                      'grave': theme.DANGER}.get(gravedad, theme.FG)
        grav_icon = {'leve': '✅ LEVE', 'media': '⚠️ MEDIA',
                     'grave': '🔴 GRAVE'}.get(gravedad, gravedad.upper())

        parent.columnconfigure(0, weight=1, minsize=160)
        parent.columnconfigure(1, weight=2, minsize=220)
        parent.columnconfigure(2, weight=3, minsize=380)
        parent.rowconfigure(0, weight=1)

        # ── Left column: patient image + name + severity badge ──────
        left = tk.Frame(parent, bg=theme.BG_CARD)
        left.grid(row=0, column=0, sticky='nsew', padx=(8, 4), pady=8)

        if self._img_paciente:
            tk.Label(left, image=self._img_paciente,
                     bg=theme.BG_CARD).pack(pady=(20, 8))
        else:
            canvas = tk.Canvas(left, width=64, height=64,
                               bg=theme.BG_CARD, highlightthickness=0)
            canvas.pack(pady=(20, 8))
            canvas.create_oval(4, 4, 60, 60, fill=theme.WARNING, outline="")

        self._lbl(left, state.nombre_paciente,
                  font=(theme.FONT, 10, "bold"), bg=theme.BG_CARD).pack()
        tk.Label(left, text=grav_icon,
                 font=(theme.FONT, 9, "bold"),
                 fg="white", bg=grav_color,
                 padx=6, pady=3).pack(pady=8)

        # ── Center column: vitals ────────────────────────────────────
        center = tk.Frame(parent, bg=theme.BG)
        center.grid(row=0, column=1, sticky='nsew', padx=4, pady=8)

        self._lbl(center, "CONSTANTES VITALES",
                  font=(theme.FONT, 10, "bold"), fg=theme.ACCENT).pack(pady=(12, 8))

        fc_txt, fc_col = _semaforo_fc(paciente.fc)
        spo2_txt, spo2_col = _semaforo_spo2(paciente.spo2)
        fr_txt, fr_col = _semaforo_fr(paciente.fr)
        pa_txt, pa_col = _semaforo_pa(paciente.pa_sis)

        vitals = [
            ("❤️  FC:", f"{paciente.fc} BPM", fc_txt, fc_col),
            ("🫁  SpO2:", f"{paciente.spo2:.1f} %", spo2_txt, spo2_col),
            ("💨  FR:", f"{paciente.fr} r/min", fr_txt, fr_col),
            ("🩸  PA:", f"{paciente.pa_sis}/{paciente.pa_dia} mmHg", pa_txt, pa_col),
        ]
        for label, val, status, color in vitals:
            row = tk.Frame(center, bg=theme.BG_CARD, relief='flat')
            row.pack(fill='x', padx=4, pady=3)
            tk.Label(row, text=label, font=(theme.FONT, 9),
                     fg=theme.FG_DIM, bg=theme.BG_CARD,
                     width=9, anchor='w').pack(side='left', padx=6, pady=4)
            tk.Label(row, text=val, font=(theme.FONT, 9, "bold"),
                     fg=theme.FG, bg=theme.BG_CARD,
                     width=16, anchor='w').pack(side='left')
            tk.Label(row, text=status, font=(theme.FONT, 8),
                     fg=color, bg=theme.BG_CARD).pack(side='left', padx=4)

        # ── Right column: critical alert + hospital selector/info ───
        right = tk.Frame(parent, bg=theme.BG)
        right.grid(row=0, column=2, sticky='nsew', padx=(4, 8), pady=8)

        if gravedad == "grave":
            self._alert_label = tk.Label(right,
                                         text="🚨 PACIENTE CRÍTICO",
                                         font=(theme.FONT, 12, "bold"),
                                         fg="white", bg=theme.DANGER,
                                         relief='flat', padx=8, pady=8)
            self._alert_label.pack(fill='x', pady=(0, 6))
            self._blink()

        if state.fase == FaseSimulacion.EN_PACIENTE:
            self._build_selector_hospital(right)
        elif state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
            self._build_info_hospital(right)

    # ------------------------------------------------------------------
    def _blink(self):
        if not hasattr(self, '_alert_label') or not self._alert_label.winfo_exists():
            return
        self._blink_on = not self._blink_on
        bg = theme.DANGER if self._blink_on else "#aa1111"
        self._alert_label.config(bg=bg)
        self._blink_job = self.after(800, self._blink)

    # ------------------------------------------------------------------
    def _build_selector_hospital(self, parent):
        state = self.state
        road = state.model.road

        self._lbl(parent, "ELIGE HOSPITAL DESTINO",
                  font=(theme.FONT, 10, "bold"), fg=theme.ACCENT).pack(anchor='w', padx=8, pady=(4, 2))

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

        scroll_frame = tk.Frame(parent, bg=theme.BG)
        scroll_frame.pack(fill='both', expand=True, padx=4)

        for i, scored in enumerate(scored_hospitals):
            dest_node_id = scored.route.nodes[-1]
            dest_node = road.get_node(dest_node_id)
            if not dest_node or not dest_node.hospital:
                continue
            hospital = dest_node.hospital

            label_prefix = "★ " if i == 0 else "   "
            tiempo = scored.route.total_time_min
            has_spec = any(hospital.has_specialty(sp) for sp in required_specs)
            spec_warning = "" if has_spec else "⚠️ Sin especialidad"

            row_frame = tk.Frame(scroll_frame, bg=theme.BG_CARD, relief='flat', bd=0)
            row_frame.pack(fill='x', padx=0, pady=3)

            tk.Radiobutton(
                row_frame,
                text=f"{label_prefix}{hospital.name}",
                variable=self._hosp_var,
                value=str(dest_node_id),
                font=(theme.FONT, 9, "bold"),
                fg=theme.GOLD if i == 0 else theme.FG,
                bg=theme.BG_CARD,
                selectcolor=theme.BG_CARD,
                activebackground=theme.BG_CARD,
                activeforeground=theme.ACCENT,
            ).pack(anchor='w', padx=6, pady=(4, 0))

            specs_str = ", ".join(hospital.specialties) if hospital.specialties else "—"
            self._lbl(row_frame, f"Esp: {specs_str}   {tiempo:.1f} min",
                      font=(theme.FONT, 8), fg=theme.FG_DIM,
                      bg=theme.BG_CARD).pack(anchor='w', padx=24)
            if spec_warning:
                self._lbl(row_frame, spec_warning,
                           font=(theme.FONT, 8), fg=theme.WARNING,
                           bg=theme.BG_CARD).pack(anchor='w', padx=24, pady=(0, 4))

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

        tk.Button(parent, text="🏥 CONFIRMAR HOSPITAL",
                  command=confirmar_hospital,
                  font=(theme.FONT, 10, "bold"),
                  bg=theme.SUCCESS, fg="white",
                  activebackground="#3d7a35", activeforeground="white",
                  relief='flat', padx=10, pady=6).pack(pady=8)

    # ------------------------------------------------------------------
    def _build_info_hospital(self, parent):
        state = self.state
        road = state.model.road

        h_node = road.get_node(state.hospital_destino_node_id)
        if not h_node or not h_node.hospital:
            self._lbl(parent, "Hospital destino no encontrado.", fg=theme.DANGER).pack(pady=10)
            return

        hospital = h_node.hospital
        self._lbl(parent, "HOSPITAL DESTINO",
                  font=(theme.FONT, 10, "bold"), fg=theme.ACCENT).pack(anchor='w', padx=8, pady=(4, 2))

        info_frame = tk.Frame(parent, bg=theme.BG_CARD, relief='flat', bd=0)
        info_frame.pack(fill='x', padx=4, pady=4)

        self._lbl(info_frame, f"  {hospital.name}",
                  font=(theme.FONT, 11, "bold"), fg=theme.GOLD,
                  bg=theme.BG_CARD).pack(anchor='w', pady=(8, 2))
        specs_str = ", ".join(hospital.specialties) if hospital.specialties else "—"
        self._lbl(info_frame, f"  Especialidades: {specs_str}",
                  font=(theme.FONT, 9), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(anchor='w')
        beds = hospital.get_available_beds()
        urg = "Sí" if hospital.has_emergency else "No"
        self._lbl(info_frame, f"  Camas libres: {beds}  │  Urgencias: {urg}",
                  font=(theme.FONT, 9), fg=theme.FG_DIM,
                  bg=theme.BG_CARD).pack(anchor='w', pady=(2, 8))

    # ------------------------------------------------------------------
    def _build_fin(self, parent):
        self._lbl(parent, "✅ MISIÓN COMPLETADA",
                  font=(theme.FONT, 14, "bold"), fg=theme.SUCCESS).pack(pady=(60, 10))
        self._lbl(parent, "El paciente fue entregado correctamente.",
                  font=(theme.FONT, 11), fg=theme.FG_DIM).pack()
