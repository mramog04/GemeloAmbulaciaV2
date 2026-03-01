import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from Model.Visualizacion.app_state import FaseSimulacion

_EMPTY_OFFSETS = np.empty((0, 2))


class VentanaMapa(tk.Toplevel):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state
        self.title("Mapa - Gemelo Digital Ambulancia")
        self.geometry("900x700")
        self.protocol("WM_DELETE_WINDOW", master.destroy)

        road = state.model.road

        # Build figure
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.ax.set_aspect('equal')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_facecolor('#f8f8f8')
        self.ax.set_title("Mapa - Gemelo Digital Ambulancia")

        # Draw static edges (once)
        for edge in road.all_edges:
            x = [edge.origin.lon, edge.destination.lon]
            y = [edge.origin.lat, edge.destination.lat]
            self.ax.plot(x, y, color='#cccccc', linewidth=0.4, zorder=1)

        # Draw static hospitals (once)
        for node in road.get_hospitals():
            self.ax.scatter(node.lon, node.lat,
                            marker='*', color='red', s=180, zorder=5)
            name = node.hospital.name[:15] if node.hospital else ""
            self.ax.annotate(name, (node.lon, node.lat),
                             textcoords="offset points", xytext=(4, 4),
                             fontsize=6, color='darkred', zorder=6)

        # Dynamic artists — route already travelled
        self._line_past, = self.ax.plot([], [], color='#aaaaaa', alpha=0.5,
                                        linewidth=2.5, zorder=3)
        # Dynamic artists — active route ahead
        self._line_route, = self.ax.plot([], [], color='#0055ff', alpha=0.4,
                                         linewidth=2.5, zorder=4)
        # Ambulance scatter
        self._scat_amb = self.ax.scatter([], [], marker='^', color='#0055ff',
                                         s=150, zorder=10)
        # Patient scatter
        self._scat_pac = self.ax.scatter([], [], marker='o', color='#ff6600',
                                         s=120, zorder=9)
        # Hospital destino scatter
        self._scat_hdest = self.ax.scatter([], [], marker='*', color='#00cc44',
                                           s=300, zorder=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Register listener
        state.registrar_listener(self.actualizar)
        self.actualizar()

    # ------------------------------------------------------------------
    def actualizar(self):
        state = self.state
        road = state.model.road

        # Ambulance position
        nodo_actual = state.model.posicion.nodo_actual
        node_obj = road.get_node(nodo_actual)
        if node_obj:
            self._scat_amb.set_offsets([[node_obj.lon, node_obj.lat]])
        else:
            self._scat_amb.set_offsets(_EMPTY_OFFSETS)

        # Patient marker
        if state.fase in (FaseSimulacion.YENDO_A_PACIENTE, FaseSimulacion.EN_PACIENTE) \
                and state.nodo_paciente:
            pac_node = road.get_node(state.nodo_paciente)
            if pac_node:
                self._scat_pac.set_offsets([[pac_node.lon, pac_node.lat]])
            else:
                self._scat_pac.set_offsets(_EMPTY_OFFSETS)
        else:
            self._scat_pac.set_offsets(_EMPTY_OFFSETS)

        # Hospital destino marker
        if state.fase == FaseSimulacion.YENDO_A_HOSPITAL and state.hospital_destino_node_id:
            h_node = road.get_node(state.hospital_destino_node_id)
            if h_node:
                self._scat_hdest.set_offsets([[h_node.lon, h_node.lat]])
            else:
                self._scat_hdest.set_offsets(_EMPTY_OFFSETS)
        else:
            self._scat_hdest.set_offsets(_EMPTY_OFFSETS)

        # Route lines
        nodes = state.ruta_activa_nodes
        if nodes:
            all_nodes = [nodo_actual] + list(nodes)
            idx = state.ruta_idx

            # Past segment: from start to ruta_idx
            past_nodes = all_nodes[:idx + 1]
            if len(past_nodes) >= 2:
                past_objs = [road.get_node(n) for n in past_nodes]
                lons_p = [nd.lon for nd in past_objs if nd]
                lats_p = [nd.lat for nd in past_objs if nd]
                self._line_past.set_data(lons_p, lats_p)
            else:
                self._line_past.set_data([], [])

            # Ahead segment: from ruta_idx to end
            ahead_nodes = all_nodes[idx:]
            if len(ahead_nodes) >= 2:
                ahead_objs = [road.get_node(n) for n in ahead_nodes]
                lons_a = [nd.lon for nd in ahead_objs if nd]
                lats_a = [nd.lat for nd in ahead_objs if nd]
                self._line_route.set_data(lons_a, lats_a)
            else:
                self._line_route.set_data([], [])
        else:
            self._line_past.set_data([], [])
            self._line_route.set_data([], [])

        self.canvas.draw_idle()