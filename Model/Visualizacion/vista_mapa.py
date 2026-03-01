import tkinter as tk
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Model.Visualizacion.app_state import AppState, FaseSimulacion


class VentanaMapa:
    """Ventana de mapa con fondo estático y elementos dinámicos."""

    def __init__(self, root: tk.Tk, state: AppState):
        self.state = state
        self.win = tk.Toplevel(root)
        self.win.title("🗺️ Vista de Mapa — Gemelo Digital Ambulancia")
        self.win.geometry("900x700")
        self.win.protocol("WM_DELETE_WINDOW", root.quit)

        self._construir_figura()
        self._dibujar_fondo()
        self._crear_dinamicos()

        state.registrar_listener(self.actualizar)

    # ------------------------------------------------------------------ #
    # Construcción inicial                                                  #
    # ------------------------------------------------------------------ #

    def _construir_figura(self):
        frame = tk.Frame(self.win)
        frame.pack(fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(9, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.fig.tight_layout(pad=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _dibujar_fondo(self):
        """Dibuja aristas y hospitales una sola vez."""
        road = self.state.model.road
        ax = self.ax

        # Aristas grises finas
        for edge in road.all_edges:
            lats = [edge.origin.lat, edge.destination.lat]
            lons = [edge.origin.lon, edge.destination.lon]
            ax.plot(lons, lats, color='#cccccc', linewidth=0.4, zorder=1)

        # Hospitales: estrella roja
        for node in road.get_hospitals():
            ax.scatter(node.lon, node.lat,
                       marker='*', color='red', s=200, zorder=5)
            nombre_corto = node.hospital.name.split('-')[0].strip()[:15]
            ax.annotate(nombre_corto, xy=(node.lon, node.lat),
                        fontsize=5, color='darkred', zorder=6,
                        ha='center', va='bottom')

    def _crear_dinamicos(self):
        """Crea los artistas dinámicos con posiciones vacías."""
        ax = self.ax

        # Ambulancia
        self._sc_ambu = ax.scatter([], [], marker='^', color='#0055ff',
                                   s=150, zorder=10, label='Ambulancia')

        # Paciente
        self._sc_paci = ax.scatter([], [], marker='o', color='#ff6600',
                                   s=120, zorder=9, label='Paciente')

        # Ruta activa (línea azul)
        self._line_ruta, = ax.plot([], [], color='#0055ff', alpha=0.5,
                                   linewidth=2, zorder=3)

        # Hospital destino
        self._sc_hosp_dest = ax.scatter([], [], marker='*', color='#00aa00',
                                        s=250, zorder=8, label='Destino')

        ax.legend(loc='upper right', fontsize=7, markerscale=0.8)

    # ------------------------------------------------------------------ #
    # Actualización dinámica                                               #
    # ------------------------------------------------------------------ #

    def actualizar(self):
        state = self.state
        model = state.model
        road = model.road

        # Posición ambulancia
        nodo_ambu = model.posicion.nodo_actual
        node_obj = road.get_node(nodo_ambu)
        if node_obj:
            self._sc_ambu.set_offsets([[node_obj.lon, node_obj.lat]])
        else:
            self._sc_ambu.set_offsets(np.empty((0, 2)))

        # Paciente (visible en fases yendo y en_paciente)
        if state.fase in (FaseSimulacion.YENDO_A_PACIENTE, FaseSimulacion.EN_PACIENTE) \
                and state.nodo_paciente is not None:
            np_node = road.get_node(state.nodo_paciente)
            if np_node:
                self._sc_paci.set_offsets([[np_node.lon, np_node.lat]])
            else:
                self._sc_paci.set_offsets(np.empty((0, 2)))
        else:
            self._sc_paci.set_offsets(np.empty((0, 2)))

        # Ruta activa
        if state.ruta_activa:
            lons, lats = [], []
            for nid in state.ruta_activa:
                n = road.get_node(nid)
                if n:
                    lons.append(n.lon)
                    lats.append(n.lat)
            self._line_ruta.set_data(lons, lats)
        else:
            self._line_ruta.set_data([], [])

        # Hospital destino
        if state.fase == FaseSimulacion.YENDO_A_HOSPITAL \
                and state.hospital_destino_node_id is not None:
            hn = road.get_node(state.hospital_destino_node_id)
            if hn:
                self._sc_hosp_dest.set_offsets([[hn.lon, hn.lat]])
            else:
                self._sc_hosp_dest.set_offsets(np.empty((0, 2)))
        else:
            self._sc_hosp_dest.set_offsets(np.empty((0, 2)))

        self.canvas.draw_idle()
