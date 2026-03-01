import random
import tkinter as tk
from tkinter import ttk, messagebox

from Model.MainModel import Model
from Model.Visualizacion.afecciones_db import AFECCIONES_DB
from Model.Visualizacion.app_state import AppState, FaseSimulacion
from Model.Visualizacion.node_selector import seleccionar_nodos_paciente
from Model.Visualizacion.route_utils import calcular_rutas_por_algoritmo
from Vista.vista_mapa import VentanaMapa
from Vista.vista_conductor import VentanaConductor
from Vista.vista_medico import VentanaMedico


def _do_tick(state):
    """Ejecuta un paso de avance de la simulación."""
    if state.ruta_activa_nodes and state.ruta_idx < len(state.ruta_activa_nodes):
        next_node = state.ruta_activa_nodes[state.ruta_idx]
        state.model.mover_ambulancia_a(next_node)
        state.model.tick()
        state.ruta_idx += 1
        state.notificar()

        if state.ruta_idx >= len(state.ruta_activa_nodes):
            if state.fase == FaseSimulacion.YENDO_A_PACIENTE:
                state.cambiar_fase(FaseSimulacion.EN_PACIENTE)
            elif state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
                state.cambiar_fase(FaseSimulacion.FIN)


def iniciar_simulacion(root, nombre, afeccion, modo_auto):
    """Crea el modelo, el estado y abre las 3 ventanas."""
    # 1. Build model
    model = Model(
        roadnetwork_dir='Model/Map/leon_graph',
        engine_data_path='Model/datosMotor/datasetMotor/engine_failure_dataset.csv'
    )
    model.paciente.nombre = nombre

    # 2. Build AppState
    state = AppState()
    state.model = model
    state.nombre_paciente = nombre
    state.afeccion_paciente = afeccion
    state.modo_automatico = modo_auto

    # 3. Select patient node
    nodos = seleccionar_nodos_paciente(model.road, 30)
    state.nodo_paciente = random.choice(nodos)

    # 4. Calculate initial routes
    state.rutas_disponibles = calcular_rutas_por_algoritmo(
        model.road,
        model.posicion.nodo_actual,
        state.nodo_paciente
    )

    # 5. Set phase
    state.cambiar_fase(FaseSimulacion.YENDO_A_PACIENTE)

    # 6. Open windows
    def tick_manual():
        _do_tick(state)

    ventana_mapa = VentanaMapa(root, state)
    ventana_conductor = VentanaConductor(root, state, tick_manual)
    ventana_medico = VentanaMedico(root, state)

    # 7. Tick loop
    def tick_loop():
        if state.modo_automatico:
            _do_tick(state)
        root.after(state.tick_interval_ms, tick_loop)

    root.after(state.tick_interval_ms, tick_loop)

    # 8. Nueva misión handler
    def nueva_mision(event=None):
        ventana_mapa.destroy()
        ventana_conductor.destroy()
        ventana_medico.destroy()
        root.deiconify()

    root.bind("<<NuevaMision>>", nueva_mision)


def main():
    root = tk.Tk()
    root.title("🚑 Gemelo Digital — Configuración")
    root.geometry("400x350")
    root.resizable(False, False)

    # ── Nombre del paciente ──────────────────────────────────────
    tk.Label(root, text="Nombre del paciente:", font=("Arial", 11)).pack(pady=(20, 4))
    entry_nombre = tk.Entry(root, font=("Arial", 11), width=30)
    entry_nombre.pack()

    # ── Afección ─────────────────────────────────────────────────
    tk.Label(root, text="Afección:", font=("Arial", 11)).pack(pady=(12, 4))
    combo_afeccion = ttk.Combobox(root, values=list(AFECCIONES_DB.keys()),
                                  state='readonly', width=34, font=("Arial", 10))
    combo_afeccion.pack()
    if AFECCIONES_DB:
        combo_afeccion.current(0)

    # ── Modo ─────────────────────────────────────────────────────
    tk.Label(root, text="Modo de ejecución:", font=("Arial", 11)).pack(pady=(12, 4))
    modo_var = tk.StringVar(value="manual")
    mode_frame = tk.Frame(root)
    mode_frame.pack()
    tk.Radiobutton(mode_frame, text="🔄 Automático", variable=modo_var,
                   value="auto", font=("Arial", 10)).pack(side='left', padx=10)
    tk.Radiobutton(mode_frame, text="🖱️ Manual", variable=modo_var,
                   value="manual", font=("Arial", 10)).pack(side='left', padx=10)

    # ── Botón iniciar ─────────────────────────────────────────────
    def on_iniciar():
        nombre = entry_nombre.get().strip()
        afeccion = combo_afeccion.get()
        if not nombre:
            messagebox.showwarning("Validación", "Por favor, introduce el nombre del paciente.")
            return
        if not afeccion:
            messagebox.showwarning("Validación", "Por favor, selecciona una afección.")
            return
        modo_auto = (modo_var.get() == "auto")
        root.withdraw()
        iniciar_simulacion(root, nombre, afeccion, modo_auto)

    tk.Button(root, text="▶ INICIAR SIMULACIÓN", command=on_iniciar,
              font=("Arial", 12, "bold"), bg='#0055ff', fg='white',
              padx=14, pady=8).pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()
