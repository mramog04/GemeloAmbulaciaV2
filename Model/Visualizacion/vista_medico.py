import tkinter as tk
from tkinter import ttk

from Model.Visualizacion.app_state import AppState, FaseSimulacion
from Model.Visualizacion.afecciones_db import AFECCIONES_DB

BG = '#1a1a2e'
FG = '#e0e0e0'

COLOR_GRAVEDAD = {
    "leve": "#27ae60",
    "media": "#f39c12",
    "grave": "#e74c3c",
}


def _color_fc(fc):
    if fc < 50 or fc > 130:
        return '#e74c3c'
    if fc > 100:
        return '#f39c12'
    return '#27ae60'


def _color_spo2(spo2):
    if spo2 < 90:
        return '#e74c3c'
    if spo2 < 95:
        return '#f39c12'
    return '#27ae60'


def _color_fr(fr):
    if fr > 30:
        return '#e74c3c'
    if fr > 20:
        return '#f39c12'
    return '#27ae60'


def _color_pa(pa_sis):
    if pa_sis > 160 or pa_sis < 70:
        return '#e74c3c'
    if pa_sis > 140 or pa_sis < 90:
        return '#f39c12'
    return '#27ae60'


def _label_fc(fc):
    if fc < 50 or fc > 130:
        return '🔴 CRÍTICO'
    if fc > 100:
        return '⚠️ ALTO'
    return '✅ OK'


def _label_spo2(spo2):
    if spo2 < 90:
        return '🔴 CRÍTICO'
    if spo2 < 95:
        return '⚠️ BAJO'
    return '✅ OK'


def _label_fr(fr):
    if fr > 30:
        return '🔴 CRÍTICO'
    if fr > 20:
        return '⚠️ ALTO'
    return '✅ OK'


def _label_pa(pa_sis):
    if pa_sis > 160 or pa_sis < 70:
        return '🔴 CRÍTICO'
    if pa_sis > 140 or pa_sis < 90:
        return '⚠️ ATENCIÓN'
    return '✅ OK'


