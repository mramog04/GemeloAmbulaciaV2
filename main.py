import random
import tkinter as tk
from tkinter import ttk

from Model.MainModel import Model
from Model.Visualizacion.afecciones_db import AFECCIONES_DB
from Model.Visualizacion.app_state import AppState, FaseSimulacion
from Model.Visualizacion.node_selector import seleccionar_nodos_paciente
from Model.Visualizacion.vista_mapa import VentanaMapa
from Model.Visualizacion.vista_conductor import VentanaConductor
from Model.Visualizacion.vista_medico import VentanaMedico

ROADNETWORK_DIR = 'Model/Map/leon_graph'
ENGINE_DATA_PATH = 'Model/datosMotor/datasetMotor/engine_failure_dataset.csv'


# ============================================================================
# Pantalla de inicio
# ============================================================================

def mostrar_inicio(root: tk.Tk, state: AppState):
    """Muestra la ventana de configuración inicial y devuelve el control."""
    root.title("🚑 Gemelo Digital — Configuración")
    root.resizable(False, False)

    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(frame, text="🚑 Gemelo Digital de Ambulancia",
             font=('Arial', 15, 'bold')).pack(pady=(0, 16))

    # Nombre del paciente
    tk.Label(frame, text="Nombre del paciente:", font=('Arial', 10)).pack(anchor='w')
    nombre_var = tk.StringVar(value="Carlos Sánchez")
    tk.Entry(frame, textvariable=nombre_var, font=('Arial', 10), width=30).pack(pady=(2, 10))

    # Afección
    tk.Label(frame, text="Afección:", font=('Arial', 10)).pack(anchor='w')
    afeccion_var = tk.StringVar()
    afecciones = list(AFECCIONES_DB.keys())
    combo = ttk.Combobox(frame, textvariable=afeccion_var, values=afecciones,
                          state='readonly', width=32, font=('Arial', 10))
    combo.current(0)
    combo.pack(pady=(2, 10))

    # Modo
    tk.Label(frame, text="Modo:", font=('Arial', 10)).pack(anchor='w')
    modo_var = tk.StringVar(value="manual")
    modos_frame = tk.Frame(frame)
    modos_frame.pack(anchor='w', pady=(2, 14))
    tk.Radiobutton(modos_frame, text="⚡ Automático", variable=modo_var,
                   value="auto", font=('Arial', 10)).pack(side=tk.LEFT, padx=4)
    tk.Radiobutton(modos_frame, text="🖱️ Manual", variable=modo_var,
                   value="manual", font=('Arial', 10)).pack(side=tk.LEFT, padx=4)

    resultado = {}

    def iniciar():
        resultado['nombre'] = nombre_var.get().strip() or "Paciente"
        resultado['afeccion'] = afeccion_var.get()
        resultado['modo_auto'] = (modo_var.get() == "auto")
        root.quit()

    tk.Button(frame, text="▶ INICIAR SIMULACIÓN", font=('Arial', 12, 'bold'),
              bg='#2980b9', fg='white', command=iniciar).pack(pady=8)

    root.mainloop()
    root.withdraw()
    return resultado


# ============================================================================
# Bucle de simulación
# ============================================================================

def crear_tick_loop(root: tk.Tk, state: AppState):
    """Devuelve la función tick que avanza la simulación un paso."""

    def tick_once():
        if state.ruta_activa and state.ruta_idx < len(state.ruta_activa):
            next_node = state.ruta_activa[state.ruta_idx]
            state.model.mover_ambulancia_a(next_node)
            state.model.tick()
            state.ruta_idx += 1
            state.notificar()

            if state.ruta_idx >= len(state.ruta_activa):
                if state.fase == FaseSimulacion.YENDO_A_PACIENTE:
                    state.cambiar_fase(FaseSimulacion.EN_PACIENTE)
                elif state.fase == FaseSimulacion.YENDO_A_HOSPITAL:
                    state.cambiar_fase(FaseSimulacion.FIN)

    def tick_loop():
        if state.modo_automatico:
            tick_once()
        root.after(state.tick_interval_ms, tick_loop)

    return tick_once, tick_loop


# ============================================================================
# Punto de entrada
# ============================================================================

def main():
    state = AppState()

    # --- Pantalla de inicio ---
    root = tk.Tk()
    config = mostrar_inicio(root, state)

    if not config:
        return

    state.nombre_paciente = config['nombre']
    state.afeccion_paciente = config['afeccion']
    state.modo_automatico = config['modo_auto']

    # --- Crear modelo ---
    model = Model(
        roadnetwork_dir=ROADNETWORK_DIR,
        engine_data_path=ENGINE_DATA_PATH
    )
    model.paciente.nombre = state.nombre_paciente
    state.model = model

    # --- Seleccionar nodo del paciente ---
    nodos_candidatos = seleccionar_nodos_paciente(model.road, n=30)
    state.nodo_paciente = random.choice(nodos_candidatos)

    # --- Cambiar a fase inicial ---
    state.fase = FaseSimulacion.YENDO_A_PACIENTE

    # --- Abrir las 3 ventanas ---
    root.deiconify()
    root.withdraw()  # Ocultar la raíz; las Toplevels son las ventanas reales

    mapa_window = VentanaMapa(root, state)
    tick_once, tick_loop = crear_tick_loop(root, state)
    conductor_window = VentanaConductor(root, state, tick_callback=tick_once)
    medico_window = VentanaMedico(root, state)

    # Notificar estado inicial para pintar las ventanas
    state.notificar()

    # Arrancar el bucle automático
    root.after(state.tick_interval_ms, tick_loop)

    # Bucle principal de Tkinter
    root.mainloop()


if __name__ == "__main__":
    main()
