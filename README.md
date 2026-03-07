# 🚑 Gemelo Digital de Ambulancia — GemeloAmbulaciaV2

> **Simulación inteligente y monitorización en tiempo real de una ambulancia urbana mediante gemelo digital, IA y algoritmos de ruta óptima**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/UI-Tkinter-lightgrey?logo=python)](https://docs.python.org/3/library/tkinter.html)
[![Matplotlib](https://img.shields.io/badge/Visualización-Matplotlib-orange?logo=matplotlib)](https://matplotlib.org/)
[![OpenStreetMap](https://img.shields.io/badge/Mapa-OpenStreetMap-green?logo=openstreetmap)](https://www.openstreetmap.org/)
[![XGBoost](https://img.shields.io/badge/IA-XGBoost-red)](https://xgboost.readthedocs.io/)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn)](https://scikit-learn.org/)
[![Estado](https://img.shields.io/badge/Estado-En%20desarrollo-yellow)]()

---

## 📋 Descripción

**GemeloAmbulaciaV2** es un gemelo digital de ambulancia desarrollado para la ciudad de **León (España)**. El sistema simula de forma fiel el comportamiento real de una ambulancia en servicio, integrando:

- 🗺️ **Navegación urbana real** sobre el grafo vial de León (OSM) con 2.627 nodos y 5.004 aristas
- 🏥 **Selección automática del hospital más cercano** mediante algoritmos de ruta óptima (Dijkstra, A\*, Contraction Hierarchies)
- 🤖 **Predicción de fallos del motor** en tiempo real con un modelo XGBoost optimizado genéticamente
- 💓 **Monitorización de constantes vitales** del paciente con alertas semafóricas
- 🚗 **Vista del conductor** con instrucciones de navegación paso a paso

### Problema que resuelve

En emergencias médicas, cada segundo cuenta. Este sistema permite:
1. Calcular en milisegundos la ruta óptima evitando cuellos de botella
2. Detectar con antelación fallos mecánicos que puedan comprometer el traslado
3. Proporcionar al equipo médico información vital del paciente durante el trayecto

---

## 🖥️ Capturas de pantalla

La aplicación cuenta con tres vistas principales, cada una orientada a un rol diferente:

| Vista | Descripción |
|-------|-------------|
| 🗺️ **Vista Mapa** | Visualización en tiempo real del grafo de la ciudad de León con la ruta activa, posición de la ambulancia, paciente y hospitales marcados. Los iconos se encuentran en `Vista/assets/`. |
| 🚑 **Vista Conductor** | Panel de navegación paso a paso con flechas de dirección, nombre de las calles, distancia restante y selector de algoritmo de ruta (Dijkstra / A\* / CH). |
| 🏥 **Vista Médico** | Monitorización de constantes vitales del paciente (FC, SpO₂, FR, PA) con semáforos de alerta en tiempo real y selección de afección. |

> Los iconos de ambulancia, hospital y paciente están disponibles en `Vista/assets/ambulancia.png`, `Vista/assets/hospital.png` y `Vista/assets/paciente.png`.

---

## 🏗️ Arquitectura del sistema

El proyecto sigue el patrón **MV (Modelo–Vista)** estructurado por capas:

```
┌──────────────────────────────────────────────────────┐
│                      VISTA (UI)                      │
│  vista_mapa.py │ vista_conductor.py │ vista_medico.py│
└────────────────────────┬─────────────────────────────┘
                         │  eventos / callbacks
┌────────────────────────▼────────────────────────────┐
│                    main.py                          │
└────────────────────────┬────────────────────────────┘
                         │  llama a
┌────────────────────────▼────────────────────────────┐
│                      MODELO                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Map /       │  │  Prediccion/ │  │ Paciente/ │  │
│  │  Algoritmos  │  │  Motor (IA)  │  │ Vitales   │  │
│  └──────────────┘  └──────────────┘  └───────────┘  │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Persistencia │  │ Visualización│                 │
│  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del proyecto

```
GemeloAmbulaciaV2/
├── main.py                          # Punto de entrada y controlador principal
├── requirements.txt                 # Dependencias del proyecto
├── testModel.py                     # Tests del modelo
│
├── Model/                           # Capa de modelo (lógica de negocio)
│   ├── MainModel.py                 # Modelo principal
│   ├── model_ambulance.py           # Modelo de la ambulancia
│   ├── fisical_ambulance.py         # Simulación física
│   │
│   ├── Map/                         # Grafo vial y algoritmos de ruta
│   │   └── ...                      # Dijkstra, A*, Contraction Hierarchies
│   │
│   ├── Prediccion/                  # Módulo de predicción (IA motor)
│   │   └── ...
│   │
│   ├── Persistencia/                # Carga/guardado de datos
│   │   └── ...
│   │
│   ├── Visualizacion/               # Lógica de renderizado del mapa
│   │   └── ...
│   │
│   ├── datosGPS/                    # Datos de posicionamiento GPS
│   │
│   ├── datosPaciente/               # Datos y simulación de constantes vitales
│   │
│   └── datosMotor/                  # Módulo de motor de la ambulancia
│       ├── engine_simulation.py     # Simulación del motor en tiempo real
│       ├── testEngine.py            # Tests del motor
│       └── datasetMotor/
│           ├── engine_failure_dataset.csv        # Dataset de fallos del motor
│           └── entrenamientomodelomotor.py       # ⭐ Script de entrenamiento IA
│
└── Vista/                           # Capa de vista (interfaz gráfica)
    ├── __init__.py
    ├── theme.py                     # Tema visual de la aplicación
    ├── vista_mapa.py                # Vista del mapa urbano
    ├── vista_conductor.py           # Vista del conductor
    ├── vista_medico.py              # Vista del médico
    └── assets/
        ├── ambulancia.png           # Icono de la ambulancia
        ├── hospital.png             # Icono de hospital
        └── paciente.png             # Icono del paciente
```

---

## 🤖 Módulo de Inteligencia Artificial

### Predicción de fallos del motor

El sistema incorpora un módulo de IA capaz de **predecir en tiempo real si el motor de la ambulancia va a fallar**, permitiendo alertar al equipo y tomar medidas preventivas antes de que ocurra una avería durante un traslado crítico.

#### 📊 Dataset

| Parámetro | Valor |
|-----------|-------|
| Muestras totales | ~20.000 |
| Features | 6 |
| Variable objetivo | `Engine Condition` (0 = OK, 1 = Fallo) |
| Distribución | ~12.000 sin fallo / ~8.000 con fallo |

**Features utilizadas:**

| Feature | Descripción |
|---------|-------------|
| `Engine rpm` | Revoluciones por minuto del motor |
| `Lub oil pressure` | Presión del aceite de lubricación |
| `Fuel pressure` | Presión del combustible |
| `Coolant pressure` | Presión del refrigerante |
| `lub oil temp` | Temperatura del aceite de lubricación |
| `Coolant temp` | Temperatura del refrigerante |

#### 🔧 Pipeline de preprocesamiento

1. **Análisis exploratorio** — distribución de clases, box plots, histogramas
2. **Eliminación de outliers por IQR** — para cada feature numérica, se eliminan muestras fuera del rango `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]`
3. **Normalización** — `StandardScaler` antes del entrenamiento de XGBoost
4. **Balanceo de clases** — `RandomOverSampler` para MLP

#### 🏆 Modelos evaluados

| Modelo | Observaciones |
|--------|--------------|
| Logistic Regression | Línea base, rendimiento moderado |
| Decision Tree | Rápido, tendencia a sobreajuste |
| Random Forest | Robusto, buena generalización |
| SelfTraining Classifier | Aprendizaje semi-supervisado |
| KMeans | No supervisado, referencia |
| MLP Classifier | Red neuronal con datos balanceados |
| MLP Regressor | Variante de regresión con umbral 0.5 |
| **XGBoost** ⭐ | **Mejor resultado — AUC ≈ 0.70** |

#### 🧬 Optimización genética de hiperparámetros

Se implementó un **algoritmo genético propio** para optimizar los hiperparámetros de XGBoost:

```
Población inicial: 15 individuos aleatorios
Generaciones:      10
Selección:         Torneo (k=3)
Cruce:             Uniforme (prob. 0.5 por hiperparámetro)
Mutación:          Aleatoria (prob. 0.2 por hiperparámetro)
Elitismo:          2 mejores pasan directamente
Evaluación:        Cross-validation AUC (3 folds)
```

**Hiperparámetros optimizados:**
`n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`, `gamma`, `reg_alpha`, `reg_lambda`

#### 📈 Resultado final

> **AUC ≈ 0.70** — Este es el techo real del dataset con 6 features. Ningún modelo, por complejo que sea, puede superarlo significativamente con la información disponible.

El umbral de clasificación se optimiza mediante la curva ROC (punto de máximo `TPR − FPR`), priorizando la detección de fallos reales (minimizar falsos negativos en un contexto crítico).

📄 **Script de entrenamiento:** [`Model/datosMotor/datasetMotor/entrenamientomodelomotor.py`](Model/datosMotor/datasetMotor/entrenamientomodelomotor.py)

---

## 🛠️ Tecnologías

| Categoría | Tecnología |
|-----------|-----------|
| Lenguaje | Python 3.10+ |
| Interfaz gráfica | Tkinter + ttkthemes |
| Visualización | Matplotlib, Seaborn |
| Mapa urbano | OpenStreetMap (OSMnx) |
| Machine Learning | scikit-learn, XGBoost, imbalanced-learn |
| Análisis de datos | Pandas, NumPy |
| Imágenes | Pillow |

---

## ⚙️ Instalación y uso

### Prerrequisitos

- Python 3.10 o superior
- pip

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/mramog04/GemeloAmbulaciaV2.git
cd GemeloAmbulaciaV2

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
# Lanzar la aplicación principal
python main.py
```

### Entrenamiento del modelo de motor (Google Colab)

El script de entrenamiento está preparado para ejecutarse en **Google Colab** con el dataset `engine_data.csv`:

```bash
# Abrir el script en Colab o ejecutarlo localmente con:
python Model/datosMotor/datasetMotor/entrenamientomodelomotor.py
```

---

## 🏥 Hospitales del grafo de León

La aplicación contempla 4 hospitales reales de la ciudad de León como nodos destino del grafo:

| Hospital | Descripción |
|----------|-------------|
| Hospital de León (CAULE) | Hospital universitario de referencia |
| Centro de salud armunia | Centro de atención primaria |
| Hospital San Juan de Dios | Hospital privado en el centro |
| Centro de Salud La Condesa | Centro de atención primaria |

---

## 🗺️ Algoritmos de ruta

| Algoritmo | Complejidad | Ventaja |
|-----------|------------|---------|
| **Dijkstra** | O((V + E) log V) | Exacto, sencillo de implementar |
| **A\*** | O(E) en media | Más rápido con heurística admisible |
| **Contraction Hierarchies (CH)** | O(V log V) preproceso | Consultas en microsegundos |

---

## 📊 Datos del grafo urbano de León

| Métrica | Valor |
|---------|-------|
| Nodos | 2.627 |
| Aristas | 5.004 |
| Completitud | 100% |
| Fuente | OpenStreetMap |

---

## 📄 Licencia y autoría

Proyecto desarrollado con fines académicos y de concurso.

**Autores:** Equipo TuxMasters — Universidad de León  
**Año:** 2024–2025