class VentanaMedico:
    """Ventana médica con signos vitales y recomendaciones hospitalarias."""

    def __init__(self, root: tk.Tk, state: AppState):
        self.state = state

        self.win = tk.Toplevel(root)
        self.win.title("🏥 Vista Médico")
        self.win.geometry("480x600")
        self.win.configure(bg=BG)
        self.win.protocol("WM_DELETE_WINDOW", root.quit)
        self.win.resizable(False, False)

        self._frame = tk.Frame(self.win, bg=BG)
        self._frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self._refrescar()
        state.registrar_listener(self._refrescar)

    # ------------------------------------------------------------------ #
    # Refresco principal                                                   #
    # ------------------------------------------------------------------ #

    def _refrescar(self):
        for w in self._frame.winfo_children():
            w.destroy()

        fase = self.state.fase
        if fase == FaseSimulacion.YENDO_A_PACIENTE:
            self._panel_espera()
        elif fase in (FaseSimulacion.EN_PACIENTE, FaseSimulacion.YENDO_A_HOSPITAL):
            self._panel_vitales()
        elif fase == FaseSimulacion.FIN:
            self._panel_fin()
        else:
            tk.Label(self._frame, text="🏥 VISTA MÉDICO", font=('Arial', 14, 'bold'),
                     bg=BG, fg=FG).pack(pady=20)

    # ------------------------------------------------------------------ #
    # Paneles por fase                                                     #
    # ------------------------------------------------------------------ #

    def _panel_espera(self):
        state = self.state
        f = self._frame

        tk.Label(f, text="🏥 VISTA MÉDICO", font=('Arial', 14, 'bold'),
                 bg=BG, fg=FG).pack(pady=(10, 20))
        tk.Label(f, text="Esperando llegada al paciente…",
                 font=('Arial', 12), bg=BG, fg='#aaaaaa').pack(pady=6)

        # Barra de progreso estimada
        total = max(len(state.ruta_activa), 1)
        progreso = state.ruta_idx / total
        bar = ttk.Progressbar(f, orient='horizontal', length=300,
                               mode='determinate', value=progreso * 100)
        bar.pack(pady=8)

        tk.Label(f, text=f"Paciente: {state.nombre_paciente}",
                 font=('Arial', 11), bg=BG, fg=FG).pack(pady=4)
        tk.Label(f, text=f"Afección: {state.afeccion_paciente}",
                 font=('Arial', 10), bg=BG, fg='#bbbbbb').pack()

        if state.nodo_paciente is not None:
            node = state.model.road.get_node(state.nodo_paciente)
            if node:
                tk.Label(f, text=f"Nodo destino: ({node.lat:.5f}, {node.lon:.5f})",
                         font=('Arial', 9), bg=BG, fg='#888888').pack(pady=4)

    def _panel_vitales(self):
        state = self.state
        model = state.model
        paciente = model.paciente
        f = self._frame

        # Cabecera
        tk.Label(f, text="🏥 VISTA MÉDICO", font=('Arial', 14, 'bold'),
                 bg=BG, fg=FG).pack(pady=(6, 2))

        grav_color = COLOR_GRAVEDAD.get(paciente.gravedad, FG)
        grav_emoji = {'leve': '🟢', 'media': '⚠️', 'grave': '🔴'}.get(paciente.gravedad, '')
        tk.Label(f, text=f"Paciente: {paciente.nombre}  |  Gravedad: {grav_emoji} {paciente.gravedad.upper()}",
                 font=('Arial', 10), bg=BG, fg=grav_color).pack()
        tk.Label(f, text=f"Afección: {state.afeccion_paciente}",
                 font=('Arial', 10), bg=BG, fg='#cccccc').pack()

        self._separador()

        # Constantes vitales
        tk.Label(f, text="CONSTANTES VITALES", font=('Arial', 11, 'bold'),
                 bg=BG, fg='#aaddff').pack(anchor='w', padx=10, pady=(6, 2))

        self._vital_row(f, "❤️  FC:", f"{paciente.fc} BPM",
                        _color_fc(paciente.fc), _label_fc(paciente.fc))
        self._vital_row(f, "🫁  SpO2:", f"{paciente.spo2:.1f} %",
                        _color_spo2(paciente.spo2), _label_spo2(paciente.spo2))
        self._vital_row(f, "💨  FR:", f"{paciente.fr} r/min",
                        _color_fr(paciente.fr), _label_fr(paciente.fr))
        self._vital_row(f, "🩸  PA:", f"{paciente.pa_sis}/{paciente.pa_dia} mmHg",
                        _color_pa(paciente.pa_sis), _label_pa(paciente.pa_sis))

        self._separador()

        # Recomendaciones hospitalarias
        tk.Label(f, text="RECOMENDACIÓN HOSPITALARIA", font=('Arial', 11, 'bold'),
                 bg=BG, fg='#aaddff').pack(anchor='w', padx=10, pady=(6, 2))

        origin_id = model.posicion.nodo_actual
        rutas_hosp = model.analisis.recomendar_hospital(origin_id)

        afeccion_info = AFECCIONES_DB.get(state.afeccion_paciente, {})
        specs_requeridas = afeccion_info.get('specialties_required', [])

        for i, sr in enumerate(rutas_hosp[:4]):
            dest_node_id = sr.route.nodes[-1]
            hn = model.road.get_node(dest_node_id)
            if hn is None or not hn.is_hospital():
                continue
            hosp = hn.hospital
            tiene_spec = any(hosp.has_specialty(s) for s in specs_requeridas)
            mins = sr.breakdown.get('tiempo', sr.route.total_time_min)
            camas = hosp.get_available_beds()

            icono = "★" if i == 0 else "○"
            color = '#27ae60' if i == 0 else '#f39c12'
            tk.Label(f, text=f"{icono} {hosp.name}",
                     font=('Arial', 10, 'bold'), bg=BG, fg=color).pack(anchor='w', padx=16)

            if specs_requeridas:
                spec_txt = "✓" if tiene_spec else "✗ No tiene especialidad requerida"
                spec_color = '#27ae60' if tiene_spec else '#e74c3c'
                specs_str = ', '.join(hosp.specialties) if hosp.specialties else '—'
                if tiene_spec:
                    tk.Label(f, text=f"   → Tiene: {specs_str} ✓",
                             font=('Arial', 9), bg=BG, fg=spec_color).pack(anchor='w', padx=20)
                else:
                    tk.Label(f, text=f"   → {spec_txt}",
                             font=('Arial', 9), bg=BG, fg=spec_color).pack(anchor='w', padx=20)

            tk.Label(f, text=f"   → Camas: {camas} libres  |  Llega en: {mins:.1f} min",
                     font=('Arial', 9), bg=BG, fg=FG).pack(anchor='w', padx=20)

    def _panel_fin(self):
        f = self._frame
        tk.Label(f, text="🏥 VISTA MÉDICO", font=('Arial', 14, 'bold'),
                 bg=BG, fg=FG).pack(pady=(30, 20))
        tk.Label(f, text="✅ Paciente entregado al hospital.", font=('Arial', 12),
                 bg=BG, fg='#27ae60').pack(pady=6)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _separador(self):
        sep = tk.Frame(self._frame, height=1, bg='#444466')
        sep.pack(fill=tk.X, padx=10, pady=6)

    def _vital_row(self, parent, label, valor, color, estado):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill=tk.X, padx=16, pady=2)
        tk.Label(row, text=label, font=('Arial', 10), bg=BG, fg=FG,
                 width=10, anchor='w').pack(side=tk.LEFT)
        tk.Label(row, text=valor, font=('Arial', 10, 'bold'), bg=BG, fg=color,
                 width=14, anchor='w').pack(side=tk.LEFT)
        tk.Label(row, text=estado, font=('Arial', 9), bg=BG, fg=color).pack(side=tk.LEFT)
