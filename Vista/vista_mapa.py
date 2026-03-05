import os
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from Model.Visualizacion.app_state import FaseSimulacion
from Vista import theme

_EMPTY_OFFSETS = np.empty((0, 2))
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


def _load_offset_image(path, zoom=0.5):
    """Load a PNG as an OffsetImage; returns None on failure."""
    try:
        img = plt.imread(path)
        return OffsetImage(img, zoom=zoom)
    except Exception:
        return None


class VentanaMapa(tk.Toplevel):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state
        self.title("Mapa - Gemelo Digital Ambulancia")
        self.geometry("900x700")
        self.configure(bg=theme.BG)
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        road = state.model.road

        # Try loading PNG icons (cached data for reuse)
        self._img_amb = _load_offset_image(os.path.join(_ASSETS_DIR, "ambulancia.png"), zoom=0.45)
        self._img_pac = _load_offset_image(os.path.join(_ASSETS_DIR, "paciente.png"), zoom=0.45)
        self._img_hdest = _load_offset_image(os.path.join(_ASSETS_DIR, "hospital.png"), zoom=0.45)

        # Cache raw image arrays for efficient OffsetImage creation during updates
        self._raw_amb = self._img_amb.get_data() if self._img_amb is not None else None
        self._raw_pac = self._img_pac.get_data() if self._img_pac is not None else None
        self._raw_hdest = self._img_hdest.get_data() if self._img_hdest is not None else None

        # Build figure with dark theme
        self.fig, self.ax = plt.subplots(figsize=(9, 6.5))
        self.fig.patch.set_facecolor(theme.BG_CARD)
        self.ax.set_facecolor(theme.BG_CARD)
        self.ax.set_aspect('equal')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title("Mapa - Gemelo Digital Ambulancia",
                          color=theme.FG, fontsize=10, pad=6)
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        # Draw static edges (once)
        for edge in road.all_edges:
            x = [edge.origin.lon, edge.destination.lon]
            y = [edge.origin.lat, edge.destination.lat]
            self.ax.plot(x, y, color='#555555', linewidth=0.4, zorder=1)

        # Draw static hospitals (once)
        for node in road.get_hospitals():
            self.ax.scatter(node.lon, node.lat,
                            marker='*', color='#ff6666', s=180, zorder=5,
                            label='_nolegend_')
            name = node.hospital.name[:15] if node.hospital else ""
            self.ax.annotate(name, (node.lon, node.lat),
                             textcoords="offset points", xytext=(4, 4),
                             fontsize=6, color='#ff9999', zorder=6)

        # Dynamic artists — route already travelled
        self._line_past, = self.ax.plot([], [], color='#888888', alpha=0.6,
                                        linewidth=2.5, zorder=3,
                                        label='Ruta recorrida')
        # Dynamic artists — active route ahead
        self._line_route, = self.ax.plot([], [], color=theme.ACCENT, alpha=0.5,
                                         linewidth=2.5, zorder=4,
                                         label='Ruta pendiente')

        # AnnotationBbox artists for PNG icons (or scatter fallback)
        self._artist_amb = None
        self._artist_pac = None
        self._artist_hdest = None

        # Scatter fallbacks when PNGs unavailable
        if self._img_amb is None:
            self._scat_amb = self.ax.scatter([], [], marker='^', color=theme.ACCENT,
                                             s=150, zorder=10, label='Ambulancia')
        else:
            self._scat_amb = None

        if self._img_pac is None:
            self._scat_pac = self.ax.scatter([], [], marker='o', color=theme.WARNING,
                                             s=120, zorder=9, label='Paciente')
        else:
            self._scat_pac = None

        if self._img_hdest is None:
            self._scat_hdest = self.ax.scatter([], [], marker='*', color=theme.SUCCESS,
                                               s=300, zorder=10, label='Hospital destino')
        else:
            self._scat_hdest = None

        # Legend (dark style)
        legend_handles = [self._line_route, self._line_past]
        if self._scat_amb is not None:
            legend_handles.append(self._scat_amb)
        if self._scat_pac is not None:
            legend_handles.append(self._scat_pac)
        if self._scat_hdest is not None:
            legend_handles.append(self._scat_hdest)

        self.ax.legend(handles=legend_handles,
                       facecolor='#3c3f41', labelcolor=theme.FG,
                       edgecolor='#555555', fontsize=7,
                       loc='lower right')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Status bar below canvas
        self._status_label = ttk.Label(self, text="Fase: Iniciando...",
                                       anchor='w')
        self._status_label.pack(fill='x', padx=6, pady=2)

        # Register listener
        state.registrar_listener(self.actualizar)
        self.actualizar()

    # ------------------------------------------------------------------
    def _place_icon(self, img_offset, lon, lat, label, existing):
        """Remove old AnnotationBbox and place a new one at (lon, lat)."""
        if existing is not None:
            try:
                existing.remove()
            except Exception:
                pass
        ab = AnnotationBbox(img_offset, (lon, lat),
                            frameon=False, zorder=10,
                            box_alignment=(0.5, 0.5),
                            label=label)
        self.ax.add_artist(ab)
        return ab

    # ------------------------------------------------------------------
    def actualizar(self):
        state = self.state
        road = state.model.road

        # Update status bar
        fase_names = {
            FaseSimulacion.INICIO: "Inicio",
            FaseSimulacion.YENDO_A_PACIENTE: "Yendo al paciente",
            FaseSimulacion.EN_PACIENTE: "En paciente",
            FaseSimulacion.YENDO_A_HOSPITAL: "Yendo al hospital",
            FaseSimulacion.FIN: "Fin",
        }
        self._status_label.config(text=f"Fase: {fase_names.get(state.fase, str(state.fase))}")

        # Ambulance position
        nodo_actual = state.model.posicion.nodo_actual
        node_obj = road.get_node(nodo_actual)
        if node_obj:
            lon, lat = node_obj.lon, node_obj.lat
            if self._img_amb is not None:
                self._artist_amb = self._place_icon(
                    OffsetImage(self._raw_amb, zoom=0.45),
                    lon, lat, 'Ambulancia', self._artist_amb)
            else:
                self._scat_amb.set_offsets([[lon, lat]])
        else:
            if self._img_amb is None:
                self._scat_amb.set_offsets(_EMPTY_OFFSETS)

        # Patient marker
        if state.fase in (FaseSimulacion.YENDO_A_PACIENTE, FaseSimulacion.EN_PACIENTE) \
                and state.nodo_paciente:
            pac_node = road.get_node(state.nodo_paciente)
            if pac_node:
                lon, lat = pac_node.lon, pac_node.lat
                if self._img_pac is not None:
                    self._artist_pac = self._place_icon(
                        OffsetImage(self._raw_pac, zoom=0.45),
                        lon, lat, 'Paciente', self._artist_pac)
                else:
                    self._scat_pac.set_offsets([[lon, lat]])
            elif self._img_pac is None:
                self._scat_pac.set_offsets(_EMPTY_OFFSETS)
        else:
            if self._artist_pac is not None:
                try:
                    self._artist_pac.remove()
                except Exception:
                    pass
                self._artist_pac = None
            if self._img_pac is None:
                self._scat_pac.set_offsets(_EMPTY_OFFSETS)

        # Hospital destino marker
        if state.fase == FaseSimulacion.YENDO_A_HOSPITAL and state.hospital_destino_node_id:
            h_node = road.get_node(state.hospital_destino_node_id)
            if h_node:
                lon, lat = h_node.lon, h_node.lat
                if self._img_hdest is not None:
                    self._artist_hdest = self._place_icon(
                        OffsetImage(self._raw_hdest, zoom=0.45),
                        lon, lat, 'Hospital destino', self._artist_hdest)
                else:
                    self._scat_hdest.set_offsets([[lon, lat]])
            elif self._img_hdest is None:
                self._scat_hdest.set_offsets(_EMPTY_OFFSETS)
        else:
            if self._artist_hdest is not None:
                try:
                    self._artist_hdest.remove()
                except Exception:
                    pass
                self._artist_hdest = None
            if self._img_hdest is None:
                self._scat_hdest.set_offsets(_EMPTY_OFFSETS)

        # Route lines — fix ghost line on phase transition
        nodes = state.ruta_activa_nodes
        idx = state.ruta_idx

        if nodes and idx > 0:
            # Past: nodos ya recorridos
            past_nodes = nodes[:idx]
            if len(past_nodes) >= 2:
                past_objs = [road.get_node(n) for n in past_nodes]
                lons_p = [nd.lon for nd in past_objs if nd]
                lats_p = [nd.lat for nd in past_objs if nd]
                self._line_past.set_data(lons_p, lats_p)
            else:
                self._line_past.set_data([], [])
        else:
            self._line_past.set_data([], [])

        if nodes and idx < len(nodes):
            # Ahead: nodos pendientes
            ahead_nodes = nodes[idx:]
            if len(ahead_nodes) >= 2:
                ahead_objs = [road.get_node(n) for n in ahead_nodes]
                lons_a = [nd.lon for nd in ahead_objs if nd]
                lats_a = [nd.lat for nd in ahead_objs if nd]
                self._line_route.set_data(lons_a, lats_a)
            else:
                self._line_route.set_data([], [])
        else:
            self._line_route.set_data([], [])

        self.canvas.draw_idle()